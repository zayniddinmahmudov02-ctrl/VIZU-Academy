from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

KIND_ORIGINAL = "ORIGINAL"
KIND_TRIMMED = "TRIMMED"


class AudioFile(BaseModel):
    """One stored audio file of the central audio service (`services/audio_files`): an uploaded ORIGINAL or a TRIMMED
    cut of one. Files live in the private lesson-listening storage under a random name (never a public URL); a trim
    is always cut from its ORIGINAL (`source_id`), so the original is kept and a slot can be re-trimmed or restored.
    Used by Media Management (lesson Hören slots) and Multilevel Audio (`listening_contents.audio_file_id`)."""

    __tablename__ = "audio_files"
    __table_args__ = (
        UniqueConstraint("storage_path", name="uq_audio_files_storage_path"),
        CheckConstraint("kind IN ('ORIGINAL','TRIMMED')", name="ck_audio_files_kind"),
        CheckConstraint("kind = 'ORIGINAL' OR (source_id IS NOT NULL AND trim_end_ms > trim_start_ms)", name="ck_audio_files_trim"),
    )

    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default=KIND_ORIGINAL)
    source_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="RESTRICT", name="fk_audio_files_source_id"), nullable=True,
                                                   index=True)
    trim_start_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trim_end_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL", name="fk_audio_files_created_by_id"),
                                                       nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source = relationship("AudioFile", remote_side="AudioFile.id")
