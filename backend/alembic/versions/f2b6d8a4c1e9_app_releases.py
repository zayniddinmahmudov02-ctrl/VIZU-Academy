"""VIZU DEUTSCH mobile app: app_releases (Android APK release management).

Additive only: one new table. No existing table or row is touched.
Partial unique index uq_app_releases_latest_per_platform: at most one `is_latest` row per platform.

Downgrade drops exactly this table (release metadata is lost; the APK files in
app/protected_storage/app-releases stay on disk).

Revision ID: f2b6d8a4c1e9
Revises: e5a9c3f1b7d2
Create Date: 2026-11-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f2b6d8a4c1e9"
down_revision: Union[str, Sequence[str], None] = "e5a9c3f1b7d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "app_releases",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False, server_default="android"),
        sa.Column("version_name", sa.String(40), nullable=False),
        sa.Column("version_code", sa.Integer(), nullable=False),
        sa.Column("min_android_version", sa.String(20), nullable=False, server_default="7.0"),
        sa.Column("release_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("storage_name", sa.String(80), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("signer_sha256", sa.String(64), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("platform", "version_code", name="uq_app_releases_platform_version_code"),
        sa.UniqueConstraint("storage_name", name="uq_app_releases_storage_name"),
    )
    op.create_index("uq_app_releases_latest_per_platform", "app_releases", ["platform"], unique=True,
                    postgresql_where=sa.text("is_latest"))


def downgrade() -> None:
    op.drop_index("uq_app_releases_latest_per_platform", table_name="app_releases")
    op.drop_table("app_releases")
