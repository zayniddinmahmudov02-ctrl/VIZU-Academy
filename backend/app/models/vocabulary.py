from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Values for Vocabulary.audio_status — see
# app/services/vocabulary/bulk_service.py's "Fehlende Audios generieren"
# queue for how a row moves between them.
AUDIO_STATUS_PENDING = "PENDING"
AUDIO_STATUS_GENERATED = "GENERATED"
AUDIO_STATUS_FAILED = "FAILED"
AUDIO_STATUS_RATE_LIMITED = "RATE_LIMITED"


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

    # Additive columns (migration 8006706ca9db -> next) backing the
    # "Fehlende Audios generieren" queue. audio_url alone can only say
    # "has audio" vs "doesn't" — this distinguishes never-attempted from
    # a real failure from a rate-limit, which the queue needs to decide
    # what's safe to retry. Existing rows are backfilled: GENERATED where
    # audio_url was already set, PENDING otherwise — nothing pre-existing
    # is ever marked FAILED or RATE_LIMITED by the migration itself.
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