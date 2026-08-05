from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Language(BaseModel):
    """A language taught on the platform. Currently only German ('de') is
    seeded, but the schema is built for unlimited future languages —
    everything content-related hangs off `courses` (course.language_id),
    so adding a language is just inserting a row here."""

    __tablename__ = "languages"
    __table_args__ = (
        # Partial unique indexes, not plain unique constraints — a plain
        # UNIQUE(code) would permanently block re-using a code/locale after
        # its language is soft-deleted, since the deleted row's value would
        # still occupy the slot forever. Scoping to `deleted_at IS NULL`
        # means "unique among languages that still exist."
        Index("uq_languages_code_active", "code", unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("uq_languages_locale_active", "locale", unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("ix_languages_is_active", "is_active"),
        Index("ix_languages_deleted_at", "deleted_at"),
        Index("ix_languages_sort_order", "sort_order"),
    )

    code: Mapped[str] = mapped_column(String(10), nullable=False)
    locale: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    native_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    english_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # SVG filename only (e.g. "de.svg") — the file itself lives in the
    # frontend's public/flags/ directory, uploaded via a dedicated Next.js
    # route handler. Never a full URL: the frontend renders it as
    # `/flags/{flag_file}`.
    flag_file: Mapped[str | None] = mapped_column(String(255), nullable=True)

    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Soft delete — NULL means "not deleted". Enforced at the service layer
    # (every read filters `deleted_at.is_(None)`); deletion itself is only
    # allowed when the language has no learners, levels, or modules left.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    courses = relationship(
        "Course",
        back_populates="language",
        cascade="all, delete-orphan",
    )
    user_languages = relationship(
        "UserLanguage",
        back_populates="language",
        cascade="all, delete-orphan",
    )
    settings = relationship(
        "LanguageSettings",
        back_populates="language",
        uselist=False,
        cascade="all, delete-orphan",
    )
