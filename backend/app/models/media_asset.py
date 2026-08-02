from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class MediaAsset(BaseModel):
    """Tracks every file uploaded through the admin Media Library so it can
    be browsed/reused ("Select Existing") instead of re-uploaded. Separate
    from the per-content-type URL columns (Video.storage_key,
    Listening.audio_url, etc.) — those stay authoritative for playback;
    this table is purely a browsable index of what's in storage."""

    __tablename__ = "media_assets"

    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    folder: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    media_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    content_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    uploaded_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
