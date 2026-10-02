from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class VizuMultilevelAudio(BaseModel):
    """A Hören audio file managed from the VIZU-Multilevel admin dashboard.
    Independent of the Course/Vorbereitung media systems by design (see
    the "must not become coupled to other systems" constraint) — the
    admin UI reuses the existing generic Media Library upload mechanism
    to get a file onto storage, but the resulting URL is recorded here,
    on a VIZU-Multilevel-owned row, not on a Course/Vorbereitung table.

    `task_id` is an optional, weak association to a future Hören
    VizuMultilevelTask row (skill=HOEREN) — nullable because no Hören task
    bank exists yet; an admin can upload and name audio now and link it
    to a task once Hören content is authored in a later phase."""

    __tablename__ = "vizu_mock_audios"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    task = relationship("VizuMultilevelTask")
