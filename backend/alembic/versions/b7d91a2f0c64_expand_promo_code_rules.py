"""Expand promo targeting, pricing, and usage rules.

Revision ID: b7d91a2f0c64
Revises: ac72e1f9b503
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7d91a2f0c64"
down_revision: Union[str, Sequence[str], None] = "ac72e1f9b503"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("promo_codes", "discount_type", type_=sa.String(length=20), existing_type=sa.String(length=10))
    op.add_column("promo_codes", sa.Column("starts_at", sa.DateTime(), nullable=True))
    op.add_column(
        "promo_codes",
        sa.Column("max_uses_per_user", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "promo_codes",
        sa.Column("applicable_course_ids", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
    )
    op.add_column(
        "promo_codes",
        sa.Column("applicable_package_codes", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
    )

    op.drop_constraint("uq_promo_redemption_user", "promo_code_redemptions", type_="unique")
    op.create_unique_constraint("uq_promo_redemption_order", "promo_code_redemptions", ["order_id"])

    op.add_column("subscription_orders", sa.Column("promo_code_snapshot", sa.String(length=40), nullable=True))
    op.add_column(
        "subscription_orders",
        sa.Column("promo_discount_amount", sa.Integer(), server_default="0", nullable=False),
    )
    op.execute(
        """
        UPDATE subscription_orders AS orders
        SET promo_code_snapshot = promos.code,
            promo_discount_amount = GREATEST(
                orders.discount_amount - COALESCE(orders.reward_discount_amount, 0),
                0
            )
        FROM promo_codes AS promos
        WHERE orders.promo_code_id = promos.id
        """
    )


def downgrade() -> None:
    op.drop_column("subscription_orders", "promo_discount_amount")
    op.drop_column("subscription_orders", "promo_code_snapshot")
    op.drop_constraint("uq_promo_redemption_order", "promo_code_redemptions", type_="unique")
    op.create_unique_constraint("uq_promo_redemption_user", "promo_code_redemptions", ["promo_code_id", "user_id"])
    op.drop_column("promo_codes", "applicable_package_codes")
    op.drop_column("promo_codes", "applicable_course_ids")
    op.drop_column("promo_codes", "max_uses_per_user")
    op.drop_column("promo_codes", "starts_at")
    op.alter_column("promo_codes", "discount_type", type_=sa.String(length=10), existing_type=sa.String(length=20))
