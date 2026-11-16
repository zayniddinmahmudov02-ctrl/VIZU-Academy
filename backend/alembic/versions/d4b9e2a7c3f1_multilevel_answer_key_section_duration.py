"""Multilevel exam: the answer key as typed (mock_questions.answer_key) and the granted section length (mock_attempt_sections.duration_seconds).

Additive only — nothing is rewritten or deleted; existing questions, options, keys, attempts and answers keep every value:
  * mock_questions.answer_key (nullable, <= 8 chars): "b", "R", "F", "H" … exactly as the admin entered it; scoring still uses options.is_correct
  * mock_attempt_sections.duration_seconds (nullable): what the server granted when the section was opened; older rows are filled from
    deadline_at - started_at (that difference IS the granted length)
Downgrade drops exactly these two columns.

Revision ID: d4b9e2a7c3f1
Revises: c2f7a9d1e4b6
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4b9e2a7c3f1"
down_revision: Union[str, Sequence[str], None] = "c2f7a9d1e4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mock_questions", sa.Column("answer_key", sa.String(8), nullable=True))
    op.add_column("mock_attempt_sections", sa.Column("duration_seconds", sa.Integer(), nullable=True))
    # sections of attempts that already exist: the granted length is deadline - start (never negative)
    op.execute("UPDATE mock_attempt_sections SET duration_seconds = GREATEST(0, EXTRACT(EPOCH FROM (deadline_at - started_at))::integer) WHERE duration_seconds IS NULL")


def downgrade() -> None:
    op.drop_column("mock_attempt_sections", "duration_seconds")
    op.drop_column("mock_questions", "answer_key")
