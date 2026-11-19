"""Medienwelt film AI subtitles: "approve when done" per job (the subtitle agents).

Additive only: `film_subtitle_jobs.auto_approve` (boolean, default false = the result waits for the admin's "Freigeben" as before).
Downgrade drops exactly this column.

Revision ID: f3b9d1a6c4e8
Revises: e8a3c5f1b7d2
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3b9d1a6c4e8"
down_revision: Union[str, Sequence[str], None] = "e8a3c5f1b7d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("film_subtitle_jobs", sa.Column("auto_approve", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("film_subtitle_jobs", "auto_approve")
