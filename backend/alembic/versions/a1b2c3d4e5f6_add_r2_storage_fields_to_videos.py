"""add r2 storage fields to videos

Revision ID: a1b2c3d4e5f6
Revises: e5a9c1f7b3d2
Create Date: 2026-07-22 00:00:00.000000

Adds the Cloudflare R2 video-storage fields to `videos`:
- `storage_key`: the R2 object key. The only thing persisted for
  R2-backed videos — never a public/signed URL.
- `is_preview`: marks a video streamable without enrollment/premium.

`video_url` is relaxed to nullable since new R2-backed videos populate
`storage_key` instead and never a public URL. Existing rows/columns are
left untouched for backward compatibility with the legacy local-URL
video flow.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e5a9c1f7b3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'videos',
        'video_url',
        existing_type=sa.Text(),
        nullable=True,
    )

    op.add_column(
        'videos',
        sa.Column('storage_key', sa.String(length=1024), nullable=True),
    )
    op.create_unique_constraint(
        'uq_videos_storage_key',
        'videos',
        ['storage_key'],
    )

    op.add_column(
        'videos',
        sa.Column(
            'is_preview',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('videos', 'is_preview')

    op.drop_constraint(
        'uq_videos_storage_key',
        'videos',
        type_='unique',
    )
    op.drop_column('videos', 'storage_key')

    op.alter_column(
        'videos',
        'video_url',
        existing_type=sa.Text(),
        nullable=False,
    )
