from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


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

    # Manual URL only (e.g. pasted or uploaded via the generic file
    # uploader) — no pronunciation-audio generation feature exists.
    audio_url: Mapped[str | None] = mapped_column(
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