from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

BTYPE_INFO = "INFO"
BTYPE_SUCCESS = "SUCCESS"
BTYPE_WARNING = "WARNING"
BTYPE_ANNOUNCEMENT = "ANNOUNCEMENT"
BROADCAST_TYPES = (BTYPE_INFO, BTYPE_SUCCESS, BTYPE_WARNING, BTYPE_ANNOUNCEMENT)

AUD_ALL = "ALL"  # every student
AUD_LEVEL = "LEVEL"  # students active in / owning a level (A1 ... C1)
AUD_LANGUAGE = "LANGUAGE"  # students by interface language (de / uz)
AUD_USER = "USER"  # one student (audience_value = user id)
AUDIENCES = (AUD_ALL, AUD_LEVEL, AUD_LANGUAGE, AUD_USER)

ST_DRAFT = "DRAFT"
ST_PUBLISHED = "PUBLISHED"  # visible once publish_at <= now (a future publish_at = scheduled)
ST_INACTIVE = "INACTIVE"  # taken down, can be published again
ST_ARCHIVED = "ARCHIVED"  # final; read history kept
STATUSES = (ST_DRAFT, ST_PUBLISHED, ST_INACTIVE, ST_ARCHIVED)

LINK_NONE = "NONE"
LINK_INTERNAL = "INTERNAL"
LINK_EXTERNAL = "EXTERNAL"


class BroadcastNotification(BaseModel):
    """An admin notification ("Benachrichtigung"). ONE row per message —
    never copied per student; who sees it is decided at read time from the
    audience, what each student has read lives in BroadcastNotificationRead.
    Texts are plain (rendered as text, never HTML)."""

    __tablename__ = "broadcast_notifications"
    __table_args__ = (Index("ix_broadcast_notifications_visible", "status", "publish_at"),)

    title_de: Mapped[str] = mapped_column(String(160), nullable=False)
    title_uz: Mapped[str] = mapped_column(String(160), nullable=False)
    message_de: Mapped[str] = mapped_column(Text, nullable=False)
    message_uz: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default=BTYPE_INFO, server_default=BTYPE_INFO)
    audience_type: Mapped[str] = mapped_column(String(20), nullable=False, default=AUD_ALL, server_default=AUD_ALL)
    audience_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    link_type: Mapped[str] = mapped_column(String(20), nullable=False, default=LINK_NONE, server_default=LINK_NONE)
    internal_route: Mapped[str | None] = mapped_column(String(60), nullable=True)
    internal_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ST_DRAFT, server_default=ST_DRAFT)
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class BroadcastNotificationRead(BaseModel):
    """Student X has read broadcast Y (no row = unread)."""

    __tablename__ = "broadcast_notification_reads"
    __table_args__ = (UniqueConstraint("notification_id", "user_id", name="uq_broadcast_notification_read"),)

    notification_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("broadcast_notifications.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
