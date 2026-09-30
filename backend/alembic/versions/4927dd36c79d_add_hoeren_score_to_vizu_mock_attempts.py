"""add hoeren_score to vizu_mock_attempts

Revision ID: 4927dd36c79d
Revises: b4d5186b61f8
Create Date: 2026-09-30 00:00:00.000000

Hören now has real content and grading (see
services/vizu_mock/hoeren_service.py), so it needs the same raw-points
column Lesen already has (lesen_score). hoeren_level already existed as
a nullable placeholder column from the original attempts table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4927dd36c79d'
down_revision: Union[str, Sequence[str], None] = 'b4d5186b61f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('vizu_mock_attempts', sa.Column('hoeren_score', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('vizu_mock_attempts', 'hoeren_score')
