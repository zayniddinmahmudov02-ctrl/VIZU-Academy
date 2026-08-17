"""add notified flag to writing_submissions and speaking_submissions

Revision ID: 0c3d0f8ef47d
Revises: ff4a32086886
Create Date: 2026-08-18 00:15:00.000000

Drives the Hausaufgaben "Zurückgegeben" (returned) tab without a
fragile join against notifications: a graded submission is "returned"
once the student has actually been notified about it, not merely the
instant it's scored. Set True by the same code path that creates the
grading notification (writing's auto-evaluation completing; speaking's
teacher review being finalized).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c3d0f8ef47d'
down_revision: Union[str, Sequence[str], None] = 'ff4a32086886'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'writing_submissions',
        sa.Column('notified', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'speaking_submissions',
        sa.Column('notified', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('speaking_submissions', 'notified')
    op.drop_column('writing_submissions', 'notified')
