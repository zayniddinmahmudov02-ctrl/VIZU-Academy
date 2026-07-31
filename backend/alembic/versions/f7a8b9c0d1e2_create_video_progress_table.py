"""create video_progress table

Revision ID: f7a8b9c0d1e2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-31 00:00:00.000000

Adds `video_progress`, the per-(user, video) continuous playback tracker
backing resume-from-position, watch-percentage completion, and the
server-side anti-skip clamp. Distinct from the pre-existing
`student_progress.video_completed` boolean, which this table's
`complete_progress` flow keeps in sync once a video is actually watched.

Also adds `videos.thumbnail_key`, the storage key for an admin-uploaded
thumbnail file (mirrors `storage_key`), so uploaded thumbnails can be
cleaned up on replace/delete the same way video files already are.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'videos',
        sa.Column('thumbnail_key', sa.String(length=1024), nullable=True),
    )

    op.create_table(
        'video_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('last_position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('watch_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'video_id', name='uq_video_progress_user_video'),
    )
    op.create_index(
        op.f('ix_video_progress_user_id'),
        'video_progress',
        ['user_id'],
    )
    op.create_index(
        op.f('ix_video_progress_video_id'),
        'video_progress',
        ['video_id'],
    )
    op.create_index(
        op.f('ix_video_progress_lesson_id'),
        'video_progress',
        ['lesson_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_video_progress_lesson_id'), table_name='video_progress')
    op.drop_index(op.f('ix_video_progress_video_id'), table_name='video_progress')
    op.drop_index(op.f('ix_video_progress_user_id'), table_name='video_progress')
    op.drop_table('video_progress')

    op.drop_column('videos', 'thumbnail_key')
