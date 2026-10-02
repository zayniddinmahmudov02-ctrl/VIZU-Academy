"""vizu mock: keep finished-but-not-kept attempts (discarded_reason)

Revision ID: d2a7e9c41f63
Revises: c8f1d3a65b20
Create Date: 2026-10-05 00:00:00.000000

Additive only. VIZU-Mock now allows exactly ONE attempt per student, so an
attempt whose result is not kept (below A1 / no content) is no longer
deleted — it is marked with `discarded_reason` instead. Existing rows are
not changed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d2a7e9c41f63"
down_revision: Union[str, None] = "c8f1d3a65b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vizu_mock_attempts", sa.Column("discarded_reason", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("vizu_mock_attempts", "discarded_reason")
