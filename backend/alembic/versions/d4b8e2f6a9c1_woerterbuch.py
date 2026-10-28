"""Wörterbuch: dictionary entries, per-student word state, Random 5 draws.

Additive only — three new tables, nothing existing is touched. Downgrade
drops exactly these three tables (students' saved words and Random 5
history are lost with them; the dictionary itself is re-importable).

Revision ID: d4b8e2f6a9c1
Revises: a7c2e9f4b1d6
Create Date: 2026-10-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4b8e2f6a9c1"
down_revision: Union[str, Sequence[str], None] = "a7c2e9f4b1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "dictionary_entries",
        *_base(),
        sa.Column("stable_id", sa.String(20), nullable=False, unique=True),
        sa.Column("german", sa.String(255), nullable=False),
        sa.Column("lemma", sa.String(255), nullable=False),
        sa.Column("article", sa.String(3), nullable=True),
        sa.Column("reflexive", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("part_of_speech", sa.String(30), nullable=True),
        sa.Column("cefr_level", sa.String(2), nullable=False),
        sa.Column("levels", postgresql.ARRAY(sa.String(2)), nullable=False),
        sa.Column("translation", sa.String(255), nullable=False),
        sa.Column("translations_extra", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("definition_de", sa.Text(), nullable=True),
        sa.Column("grammar", postgresql.JSONB(), nullable=True),
        sa.Column("grammar_source", sa.String(30), nullable=False, server_default="none"),
        sa.Column("ipa", sa.String(120), nullable=True),
        sa.Column("example_de", sa.Text(), nullable=True),
        sa.Column("example_uz", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("translation_status", sa.String(20), nullable=False),
        sa.Column("grammar_status", sa.String(20), nullable=False),
        sa.Column("example_status", sa.String(20), nullable=False),
        sa.Column("review_notes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("sources", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("search_de", sa.String(255), nullable=False),
        sa.Column("search_uz", sa.String(1000), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_dictionary_entries_part_of_speech", "dictionary_entries", ["part_of_speech"])
    op.create_index("ix_dictionary_entries_cefr_level", "dictionary_entries", ["cefr_level"])
    op.create_index("ix_dictionary_entries_search_de", "dictionary_entries", ["search_de"], postgresql_ops={"search_de": "text_pattern_ops"})
    op.create_index("ix_dictionary_entries_search_uz", "dictionary_entries", ["search_uz"], postgresql_ops={"search_uz": "text_pattern_ops"})
    op.create_index("ix_dictionary_entries_levels", "dictionary_entries", ["levels"], postgresql_using="gin")

    op.create_table(
        "dictionary_user_words",
        *_base(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dictionary_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("saved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(10), nullable=True),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("known_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unknown_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_marked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "entry_id", name="uq_dictionary_user_word"),
    )
    op.create_index("ix_dictionary_user_words_user_id", "dictionary_user_words", ["user_id"])
    op.create_index("ix_dictionary_user_words_user_saved", "dictionary_user_words", ["user_id", "saved"])

    op.create_table(
        "dictionary_random_sessions",
        *_base(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(3), nullable=False),
        sa.Column("entry_ids", postgresql.JSONB(), nullable=False),
        sa.Column("pool_size", sa.Integer(), nullable=False),
        sa.Column("unseen_before", sa.Integer(), nullable=False),
    )
    op.create_index("ix_dictionary_random_sessions_user_created", "dictionary_random_sessions", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("dictionary_random_sessions")
    op.drop_table("dictionary_user_words")
    op.drop_table("dictionary_entries")
