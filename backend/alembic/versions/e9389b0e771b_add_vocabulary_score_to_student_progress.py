"""add StudentProgress.vocabulary_score

Revision ID: e9389b0e771b
Revises: 3afca6f269b1
Create Date: 2026-08-18 00:00:00.000000

Wortschatz becomes interactive exercises with partial credit (100% = 10
points, 80% = 8 points, ...) instead of a binary "marked as learned"
toggle. `vocabulary_completed` (existing boolean) is kept unchanged for
backward compatibility — students who already completed the old flow
keep full credit via the scoring service's fallback. This column is
purely additive and nullable: null means "no exercise score recorded
yet", not zero.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9389b0e771b'
down_revision: Union[str, Sequence[str], None] = '3afca6f269b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'student_progress',
        sa.Column('vocabulary_score', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('student_progress', 'vocabulary_score')
