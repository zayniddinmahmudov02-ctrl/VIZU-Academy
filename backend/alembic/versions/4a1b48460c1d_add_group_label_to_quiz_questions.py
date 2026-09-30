"""add group_label to quiz_questions

Revision ID: 4a1b48460c1d
Revises: 28adb706c79a
Create Date: 2026-09-30 00:00:00.000000

Adds a nullable `group_label` column to quiz_questions — used to cluster
CSV-imported questions under a heading (e.g. "Aufgabe 1") in the student
quiz player. Existing GRAMMAR/LESSON/VOCABULARY questions get NULL and
render exactly as before. No other schema change; QUIZ_TYPE_HOEREN is a
new value for the existing `quiz_type` string column, not a new column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a1b48460c1d'
down_revision: Union[str, Sequence[str], None] = '28adb706c79a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('quiz_questions', sa.Column('group_label', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('quiz_questions', 'group_label')
