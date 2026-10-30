"""A2 audio processing: a2_audio_transcripts (one row per audio content).

Additive only: a new table. Downgrade drops it — tasks, keys and audio files
are untouched (transcripts written into listenings.transcript stay there).

Revision ID: c4f7a9e2d6b3
Revises: b8e3d1a7c5f2
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4f7a9e2d6b3"
down_revision: Union[str, Sequence[str], None] = "b8e3d1a7c5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "a2_audio_transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("segments", postgresql.JSONB(), nullable=True),
        sa.Column("model", sa.String(80), nullable=True),
        sa.Column("quality", postgresql.JSONB(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("storage_paths", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("matches", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('TRANSCRIBING', 'TRANSCRIBED', 'NEEDS_REVIEW', 'FAILED')", name="ck_a2_audio_transcripts_status"),
    )
    op.create_index("uq_a2_audio_transcripts_sha256", "a2_audio_transcripts", ["sha256"], unique=True)


def downgrade() -> None:
    op.drop_table("a2_audio_transcripts")
