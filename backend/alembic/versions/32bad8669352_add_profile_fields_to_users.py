"""add profile fields to users

Revision ID: 32bad8669352
Revises: cdc63bc24b16
Create Date: 2026-08-10 08:51:50.189965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '32bad8669352'
down_revision: Union[str, Sequence[str], None] = 'cdc63bc24b16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=30), nullable=True))
    op.add_column('users', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('profile_image', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('preferred_language', sa.String(length=10), server_default='de', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'preferred_language')
    op.drop_column('users', 'profile_image')
    op.drop_column('users', 'country')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
