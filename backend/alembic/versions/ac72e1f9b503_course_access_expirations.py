"""Add independent calendar-month access windows to course orders.

Revision ID: ac72e1f9b503
Revises: f4b8d2e6a1c3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ac72e1f9b503"
down_revision: Union[str, Sequence[str], None] = "f4b8d2e6a1c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subscription_orders", sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscription_orders", sa.Column("access_start_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscription_orders", sa.Column("access_end_date", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_subscription_orders_access_window", "subscription_orders", ["user_id", "access_start_date", "access_end_date"])

    # Snapshot of the offer durations at migration time. Keep historical
    # approvals usable from their recorded approval time; pending and failed
    # orders deliberately receive no access window.
    op.execute(
        """
        UPDATE subscription_orders
        SET purchase_date = COALESCE(reviewed_at AT TIME ZONE 'UTC', created_at),
            access_start_date = COALESCE(reviewed_at AT TIME ZONE 'UTC', created_at),
            access_end_date = COALESCE(reviewed_at AT TIME ZONE 'UTC', created_at)
                + make_interval(months => CASE plan
                    WHEN 'A1' THEN 1 WHEN 'A2' THEN 1 WHEN 'B1' THEN 2
                    WHEN 'B2' THEN 3 WHEN 'C1' THEN 2 WHEN 'A1_B1' THEN 4
                    WHEN 'A1_C1' THEN 9 END)
        WHERE status = 'APPROVED'
          AND plan IN ('A1', 'A2', 'B1', 'B2', 'C1', 'A1_B1', 'A1_C1')
        """
    )


def downgrade() -> None:
    op.drop_index("ix_subscription_orders_access_window", table_name="subscription_orders")
    op.drop_column("subscription_orders", "access_end_date")
    op.drop_column("subscription_orders", "access_start_date")
    op.drop_column("subscription_orders", "purchase_date")
