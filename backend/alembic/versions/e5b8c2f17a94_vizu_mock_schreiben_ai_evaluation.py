"""vizu mock schreiben: store the server-side AI evaluation per Aufgabe

Revision ID: e5b8c2f17a94
Revises: d2a7e9c41f63
Create Date: 2026-10-06 00:00:00.000000

Additive only. Each Schreiben submission gets its evaluation state and the
structured AI feedback (strengths / verified errors with corrections /
feedback / next steps). Per-criterion points keep using the existing
vizu_mock_writing_criterion_scores table and the per-task total keeps
using teacher_score, so the existing result flow is reused unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5b8c2f17a94"
down_revision: Union[str, None] = "d2a7e9c41f63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vizu_mock_writing_submissions", sa.Column("evaluation_status", sa.String(20), nullable=True))
    op.add_column("vizu_mock_writing_submissions", sa.Column("ai_feedback", postgresql.JSONB(), nullable=True))
    op.add_column("vizu_mock_writing_submissions", sa.Column("evaluation_error", sa.Text(), nullable=True))
    op.add_column(
        "vizu_mock_writing_submissions", sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    for col in ("evaluated_at", "evaluation_error", "ai_feedback", "evaluation_status"):
        op.drop_column("vizu_mock_writing_submissions", col)
