"""VIZU DEUTSCH BATTLE — two-player picture-vocabulary battles.

* battle_words: a picture word = a copy of one VERIFIED Wörterbuch row (dictionary_entries) + a category for the
  distractor engine + one image. Only `published` words with a `published` image reach a match.
* battle_images: files in app/protected_storage/battle-images (random names), with source, author and
  licence; Draft → Verified → Published (or Rejected).
* battle_matches / battle_answers: server-authoritative state. `questions` (word, options, correct index,
  bot plan) never leaves the server; the client only gets the running round.
* battle_points_ledger: every Battle Points change, unique per (user, match, reason) = idempotent.
* battle_themes: the arena look per CEFR stage (A1 … C1, C1+); admins edit `draft` and publish it."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BattleProfile(BaseModel):
    __tablename__ = "battle_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_battle_profiles_user_id"), Index("ix_battle_profiles_points", "points"))

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    best_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    avatar: Mapped[str] = mapped_column(String(30), nullable=False, default="student", server_default="student")
    last_match_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BattleImage(BaseModel):
    __tablename__ = "battle_images"
    __table_args__ = (UniqueConstraint("storage_name", name="uq_battle_images_storage_name"),)

    storage_name: Mapped[str] = mapped_column(String(80), nullable=False)
    mime: Mapped[str] = mapped_column(String(30), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # wikimedia | upload
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(80), nullable=True)
    license_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # draft | verified | published | rejected
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="draft", server_default="draft")
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class BattleWord(BaseModel):
    __tablename__ = "battle_words"
    __table_args__ = (UniqueConstraint("entry_id", name="uq_battle_words_entry_id"), Index("ix_battle_words_pool", "level", "status", "category"))

    # NULL when the Wörterbuch row was removed by a re-import; the word keeps its own copy of lemma / translation
    entry_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("dictionary_entries.id", ondelete="SET NULL"), nullable=True)
    level: Mapped[str] = mapped_column(String(2), nullable=False)
    article: Mapped[str | None] = mapped_column(String(3), nullable=True)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    # draft | published | disabled
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="draft", server_default="draft")
    image_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("battle_images.id", ondelete="SET NULL"), nullable=True)

    @property
    def display(self) -> str:
        return f"{self.article} {self.lemma}" if self.article else self.lemma


class BattleMatch(BaseModel):
    __tablename__ = "battle_matches"
    __table_args__ = (
        UniqueConstraint("room_code", name="uq_battle_matches_room_code"),
        Index("ix_battle_matches_lookup", "status", "mode", "level"),
        Index("ix_battle_matches_player1", "player1_id", "status"),
        Index("ix_battle_matches_player2", "player2_id", "status"),
    )

    # ranked | private | bot
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    # waiting | active | finished | cancelled
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    room_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    player1_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    player2_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    p1_points_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    p2_points_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default="10")
    # server only: [{"w": word id, "img": image id, "opts": [4 word ids], "c": correct index, "bot": {...}}]
    questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    round_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    round_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    p1_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    p2_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    p1_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    p2_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 1 | 2 | 0 = draw; NULL while running or when cancelled
    winner_slot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # normal | forfeit | afk
    finish_reason: Mapped[str | None] = mapped_column(String(12), nullable=True)
    p1_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    p2_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BattleAnswer(BaseModel):
    __tablename__ = "battle_answers"
    __table_args__ = (UniqueConstraint("match_id", "round_no", "slot", name="uq_battle_answer_round_slot"),)

    match_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("battle_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    round_no: Mapped[int] = mapped_column(Integer, nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    # NULL = time ran out
    choice: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class BattlePointsLedger(BaseModel):
    __tablename__ = "battle_points_ledger"
    __table_args__ = (UniqueConstraint("user_id", "match_id", "reason", name="uq_battle_points_ledger_event"),)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("battle_matches.id", ondelete="SET NULL"), nullable=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)


class BattleTheme(BaseModel):
    __tablename__ = "battle_themes"
    __table_args__ = (UniqueConstraint("level", name="uq_battle_themes_level"),)

    # A1 | A2 | B1 | B2 | C1 | C1+
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    city: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # "static:/battle/themes/<file>" (shipped with the frontend) or "asset:<storage name>" (admin upload)
    desktop_image: Mapped[str | None] = mapped_column(String(300), nullable=True)
    mobile_image: Mapped[str | None] = mapped_column(String(300), nullable=True)
    accent: Mapped[str] = mapped_column(String(9), nullable=False, default="#3984E8", server_default="#3984E8")
    overlay: Mapped[int] = mapped_column(Integer, nullable=False, default=55, server_default="55")
    # {"author", "license", "license_url", "source_url", "title"}
    attribution: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    # unpublished edits (same keys as the columns above); NULL = nothing pending
    draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
