from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ListeningAudioArchive(BaseModel):
    """Metadata for a previous audio version; archived files stay in private storage."""

    __tablename__ = "listening_audio_archives"

    listening_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listenings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replaced_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
