"""revert group_label from quiz_questions

Revision ID: 384d4fb96e12
Revises: 4a1b48460c1d
Create Date: 2026-09-30 00:00:00.000000

Undoes 4a1b48460c1d: that migration (and the HOEREN quiz_type/CSV import
it supported) targeted the *regular course lesson* Quiz system, but the
Hören listening-comprehension questions it was meant to hold belong
exclusively to VIZU-Mock instead (see
services/vizu_mock/hoeren_service.py / VizuMockTask). Rather than
deleting the already-applied 4a1b48460c1d migration file outright (which
would break `alembic history` for any database that already ran it),
this adds a proper reverting migration on top of it, the normal safe way
to undo a migration that may already be live somewhere.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '384d4fb96e12'
down_revision: Union[str, Sequence[str], None] = '4a1b48460c1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('quiz_questions', 'group_label')


def downgrade() -> None:
    """Downgrade schema."""
    import sqlalchemy as sa

    op.add_column('quiz_questions', sa.Column('group_label', sa.String(length=100), nullable=True))
