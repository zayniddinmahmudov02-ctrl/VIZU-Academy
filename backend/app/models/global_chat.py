"""Global Chat: one chat room for every logged-in user, separate from the
study-group chats (own tables, own API, nothing shared with study_group_*).

* global_chat_messages — plain text. No row is ever deleted: a hidden message
  (moderator) or a deleted one (its author) keeps its body for the moderators
  and the audit trail, users just stop seeing it. Authors may edit their own
  messages; the earlier text goes to global_chat_message_edits. A message the word filter flagged is held ("pending") —
  only its sender and the moderators see it until a moderator approves or
  hides it. Pins live on the message (pinned_at/pinned_by); hiding unpins.
  A message may answer another Global Chat message (reply_to_id).
* global_chat_restrictions — mute / ban for the Global Chat only (never the
  account, the LMS or group chats). Active = not revoked, started and not
  yet ended; an expired row simply stops counting, no job needed. At most
  one live (non-revoked) row per user and kind: a new one supersedes the old.
* global_chat_moderation_actions — audit log: who did what, when and why.
  Never holds a token, password or other secret.
* global_chat_reads — per user: messages up to last_read_at count as read."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

MESSAGE_VISIBLE = "visible"
MESSAGE_PENDING = "pending"  # held by the word filter for a moderator
MESSAGE_HIDDEN = "hidden"  # hidden by a moderator
MESSAGE_DELETED = "deleted"  # deleted by its author (row and text stay for the moderators)
MESSAGE_STATUSES = (MESSAGE_VISIBLE, MESSAGE_PENDING, MESSAGE_HIDDEN, MESSAGE_DELETED)

KIND_MUTE = "mute"
KIND_BAN = "ban"
RESTRICTION_KINDS = (KIND_MUTE, KIND_BAN)


def _ids(*values: str) -> str:
    return ", ".join(f"'{v}'" for v in values)


class GlobalChatMessage(BaseModel):
    __tablename__ = "global_chat_messages"
    __table_args__ = (
        CheckConstraint(f"status IN ({_ids(*MESSAGE_STATUSES)})", name="ck_global_chat_messages_status"),
        Index("ix_global_chat_messages_created_id", "created_at", "id"),
        Index("ix_global_chat_messages_updated", "updated_at"),  # polling: what changed since the last sync
        Index("ix_global_chat_messages_sender_created", "sender_id", "created_at"),
        Index("ix_global_chat_messages_pinned", "pinned_at", postgresql_where=text("pinned_at IS NOT NULL")),
        Index("ix_global_chat_messages_status_created", "status", "created_at",
              postgresql_where=text("status <> 'visible'")),
        Index("ix_global_chat_messages_reply_to", "reply_to_id", postgresql_where=text("reply_to_id IS NOT NULL")),
    )

    sender_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=MESSAGE_VISIBLE, server_default=MESSAGE_VISIBLE)
    # what the word filter matched (normalised words, never shown to users)
    flagged_words: Mapped[list | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hidden_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    hidden_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pinned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pinned_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # only the author edits / deletes, so no edited_by / deleted_by column
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # the Global Chat message this one answers (NULL: no reply; older messages). The FK only allows
    # rows of this table, so a group-chat message can never be the target.
    reply_to_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("global_chat_messages.id", ondelete="SET NULL"),
                                                     nullable=True)

    sender = relationship("User", foreign_keys=[sender_id], lazy="joined")
    reply_to = relationship("GlobalChatMessage", remote_side="GlobalChatMessage.id", foreign_keys=[reply_to_id], lazy="selectin")


class GlobalChatMessageEdit(BaseModel):
    """The text before each edit — moderators only, so editing cannot wipe an
    insult that is waiting for review."""

    __tablename__ = "global_chat_message_edits"
    __table_args__ = (
        Index("ix_global_chat_message_edits_message_created", "message_id", "created_at"),
        Index("ix_global_chat_message_edits_editor_created", "editor_id", "created_at"),
    )

    message_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("global_chat_messages.id", ondelete="CASCADE"), nullable=False)
    editor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_body: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String(10), nullable=False)


class GlobalChatRestriction(BaseModel):
    __tablename__ = "global_chat_restrictions"
    __table_args__ = (
        CheckConstraint(f"kind IN ({_ids(*RESTRICTION_KINDS)})", name="ck_global_chat_restrictions_kind"),
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="ck_global_chat_restrictions_period"),
        CheckConstraint("kind = 'ban' OR ends_at IS NOT NULL", name="ck_global_chat_restrictions_mute_ends"),
        # one live row per user and kind (a new mute/ban revokes the previous one)
        Index("uq_global_chat_restrictions_live", "user_id", "kind", unique=True, postgresql_where=text("revoked_at IS NULL")),
        Index("ix_global_chat_restrictions_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # NULL = permanent ban
    reason: Mapped[str] = mapped_column(Text, nullable=False)  # internal, moderators only
    public_note: Mapped[str | None] = mapped_column(String(300), nullable=True)  # shown to the user
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")


class GlobalChatModerationAction(BaseModel):
    __tablename__ = "global_chat_moderation_actions"
    __table_args__ = (
        Index("ix_global_chat_moderation_actions_created", "created_at"),
        Index("ix_global_chat_moderation_actions_target_created", "target_user_id", "created_at"),
    )

    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    target_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("global_chat_messages.id", ondelete="SET NULL"), nullable=True)
    restriction_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("global_chat_restrictions.id", ondelete="SET NULL"),
                                                        nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    actor = relationship("User", foreign_keys=[actor_id], lazy="joined")
    target_user = relationship("User", foreign_keys=[target_user_id], lazy="joined")


class GlobalChatRead(BaseModel):
    __tablename__ = "global_chat_reads"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    last_read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
