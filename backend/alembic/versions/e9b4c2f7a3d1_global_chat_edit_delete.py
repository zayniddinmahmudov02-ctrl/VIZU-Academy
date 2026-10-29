"""Global Chat: authors edit and delete their own messages.

* global_chat_messages: + edited_at, + deleted_at, status may also be
  'deleted' (the row and text stay, users stop seeing it);
* global_chat_message_edits: the text before each edit (moderators only).

Nothing existing is changed or removed: messages, pins, mutes, bans and the
audit log stay as they are. Downgrade first turns deleted messages into
hidden ones (so the old status constraint holds), then drops the additions.

Revision ID: e9b4c2f7a3d1
Revises: c8f2a6d4e1b9
Create Date: 2026-10-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e9b4c2f7a3d1"
down_revision: Union[str, Sequence[str], None] = "c8f2a6d4e1b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("global_chat_messages", sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("global_chat_messages", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint("ck_global_chat_messages_status", "global_chat_messages", type_="check")
    op.create_check_constraint("ck_global_chat_messages_status", "global_chat_messages",
                               "status IN ('visible', 'pending', 'hidden', 'deleted')")

    op.create_table(
        "global_chat_message_edits",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("message_id", UUID, sa.ForeignKey("global_chat_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("editor_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("previous_body", sa.Text(), nullable=False),
        sa.Column("previous_status", sa.String(10), nullable=False),
    )
    op.create_index("ix_global_chat_message_edits_message_created", "global_chat_message_edits", ["message_id", "created_at"])
    op.create_index("ix_global_chat_message_edits_editor_created", "global_chat_message_edits", ["editor_id", "created_at"])


def downgrade() -> None:
    op.drop_table("global_chat_message_edits")
    op.execute("UPDATE global_chat_messages SET status = 'hidden', hidden_at = deleted_at, hidden_reason = 'deleted by author' "
               "WHERE status = 'deleted'")
    op.drop_constraint("ck_global_chat_messages_status", "global_chat_messages", type_="check")
    op.create_check_constraint("ck_global_chat_messages_status", "global_chat_messages",
                               "status IN ('visible', 'pending', 'hidden')")
    op.drop_column("global_chat_messages", "deleted_at")
    op.drop_column("global_chat_messages", "edited_at")
