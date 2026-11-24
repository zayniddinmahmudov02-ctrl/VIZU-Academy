"""Group video lessons and free special lessons (LiveKit SFU): rooms, who took part, and what happened.

* A room belongs to one study group (study_groups.id) OR to one approved special lesson (special_lessons.id; since
  2026-11-24, ck_video_rooms_owner: exactly one of the two). Its LiveKit room name is made by the backend
  ("vizu-<room id>") and never chosen by a client.
* At most one room per group is live at a time, at most one room per special lesson (partial unique indexes).
* `hard_end_at`: the server closes the room at this time at the latest (special lessons: start + duration, ≤ 90 min).
* Camera, microphone and screen share are separate permissions (`can_video`, `can_speak`, `can_share_screen`); a special
  lesson starts with students muted and without camera until the teacher allows it.
* One participant row per user per room (a rejoin updates it). Moderation state
  (mic / screen share / chat allowed, removed, blocked) lives here and is pushed
  to LiveKit as participant permissions; a new join token is built from it.
* Events are an append-only log: never a token, a secret or chat text.

Media never passes through the backend; meeting chat goes over the LiveKit data
channel and is not stored."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

ROOM_SCHEDULED = "scheduled"
ROOM_LIVE = "live"
ROOM_ENDED = "ended"
ROOM_CANCELLED = "cancelled"
ROOM_STATUSES = (ROOM_SCHEDULED, ROOM_LIVE, ROOM_ENDED, ROOM_CANCELLED)

ROLE_HOST = "host"  # the group's teacher (or a SUPER_ADMIN): moderates
ROLE_STUDENT = "student"
PARTICIPANT_ROLES = (ROLE_HOST, ROLE_STUDENT)

CONN_JOINING = "joining"  # a join token was issued, LiveKit has not confirmed yet
CONN_CONNECTED = "connected"
CONN_RECONNECTING = "reconnecting"
CONN_DISCONNECTED = "disconnected"
CONN_LEFT = "left"
CONN_REMOVED = "removed"
CONNECTION_STATUSES = (CONN_JOINING, CONN_CONNECTED, CONN_RECONNECTING, CONN_DISCONNECTED, CONN_LEFT, CONN_REMOVED)
ONLINE = (CONN_CONNECTED, CONN_RECONNECTING)


def _ids(*values: str) -> str:
    return ", ".join(f"'{v}'" for v in values)


class VideoRoom(BaseModel):
    __tablename__ = "video_rooms"
    __table_args__ = (
        CheckConstraint(f"status IN ({_ids(*ROOM_STATUSES)})", name="ck_video_rooms_status"),
        CheckConstraint("max_participants BETWEEN 2 AND 500", name="ck_video_rooms_max_participants"),
        UniqueConstraint("room_name", name="uq_video_rooms_room_name"),
        CheckConstraint("(group_id IS NULL) <> (special_lesson_id IS NULL)", name="ck_video_rooms_owner"),
        Index("ix_video_rooms_group_status", "group_id", "status"),
        Index("ix_video_rooms_status_scheduled", "status", "scheduled_at"),
        Index("uq_video_rooms_one_live_per_group", "group_id", unique=True, postgresql_where=text("status = 'live'")),
        Index("uq_video_rooms_special_lesson", "special_lesson_id", unique=True, postgresql_where=text("special_lesson_id IS NOT NULL")),
        Index("ix_video_rooms_hard_end", "hard_end_at", postgresql_where=text("status = 'live' AND hard_end_at IS NOT NULL")),
    )

    group_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=True)
    special_lesson_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("special_lessons.id", ondelete="CASCADE"),
                                                           nullable=True)
    hard_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    room_name: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default=ROOM_SCHEDULED, server_default=ROOM_SCHEDULED)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(String(20), nullable=True)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=25, server_default="25")
    # room-wide moderation defaults; a new participant starts with these
    chat_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    students_can_share_screen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    students_mic_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    students_camera_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    creator = relationship("User", foreign_keys=[created_by], lazy="joined")


class VideoRoomParticipant(BaseModel):
    __tablename__ = "video_room_participants"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_video_room_participant"),
        CheckConstraint(f"role IN ({_ids(*PARTICIPANT_ROLES)})", name="ck_video_room_participants_role"),
        CheckConstraint(f"connection_status IN ({_ids(*CONNECTION_STATUSES)})", name="ck_video_room_participants_connection"),
        Index("ix_video_room_participants_room_status", "room_id", "connection_status"),
        Index("ix_video_room_participants_user", "user_id"),
    )

    room_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("video_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default=ROLE_STUDENT, server_default=ROLE_STUDENT)
    connection_status: Mapped[str] = mapped_column(String(15), nullable=False, default=CONN_JOINING, server_default=CONN_JOINING)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    join_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_token_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    can_speak: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    can_video: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    can_share_screen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_chat: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    hand_raised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # removed and may not join this room again
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    user = relationship("User", foreign_keys=[user_id], lazy="joined")


class VideoRoomEvent(BaseModel):
    __tablename__ = "video_room_events"
    __table_args__ = (Index("ix_video_room_events_room_created", "room_id", "created_at"),)

    room_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("video_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # "metadata" is reserved on declarative classes: attribute meta, column metadata
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
