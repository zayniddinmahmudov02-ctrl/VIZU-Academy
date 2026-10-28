"""Wörterbuch — the global German–Uzbek dictionary (A1–C1), separate from the
lesson-bound `vocabularies` (a lesson's word list, lesson_id NOT NULL).

Entries come from app/data/woerterbuch/dictionary.json (import_woerterbuch);
every content part carries its own status so unchecked data is never shown as
fact: translation_status source|needs_review|reviewed, grammar_status
sourced|needs_review|none|reviewed, example_status needs_review|none|reviewed."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_KNOWN = "known"
STATUS_UNKNOWN = "unknown"


class DictionaryEntry(BaseModel):
    __tablename__ = "dictionary_entries"
    __table_args__ = (
        Index("ix_dictionary_entries_search_de", "search_de", postgresql_ops={"search_de": "text_pattern_ops"}),
        Index("ix_dictionary_entries_search_uz", "search_uz", postgresql_ops={"search_uz": "text_pattern_ops"}),
        Index("ix_dictionary_entries_levels", "levels", postgresql_using="gin"),
    )

    # sha1 of the normalized headword — survives re-imports (source.stable_id)
    stable_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    german: Mapped[str] = mapped_column(String(255), nullable=False)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False)
    article: Mapped[str | None] = mapped_column(String(3), nullable=True)
    reflexive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    part_of_speech: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    cefr_level: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    # every word list the headword appears in (cefr_level = the lowest)
    levels: Mapped[list[str]] = mapped_column(ARRAY(String(2)), nullable=False)
    translation: Mapped[str] = mapped_column(String(255), nullable=False)
    translations_extra: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    definition_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    grammar: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    grammar_source: Mapped[str] = mapped_column(String(30), nullable=False, default="none", server_default="none")
    ipa: Mapped[str | None] = mapped_column(String(120), nullable=True)
    example_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    # recorded / provider-made pronunciation; None = the browser's TTS is used
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_status: Mapped[str] = mapped_column(String(20), nullable=False)
    grammar_status: Mapped[str] = mapped_column(String(20), nullable=False)
    example_status: Mapped[str] = mapped_column(String(20), nullable=False)
    review_notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # the word-list rows behind the entry, incl. the game's distractors (audit trail, never shown)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    search_de: Mapped[str] = mapped_column(String(255), nullable=False)
    search_uz: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class DictionaryUserWord(BaseModel):
    """One student's state for one word — saved, known / unknown, seen."""

    __tablename__ = "dictionary_user_words"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_id", name="uq_dictionary_user_word"),
        Index("ix_dictionary_user_words_user_saved", "user_id", "saved"),
    )

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dictionary_entries.id", ondelete="CASCADE"), nullable=False)
    saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str | None] = mapped_column(String(10), nullable=True)
    seen_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    known_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unknown_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_marked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    entry = relationship("DictionaryEntry", lazy="joined")


class DictionaryRandomSession(BaseModel):
    """One "Random 5" draw: which words were shown, from which pool."""

    __tablename__ = "dictionary_random_sessions"
    __table_args__ = (Index("ix_dictionary_random_sessions_user_created", "user_id", "created_at"),)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(3), nullable=False)
    entry_ids: Mapped[list] = mapped_column(JSONB, nullable=False)
    pool_size: Mapped[int] = mapped_column(Integer, nullable=False)
    unseen_before: Mapped[int] = mapped_column(Integer, nullable=False)
