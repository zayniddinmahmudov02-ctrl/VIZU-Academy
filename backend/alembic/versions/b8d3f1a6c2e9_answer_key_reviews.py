"""answer_key_reviews: manual verification of Lesen / Hören answer keys (Lösung)

A new table only — no existing table or row is changed. One row per reviewed
reading or listening question (CASCADE with the question). The answer key
itself stays in reading_options / listening_options / *.config, where the
scoring engine reads it. Reversible: downgrade drops only this table.

Revision ID: b8d3f1a6c2e9
Revises: a7c2e9d4b1f3
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b8d3f1a6c2e9"
down_revision = "a7c2e9d4b1f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "answer_key_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reading_question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reading_questions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("listening_question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listening_questions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("key_fingerprint", sa.String(64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("(reading_question_id IS NULL) <> (listening_question_id IS NULL)", name="ck_answer_key_reviews_one_question"),
        sa.CheckConstraint("status IN ('verified', 'needs_review', 'unverified')", name="ck_answer_key_reviews_status"),
    )
    op.create_index("uq_answer_key_reviews_reading", "answer_key_reviews", ["reading_question_id"], unique=True,
                    postgresql_where=sa.text("reading_question_id IS NOT NULL"))
    op.create_index("uq_answer_key_reviews_listening", "answer_key_reviews", ["listening_question_id"], unique=True,
                    postgresql_where=sa.text("listening_question_id IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("uq_answer_key_reviews_listening", table_name="answer_key_reviews")
    op.drop_index("uq_answer_key_reviews_reading", table_name="answer_key_reviews")
    op.drop_table("answer_key_reviews")
