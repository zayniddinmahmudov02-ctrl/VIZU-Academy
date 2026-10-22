"""Add metadata and append-only history for managed admin routes.

Revision ID: d2e6a9f4b7c1
Revises: c8a71d4e2f09
Create Date: 2026-10-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d2e6a9f4b7c1"
down_revision: Union[str, Sequence[str], None] = "c8a71d4e2f09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "managed_pages",
        sa.Column("route", sa.String(length=255), nullable=False),
        sa.Column("navigation_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("route"),
    )
    op.create_index("ix_managed_pages_route", "managed_pages", ["route"], unique=False)
    op.create_index("ix_managed_pages_updated_by_id", "managed_pages", ["updated_by_id"], unique=False)

    op.create_table(
        "managed_page_audits",
        sa.Column("route", sa.String(length=255), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("previous_state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("new_state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_managed_page_audits_route", "managed_page_audits", ["route"], unique=False)
    op.create_index("ix_managed_page_audits_actor_id", "managed_page_audits", ["actor_id"], unique=False)
    op.create_index("ix_managed_page_audits_action", "managed_page_audits", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_managed_page_audits_action", table_name="managed_page_audits")
    op.drop_index("ix_managed_page_audits_actor_id", table_name="managed_page_audits")
    op.drop_index("ix_managed_page_audits_route", table_name="managed_page_audits")
    op.drop_table("managed_page_audits")
    op.drop_index("ix_managed_pages_updated_by_id", table_name="managed_pages")
    op.drop_index("ix_managed_pages_route", table_name="managed_pages")
    op.drop_table("managed_pages")
