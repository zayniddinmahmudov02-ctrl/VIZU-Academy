from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserLanguage(BaseModel):
    """Which languages a user is learning — distinct from `Enrollment`
    (which tracks per-course progress state). This is the source of truth
    for "Learners" counts on the admin Language Management module; always
    aggregate via COUNT(DISTINCT user_id), never a raw row count, since a
    future feature could in principle add more than one row per user
    (there isn't one today — the unique constraint below prevents it, but
    the aggregation convention is kept literal per spec regardless)."""

    __tablename__ = "user_languages"
    __table_args__ = (
        UniqueConstraint("user_id", "language_id", name="uq_user_languages_user_language"),
    )

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    language = relationship("Language", back_populates="user_languages")
