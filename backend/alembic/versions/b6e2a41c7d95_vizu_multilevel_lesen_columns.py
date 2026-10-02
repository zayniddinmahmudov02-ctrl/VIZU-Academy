"""vizu multilevel lesen: question.is_active + lesen correct/wrong/unanswered

Revision ID: b6e2a41c7d95
Revises: 9d3f6b21e8a7
Create Date: 2026-10-03 00:00:00.000000

Additive only: an on/off switch per Lesen question, and the correct /
wrong / unanswered breakdown stored next to lesen_score / lesen_level so
the competencies can later be merged into one certificate.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b6e2a41c7d95"
down_revision: Union[str, None] = "9d3f6b21e8a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vizu_mock_questions", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False))
    for col in ("lesen_correct", "lesen_wrong", "lesen_unanswered"):
        op.add_column("vizu_mock_attempts", sa.Column(col, sa.Integer(), nullable=True))


def downgrade() -> None:
    for col in ("lesen_unanswered", "lesen_wrong", "lesen_correct"):
        op.drop_column("vizu_mock_attempts", col)
    op.drop_column("vizu_mock_questions", "is_active")
