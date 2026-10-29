"""A2 Audio Manager: a2_audio_assets (one row per uploaded A2 audio file).

Additive only: a new table, nothing existing changes. Files stay in the
private Hören storage; listenings keep pointing at their audio as before.
Downgrade drops the table — the stored files are NOT deleted (they then
show up as "no database entry" in Media Management and can be reviewed).

Revision ID: a6d2f9c4e8b1
Revises: f3a8c1d5e7b2
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a6d2f9c4e8b1"
down_revision: Union[str, Sequence[str], None] = "f3a8c1d5e7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "a2_audio_assets",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("level", sa.String(5), nullable=False, server_default="A2"),
        sa.Column("unterricht", sa.Integer(), nullable=True),
        sa.Column("audio_kind", sa.String(20), nullable=True),
        sa.Column("part", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("parsed", postgresql.JSONB(), nullable=True),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("audio_format", sa.String(10), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verification", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("listening_id", UUID, sa.ForeignKey("listenings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("level = 'A2'", name="ck_a2_audio_assets_level"),
        sa.CheckConstraint("audio_kind IS NULL OR audio_kind IN ('HOEREN', 'TEXT', 'UNTERRICHT', 'OTHER')", name="ck_a2_audio_assets_kind"),
        sa.CheckConstraint("verification IN ('pending', 'verified', 'problem')", name="ck_a2_audio_assets_verification"),
        sa.CheckConstraint("unterricht IS NULL OR unterricht BETWEEN 1 AND 99", name="ck_a2_audio_assets_unterricht"),
        sa.CheckConstraint("part IS NULL OR part BETWEEN 1 AND 99", name="ck_a2_audio_assets_part"),
    )
    op.create_index("uq_a2_audio_assets_sha256", "a2_audio_assets", ["sha256"], unique=True)
    op.create_index("uq_a2_audio_assets_listening", "a2_audio_assets", ["listening_id"], unique=True,
                    postgresql_where=sa.text("listening_id IS NOT NULL"))
    op.create_index("ix_a2_audio_assets_unterricht_order", "a2_audio_assets", ["unterricht", "sort_order"])


def downgrade() -> None:
    op.drop_table("a2_audio_assets")
