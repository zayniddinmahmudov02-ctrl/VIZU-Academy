"""create video_upload_sessions table

Revision ID: 8006706ca9db
Revises: d8f4805044a1
Create Date: 2026-08-13 00:00:00.000000

Backs the chunked/resumable admin video upload flow (POST /init, /chunk,
/complete) added to work around Cloudflare's edge upload-size cap on any
single request. One row per in-progress upload; deleted the moment
/complete succeeds. Which chunks have actually arrived is answered by
listing the session's temp chunk directory on disk, not tracked here, so
there's no separate chunk table that could drift from the filesystem.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8006706ca9db'
down_revision: Union[str, Sequence[str], None] = 'd8f4805044a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'video_upload_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('replace_video_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_preview', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extension', sa.String(length=16), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['replace_video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_video_upload_sessions_admin_id'),
        'video_upload_sessions',
        ['admin_id'],
    )
    op.create_index(
        op.f('ix_video_upload_sessions_lesson_id'),
        'video_upload_sessions',
        ['lesson_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_video_upload_sessions_lesson_id'), table_name='video_upload_sessions')
    op.drop_index(op.f('ix_video_upload_sessions_admin_id'), table_name='video_upload_sessions')
    op.drop_table('video_upload_sessions')
