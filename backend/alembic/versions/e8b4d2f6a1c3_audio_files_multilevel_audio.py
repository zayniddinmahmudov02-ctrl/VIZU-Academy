"""Central audio files (upload + trim) and Multilevel Audio slots.

Adds
- table audio_files: one stored audio file of the central audio service — an uploaded ORIGINAL or a TRIMMED cut of
  one (source_id, trim_start_ms, trim_end_ms), with content type, size, duration, sha256, uploader. Files stay in the
  private lesson-listening storage; nothing is copied or moved;
- nullable listening_contents.audio_file_id (Multilevel Hören Teil -> the file the exam plays; NULL = as before, the
  legacy audio_url is used).

No existing row or file is changed. Downgrade drops exactly these objects (the files on disk stay).

Revision ID: e8b4d2f6a1c3
Revises: c7e1f3a9b2d5
Create Date: 2026-11-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e8b4d2f6a1c3"
down_revision: Union[str, Sequence[str], None] = "c7e1f3a9b2d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "audio_files",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("audio_files.id", ondelete="RESTRICT", name="fk_audio_files_source_id"), nullable=True),
        sa.Column("trim_start_ms", sa.Integer(), nullable=True),
        sa.Column("trim_end_ms", sa.Integer(), nullable=True),
        sa.Column("original_name", sa.String(255), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_audio_files_created_by_id"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("storage_path", name="uq_audio_files_storage_path"),
        sa.CheckConstraint("kind IN ('ORIGINAL','TRIMMED')", name="ck_audio_files_kind"),
        sa.CheckConstraint("kind = 'ORIGINAL' OR (source_id IS NOT NULL AND trim_end_ms > trim_start_ms)", name="ck_audio_files_trim"),
    )
    op.create_index("ix_audio_files_source_id", "audio_files", ["source_id"])
    op.add_column("listening_contents", sa.Column("audio_file_id", UUID, nullable=True))
    op.create_foreign_key("fk_listening_contents_audio_file_id", "listening_contents", "audio_files", ["audio_file_id"], ["id"],
                          ondelete="SET NULL")
    op.create_index("ix_listening_contents_audio_file_id", "listening_contents", ["audio_file_id"])


def downgrade() -> None:
    op.drop_index("ix_listening_contents_audio_file_id", table_name="listening_contents")
    op.drop_constraint("fk_listening_contents_audio_file_id", "listening_contents", type_="foreignkey")
    op.drop_column("listening_contents", "audio_file_id")
    op.drop_index("ix_audio_files_source_id", table_name="audio_files")
    op.drop_table("audio_files")
