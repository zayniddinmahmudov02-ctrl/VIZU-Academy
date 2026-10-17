"""app_settings: admin-editable configuration (Angebote prices / sale status /
packages / free lessons / level availability)

A new, empty table — nothing existing is changed; without a row the code
defaults (app/services/vizu_pay/offers.py) apply exactly as before.
Reversible: downgrade drops only this table.

Revision ID: a7c2e9d4b1f3
Revises: f3d9b2e7c4a1
Create Date: 2026-10-17
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a7c2e9d4b1f3"
down_revision = "f3d9b2e7c4a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False, unique=True),
        sa.Column("value", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
