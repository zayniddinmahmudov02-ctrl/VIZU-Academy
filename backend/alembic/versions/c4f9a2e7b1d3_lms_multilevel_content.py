"""LMS A1-C1: question types, task metadata, result config, content imports

Additive and reversible — no existing row is changed or deleted:
* reading_questions / listening_questions: `config` (MATCHING / GAP_FILL /
  SHORT_ANSWER definition incl. answer key; NULL for option-based types).
* readings: image_url, content_id; listenings: content_id.
* writings: text_type, audience, time_limit_minutes, content_id.
* speakings: response_type (default MONOLOG), questions, speech_goal, content_id.
* courses: result_config (NULL = equal weights, all four skills required).
* content_imports: committed Claude/JSON import batches.

Revision ID: c4f9a2e7b1d3
Revises: b3e8d1c5a7f2
Create Date: 2026-10-11
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c4f9a2e7b1d3"
down_revision = "b3e8d1c5a7f2"
branch_labels = None
depends_on = None

CONTENT_TABLES = ("readings", "listenings", "writings", "speakings")


def upgrade() -> None:
    for table in ("reading_questions", "listening_questions"):
        op.add_column(table, sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.add_column("readings", sa.Column("image_url", sa.String(length=500), nullable=True))
    for table in CONTENT_TABLES:
        op.add_column(table, sa.Column("content_id", sa.String(length=120), nullable=True))
        op.create_index(f"ix_{table}_content_id", table, ["content_id"])

    op.add_column("writings", sa.Column("text_type", sa.String(length=30), nullable=True))
    op.add_column("writings", sa.Column("audience", sa.Text(), nullable=True))
    op.add_column("writings", sa.Column("time_limit_minutes", sa.Integer(), nullable=True))

    op.add_column("speakings", sa.Column("response_type", sa.String(length=20), server_default="MONOLOG", nullable=False))
    op.add_column("speakings", sa.Column("questions", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("speakings", sa.Column("speech_goal", sa.Text(), nullable=True))

    op.add_column("courses", sa.Column("result_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_table(
        "content_imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("levels", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("content_imports")
    op.drop_column("courses", "result_config")
    for column in ("speech_goal", "questions", "response_type"):
        op.drop_column("speakings", column)
    for column in ("time_limit_minutes", "audience", "text_type"):
        op.drop_column("writings", column)
    for table in CONTENT_TABLES:
        op.drop_index(f"ix_{table}_content_id", table_name=table)
        op.drop_column(table, "content_id")
    op.drop_column("readings", "image_url")
    for table in ("reading_questions", "listening_questions"):
        op.drop_column(table, "config")
