"""Add group video chat rooms, sessions and participant events.

Revision ID: c1v7d3e9a5b2
Revises: a6c2e8f4b9d1

Existing groups receive one scheduled room. Downgrade drops the video-chat
tables and their data, leaving groups and memberships untouched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c1v7d3e9a5b2"
down_revision: Union[str, Sequence[str], None] = "a6c2e8f4b9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _base() -> list[sa.Column]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "study_group_video_rooms",
        *_base(),
        sa.Column("group_id", UUID, sa.ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("livekit_room_name", sa.String(128), nullable=False, unique=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column("recording_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.CheckConstraint("status IN ('scheduled', 'live', 'ended')", name="ck_study_group_video_rooms_status"),
        sa.CheckConstraint("max_participants IS NULL OR max_participants > 0", name="ck_study_group_video_rooms_limit"),
    )
    op.create_index("ix_study_group_video_rooms_group_id", "study_group_video_rooms", ["group_id"])

    op.create_table(
        "study_group_video_sessions",
        *_base(),
        sa.Column("room_id", UUID, sa.ForeignKey("study_group_video_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ended_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("peak_participants", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_study_group_video_sessions_room_id", "study_group_video_sessions", ["room_id"])
    op.create_index("ix_study_group_video_sessions_room_started", "study_group_video_sessions", ["room_id", "started_at"])

    op.create_table(
        "study_group_video_events",
        *_base(),
        sa.Column("session_id", UUID, sa.ForeignKey("study_group_video_sessions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("room_id", UUID, sa.ForeignKey("study_group_video_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_study_group_video_events_session_id", "study_group_video_events", ["session_id"])
    op.create_index("ix_study_group_video_events_session_created", "study_group_video_events", ["session_id", "created_at"])

    op.execute(
        """
        INSERT INTO study_group_video_rooms
            (id, created_at, updated_at, group_id, livekit_room_name, status, max_participants, recording_enabled)
        SELECT gen_random_uuid(), now(), now(), id, 'group-' || id::text, 'scheduled', 20, false
        FROM study_groups
        """
    )


def downgrade() -> None:
    op.drop_table("study_group_video_events")
    op.drop_table("study_group_video_sessions")
    op.drop_table("study_group_video_rooms")
