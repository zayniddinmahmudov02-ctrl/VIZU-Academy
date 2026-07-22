from uuid import uuid4

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Video(BaseModel):
    __tablename__ = "videos"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    lesson_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    video_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # R2 object key (e.g. "videos/<uuid>.mp4"). The only thing persisted
    # for R2-backed videos — never a public/signed URL. Streaming URLs are
    # generated on demand and expire after
    # settings.R2_SIGNED_URL_EXPIRE_SECONDS.
    storage_key: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        unique=True,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    # Free-preview videos are streamable without an active enrollment or
    # premium subscription (e.g. a course trailer / sample lesson).
    is_preview: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    lesson = relationship(
        "Lesson",
        back_populates="videos",
    )