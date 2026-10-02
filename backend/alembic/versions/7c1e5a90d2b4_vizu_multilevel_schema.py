"""vizu multilevel schema: publish flag, transcript, timing, sprechen, discarded tally

Revision ID: 7c1e5a90d2b4
Revises: 46eb84ea78a4
Create Date: 2026-10-02 00:00:00.000000

Structural changes for the VIZU-Mock -> VIZU-Multilevel transformation.
Existing `vizu_mock_*` table names are intentionally kept (renaming them
buys nothing and risks the FK/constraint names); only additive changes:

* vizu_mock_tasks: is_published (default true), transcript
* vizu_mock_attempts: per-competency started/submitted timestamps (the
  server-authoritative 20-minute timer), sprechen_score/sprechen_feedback
* vizu_multilevel_speaking_tasks / _speaking_submissions (new)
* vizu_multilevel_discarded_attempts (new, anonymous tally for statistics)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "7c1e5a90d2b4"
down_revision: Union[str, None] = "46eb84ea78a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = sa.DateTime(timezone=True)


def _base_cols() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", _TS, server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.add_column("vizu_mock_tasks", sa.Column("transcript", sa.Text(), nullable=True))
    op.add_column(
        "vizu_mock_tasks",
        sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False),
    )

    for col in (
        "lesen_started_at",
        "lesen_submitted_at",
        "hoeren_started_at",
        "hoeren_submitted_at",
        "schreiben_started_at",
        "sprechen_started_at",
        "sprechen_submitted_at",
    ):
        op.add_column("vizu_mock_attempts", sa.Column(col, _TS, nullable=True))
    op.add_column("vizu_mock_attempts", sa.Column("sprechen_score", sa.Integer(), nullable=True))
    op.add_column("vizu_mock_attempts", sa.Column("sprechen_feedback", sa.Text(), nullable=True))

    op.create_table(
        "vizu_multilevel_speaking_tasks",
        *_base_cols(),
        sa.Column("level", sa.String(10), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("preparation_text", sa.Text(), nullable=True),
        sa.Column("prep_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_seconds", sa.Integer(), server_default="120", nullable=False),
        sa.Column("points", sa.Integer(), server_default="20", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.UniqueConstraint("order_index", name="uq_vizu_multilevel_speaking_task_order"),
    )
    op.create_index("ix_vizu_multilevel_speaking_tasks_level", "vizu_multilevel_speaking_tasks", ["level"])

    op.create_table(
        "vizu_multilevel_speaking_submissions",
        *_base_cols(),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vizu_mock_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vizu_multilevel_speaking_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("submitted_at", _TS, nullable=True),
        sa.Column("teacher_score", sa.Integer(), nullable=True),
        sa.Column("teacher_comment", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", _TS, nullable=True),
        sa.UniqueConstraint("attempt_id", "task_id", name="uq_vizu_multilevel_speaking_submission_attempt_task"),
    )
    op.create_index(
        "ix_vizu_multilevel_speaking_submissions_attempt_id", "vizu_multilevel_speaking_submissions", ["attempt_id"]
    )
    op.create_index(
        "ix_vizu_multilevel_speaking_submissions_task_id", "vizu_multilevel_speaking_submissions", ["task_id"]
    )

    op.create_table(
        "vizu_multilevel_discarded_attempts",
        *_base_cols(),
        sa.Column("reason", sa.String(20), nullable=False),
        sa.Column("started_at", _TS, nullable=False),
        sa.Column("lesen_score", sa.Integer(), nullable=True),
        sa.Column("hoeren_score", sa.Numeric(5, 1), nullable=True),
        sa.Column("schreiben_score", sa.Integer(), nullable=True),
        sa.Column("sprechen_score", sa.Integer(), nullable=True),
    )
    op.create_index("ix_vizu_multilevel_discarded_attempts_reason", "vizu_multilevel_discarded_attempts", ["reason"])


def downgrade() -> None:
    op.drop_table("vizu_multilevel_discarded_attempts")
    op.drop_table("vizu_multilevel_speaking_submissions")
    op.drop_table("vizu_multilevel_speaking_tasks")
    for col in (
        "sprechen_feedback",
        "sprechen_score",
        "sprechen_submitted_at",
        "sprechen_started_at",
        "schreiben_started_at",
        "hoeren_submitted_at",
        "hoeren_started_at",
        "lesen_submitted_at",
        "lesen_started_at",
    ):
        op.drop_column("vizu_mock_attempts", col)
    op.drop_column("vizu_mock_tasks", "is_published")
    op.drop_column("vizu_mock_tasks", "transcript")
