"""add_user_management_module

Revision ID: b1a4c6e8f2d0
Revises: 9e2c7b4f1a3d
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1a4c6e8f2d0'
down_revision: Union[str, Sequence[str], None] = '9e2c7b4f1a3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- users: ban / suspend / premium columns ---
    op.add_column(
        'users',
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column('users', sa.Column('ban_reason', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('banned_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('suspended_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('suspend_reason', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('premium_until', sa.DateTime(), nullable=True))

    # --- user_tags ---
    op.create_table(
        'user_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('user_id', 'label', name='uq_user_tags_user_label'),
    )
    op.create_index(op.f('ix_user_tags_user_id'), 'user_tags', ['user_id'], unique=False)

    # --- login_history ---
    op.create_table(
        'login_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('device', sa.String(length=50), nullable=False, server_default='Unknown'),
        sa.Column('os', sa.String(length=50), nullable=False, server_default='Unknown'),
        sa.Column('browser', sa.String(length=50), nullable=False, server_default='Unknown'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index(op.f('ix_login_history_user_id'), 'login_history', ['user_id'], unique=False)

    # --- audit_logs ---
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
    )
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_target_user_id'), 'audit_logs', ['target_user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_target_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_login_history_user_id'), table_name='login_history')
    op.drop_table('login_history')

    op.drop_index(op.f('ix_user_tags_user_id'), table_name='user_tags')
    op.drop_table('user_tags')

    op.drop_column('users', 'premium_until')
    op.drop_column('users', 'suspend_reason')
    op.drop_column('users', 'suspended_until')
    op.drop_column('users', 'banned_at')
    op.drop_column('users', 'ban_reason')
    op.drop_column('users', 'is_banned')
