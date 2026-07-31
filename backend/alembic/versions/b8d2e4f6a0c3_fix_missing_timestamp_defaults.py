"""fix missing timestamp defaults

Revision ID: b8d2e4f6a0c3
Revises: a3f5c9e1b7d4
Create Date: 2026-07-31 00:00:00.000000

Found while smoke-testing the Courses fix during the Super Admin Panel
audit: `courses`, `lessons`, `refresh_tokens`, and `users` all have
`created_at`/`updated_at` columns declared `NOT NULL` with no DB-level
default, even though `BaseModel` declares `server_default=func.now()` for
both. Every other table created since has the default correctly applied —
these four are leftovers from an early migration written before that
became the standard. In practice this meant a plain `INSERT` relying on
the ORM's declared default (i.e. any create path that doesn't manually
stamp both timestamps in Python) hits a NotNullViolation — confirmed via
`courses`/`lessons` having zero rows in the live database despite the API
supposedly supporting course/lesson creation. This migration adds the
missing `now()` server default to all eight columns; existing rows are
untouched (a `server_default` only affects future inserts that omit the
column).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d2e4f6a0c3'
down_revision: Union[str, Sequence[str], None] = 'a3f5c9e1b7d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ['courses', 'lessons', 'refresh_tokens', 'users']


def upgrade() -> None:
    """Upgrade schema."""
    for table in TABLES:
        op.alter_column(
            table,
            'created_at',
            server_default=sa.text('now()'),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.alter_column(
            table,
            'updated_at',
            server_default=sa.text('now()'),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.alter_column(
            table,
            'updated_at',
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.alter_column(
            table,
            'created_at',
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
