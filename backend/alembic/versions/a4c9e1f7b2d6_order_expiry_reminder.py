"""Course access reminder: `subscription_orders.expiry_reminder_sent_at`.

Additive: one nullable timestamptz column. The owner (2026-11-25) keeps course access time-limited; a student gets one
notification three days before the access of an approved course order ends (app/services/vizu_pay/expiry_reminders.py), and this
column makes it one per order. Existing rows stay NULL.

Downgrade: drops the column (reminders could then be sent again for orders still running).

Revision ID: a4c9e1f7b2d6
Revises: f3b8d2a6c9e1
Create Date: 2026-11-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a4c9e1f7b2d6"
down_revision: Union[str, Sequence[str], None] = "f3b8d2a6c9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subscription_orders", sa.Column("expiry_reminder_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("subscription_orders", "expiry_reminder_sent_at")
