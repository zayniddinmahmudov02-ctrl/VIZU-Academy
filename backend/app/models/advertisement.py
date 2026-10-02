from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

EVENT_IMPRESSION = "impression"
EVENT_CLICK = "click"
ALL_EVENTS = {EVENT_IMPRESSION, EVENT_CLICK}


class Advertisement(BaseModel):
    """A dashboard "Werbung-Banner", managed in the admin panel.

    The image is a URL produced by the existing media-library upload
    (`/uploads/images/...`) — never base64 in the database. Of all
    advertisements that are active and inside their date range, the one
    with the HIGHEST `priority` is shown (ties: most recently updated)."""

    __tablename__ = "advertisements"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    cta_text: Mapped[str] = mapped_column(String(60), nullable=False, default="Mehr erfahren", server_default="Mehr erfahren")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdvertisementEvent(BaseModel):
    """One real impression or click. `user_id` is set for impressions (the
    dashboard is authenticated); clicks arrive as a plain browser navigation
    to the redirect endpoint, so they are attributed via `client_hash` (a
    hash of IP + user agent — no raw personal data) for de-duplication."""

    __tablename__ = "advertisement_events"

    advertisement_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("advertisements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
