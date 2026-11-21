"""Group video lessons (LiveKit SFU): rooms, participants and an event log per study group.

Additive only: three new tables.
* `video_rooms`: group FK (CASCADE), creator / ended_by FKs (SET NULL), backend-made `room_name` (unique), title, description,
  status scheduled / live / ended / cancelled, scheduled_at / started_at / ended_at, end_reason, max_participants and the
  room-wide moderation defaults (chat, student screen share, student microphone). Partial unique index: one live room per group.
* `video_room_participants`: one row per (room, user) (unique), role host / student, connection status, join / leave times,
  per-participant mic / screen share / chat permission, raised hand, removed / blocked.
* `video_room_events`: append-only log (event_type, JSONB metadata; never tokens or chat text).
study_groups, study_group_members and users are not changed. Downgrade drops exactly these three tables (and their data).

Revision ID: b7e4c2a9d6f1
Revises: a6c2e8f4b9d1
Create Date: 2026-11-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b7e4c2a9d6f1"
down_revision: Union[str, Sequence[str], None] = "a6c2e8f4b9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_fk(name: str, target: str, ondelete: str, nullable: bool) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), sa.ForeignKey(target, ondelete=ondelete), nullable=nullable)


def _times() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "video_rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _uuid_fk("group_id", "study_groups.id", "CASCADE", False),
        _uuid_fk("created_by", "users.id", "SET NULL", True),
        sa.Column("room_name", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        _uuid_fk("ended_by", "users.id", "SET NULL", True),
        sa.Column("end_reason", sa.String(20), nullable=True),
        sa.Column("max_participants", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("chat_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("students_can_share_screen", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("students_mic_allowed", sa.Boolean(), nullable=False, server_default="true"),
        *_times(),
        sa.CheckConstraint("status IN ('scheduled', 'live', 'ended', 'cancelled')", name="ck_video_rooms_status"),
        sa.CheckConstraint("max_participants BETWEEN 2 AND 500", name="ck_video_rooms_max_participants"),
        sa.UniqueConstraint("room_name", name="uq_video_rooms_room_name"),
    )
    op.create_index("ix_video_rooms_group_status", "video_rooms", ["group_id", "status"])
    op.create_index("ix_video_rooms_status_scheduled", "video_rooms", ["status", "scheduled_at"])
    op.create_index("uq_video_rooms_one_live_per_group", "video_rooms", ["group_id"], unique=True,
                    postgresql_where=sa.text("status = 'live'"))

    op.create_table(
        "video_room_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _uuid_fk("room_id", "video_rooms.id", "CASCADE", False),
        _uuid_fk("user_id", "users.id", "CASCADE", False),
        sa.Column("role", sa.String(10), nullable=False, server_default="student"),
        sa.Column("connection_status", sa.String(15), nullable=False, server_default="joining"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("join_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_token_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("can_speak", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("can_share_screen", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_chat", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("hand_raised_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        _uuid_fk("removed_by", "users.id", "SET NULL", True),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default="false"),
        *_times(),
        sa.UniqueConstraint("room_id", "user_id", name="uq_video_room_participant"),
        sa.CheckConstraint("role IN ('host', 'student')", name="ck_video_room_participants_role"),
        sa.CheckConstraint("connection_status IN ('joining', 'connected', 'reconnecting', 'disconnected', 'left', 'removed')",
                           name="ck_video_room_participants_connection"),
    )
    op.create_index("ix_video_room_participants_room_status", "video_room_participants", ["room_id", "connection_status"])
    op.create_index("ix_video_room_participants_user", "video_room_participants", ["user_id"])

    op.create_table(
        "video_room_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _uuid_fk("room_id", "video_rooms.id", "CASCADE", False),
        _uuid_fk("user_id", "users.id", "SET NULL", True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        *_times(),
    )
    op.create_index("ix_video_room_events_room_created", "video_room_events", ["room_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_video_room_events_room_created", table_name="video_room_events")
    op.drop_table("video_room_events")
    op.drop_index("ix_video_room_participants_user", table_name="video_room_participants")
    op.drop_index("ix_video_room_participants_room_status", table_name="video_room_participants")
    op.drop_table("video_room_participants")
    op.drop_index("uq_video_rooms_one_live_per_group", table_name="video_rooms")
    op.drop_index("ix_video_rooms_status_scheduled", table_name="video_rooms")
    op.drop_index("ix_video_rooms_group_status", table_name="video_rooms")
    op.drop_table("video_rooms")
