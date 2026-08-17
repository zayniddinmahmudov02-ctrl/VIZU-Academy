"""add question_type/correct_text_answer to quiz_questions, match_value to quiz_options

Revision ID: 41ebb453d245
Revises: e9389b0e771b
Create Date: 2026-08-18 00:05:00.000000

Extends the existing legacy Quiz system (used for Grammatik Quiz) beyond
plain multiple-choice, without creating a parallel content model:

- quiz_questions.question_type: MULTIPLE_CHOICE (existing behavior,
  default for all existing rows), TRUE_FALSE, CLOZE_TEXT,
  SENTENCE_COMPLETION, SENTENCE_ORDERING, ERROR_FINDING, MATCHING.
  TRUE_FALSE and ERROR_FINDING need no other new columns — both are
  still "pick the correct option(s)" via the existing quiz_options/
  is_correct mechanism, just different authoring conventions.
- quiz_questions.correct_text_answer: free-text answer for CLOZE_TEXT/
  SENTENCE_COMPLETION, mirroring TaskQuestion.correct_text_answer's
  naming in the Assessment Engine for consistency.
- quiz_options.match_value: pairing value for MATCHING, mirroring
  TaskOption.match_value. SENTENCE_ORDERING reuses the option's
  existing order_index as the correct order — no new column needed.

Purely additive: new nullable-or-defaulted columns only.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41ebb453d245'
down_revision: Union[str, Sequence[str], None] = 'e9389b0e771b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'quiz_questions',
        sa.Column('question_type', sa.String(length=30), nullable=False, server_default='MULTIPLE_CHOICE'),
    )
    op.add_column(
        'quiz_questions',
        sa.Column('correct_text_answer', sa.Text(), nullable=True),
    )
    op.add_column(
        'quiz_options',
        sa.Column('match_value', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('quiz_options', 'match_value')
    op.drop_column('quiz_questions', 'correct_text_answer')
    op.drop_column('quiz_questions', 'question_type')
