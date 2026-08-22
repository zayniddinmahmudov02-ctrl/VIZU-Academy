from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db

from app.models.user import User

from app.schemas.book import BookPublicResponse

from app.services.book import BookService

router = APIRouter(
    prefix="/books",
    tags=["Books"],
)


@router.get("", response_model=list[BookPublicResponse])
def list_books(
    level: str | None = None,
    db: Session = Depends(get_db),
):
    """Public, unauthenticated — same access rule as course/module/lesson
    listing (title/cover/level are meant to be visible to everyone,
    including free/logged-out visitors; only the PDF itself is
    Premium-gated). Published-only, and BookPublicResponse never
    includes storage_key."""
    service = BookService(db)
    books = service.get_published_by_level(level) if level else service.get_all()
    if level is None:
        books = [b for b in books if b.is_published]
    return books


@router.get("/{book_id}/file")
def get_book_file(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The only real way to fetch a book's PDF bytes — not a public URL,
    not the /uploads static mount. Re-checks published + Premium status
    on every single request (see BookService.get_downloadable_book) —
    a free user can never get the file here regardless of what any
    frontend state claims."""
    service = BookService(db)
    book = service.get_downloadable_book(book_id, current_user)
    path = service.resolve_pdf_path(book)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Book file missing on disk.")
    return FileResponse(path=path, media_type="application/pdf", filename=book.original_filename or "book.pdf")
