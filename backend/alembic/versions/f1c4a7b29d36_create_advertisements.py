"""create advertisements + advertisement_events (dashboard Werbung-Banner)

Revision ID: f1c4a7b29d36
Revises: e5b8c2f17a94
Create Date: 2026-10-07 00:00:00.000000

New, additive tables only.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f1c4a7b29d36"
down_revision: Union[str, None] = "e5b8c2f17a94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "advertisements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("target_url", sa.String(1000), nullable=False),
        sa.Column("cta_text", sa.String(60), server_default="Mehr erfahren", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("starts_at", _TS, nullable=True),
        sa.Column("ends_at", _TS, nullable=True),
    )
    op.create_index("ix_advertisements_is_active", "advertisements", ["is_active"])

    op.create_table(
        "advertisement_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", _TS, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "advertisement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("advertisements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_advertisement_events_advertisement_id", "advertisement_events", ["advertisement_id"])
    op.create_index("ix_advertisement_events_event_type", "advertisement_events", ["event_type"])
    op.create_index("ix_advertisement_events_user_id", "advertisement_events", ["user_id"])
    op.create_index("ix_advertisement_events_client_hash", "advertisement_events", ["client_hash"])
    op.create_index("ix_advertisement_events_created_at", "advertisement_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("advertisement_events")
    op.drop_table("advertisements")
