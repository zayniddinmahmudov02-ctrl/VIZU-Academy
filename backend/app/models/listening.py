from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class Listening(BaseModel):

    __tablename__ = "listenings"

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Legacy external/public URL (older tasks). New tasks upload the audio
    # instead: it is stored privately (audio_storage_path) and only streamed
    # to students with lesson access — see services/lesson_skills.
    audio_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    audio_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # label of the main audio when the task has several (e.g. "Audio von Alisa"); NULL = plain "Audio"
    audio_label: Mapped[str | None] = mapped_column(String(120), nullable=True)

    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    # stable id of imported (Claude JSON) content — duplicate detection
    content_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    lesson = relationship(
        "Lesson",
        back_populates="listenings",
    )

    @property
    def has_uploaded_audio(self) -> bool:
        return bool(self.audio_storage_path)

    @property
    def question_count(self) -> int:
        return len(self.questions)

    questions = relationship(
        "ListeningQuestion",
        cascade="all, delete-orphan",
        order_by="ListeningQuestion.order_index",
        lazy="selectin",
    )
<<<<<<< HEAD

=======
>>>>>>> d267d227cbf9226d26331600cd4d2a06ac7e0ac5
    # additional labelled audio files (listening_audio_track.py) after the main audio
    audio_tracks = relationship(
        "ListeningAudioTrack",
        cascade="all, delete-orphan",
        order_by="ListeningAudioTrack.order_index",
        lazy="selectin",
    )
