from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Values for Vocabulary.audio_status. Audio is always the admin's own
# microphone recording (see app/services/vocabulary/audio_processing.py)
# — never AI-generated. PENDING until recorded, GENERATED once a
# recording is saved, FAILED if saving one somehow didn't work out.
AUDIO_STATUS_PENDING = "PENDING"
AUDIO_STATUS_GENERATED = "GENERATED"
AUDIO_STATUS_FAILED = "FAILED"


class Vocabulary(BaseModel):
    __tablename__ = "vocabularies"

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

    german_word: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    article: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    plural: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    translation: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    example_sentence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    example_translation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # audio_url alone can only say "has audio" vs "doesn't" — this
    # distinguishes never-recorded from a real save failure, which the
    # "Audio nacheinander aufnehmen" queue (get_missing_audio) needs to
    # show which words still need the admin's voice.
    audio_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AUDIO_STATUS_PENDING,
        server_default=AUDIO_STATUS_PENDING,
    )

    audio_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
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

    lesson = relationship(
        "Lesson",
        back_populates="vocabularies",
    )