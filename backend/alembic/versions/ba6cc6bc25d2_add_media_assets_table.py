"""add media_assets table

Revision ID: ba6cc6bc25d2
Revises: b8d2e4f6a0c3
Create Date: 2026-08-02 13:41:35.405738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ba6cc6bc25d2'
down_revision: Union[str, Sequence[str], None] = 'b8d2e4f6a0c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    NOTE: this file started as an `alembic revision --autogenerate` output
    that also picked up a large amount of unrelated schema drift against
    the live DB (leftover tables from an older, unmodeled schema — e.g.
    teacher_questions, homework_assignments, vizu_lesen_results, music,
    films, books, access_codes, etc. — plus several dropped `users`
    columns). None of that belongs to this change and was manually
    stripped out; this migration only ever creates `media_assets`.
    """
    op.create_table(
        'media_assets',
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('folder', sa.String(length=50), nullable=False),
        sa.Column('media_type', sa.String(length=20), nullable=False),
        sa.Column('content_type', sa.String(length=150), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('uploaded_by', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_media_assets_folder'), 'media_assets', ['folder'], unique=False)
    op.create_index(op.f('ix_media_assets_media_type'), 'media_assets', ['media_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_media_assets_media_type'), table_name='media_assets')
    op.drop_index(op.f('ix_media_assets_folder'), table_name='media_assets')
    op.drop_table('media_assets')
