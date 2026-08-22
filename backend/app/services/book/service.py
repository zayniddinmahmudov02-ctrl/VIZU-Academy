"""Admin CRUD + PDF upload/serving for the Books/Bücher feature. Follows
this session's established "small service, no separate repository
layer" pattern (see section_gate.py, quiz_generation_service.py) rather
than the older Repository+Service split Video/Vocabulary use — simpler,
and there's no shared query logic here worth factoring out yet.

Security-critical: get_downloadable_book() is the ONLY way to resolve a
Book's PDF path, and it's the sole gate — 404 for missing/unpublished
(never reveals draft existence, same principle as
audio_service.authorize_audio_access), then requires
is_user_premium(user) or has_premium_bypass(user), else
403 PREMIUM_REQUIRED. The API layer never resolves a storage path any
other way."""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.storage.protected_local import ProtectedBookStorage
from app.models.book import Book
from app.models.user import User
from app.services.vizu_pay.access import has_premium_bypass, is_user_premium

storage = ProtectedBookStorage()

ALLOWED_PDF_CONTENT_TYPES = {"application/pdf"}
MAX_PDF_SIZE_BYTES = 200 * 1024 * 1024  # 200MB — generous for a scanned book


class BookService:
    def __init__(self, db: Session):
        self.db = db

    # ==========================
    # CRUD
    # ==========================

    def get_all(self, level: str | None = None) -> list[Book]:
        query = self.db.query(Book)
        if level is not None:
            query = query.filter(Book.level == level)
        return query.order_by(Book.order_index.asc(), Book.created_at.asc()).all()

    def get(self, book_id: UUID) -> Book | None:
        return self.db.get(Book, book_id)

    def get_published_by_level(self, level: str) -> list[Book]:
        return (
            self.db.query(Book)
            .filter(Book.level == level, Book.is_published.is_(True))
            .order_by(Book.order_index.asc(), Book.created_at.asc())
            .all()
        )

    def create(self, data: dict) -> Book:
        book = Book(**data)
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def update(self, book: Book, data: dict) -> Book:
        for key, value in data.items():
            setattr(book, key, value)
        self.db.commit()
        self.db.refresh(book)
        return book

    def publish(self, book: Book) -> Book:
        book.is_published = True
        self.db.commit()
        self.db.refresh(book)
        return book

    async def delete(self, book: Book) -> None:
        """Deletes the backing PDF file first — same ordering rationale
        as VideoService.delete: a leaked file is recoverable, a lost DB
        row referencing an already-deleted file is not."""
        if book.storage_key:
            await storage.delete(book.storage_key)
        self.db.delete(book)
        self.db.commit()

    # ==========================
    # PDF upload (admin)
    # ==========================

    async def upload_pdf(self, book: Book, file: UploadFile) -> Book:
        content_type = (file.content_type or "").split(";")[0].strip()
        if content_type not in ALLOWED_PDF_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type '{file.content_type}'. Only PDF is allowed.")

        contents = await file.read()
        if len(contents) > MAX_PDF_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"PDF exceeds the maximum upload size of {MAX_PDF_SIZE_BYTES // (1024 * 1024)}MB.",
            )
        await file.seek(0)

        # Replace semantics: uploading a new PDF for a book always
        # removes the previous file first, matching the same convention
        # audio_service.upload_audio / VideoService.replace_video use.
        if book.storage_key:
            await storage.delete(book.storage_key)

        unique_name = f"{uuid4().hex}.pdf"
        storage_key = f"{unique_name}"
        file.filename = unique_name
        await storage.upload(file, storage_key)

        book.storage_key = storage_key
        book.original_filename = file.filename
        self.db.commit()
        self.db.refresh(book)
        return book

    # ==========================
    # Secure access + serving
    # ==========================

    def resolve_pdf_path(self, book: Book) -> Path:
        return storage.ROOT / book.storage_key

    def get_downloadable_book(self, book_id: UUID, user: User) -> Book:
        book = self.get(book_id)
        if book is None or not book.is_published or not book.storage_key:
            # Never distinguishes "doesn't exist" from "exists but draft"
            # — same principle as audio_service.authorize_audio_access.
            raise HTTPException(status_code=404, detail="Book not found")

        if not (is_user_premium(user) or has_premium_bypass(user)):
            raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

        return book
