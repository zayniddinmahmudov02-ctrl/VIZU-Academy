"""Groups & Classroom: a teacher's study group, its members, join codes,
chat, announcements, lesson tasks with deadlines and an audit log.

Only group data lives here. Learning progress, submissions and grades stay
in the existing LMS tables (student_progress, student_competency_progress,
student_writings, student_speakings, homework_submissions) and are read from
there (app.services.study_groups.progress) — there is no second progress
store. Joining a group never enrolls a student in a course.

Table names are prefixed study_ ("groups" is too generic next to the
existing user/role tables)."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

GROUP_ACTIVE = "active"
GROUP_PAUSED = "paused"
GROUP_ARCHIVED = "archived"
GROUP_BLOCKED = "blocked"  # set by a SUPER_ADMIN only
GROUP_STATUSES = (GROUP_ACTIVE, GROUP_PAUSED, GROUP_ARCHIVED, GROUP_BLOCKED)

MODES = ("online", "offline", "hybrid")

CHAT_OPEN = "open"  # every member may write
CHAT_TEACHER_ONLY = "teacher_only"  # only the teacher writes, students read
CHAT_CLOSED = "closed"  # nobody writes
CHAT_MODES = (CHAT_OPEN, CHAT_TEACHER_ONLY, CHAT_CLOSED)

MEMBER_TEACHER = "teacher"
MEMBER_STUDENT = "student"
MEMBER_ACTIVE = "active"
MEMBER_REMOVED = "removed"
MEMBER_LEFT = "left"

CODE_ACTIVE = "active"
CODE_PAUSED = "paused"
CODE_REVOKED = "revoked"

MESSAGE_TEXT = "text"
MESSAGE_SYSTEM = "system"


def _ids(*values: str) -> str:
    return ", ".join(f"'{v}'" for v in values)


class StudyGroup(BaseModel):
    __tablename__ = "study_groups"
    __table_args__ = (
        CheckConstraint(f"status IN ({_ids(*GROUP_STATUSES)})", name="ck_study_groups_status"),
        CheckConstraint(f"mode IN ({_ids(*MODES)})", name="ck_study_groups_mode"),
        CheckConstraint(f"chat_mode IN ({_ids(*CHAT_MODES)})", name="ck_study_groups_chat_mode"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_study_groups_capacity"),
        Index("ix_study_groups_teacher_status", "teacher_id", "status"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    level: Mapped[str] = mapped_column(String(2), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False, default="online", server_default="online")
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=GROUP_ACTIVE, server_default=GROUP_ACTIVE, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chat_mode: Mapped[str] = mapped_column(String(15), nullable=False, default=CHAT_OPEN, server_default=CHAT_OPEN)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    teacher = relationship("User", foreign_keys=[teacher_id], lazy="joined")


class StudyGroupCourse(BaseModel):
    """A course (and so its lessons) the group works with. Not an enrollment."""

    __tablename__ = "study_group_courses"
    __table_args__ = (UniqueConstraint("group_id", "course_id", name="uq_study_group_course"),)

    group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)


class StudyGroupMember(BaseModel):
    __tablename__ = "study_group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_study_group_member"),
        Index("ix_study_group_members_user_status", "user_id", "status"),
    )

    group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default=MEMBER_STUDENT, server_default=MEMBER_STUDENT)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=MEMBER_ACTIVE, server_default=MEMBER_ACTIVE)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # a teacher may take away one student's right to write in the chat
    can_post: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    # chat messages up to here count as read
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", lazy="joined")


class StudyGroupJoinCode(BaseModel):
    """Only a keyed hash of the code is stored (HMAC-SHA256 with SECRET_KEY);
    the plain code is shown once, when it is generated."""

    __tablename__ = "study_group_join_codes"

    group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=CODE_ACTIVE, server_default=CODE_ACTIVE)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudyGroupMessage(BaseModel):
    __tablename__ = "study_group_messages"
    __table_args__ = (Index("ix_study_group_messages_group_created", "group_id", "created_at"),)

    group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default=MESSAGE_TEXT, server_default=MESSAGE_TEXT)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # moderation hides the text; the row stays (audit log has who and why)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    sender = relationship("User", foreign_keys=[sender_id], lazy="joined")


class StudyGroupAnnouncement(BaseModel):
    __tablename__ = "study_group_announcements"
    __table_args__ = (Index("ix_study_group_announcements_group_created", "group_id", "created_at"),)

    group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author = relationship("User", lazy="joined")


class StudyGroupTask(BaseModel):
    """A lesson the teacher sets as group work, with an optional deadline.
    Whether a student did it is read from the LMS, never stored here."""

    __tablename__ = "study_group_tasks"
    __table_args__ = (UniqueConstraint("group_id", "lesson_id", name="uq_study_group_task_lesson"),)

    group_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class StudyGroupAuditLog(BaseModel):
    """Who did what in a group. Never holds a join code, token or password."""

    __tablename__ = "study_group_audit_logs"
    __table_args__ = (Index("ix_study_group_audit_logs_group_created", "group_id", "created_at"),)

    group_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="SET NULL"), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
