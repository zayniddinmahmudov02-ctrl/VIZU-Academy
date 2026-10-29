"""Global Chat: messages, restrictions (mute / ban), moderation log, reads.

Additive only — four new tables, nothing existing is touched (study_group_*
chats stay separate). Downgrade drops exactly these tables.

Revision ID: c8f2a6d4e1b9
Revises: b7e3d9a2c5f1
Create Date: 2026-10-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c8f2a6d4e1b9"
down_revision: Union[str, Sequence[str], None] = "b7e3d9a2c5f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _base() -> list[sa.Column]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _fk(name: str, target: str, ondelete: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, UUID, sa.ForeignKey(target, ondelete=ondelete), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "global_chat_messages",
        *_base(),
        _fk("sender_id", "users.id", "SET NULL", nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="visible"),
        sa.Column("flagged_words", postgresql.JSONB(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        _fk("reviewed_by", "users.id", "SET NULL", nullable=True),
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
        _fk("hidden_by", "users.id", "SET NULL", nullable=True),
        sa.Column("hidden_reason", sa.String(500), nullable=True),
        sa.Column("pinned_at", sa.DateTime(timezone=True), nullable=True),
        _fk("pinned_by", "users.id", "SET NULL", nullable=True),
        sa.CheckConstraint("status IN ('visible', 'pending', 'hidden')", name="ck_global_chat_messages_status"),
    )
    op.create_index("ix_global_chat_messages_created_id", "global_chat_messages", ["created_at", "id"])
    op.create_index("ix_global_chat_messages_updated", "global_chat_messages", ["updated_at"])
    op.create_index("ix_global_chat_messages_sender_created", "global_chat_messages", ["sender_id", "created_at"])
    op.create_index("ix_global_chat_messages_pinned", "global_chat_messages", ["pinned_at"],
                    postgresql_where=sa.text("pinned_at IS NOT NULL"))
    op.create_index("ix_global_chat_messages_status_created", "global_chat_messages", ["status", "created_at"],
                    postgresql_where=sa.text("status <> 'visible'"))

    op.create_table(
        "global_chat_restrictions",
        *_base(),
        _fk("user_id", "users.id", "CASCADE"),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("public_note", sa.String(300), nullable=True),
        _fk("created_by", "users.id", "SET NULL", nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        _fk("revoked_by", "users.id", "SET NULL", nullable=True),
        sa.Column("revoke_reason", sa.String(500), nullable=True),
        sa.CheckConstraint("kind IN ('mute', 'ban')", name="ck_global_chat_restrictions_kind"),
        sa.CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="ck_global_chat_restrictions_period"),
        sa.CheckConstraint("kind = 'ban' OR ends_at IS NOT NULL", name="ck_global_chat_restrictions_mute_ends"),
    )
    op.create_index("uq_global_chat_restrictions_live", "global_chat_restrictions", ["user_id", "kind"], unique=True,
                    postgresql_where=sa.text("revoked_at IS NULL"))
    op.create_index("ix_global_chat_restrictions_user_created", "global_chat_restrictions", ["user_id", "created_at"])

    op.create_table(
        "global_chat_moderation_actions",
        *_base(),
        _fk("actor_id", "users.id", "SET NULL", nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        _fk("target_user_id", "users.id", "SET NULL", nullable=True),
        _fk("message_id", "global_chat_messages.id", "SET NULL", nullable=True),
        _fk("restriction_id", "global_chat_restrictions.id", "SET NULL", nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_global_chat_moderation_actions_created", "global_chat_moderation_actions", ["created_at"])
    op.create_index("ix_global_chat_moderation_actions_target_created", "global_chat_moderation_actions",
                    ["target_user_id", "created_at"])

    op.create_table(
        "global_chat_reads",
        *_base(),
        _fk("user_id", "users.id", "CASCADE"),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_global_chat_reads_user_id"),
    )


def downgrade() -> None:
    for table in ("global_chat_reads", "global_chat_moderation_actions", "global_chat_restrictions", "global_chat_messages"):
        op.drop_table(table)
