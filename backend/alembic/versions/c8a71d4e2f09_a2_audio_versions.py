"""Add safe audio replacement history and A2 material mapping.

Revision ID: c8a71d4e2f09
Revises: b7d91a2f0c64
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c8a71d4e2f09"
down_revision: Union[str, Sequence[str], None] = "b7d91a2f0c64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("listenings", sa.Column("a2_material_key", sa.String(length=50), nullable=True))
    op.create_unique_constraint("uq_listenings_a2_material_key", "listenings", ["a2_material_key"])
    op.create_table(
        "listening_audio_archives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "listening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listenings.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "replaced_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_listening_audio_archives_listening_id",
        "listening_audio_archives",
        ["listening_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_listening_audio_archives_listening_id", table_name="listening_audio_archives")
    op.drop_table("listening_audio_archives")
    op.drop_constraint("uq_listenings_a2_material_key", "listenings", type_="unique")
    op.drop_column("listenings", "a2_material_key")
