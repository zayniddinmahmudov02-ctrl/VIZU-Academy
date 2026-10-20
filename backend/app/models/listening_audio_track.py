from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ListeningAudioTrack(BaseModel):
    """An additional, labelled audio file of one Hören task — e.g. A1 lesson 14
    "Audio von Alex" next to the task's main audio "Audio von Alisa". The main
    audio stays on the Listening row (audio_storage_path …); every rule that
    needs "the task has audio" keeps reading it there. Files are stored
    privately like the main audio and only streamed to students with access."""

    __tablename__ = "listening_audio_tracks"

    listening_id: Mapped[str] = mapped_column(ForeignKey("listenings.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
