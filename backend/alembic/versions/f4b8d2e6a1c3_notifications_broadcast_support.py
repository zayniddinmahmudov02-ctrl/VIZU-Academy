"""broadcast notifications (+ read state), support tickets / messages, notifications.link_path

Revision ID: f4b8d2e6a1c3
Revises: e7c3a9f1b5d2
Create Date: 2026-10-20 21:00:00.000000

Additive and backward-compatible: new tables + sequence, one nullable
column on notifications. Existing notifications are untouched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f4b8d2e6a1c3"
down_revision: Union[str, None] = "e7c3a9f1b5d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = sa.DateTime(timezone=True)
_UUID = postgresql.UUID(as_uuid=True)


def _base():
    return [
        sa.Column("id", _UUID, primary_key=True),
        sa.Column("created_at", _TS, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _TS, server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.add_column("notifications", sa.Column("link_path", sa.String(300), nullable=True))
    # badge count: unread personal notifications of one user
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "is_read"])

    op.create_table(
        "broadcast_notifications", *_base(),
        sa.Column("title_de", sa.String(160), nullable=False),
        sa.Column("title_uz", sa.String(160), nullable=False),
        sa.Column("message_de", sa.Text(), nullable=False),
        sa.Column("message_uz", sa.Text(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default="INFO"),
        sa.Column("audience_type", sa.String(20), nullable=False, server_default="ALL"),
        sa.Column("audience_value", sa.String(64), nullable=True),
        sa.Column("link_type", sa.String(20), nullable=False, server_default="NONE"),
        sa.Column("internal_route", sa.String(60), nullable=True),
        sa.Column("internal_params", postgresql.JSONB(), nullable=True),
        sa.Column("external_url", sa.String(1000), nullable=True),
        sa.Column("is_important", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("publish_at", _TS, nullable=True),
        sa.Column("archived_at", _TS, nullable=True),
        sa.Column("created_by_id", _UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("type IN ('INFO','SUCCESS','WARNING','ANNOUNCEMENT')", name="ck_broadcast_type"),
        sa.CheckConstraint("audience_type IN ('ALL','LEVEL','LANGUAGE','USER')", name="ck_broadcast_audience"),
        sa.CheckConstraint("status IN ('DRAFT','PUBLISHED','INACTIVE','ARCHIVED')", name="ck_broadcast_status"),
    )
    op.create_index("ix_broadcast_notifications_visible", "broadcast_notifications", ["status", "publish_at"])
    op.create_table(
        "broadcast_notification_reads", *_base(),
        sa.Column("notification_id", _UUID, sa.ForeignKey("broadcast_notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", _UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("read_at", _TS, nullable=False),
        sa.UniqueConstraint("notification_id", "user_id", name="uq_broadcast_notification_read"),
    )
    op.create_index("ix_broadcast_notification_reads_user_id", "broadcast_notification_reads", ["user_id"])

    op.execute("CREATE SEQUENCE IF NOT EXISTS support_ticket_number_seq START WITH 1001")
    op.create_table(
        "support_tickets", *_base(),
        sa.Column("number", sa.Integer(), nullable=False, unique=True, server_default=sa.text("nextval('support_ticket_number_seq')")),
        sa.Column("user_id", _UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="NEW"),
        sa.Column("assigned_to_id", _UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_message_at", _TS, nullable=False),
        sa.Column("status_changed_at", _TS, nullable=True),
        sa.Column("client_request_id", sa.String(64), nullable=True),
        sa.UniqueConstraint("user_id", "client_request_id", name="uq_support_ticket_request"),
        sa.CheckConstraint("status IN ('NEW','IN_PROGRESS','WAITING','ANSWERED','CLOSED')", name="ck_support_ticket_status"),
        sa.CheckConstraint("category IN ('COURSE','PAYMENT','MEDIA','TESTS','CERTIFICATE','TECHNICAL','OTHER')", name="ck_support_ticket_category"),
    )
    op.execute("ALTER SEQUENCE support_ticket_number_seq OWNED BY support_tickets.number")
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("ix_support_tickets_assigned_to_id", "support_tickets", ["assigned_to_id"])
    op.create_index("ix_support_tickets_status_last", "support_tickets", ["status", "last_message_at"])
    op.create_table(
        "support_messages", *_base(),
        sa.Column("ticket_id", _UUID, sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", _UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("author_role", sa.String(10), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("client_request_id", sa.String(64), nullable=True),
        sa.UniqueConstraint("ticket_id", "client_request_id", name="uq_support_message_request"),
        sa.CheckConstraint("author_role IN ('STUDENT','STAFF')", name="ck_support_message_author"),
    )
    op.create_index("ix_support_messages_ticket_created", "support_messages", ["ticket_id", "created_at"])


def downgrade() -> None:
    op.drop_table("support_messages")
    op.drop_table("support_tickets")
    op.execute("DROP SEQUENCE IF EXISTS support_ticket_number_seq")
    op.drop_table("broadcast_notification_reads")
    op.drop_table("broadcast_notifications")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_column("notifications", "link_path")
