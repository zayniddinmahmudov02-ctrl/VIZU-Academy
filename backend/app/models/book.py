from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

# A1-C1 — same CEFR range used throughout the platform (no C2 course
# level exists yet). Stored as a plain indexed string, matching how
# Course.level already works, rather than a DB enum — consistent with
# the rest of this codebase's level fields.
ALL_BOOK_LEVELS = {"A1", "A2", "B1", "B2", "C1"}


class Book(BaseModel):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Public — served straight from the existing public media_library
    # storage, same as any other admin-uploaded image. Fine to be public:
    # free students seeing a book's cover/title is the intended behavior,
    # only the PDF itself is Premium-gated.
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Never a URL — a path into ProtectedBookStorage, resolved only by
    # BookService.get_downloadable_book after a real auth+premium check.
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
