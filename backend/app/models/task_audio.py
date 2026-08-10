from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

FORMAT_MP3 = "mp3"
FORMAT_WAV = "wav"
FORMAT_M4A = "m4a"
# Browser MediaRecorder (used by the Sprechen recording UI) does not
# produce mp3/wav/m4a — Chrome/Firefox default to webm, Safari to mp4/aac.
# Admin-uploaded Hören audio realistically never needs these, but the
# format set is shared, and rejecting a browser's own native recording
# output would break student submissions entirely.
FORMAT_WEBM = "webm"
FORMAT_OGG = "ogg"
ALL_AUDIO_FORMATS = {FORMAT_MP3, FORMAT_WAV, FORMAT_M4A, FORMAT_WEBM, FORMAT_OGG}

CONTENT_TYPE_BY_FORMAT = {
    FORMAT_MP3: "audio/mpeg",
    FORMAT_WAV: "audio/wav",
    FORMAT_M4A: "audio/mp4",
    FORMAT_WEBM: "audio/webm",
    FORMAT_OGG: "audio/ogg",
}


class TaskAudio(BaseModel):
    """The audio file attached to a HOEREN AssessmentTask — 1:1.

    `storage_path` is a path relative to the *protected* storage root
    (see app/core/storage/protected_local.py), deliberately NOT under the
    publicly-mounted `uploads/` static directory — the only way to fetch
    the actual bytes is the authenticated `GET /audio/{task_id}` endpoint,
    which checks the task's assessment is published (or the caller is a
    super admin) before streaming anything. No raw file URL is ever
    returned by any API response.
    """

    __tablename__ = "task_audio"

    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    task = relationship("AssessmentTask", back_populates="audio")
