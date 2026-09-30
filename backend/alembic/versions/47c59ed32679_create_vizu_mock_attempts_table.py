"""create vizu_mock_attempts table

Revision ID: 47c59ed32679
Revises: d4f8b2a6c1e9
Create Date: 2026-09-30 00:00:00.000000

Adds `vizu_mock_attempts` — one row per student attempt at the new
standalone "VIZU-Mock" free level check (framework only, per spec: no
question bank, no grading, no level-determination algorithm exist yet).
The four per-skill level columns and overall_level are nullable
placeholders, left NULL until a later phase fills them in place; no
further migration should be needed for that, only new write paths.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '47c59ed32679'
down_revision: Union[str, Sequence[str], None] = 'd4f8b2a6c1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'vizu_mock_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='IN_PROGRESS', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lesen_level', sa.String(length=10), nullable=True),
        sa.Column('hoeren_level', sa.String(length=10), nullable=True),
        sa.Column('schreiben_level', sa.String(length=10), nullable=True),
        sa.Column('sprechen_level', sa.String(length=10), nullable=True),
        sa.Column('overall_level', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_vizu_mock_attempts_user_id'),
        'vizu_mock_attempts',
        ['user_id'],
    )
    op.create_index(
        op.f('ix_vizu_mock_attempts_status'),
        'vizu_mock_attempts',
        ['status'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_vizu_mock_attempts_status'), table_name='vizu_mock_attempts')
    op.drop_index(op.f('ix_vizu_mock_attempts_user_id'), table_name='vizu_mock_attempts')
    op.drop_table('vizu_mock_attempts')
