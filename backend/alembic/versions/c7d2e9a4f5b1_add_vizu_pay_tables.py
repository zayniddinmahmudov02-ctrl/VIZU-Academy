"""add_vizu_pay_tables

Revision ID: c7d2e9a4f5b1
Revises: b1a4c6e8f2d0
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c7d2e9a4f5b1'
down_revision: Union[str, Sequence[str], None] = 'b1a4c6e8f2d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column('users', sa.Column('trial_used_at', sa.DateTime(), nullable=True))

    op.create_table(
        'promo_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('code', sa.String(length=40), nullable=False),
        sa.Column('campaign', sa.String(length=120), nullable=True),
        sa.Column('discount_type', sa.String(length=10), nullable=False),
        sa.Column('discount_value', sa.Integer(), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('code', name='uq_promo_codes_code'),
    )
    op.create_index(op.f('ix_promo_codes_code'), 'promo_codes', ['code'], unique=True)

    op.create_table(
        'subscription_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan', sa.String(length=20), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('base_amount', sa.Integer(), nullable=False),
        sa.Column('discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('final_amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='UZS'),
        sa.Column('payment_method', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('proof_url', sa.String(length=500), nullable=True),
        sa.Column('proof_type', sa.String(length=10), nullable=True),
        sa.Column('promo_code_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('promo_codes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('gateway', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('gateway_reference', sa.String(length=255), nullable=True),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_subscription_orders_user_id'), 'subscription_orders', ['user_id'], unique=False)
    op.create_index(op.f('ix_subscription_orders_status'), 'subscription_orders', ['status'], unique=False)

    op.create_table(
        'promo_code_redemptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('promo_code_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('promo_codes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscription_orders.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('promo_code_id', 'user_id', name='uq_promo_redemption_user'),
    )
    op.create_index(op.f('ix_promo_code_redemptions_promo_code_id'), 'promo_code_redemptions', ['promo_code_id'], unique=False)
    op.create_index(op.f('ix_promo_code_redemptions_user_id'), 'promo_code_redemptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_promo_code_redemptions_order_id'), 'promo_code_redemptions', ['order_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f('ix_promo_code_redemptions_order_id'), table_name='promo_code_redemptions')
    op.drop_index(op.f('ix_promo_code_redemptions_user_id'), table_name='promo_code_redemptions')
    op.drop_index(op.f('ix_promo_code_redemptions_promo_code_id'), table_name='promo_code_redemptions')
    op.drop_table('promo_code_redemptions')

    op.drop_index(op.f('ix_subscription_orders_status'), table_name='subscription_orders')
    op.drop_index(op.f('ix_subscription_orders_user_id'), table_name='subscription_orders')
    op.drop_table('subscription_orders')

    op.drop_index(op.f('ix_promo_codes_code'), table_name='promo_codes')
    op.drop_table('promo_codes')

    op.drop_column('users', 'trial_used_at')
