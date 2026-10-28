"""Groups & Classroom: study groups, members, join codes, chat,
announcements, lesson tasks, audit log.

Additive only — eight new tables, nothing existing is touched. Progress and
submissions stay in the LMS tables. Downgrade drops exactly these tables.

Revision ID: b7e3d9a2c5f1
Revises: d4b8e2f6a9c1
Create Date: 2026-10-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7e3d9a2c5f1"
down_revision: Union[str, Sequence[str], None] = "d4b8e2f6a9c1"
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
        "study_groups",
        *_base(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        _fk("teacher_id", "users.id", "RESTRICT"),
        sa.Column("level", sa.String(2), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False, server_default="online"),
        sa.Column("status", sa.String(10), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("chat_mode", sa.String(15), nullable=False, server_default="open"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        _fk("created_by", "users.id", "SET NULL", nullable=True),
        sa.CheckConstraint("status IN ('active', 'paused', 'archived', 'blocked')", name="ck_study_groups_status"),
        sa.CheckConstraint("mode IN ('online', 'offline', 'hybrid')", name="ck_study_groups_mode"),
        sa.CheckConstraint("chat_mode IN ('open', 'teacher_only', 'closed')", name="ck_study_groups_chat_mode"),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_study_groups_capacity"),
    )
    op.create_index("ix_study_groups_status", "study_groups", ["status"])
    op.create_index("ix_study_groups_teacher_status", "study_groups", ["teacher_id", "status"])

    op.create_table(
        "study_group_courses",
        *_base(),
        _fk("group_id", "study_groups.id", "CASCADE"),
        _fk("course_id", "courses.id", "CASCADE"),
        sa.UniqueConstraint("group_id", "course_id", name="uq_study_group_course"),
    )
    op.create_index("ix_study_group_courses_group_id", "study_group_courses", ["group_id"])
    op.create_index("ix_study_group_courses_course_id", "study_group_courses", ["course_id"])

    op.create_table(
        "study_group_members",
        *_base(),
        _fk("group_id", "study_groups.id", "CASCADE"),
        _fk("user_id", "users.id", "CASCADE"),
        sa.Column("role", sa.String(10), nullable=False, server_default="student"),
        sa.Column("status", sa.String(10), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("can_post", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("group_id", "user_id", name="uq_study_group_member"),
    )
    op.create_index("ix_study_group_members_group_id", "study_group_members", ["group_id"])
    op.create_index("ix_study_group_members_user_status", "study_group_members", ["user_id", "status"])

    op.create_table(
        "study_group_join_codes",
        *_base(),
        _fk("group_id", "study_groups.id", "CASCADE"),
        sa.Column("code_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        _fk("created_by", "users.id", "SET NULL", nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_study_group_join_codes_group_id", "study_group_join_codes", ["group_id"])

    op.create_table(
        "study_group_messages",
        *_base(),
        _fk("group_id", "study_groups.id", "CASCADE"),
        _fk("sender_id", "users.id", "SET NULL", nullable=True),
        sa.Column("kind", sa.String(10), nullable=False, server_default="text"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        _fk("deleted_by", "users.id", "SET NULL", nullable=True),
    )
    op.create_index("ix_study_group_messages_group_created", "study_group_messages", ["group_id", "created_at"])

    op.create_table(
        "study_group_announcements",
        *_base(),
        _fk("group_id", "study_groups.id", "CASCADE"),
        _fk("author_id", "users.id", "SET NULL", nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_study_group_announcements_group_created", "study_group_announcements", ["group_id", "created_at"])

    op.create_table(
        "study_group_tasks",
        *_base(),
        _fk("group_id", "study_groups.id", "CASCADE"),
        _fk("lesson_id", "lessons.id", "CASCADE"),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        _fk("created_by", "users.id", "SET NULL", nullable=True),
        sa.UniqueConstraint("group_id", "lesson_id", name="uq_study_group_task_lesson"),
    )
    op.create_index("ix_study_group_tasks_group_id", "study_group_tasks", ["group_id"])

    op.create_table(
        "study_group_audit_logs",
        *_base(),
        _fk("group_id", "study_groups.id", "SET NULL", nullable=True),
        _fk("actor_id", "users.id", "SET NULL", nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=True),
        sa.Column("target_id", sa.String(64), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_study_group_audit_logs_group_created", "study_group_audit_logs", ["group_id", "created_at"])


def downgrade() -> None:
    for table in ("study_group_audit_logs", "study_group_tasks", "study_group_announcements", "study_group_messages",
                  "study_group_join_codes", "study_group_members", "study_group_courses", "study_groups"):
        op.drop_table(table)
