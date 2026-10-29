"""Global Chat: reply to a message.

* global_chat_messages: + reply_to_id (FK to the same table, ON DELETE SET
  NULL) and a partial index on it.

Additive only: every existing message keeps reply_to_id = NULL and behaves
as before. Rows are never deleted by the chat, the SET NULL only matters if
someone removes a row by hand. Downgrade drops the index and the column
(the replies stay as plain messages).

Revision ID: f3a8c1d5e7b2
Revises: e9b4c2f7a3d1
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f3a8c1d5e7b2"
down_revision: Union[str, Sequence[str], None] = "e9b4c2f7a3d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("global_chat_messages", sa.Column("reply_to_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_global_chat_messages_reply_to_id", "global_chat_messages", "global_chat_messages",
                          ["reply_to_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_global_chat_messages_reply_to", "global_chat_messages", ["reply_to_id"],
                    postgresql_where=sa.text("reply_to_id IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("ix_global_chat_messages_reply_to", table_name="global_chat_messages")
    op.drop_constraint("fk_global_chat_messages_reply_to_id", "global_chat_messages", type_="foreignkey")
    op.drop_column("global_chat_messages", "reply_to_id")
