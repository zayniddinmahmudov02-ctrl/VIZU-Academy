"""create books table

Revision ID: b3c7f1a2d5e8
Revises: a0b7ea1ef39b
Create Date: 2026-08-24 00:00:00.000000

Adds `books` — admin-uploaded PDF books, tagged by CEFR level, shown to
students at the top of their level's lesson list. `storage_key` is a
path into ProtectedBookStorage (app/protected_storage/books/), never a
public URL; `cover_url` is a public media_library URL. No FK to any
other table — books aren't lesson/course-scoped, only level-tagged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3c7f1a2d5e8'
down_revision: Union[str, Sequence[str], None] = 'a0b7ea1ef39b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('cover_url', sa.String(length=1024), nullable=True),
        sa.Column('storage_key', sa.String(length=1024), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_books_level'),
        'books',
        ['level'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_books_level'), table_name='books')
    op.drop_table('books')
