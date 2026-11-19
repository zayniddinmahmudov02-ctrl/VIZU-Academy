"""VIZU Battle text questions: vocabulary and grammar rounds per CEFR level next to the picture rounds.

Additive only: new table `battle_questions` (level, kind vocab / grammar, format, topic, prompt, hint, answer, wrong options JSONB,
explanation, `norm_key` unique per level = no duplicate questions, `seed_id` unique = the shipped data files, status draft / published /
disabled, source seed / admin / import, `ref` = the lemma asked about, dictionary entry + users FKs SET NULL, pool index).
The picture tables (battle_words, battle_images) and running matches are not touched. Downgrade drops exactly this table.

Revision ID: a6c2e8f4b9d1
Revises: f3b9d1a6c4e8
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a6c2e8f4b9d1"
down_revision: Union[str, Sequence[str], None] = "f3b9d1a6c4e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "battle_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("seed_id", sa.String(40), nullable=True),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("topic", sa.String(40), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("wrong", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("norm_key", sa.String(400), nullable=False),
        sa.Column("ref", sa.String(255), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("source", sa.String(12), nullable=False, server_default="admin"),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dictionary_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("level", "norm_key", name="uq_battle_questions_level_norm_key"),
        sa.UniqueConstraint("seed_id", name="uq_battle_questions_seed_id"),
    )
    op.create_index("ix_battle_questions_pool", "battle_questions", ["level", "status", "kind"])


def downgrade() -> None:
    op.drop_index("ix_battle_questions_pool", table_name="battle_questions")
    op.drop_table("battle_questions")
