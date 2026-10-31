from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Vocabulary(BaseModel):
    """A lesson's word (the course book's list). The grammar fields (word type,
    verb forms) and examples are filled from the course book or from a VERIFIED
    Wörterbuch entry with the same article + lemma (migration d7e2b4f8a1c6,
    app/services/lesson_skills/wortschatz.py); `data_sources` says where each
    filled field came from. Nothing is guessed: an empty field is shown to the
    admin as missing."""
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

    # stable id of imported book content — duplicate detection on re-import
    content_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    word_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    verb_praeteritum: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verb_partizip_ii: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verb_auxiliary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dictionary_entry_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dictionary_entries.id", ondelete="SET NULL"), nullable=True
    )
    # {"plural": "woerterbuch:A2-12", "word_type": "book", ...}
    data_sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    lesson = relationship(
        "Lesson",
        back_populates="vocabularies",
    )


class VocabularyUserWord(BaseModel):
    """One student's state for one lesson word: saved ("Meine Wörter") and
    learned. Only the student's own rows are ever read or written."""

    __tablename__ = "vocabulary_user_words"
    __table_args__ = (UniqueConstraint("user_id", "vocabulary_id", name="uq_vocabulary_user_word"),)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vocabularies.id", ondelete="CASCADE"), nullable=False, index=True)
    saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    learned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    learned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)