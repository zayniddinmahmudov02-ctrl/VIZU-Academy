"""Wörterbuch — the global German–Uzbek dictionary (A1–C1), separate from the
lesson-bound `vocabularies` (a lesson's word list, lesson_id NOT NULL).

Source of truth: docs/{A1..C1}-words.csv (22 columns) + worterbuch-extra-data.csv
+ worterbuch-needs-review.csv, imported by app.scripts.import_woerterbuch.
One row here = one CSV row, keyed by (level, source_id) = the file's own id, so
a re-import updates in place and every student's saved word stays attached.

A word listed twice in the same level file is kept twice; only the first
row of such a group (is_primary) is offered in search and Random 5.
`status` is the CSV's own status — nothing becomes "verified" here."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DictionaryEntry(BaseModel):
    __tablename__ = "dictionary_entries"
    __table_args__ = (
        UniqueConstraint("level", "source_id", name="uq_dictionary_entry_level_source_id"),
        Index("ix_dictionary_entries_search_de", "search_de", postgresql_ops={"search_de": "text_pattern_ops"}),
        Index("ix_dictionary_entries_visible", "is_published", "is_primary", "level"),
        Index("ix_dictionary_entries_group", "level", "group_key"),
    )

    level: Mapped[str] = mapped_column(String(2), nullable=False)
    # the CSV's id column (1..N per level file)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False)
    word_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    article: Mapped[str | None] = mapped_column(String(3), nullable=True)
    plural: Mapped[str | None] = mapped_column(String(255), nullable=True)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    verb_praeteritum: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verb_partizip_ii: Mapped[str | None] = mapped_column(String(120), nullable=True)
    verb_auxiliary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    presens_ich: Mapped[str | None] = mapped_column(String(120), nullable=True)
    presens_du: Mapped[str | None] = mapped_column(String(120), nullable=True)
    presens_er_sie_es: Mapped[str | None] = mapped_column(String(120), nullable=True)
    presens_wir: Mapped[str | None] = mapped_column(String(120), nullable=True)
    presens_ihr: Mapped[str | None] = mapped_column(String(120), nullable=True)
    presens_sie_Sie: Mapped[str | None] = mapped_column("presens_sie_sie", String(120), nullable=True)
    adjective_komparativ: Mapped[str | None] = mapped_column(String(120), nullable=True)
    adjective_superlativ: Mapped[str | None] = mapped_column(String(120), nullable=True)
    example_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    # text for the browser's TTS — not an audio file
    audio_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # worterbuch-extra-data.csv for this row: other_translation, quiz_distractors, noun_genitive …
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    # worterbuch-needs-review.csv for this row: priority, reasons, suggestion
    review: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    group_key: Mapped[str] = mapped_column(String(300), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    search_de: Mapped[str] = mapped_column(String(255), nullable=False)
    search_uz: Mapped[str] = mapped_column(Text, nullable=False)
    search_forms: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    @property
    def word_id(self) -> str:
        """Public id: "A1-2" = level file + its own id."""
        return f"{self.level}-{self.source_id}"


class DictionaryUserWord(BaseModel):
    """One student's state for one word: saved (the star) and seen in Random 5."""

    __tablename__ = "dictionary_user_words"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_id", name="uq_dictionary_user_word"),
        Index("ix_dictionary_user_words_user_saved", "user_id", "saved"),
    )

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dictionary_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seen_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    entry = relationship("DictionaryEntry", lazy="joined")
