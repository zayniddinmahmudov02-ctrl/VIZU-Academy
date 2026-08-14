"""add Quiz.quiz_type and StudentProgress.vocabulary_completed

Revision ID: 3afca6f269b1
Revises: 141f83a602bd
Create Date: 2026-08-14 04:00:00.000000

Backs the per-lesson 100-point scoring system:
- `quizzes.quiz_type` distinguishes the mid-lesson "Grammatik Quiz"
  (worth 10 of the 100 points) from the end-of-lesson "Lesson Quiz" (a
  separate diagnostic that does NOT add to the 100) — both are plain
  `Quiz` rows today with nothing to tell them apart. Existing rows all
  backfill to 'GRAMMAR', matching their only real use case so far.
- `student_progress.vocabulary_completed` mirrors the existing
  `video_completed` pattern (see StudentProgressRepository.
  mark_video_completed) — nothing previously tracked whether a student
  had gone through the Wortschatz section at all.

Purely additive: new nullable-or-defaulted columns only, nothing
existing renamed, retyped, or dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3afca6f269b1'
down_revision: Union[str, Sequence[str], None] = '141f83a602bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'quizzes',
        sa.Column('quiz_type', sa.String(length=20), nullable=False, server_default='GRAMMAR'),
    )
    op.create_index(op.f('ix_quizzes_quiz_type'), 'quizzes', ['quiz_type'])

    op.add_column(
        'student_progress',
        sa.Column('vocabulary_completed', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('student_progress', 'vocabulary_completed')

    op.drop_index(op.f('ix_quizzes_quiz_type'), table_name='quizzes')
    op.drop_column('quizzes', 'quiz_type')
