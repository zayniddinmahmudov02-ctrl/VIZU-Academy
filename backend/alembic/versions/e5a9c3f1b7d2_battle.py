"""VIZU DEUTSCH BATTLE: profiles, picture words, images, matches, answers, Battle Points ledger, arena themes.

Additive only: seven new tables (battle_profiles, battle_images, battle_words, battle_matches,
battle_answers, battle_points_ledger, battle_themes). No existing table or row is touched;
battle_words reference dictionary_entries with ON DELETE SET NULL (a Wörterbuch re-import never blocks).

Downgrade drops exactly these seven tables (battle data is lost, nothing else).

Revision ID: e5a9c3f1b7d2
Revises: d7e2b4f8a1c6
Create Date: 2026-11-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e5a9c3f1b7d2"
down_revision: Union[str, Sequence[str], None] = "d7e2b4f8a1c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _base_columns():
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _user(name, nullable=False, ondelete="CASCADE"):
    return sa.Column(name, UUID, sa.ForeignKey("users.id", ondelete=ondelete), nullable=nullable)


def _int(name, default="0"):
    return sa.Column(name, sa.Integer(), nullable=False, server_default=default)


def upgrade() -> None:
    op.create_table(
        "battle_profiles",
        *_base_columns(),
        _user("user_id"),
        _int("points"), _int("wins"), _int("losses"), _int("draws"), _int("streak"), _int("best_streak"),
        sa.Column("avatar", sa.String(30), nullable=False, server_default="student"),
        sa.Column("last_match_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_battle_profiles_user_id"),
    )
    op.create_index("ix_battle_profiles_points", "battle_profiles", ["points"])

    op.create_table(
        "battle_images",
        *_base_columns(),
        sa.Column("storage_name", sa.String(80), nullable=False),
        sa.Column("mime", sa.String(30), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("file_title", sa.String(300), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("license", sa.String(80), nullable=True),
        sa.Column("license_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("review_note", sa.Text(), nullable=True),
        _user("verified_by", nullable=True, ondelete="SET NULL"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        _user("created_by", nullable=True, ondelete="SET NULL"),
        sa.UniqueConstraint("storage_name", name="uq_battle_images_storage_name"),
    )
    op.create_index("ix_battle_images_sha256", "battle_images", ["sha256"])

    op.create_table(
        "battle_words",
        *_base_columns(),
        sa.Column("entry_id", UUID, sa.ForeignKey("dictionary_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("article", sa.String(3), nullable=True),
        sa.Column("lemma", sa.String(255), nullable=False),
        sa.Column("translation", sa.Text(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("image_id", UUID, sa.ForeignKey("battle_images.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("entry_id", name="uq_battle_words_entry_id"),
    )
    op.create_index("ix_battle_words_pool", "battle_words", ["level", "status", "category"])

    op.create_table(
        "battle_matches",
        *_base_columns(),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("level", sa.String(4), nullable=False),
        sa.Column("room_code", sa.String(8), nullable=True),
        _user("player1_id"),
        _user("player2_id", nullable=True),
        _int("p1_points_start"), _int("p2_points_start"), _int("rounds", "10"),
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default="[]"),
        _int("current_round"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("round_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("round_ended_at", sa.DateTime(timezone=True), nullable=True),
        _int("p1_score"), _int("p2_score"),
        sa.Column("p1_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("p2_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_slot", sa.Integer(), nullable=True),
        sa.Column("finish_reason", sa.String(12), nullable=True),
        _int("p1_delta"), _int("p2_delta"),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("room_code", name="uq_battle_matches_room_code"),
    )
    op.create_index("ix_battle_matches_lookup", "battle_matches", ["status", "mode", "level"])
    op.create_index("ix_battle_matches_player1", "battle_matches", ["player1_id", "status"])
    op.create_index("ix_battle_matches_player2", "battle_matches", ["player2_id", "status"])

    op.create_table(
        "battle_answers",
        *_base_columns(),
        sa.Column("match_id", UUID, sa.ForeignKey("battle_matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_no", sa.Integer(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("choice", sa.Integer(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("time_ms", sa.Integer(), nullable=False),
        _int("score"),
        sa.UniqueConstraint("match_id", "round_no", "slot", name="uq_battle_answer_round_slot"),
    )
    op.create_index("ix_battle_answers_match_id", "battle_answers", ["match_id"])

    op.create_table(
        "battle_points_ledger",
        *_base_columns(),
        _user("user_id"),
        sa.Column("match_id", UUID, sa.ForeignKey("battle_matches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.UniqueConstraint("user_id", "match_id", "reason", name="uq_battle_points_ledger_event"),
    )
    op.create_index("ix_battle_points_ledger_user_id", "battle_points_ledger", ["user_id"])

    op.create_table(
        "battle_themes",
        *_base_columns(),
        sa.Column("level", sa.String(4), nullable=False),
        sa.Column("city", sa.String(60), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("subtitle", sa.String(200), nullable=True),
        sa.Column("desktop_image", sa.String(300), nullable=True),
        sa.Column("mobile_image", sa.String(300), nullable=True),
        sa.Column("accent", sa.String(9), nullable=False, server_default="#3984E8"),
        _int("overlay", "55"),
        sa.Column("attribution", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("draft", postgresql.JSONB(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        _user("updated_by", nullable=True, ondelete="SET NULL"),
        sa.UniqueConstraint("level", name="uq_battle_themes_level"),
    )


def downgrade() -> None:
    op.drop_table("battle_themes")
    op.drop_index("ix_battle_points_ledger_user_id", table_name="battle_points_ledger")
    op.drop_table("battle_points_ledger")
    op.drop_index("ix_battle_answers_match_id", table_name="battle_answers")
    op.drop_table("battle_answers")
    for name in ("ix_battle_matches_player2", "ix_battle_matches_player1", "ix_battle_matches_lookup"):
        op.drop_index(name, table_name="battle_matches")
    op.drop_table("battle_matches")
    op.drop_index("ix_battle_words_pool", table_name="battle_words")
    op.drop_table("battle_words")
    op.drop_index("ix_battle_images_sha256", table_name="battle_images")
    op.drop_table("battle_images")
    op.drop_index("ix_battle_profiles_points", table_name="battle_profiles")
    op.drop_table("battle_profiles")
