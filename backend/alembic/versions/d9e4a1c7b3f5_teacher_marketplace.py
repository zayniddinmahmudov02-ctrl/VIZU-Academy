"""My Teacher marketplace: public teacher profiles, certificates, teacher courses + enrollments, reviews, free special lessons
with a LiveKit room, VIZU Pay orders for paid teacher courses.

Additive schema (no row is changed or deleted):
* `teacher_profiles` + public profile columns (photo, headline, bio, experience, methodology, exam prep, languages, levels),
  admin flags `catalog_hidden` / `profile_disabled` / `verified` (+ who / when), server-computed `rating_avg` / `rating_count`.
* new tables `teacher_certificates`, `teacher_courses`, `teacher_course_enrollments` (one live enrollment per student and
  course = partial unique index), `teacher_course_interests`, `teacher_reviews` (one per student and course, 1–5),
  `teacher_review_reports`, `special_lessons` (15–90 min), `special_lesson_signups`.
* `subscription_orders.teacher_course_id` (nullable FK + index): a VIZU Pay order for a teacher course (plan TEACHER_COURSE).
* `video_rooms`: `group_id` becomes nullable, new `special_lesson_id` (FK, unique when set) and `hard_end_at`, check
  `ck_video_rooms_owner` (exactly one of group / special lesson — every existing row has a group), room default
  `students_camera_allowed` (true = the behaviour so far); `video_room_participants.can_video` (true = so far).

Downgrade: deletes the special-lesson rooms (they have no group), restores `video_rooms.group_id NOT NULL`, drops the new
columns and tables — their data is lost. Never run on production without a backup.

Revision ID: d9e4a1c7b3f5
Revises: c8d3f5a1e7b2
Create Date: 2026-11-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d9e4a1c7b3f5"
down_revision: Union[str, Sequence[str], None] = "c8d3f5a1e7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _fk(name: str, target: str, ondelete: str, nullable: bool = True) -> sa.Column:
    return sa.Column(name, UUID, sa.ForeignKey(target, ondelete=ondelete), nullable=nullable)


def _base() -> list[sa.Column]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _in(*values: str) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    # ---- teacher_profiles: public profile ----
    for col in (
        sa.Column("photo_path", sa.String(300), nullable=True),
        sa.Column("headline", sa.String(160), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("teaching_since", sa.Integer(), nullable=True),
        sa.Column("specialization", sa.String(300), nullable=True),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("exam_prep", postgresql.JSONB(), nullable=True),
        sa.Column("languages", postgresql.JSONB(), nullable=True),
        sa.Column("levels", postgresql.JSONB(), nullable=True),
        sa.Column("profile_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("catalog_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("profile_disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        _fk("verified_by", "users.id", "SET NULL"),
        sa.Column("rating_avg", sa.Numeric(3, 2), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
    ):
        op.add_column("teacher_profiles", col)
    op.create_check_constraint("ck_teacher_profiles_rating_count", "teacher_profiles", "rating_count >= 0")
    op.create_check_constraint("ck_teacher_profiles_experience", "teacher_profiles",
                               "experience_years IS NULL OR experience_years BETWEEN 0 AND 70")

    # ---- certificates ----
    op.create_table(
        "teacher_certificates", *_base(),
        _fk("teacher_id", "users.id", "CASCADE", nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("issuer", sa.String(200), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=True),
        sa.Column("level", sa.String(40), nullable=True),
        sa.Column("file_name", sa.String(120), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        _fk("reviewed_by", "users.id", "SET NULL"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.String(500), nullable=True),
        sa.CheckConstraint(f"status IN ({_in('pending', 'verified', 'rejected')})", name="ck_teacher_certificates_status"),
    )
    op.create_index("ix_teacher_certificates_teacher_status", "teacher_certificates", ["teacher_id", "status"])

    # ---- courses ----
    op.create_table(
        "teacher_courses", *_base(),
        _fk("teacher_id", "users.id", "CASCADE", nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(40), nullable=False, server_default="Deutsch"),
        sa.Column("level", sa.String(4), nullable=False),
        sa.Column("course_type", sa.String(10), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("duration_weeks", sa.Integer(), nullable=True),
        sa.Column("lessons_per_week", sa.Integer(), nullable=True),
        sa.Column("weekdays", postgresql.JSONB(), nullable=True),
        sa.Column("lesson_time", sa.String(5), nullable=True),
        sa.Column("lesson_minutes", sa.Integer(), nullable=True),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("enrollment_deadline", sa.Date(), nullable=True),
        sa.Column("image_path", sa.String(300), nullable=True),
        sa.Column("status", sa.String(14), nullable=False, server_default="VORBEREITUNG"),
        sa.Column("approval_status", sa.String(12), nullable=False, server_default="DRAFT"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        _fk("reviewed_by", "users.id", "SET NULL"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.String(500), nullable=True),
        _fk("group_id", "study_groups.id", "SET NULL"),
        sa.CheckConstraint(f"course_type IN ({_in('PAID', 'FREE', 'UPCOMING')})", name="ck_teacher_courses_type"),
        sa.CheckConstraint(f"status IN ({_in('ANMELDUNG', 'BALD', 'VORBEREITUNG', 'LAUFEND', 'ABGESCHLOSSEN', 'ABGESAGT')})",
                           name="ck_teacher_courses_status"),
        sa.CheckConstraint(f"approval_status IN ({_in('DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'UNPUBLISHED')})",
                           name="ck_teacher_courses_approval"),
        sa.CheckConstraint("price >= 0 AND (course_type <> 'FREE' OR price = 0)", name="ck_teacher_courses_price"),
        sa.CheckConstraint("max_students BETWEEN 1 AND 500", name="ck_teacher_courses_max_students"),
        sa.CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_teacher_courses_dates"),
    )
    op.create_index("ix_teacher_courses_teacher", "teacher_courses", ["teacher_id", "approval_status"])
    op.create_index("ix_teacher_courses_catalog", "teacher_courses", ["approval_status", "status"])

    op.add_column("subscription_orders", _fk("teacher_course_id", "teacher_courses.id", "SET NULL"))
    op.create_index("ix_subscription_orders_teacher_course_id", "subscription_orders", ["teacher_course_id"])

    live = _in("PENDING_PAYMENT", "ACTIVE", "COMPLETED")
    op.create_table(
        "teacher_course_enrollments", *_base(),
        _fk("course_id", "teacher_courses.id", "CASCADE", nullable=False),
        _fk("student_id", "users.id", "CASCADE", nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        _fk("order_id", "subscription_orders.id", "SET NULL"),
        sa.Column("price_snapshot", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"status IN ({_in('PENDING_PAYMENT', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'REJECTED', 'REFUNDED')})",
                           name="ck_teacher_course_enrollments_status"),
    )
    op.create_index("uq_teacher_course_enrollments_live", "teacher_course_enrollments", ["course_id", "student_id"], unique=True,
                    postgresql_where=sa.text(f"status IN ({live})"))
    op.create_index("ix_teacher_course_enrollments_course_status", "teacher_course_enrollments", ["course_id", "status"])
    op.create_index("ix_teacher_course_enrollments_student", "teacher_course_enrollments", ["student_id"])

    op.create_table(
        "teacher_course_interests", *_base(),
        _fk("course_id", "teacher_courses.id", "CASCADE", nullable=False),
        _fk("student_id", "users.id", "CASCADE", nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("course_id", "student_id", name="uq_teacher_course_interests"),
    )

    # ---- reviews ----
    op.create_table(
        "teacher_reviews", *_base(),
        _fk("teacher_id", "users.id", "CASCADE", nullable=False),
        _fk("student_id", "users.id", "CASCADE", nullable=False),
        _fk("course_id", "teacher_courses.id", "CASCADE", nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="visible"),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
        _fk("hidden_by", "users.id", "SET NULL"),
        sa.Column("hidden_reason", sa.String(500), nullable=True),
        sa.UniqueConstraint("student_id", "course_id", name="uq_teacher_reviews_student_course"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_teacher_reviews_rating"),
        sa.CheckConstraint(f"status IN ({_in('visible', 'hidden')})", name="ck_teacher_reviews_status"),
    )
    op.create_index("ix_teacher_reviews_teacher_status", "teacher_reviews", ["teacher_id", "status", "created_at"])
    op.create_table(
        "teacher_review_reports", *_base(),
        _fk("review_id", "teacher_reviews.id", "CASCADE", nullable=False),
        _fk("reporter_id", "users.id", "CASCADE", nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="open"),
        _fk("resolved_by", "users.id", "SET NULL"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("review_id", "reporter_id", name="uq_teacher_review_reports"),
        sa.CheckConstraint(f"status IN ({_in('open', 'resolved')})", name="ck_teacher_review_reports_status"),
    )
    op.create_index("ix_teacher_review_reports_status", "teacher_review_reports", ["status", "created_at"])

    # ---- special lessons ----
    op.create_table(
        "special_lessons", *_base(),
        _fk("teacher_id", "users.id", "CASCADE", nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("language", sa.String(40), nullable=False, server_default="Deutsch"),
        sa.Column("level", sa.String(4), nullable=False),
        sa.Column("objectives", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(10), nullable=False, server_default="PENDING"),
        _fk("reviewed_by", "users.id", "SET NULL"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.String(500), nullable=True),
        _fk("cancelled_by", "users.id", "SET NULL"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.String(500), nullable=True),
        sa.Column("announcement_message_id", UUID, nullable=True),  # Global Chat message id (no FK: the chat stays independent)
        sa.Column("teacher_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"status IN ({_in('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'ENDED')})", name="ck_special_lessons_status"),
        sa.CheckConstraint("duration_minutes BETWEEN 15 AND 90", name="ck_special_lessons_duration"),
        sa.CheckConstraint("max_participants BETWEEN 2 AND 500", name="ck_special_lessons_max_participants"),
    )
    op.create_index("ix_special_lessons_status_start", "special_lessons", ["status", "starts_at"])
    op.create_index("ix_special_lessons_teacher", "special_lessons", ["teacher_id", "starts_at"])
    op.create_table(
        "special_lesson_signups", *_base(),
        _fk("lesson_id", "special_lessons.id", "CASCADE", nullable=False),
        _fk("user_id", "users.id", "CASCADE", nullable=False),
        sa.UniqueConstraint("lesson_id", "user_id", name="uq_special_lesson_signups"),
    )

    # ---- video rooms: special-lesson rooms, hard end, separate camera permission ----
    op.alter_column("video_rooms", "group_id", existing_type=UUID, nullable=True)
    op.add_column("video_rooms", _fk("special_lesson_id", "special_lessons.id", "CASCADE"))
    op.add_column("video_rooms", sa.Column("hard_end_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("video_rooms", sa.Column("students_camera_allowed", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("video_room_participants", sa.Column("can_video", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_check_constraint("ck_video_rooms_owner", "video_rooms", "(group_id IS NULL) <> (special_lesson_id IS NULL)")
    op.create_index("uq_video_rooms_special_lesson", "video_rooms", ["special_lesson_id"], unique=True,
                    postgresql_where=sa.text("special_lesson_id IS NOT NULL"))
    op.create_index("ix_video_rooms_hard_end", "video_rooms", ["hard_end_at"],
                    postgresql_where=sa.text("status = 'live' AND hard_end_at IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("ix_video_rooms_hard_end", table_name="video_rooms")
    op.drop_index("uq_video_rooms_special_lesson", table_name="video_rooms")
    op.drop_constraint("ck_video_rooms_owner", "video_rooms", type_="check")
    op.execute("DELETE FROM video_rooms WHERE group_id IS NULL")
    op.drop_column("video_room_participants", "can_video")
    op.drop_column("video_rooms", "students_camera_allowed")
    op.drop_column("video_rooms", "hard_end_at")
    op.drop_column("video_rooms", "special_lesson_id")
    op.alter_column("video_rooms", "group_id", existing_type=UUID, nullable=False)

    op.drop_table("special_lesson_signups")
    op.drop_index("ix_special_lessons_teacher", table_name="special_lessons")
    op.drop_index("ix_special_lessons_status_start", table_name="special_lessons")
    op.drop_table("special_lessons")
    op.drop_index("ix_teacher_review_reports_status", table_name="teacher_review_reports")
    op.drop_table("teacher_review_reports")
    op.drop_index("ix_teacher_reviews_teacher_status", table_name="teacher_reviews")
    op.drop_table("teacher_reviews")
    op.drop_table("teacher_course_interests")
    op.drop_index("ix_teacher_course_enrollments_student", table_name="teacher_course_enrollments")
    op.drop_index("ix_teacher_course_enrollments_course_status", table_name="teacher_course_enrollments")
    op.drop_index("uq_teacher_course_enrollments_live", table_name="teacher_course_enrollments")
    op.drop_table("teacher_course_enrollments")
    op.drop_index("ix_subscription_orders_teacher_course_id", table_name="subscription_orders")
    op.drop_column("subscription_orders", "teacher_course_id")
    op.drop_index("ix_teacher_courses_catalog", table_name="teacher_courses")
    op.drop_index("ix_teacher_courses_teacher", table_name="teacher_courses")
    op.drop_table("teacher_courses")
    op.drop_index("ix_teacher_certificates_teacher_status", table_name="teacher_certificates")
    op.drop_table("teacher_certificates")

    op.drop_constraint("ck_teacher_profiles_experience", "teacher_profiles", type_="check")
    op.drop_constraint("ck_teacher_profiles_rating_count", "teacher_profiles", type_="check")
    for name in ("rating_count", "rating_avg", "verified_by", "verified_at", "verified", "profile_disabled", "catalog_hidden",
                 "profile_updated_at", "levels", "languages", "exam_prep", "methodology", "specialization", "teaching_since",
                 "experience_years", "bio", "headline", "photo_path"):
        op.drop_column("teacher_profiles", name)
