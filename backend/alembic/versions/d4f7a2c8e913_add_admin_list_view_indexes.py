"""add_admin_list_view_indexes

Revision ID: d4f7a2c8e913
Revises: c7d2e9a4f5b1
Create Date: 2026-07-19 00:00:00.000000

Admin panel audit: login_history, audit_logs and subscription_orders are
all listed/paginated sorted by created_at DESC, but none had an index on
that column — every admin list view was doing a full table sort. Additive,
safe, no data change.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4f7a2c8e913'
down_revision: Union[str, Sequence[str], None] = 'c7d2e9a4f5b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_login_history_created_at'), 'login_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_subscription_orders_created_at'), 'subscription_orders', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_subscription_orders_created_at'), table_name='subscription_orders')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_login_history_created_at'), table_name='login_history')
