"""promote_initial_super_admin

Revision ID: 9e2c7b4f1a3d
Revises: d3f8a1c92b6e
Create Date: 2026-07-19 00:05:00.000000

Data migration: grants SUPER_ADMIN to the project owner's account so the
new admin panel has at least one usable super admin from day one.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e2c7b4f1a3d'
down_revision: Union[str, Sequence[str], None] = 'd3f8a1c92b6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SUPER_ADMIN_EMAIL = 'zayniddin.mahmudov.02@gmail.com'


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            "UPDATE users SET role = 'SUPER_ADMIN' WHERE email = :email"
        ).bindparams(email=SUPER_ADMIN_EMAIL)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            "UPDATE users SET role = 'STUDENT' WHERE email = :email"
        ).bindparams(email=SUPER_ADMIN_EMAIL)
    )
