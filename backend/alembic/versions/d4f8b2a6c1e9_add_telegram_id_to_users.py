"""add telegram_id to users

Revision ID: d4f8b2a6c1e9
Revises: c9e4f2b8a1d7
Create Date: 2026-09-28 00:00:00.000000

Adds `users.telegram_id` (nullable, unique) — the one field genuinely
missing for Telegram Mini App login (POST /auth/telegram,
app/services/auth/service.py's get_or_create_telegram_user): the stable
key that finds the SAME account again on a later Telegram login, since
email/username on a Telegram-originated account are synthetic
placeholders, not something to look up by. Nullable so every existing
email/password account is completely unaffected — this column only ever
gets a value the first time an account logs in via Telegram.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f8b2a6c1e9'
down_revision: Union[str, Sequence[str], None] = 'c9e4f2b8a1d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_column('users', 'telegram_id')
