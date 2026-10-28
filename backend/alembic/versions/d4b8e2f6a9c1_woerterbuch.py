"""Wörterbuch: dictionary entries (one per docs/*-words.csv row) and the
student's word state (saved star, seen in Random 5).

Additive only — two new tables, nothing existing is touched. Downgrade
drops exactly these two tables (students' saved words are lost with them;
the dictionary itself is re-importable from docs/).

Never applied outside local test databases before 2026-10-28, so this
revision was rewritten for the CSV-based schema instead of being followed
by a drop-and-recreate revision.

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


def _form(name: str) -> sa.Column:
    return sa.Column(name, sa.String(120), nullable=True)


def upgrade() -> None:
    op.create_table(
        "dictionary_entries",
        *_base(),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("lemma", sa.String(255), nullable=False),
        sa.Column("word_type", sa.String(30), nullable=True),
        sa.Column("article", sa.String(3), nullable=True),
        sa.Column("plural", sa.String(255), nullable=True),
        sa.Column("translation", sa.Text(), nullable=False),
        _form("verb_praeteritum"),
        _form("verb_partizip_ii"),
        sa.Column("verb_auxiliary", sa.String(20), nullable=True),
        _form("presens_ich"),
        _form("presens_du"),
        _form("presens_er_sie_es"),
        _form("presens_wir"),
        _form("presens_ihr"),
        _form("presens_sie_sie"),
        _form("adjective_komparativ"),
        _form("adjective_superlativ"),
        sa.Column("example_de", sa.Text(), nullable=True),
        sa.Column("example_uz", sa.Text(), nullable=True),
        sa.Column("audio_text", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("extra", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("review", postgresql.JSONB(), nullable=True),
        sa.Column("group_key", sa.String(300), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("search_de", sa.String(255), nullable=False),
        sa.Column("search_uz", sa.Text(), nullable=False),
        sa.Column("search_forms", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("level", "source_id", name="uq_dictionary_entry_level_source_id"),
    )
    op.create_index("ix_dictionary_entries_word_type", "dictionary_entries", ["word_type"])
    op.create_index("ix_dictionary_entries_search_de", "dictionary_entries", ["search_de"], postgresql_ops={"search_de": "text_pattern_ops"})
    op.create_index("ix_dictionary_entries_visible", "dictionary_entries", ["is_published", "is_primary", "level"])
    op.create_index("ix_dictionary_entries_group", "dictionary_entries", ["level", "group_key"])

    op.create_table(
        "dictionary_user_words",
        *_base(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dictionary_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("saved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "entry_id", name="uq_dictionary_user_word"),
    )
    op.create_index("ix_dictionary_user_words_user_id", "dictionary_user_words", ["user_id"])
    op.create_index("ix_dictionary_user_words_entry_id", "dictionary_user_words", ["entry_id"])
    op.create_index("ix_dictionary_user_words_user_saved", "dictionary_user_words", ["user_id", "saved"])


def downgrade() -> None:
    op.drop_table("dictionary_user_words")
    op.drop_table("dictionary_entries")
