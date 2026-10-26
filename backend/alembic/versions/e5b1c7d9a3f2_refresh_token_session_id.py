"""Session id on refresh tokens, so logout also revokes access tokens.

Every refresh token of one login shares a session_id (rotation keeps it);
access tokens carry it as the `sid` claim and are refused once no live
refresh token of that session exists. Nullable: rows issued before this
migration keep working until they are rotated or expire.

Revision ID: e5b1c7d9a3f2
Revises: d2e6a9f4b7c1
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e5b1c7d9a3f2"
down_revision: Union[str, Sequence[str], None] = "d2e6a9f4b7c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("refresh_tokens", sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_refresh_tokens_session_id", "refresh_tokens", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_session_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "session_id")
