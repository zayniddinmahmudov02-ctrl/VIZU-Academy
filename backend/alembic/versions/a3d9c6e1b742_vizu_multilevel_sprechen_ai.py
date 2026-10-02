"""vizu multilevel sprechen: 25-task bank (slot x level) + server-side STT / AI evaluation per answer

Revision ID: a3d9c6e1b742
Revises: f1c4a7b29d36
Create Date: 2026-10-02

Additive only:
* vizu_multilevel_speaking_tasks: the Aufgabe number (order_index) is no
  longer unique on its own — the bank holds one variant per CEFR level for
  every Aufgabe, so uniqueness is (order_index, level). + min_seconds.
* vizu_multilevel_speaking_submissions: pipeline status, transcript, STT
  metadata, audio observations, AI score/criteria/feedback, worker lock.
No data is deleted or rewritten.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a3d9c6e1b742"
down_revision = "f1c4a7b29d36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_vizu_multilevel_speaking_task_order", "vizu_multilevel_speaking_tasks", type_="unique")
    op.create_unique_constraint(
        "uq_vizu_multilevel_speaking_task_slot_level", "vizu_multilevel_speaking_tasks", ["order_index", "level"]
    )
    op.add_column(
        "vizu_multilevel_speaking_tasks",
        sa.Column("min_seconds", sa.Integer(), server_default="0", nullable=False),
    )

    table = "vizu_multilevel_speaking_submissions"
    op.add_column(table, sa.Column("status", sa.String(length=20), nullable=True))
    op.add_column(table, sa.Column("transcript", sa.Text(), nullable=True))
    op.add_column(table, sa.Column("transcript_language", sa.String(length=10), nullable=True))
    op.add_column(table, sa.Column("transcript_confidence", sa.Float(), nullable=True))
    op.add_column(table, sa.Column("stt_provider", sa.String(length=30), nullable=True))
    op.add_column(table, sa.Column("audio_observations", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(table, sa.Column("ai_score", sa.Integer(), nullable=True))
    op.add_column(table, sa.Column("ai_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(table, sa.Column("ai_feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(table, sa.Column("evaluation_error", sa.Text(), nullable=True))
    op.add_column(table, sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(table, sa.Column("worker_started_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_vizu_multilevel_speaking_submissions_status", table, ["status"])


def downgrade() -> None:
    table = "vizu_multilevel_speaking_submissions"
    op.drop_index("ix_vizu_multilevel_speaking_submissions_status", table_name=table)
    for column in (
        "worker_started_at",
        "evaluated_at",
        "evaluation_error",
        "ai_feedback",
        "ai_criteria",
        "ai_score",
        "audio_observations",
        "stt_provider",
        "transcript_confidence",
        "transcript_language",
        "transcript",
        "status",
    ):
        op.drop_column(table, column)
    op.drop_column("vizu_multilevel_speaking_tasks", "min_seconds")
    op.drop_constraint("uq_vizu_multilevel_speaking_task_slot_level", "vizu_multilevel_speaking_tasks", type_="unique")
    op.create_unique_constraint("uq_vizu_multilevel_speaking_task_order", "vizu_multilevel_speaking_tasks", ["order_index"])
