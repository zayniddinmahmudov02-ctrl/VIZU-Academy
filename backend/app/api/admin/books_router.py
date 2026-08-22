from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db

from app.models.user import User

from app.schemas.book import BookCreate, BookResponse, BookUpdate

from app.services.book import BookService

router = APIRouter(
    prefix="/admin/books",
    tags=["Admin - Books"],
)


@router.get("", response_model=list[BookResponse])
def list_books(
    level: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return BookService(db).get_all(level=level)


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return BookService(db).create(payload.model_dump())


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    book = BookService(db).get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: UUID,
    payload: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = BookService(db)
    book = service.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return service.update(book, payload.model_dump(exclude_unset=True))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = BookService(db)
    book = service.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    await service.delete(book)


@router.post("/{book_id}/publish", response_model=BookResponse)
def publish_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = BookService(db)
    book = service.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return service.publish(book)


@router.post("/{book_id}/upload-pdf", response_model=BookResponse)
async def upload_book_pdf(
    book_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """The only way a book's storage_key can be set — there is no
    endpoint that accepts a client-supplied storage key, same rule as
    video uploads."""
    service = BookService(db)
    book = service.get(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return await service.upload_pdf(book, file)
