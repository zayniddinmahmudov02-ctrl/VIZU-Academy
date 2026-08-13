from uuid import UUID as PyUUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VideoUploadSession(BaseModel):
    """A chunked video upload in progress. `id` (inherited from
    BaseModel) IS the upload_id the client uses on every chunk request.

    Deliberately holds every field VideoService.upload_video() needs so
    /complete can create (or, if replace_video_id is set, update) the
    real Video row without the client re-submitting metadata it already
    sent at /init. Which chunks have arrived is never tracked here —
    that's answered by listing the session's temp chunk directory
    (see VideoService._uploaded_chunk_numbers), so there's no chunk-table
    bookkeeping that could drift from what's actually on disk.

    Rows are deleted the moment /complete succeeds; anything left behind
    past VIDEO_UPLOAD_SESSION_MAX_AGE_HOURS is an abandoned upload, swept
    by VideoService.cleanup_stale_upload_sessions()."""

    __tablename__ = "video_upload_sessions"

    admin_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lesson_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Set only for a "replace this video's file" upload — /complete then
    # swaps replace_video_id's storage_key instead of inserting a new
    # Video row, same distinction VideoService.upload_video() vs
    # replace_video() already draws for the single-shot path.
    replace_video_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    order_index: Mapped[int] = mapped_column(Integer, default=1)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # BigInteger, not Integer: VIDEO_MAX_UPLOAD_SIZE_MB (2048) * 1024 * 1024
    # is 2,147,483,648 — one byte over Postgres int32's ceiling.
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False)
