"""add hoeren audio support

Revision ID: bad96c1fb729
Revises: 67da12c5649f
Create Date: 2026-08-10 13:33:36.842894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bad96c1fb729'
down_revision: Union[str, Sequence[str], None] = '67da12c5649f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('task_audio',
    sa.Column('task_id', sa.UUID(), nullable=False),
    sa.Column('storage_path', sa.String(length=500), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('format', sa.String(length=10), nullable=False),
    sa.Column('content_type', sa.String(length=100), nullable=False),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('file_size_bytes', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['assessment_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_audio_task_id'), 'task_audio', ['task_id'], unique=True)
    op.add_column('assessment_tasks', sa.Column('audio_play_limit', sa.Integer(), nullable=True))
    op.add_column('assessment_tasks', sa.Column('allow_pause', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('assessment_tasks', sa.Column('allow_seek', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('assessment_tasks', sa.Column('allow_replay', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('assessment_tasks', sa.Column('allow_speed_change', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('task_attempts', sa.Column('audio_play_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('task_attempts', 'audio_play_count')
    op.drop_column('assessment_tasks', 'allow_speed_change')
    op.drop_column('assessment_tasks', 'allow_replay')
    op.drop_column('assessment_tasks', 'allow_seek')
    op.drop_column('assessment_tasks', 'allow_pause')
    op.drop_column('assessment_tasks', 'audio_play_limit')
    op.drop_index(op.f('ix_task_audio_task_id'), table_name='task_audio')
    op.drop_table('task_audio')
