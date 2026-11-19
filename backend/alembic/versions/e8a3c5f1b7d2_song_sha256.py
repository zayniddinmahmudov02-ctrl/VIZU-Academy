"""Medienwelt songs: SHA-256 of the stored original (duplicate check of the bulk upload of up to 500 songs).

Additive only: `songs.sha256` (nullable, not unique — a deliberate copy stays possible) + index `ix_songs_sha256`. Existing songs get their hash from
`python -m app.scripts.medien_song_hashes plan | apply --confirm <plan id>` (reads the stored files, writes only this column).
Downgrade drops exactly the column and the index.

Revision ID: e8a3c5f1b7d2
Revises: d5f1b8e3a9c7
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e8a3c5f1b7d2"
down_revision: Union[str, Sequence[str], None] = "d5f1b8e3a9c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("songs", sa.Column("sha256", sa.String(64), nullable=True))
    op.create_index("ix_songs_sha256", "songs", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_songs_sha256", table_name="songs")
    op.drop_column("songs", "sha256")
