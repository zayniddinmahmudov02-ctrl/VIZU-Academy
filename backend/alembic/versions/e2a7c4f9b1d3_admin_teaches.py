"""Admin who also teaches: `teacher_profiles.teaches`.

Additive: one boolean column, NOT NULL with server default false — every existing row (TEACHER accounts) keeps its meaning (a
TEACHER account always teaches; the flag only matters for a SUPER_ADMIN account that is also listed in Team / My Teacher).

Downgrade: drops the column (a SUPER_ADMIN that taught is then no longer listed as a teacher; its courses / lessons stay).

Revision ID: e2a7c4f9b1d3
Revises: d9e4a1c7b3f5
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e2a7c4f9b1d3"
down_revision: Union[str, Sequence[str], None] = "d9e4a1c7b3f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teacher_profiles", sa.Column("teaches", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("teacher_profiles", "teaches")
