from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

PURPOSE_REGISTRATION = "registration_verification"
PURPOSE_PASSWORD_RESET = "password_reset"
ALL_PURPOSES = (PURPOSE_REGISTRATION, PURPOSE_PASSWORD_RESET)


class EmailVerificationCode(BaseModel):
    """One 6-digit email code (registration verification or password reset).

    Only an HMAC of the code is stored (bound to user + purpose), never the
    code itself. A code is active while used_at and invalidated_at are both
    NULL; at most one active code exists per (user, purpose) — enforced by a
    partial unique index. Every wrong guess increments `attempts`; at the
    limit the code is invalidated."""

    __tablename__ = "email_verification_codes"
    __table_args__ = (
        Index(
            "uq_email_verification_codes_active",
            "user_id",
            "purpose",
            unique=True,
            postgresql_where=text("used_at IS NULL AND invalidated_at IS NULL"),
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Normalised (lower-case) address the code was sent to.
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
