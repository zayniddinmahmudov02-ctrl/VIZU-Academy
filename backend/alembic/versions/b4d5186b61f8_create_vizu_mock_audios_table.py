"""create vizu_mock_audios table

Revision ID: b4d5186b61f8
Revises: 39f489a43397
Create Date: 2026-09-30 00:00:00.000000

Adds vizu_mock_audios — the Hören audio library managed from the
VIZU-Mock admin dashboard. Independent of Course/Vorbereitung media
tables by design; the admin UI reuses the existing generic Media
Library upload endpoint to place a file on storage, but the resulting
URL/metadata is stored here. `task_id` weakly (nullable, SET NULL)
associates an audio file with a future Hören vizu_mock_tasks row —
no Hören task bank exists yet, so it stays unset until one does.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b4d5186b61f8'
down_revision: Union[str, Sequence[str], None] = '39f489a43397'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'vizu_mock_audios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('audio_url', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['vizu_mock_tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_vizu_mock_audios_task_id'), 'vizu_mock_audios', ['task_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_vizu_mock_audios_task_id'), table_name='vizu_mock_audios')
    op.drop_table('vizu_mock_audios')
