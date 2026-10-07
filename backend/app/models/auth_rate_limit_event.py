from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuthRateLimitEvent(BaseModel):
    """One rate-limited auth action (code e-mail request, code check). Email
    and IP are stored only as keyed hashes (HMAC with SECRET_KEY) — enough to
    count, useless for anything else. Works across all server workers
    (database-backed). Rows older than a day are pruned opportunistically."""

    __tablename__ = "auth_rate_limit_events"
    __table_args__ = (
        Index("ix_auth_rate_limit_events_email", "action", "email_hash", "created_at"),
        Index("ix_auth_rate_limit_events_ip", "action", "ip_hash", "created_at"),
    )

    action: Mapped[str] = mapped_column(String(40), nullable=False)
    email_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
