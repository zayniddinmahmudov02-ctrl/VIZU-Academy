"""listening_audio_tracks + listenings.audio_label: several labelled audio files per Hören task

Additive only: a new table and one nullable column. Every existing Hören task
keeps its main audio exactly as it is (no row is changed). Reversible:
downgrade drops the table and the column (the files of extra tracks stay on
disk and must be removed by hand if wanted).

Revision ID: c3e7a9d2f4b1
Revises: b8d3f1a6c2e9
Create Date: 2026-10-20
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c3e7a9d2f4b1"
down_revision = "b8d3f1a6c2e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listenings", sa.Column("audio_label", sa.String(120), nullable=True))
    op.create_table(
        "listening_audio_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listening_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listenings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("storage_path", sa.String(500), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("original_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_listening_audio_tracks_listening_id", "listening_audio_tracks", ["listening_id"])


def downgrade() -> None:
    op.drop_index("ix_listening_audio_tracks_listening_id", table_name="listening_audio_tracks")
    op.drop_table("listening_audio_tracks")
    op.drop_column("listenings", "audio_label")
