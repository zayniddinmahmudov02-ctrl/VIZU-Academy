"""My Teacher marketplace (2026-11-24, migration d9e4a1c7b3f5): teacher certificates, teacher courses with enrollments and
interest lists, reviews with reports, free special lessons with sign-ups. The rules live in app.services.teacher_market.

* teacher_certificates — files in protected storage (random names); only VERIFIED ones are public.
* teacher_courses — a teacher's own course (not the A1–C1 LMS courses). `approval_status` is the admin side
  (DRAFT → PENDING → APPROVED / REJECTED / UNPUBLISHED), `status` the teacher's public state; an approved course gets a study
  group (`group_id`) — enrolled students become its members, so the group chat and group video lessons are the classroom.
* teacher_course_enrollments — one live enrollment per student and course (partial unique index). A paid course is paid
  through VIZU Pay (subscription_orders.teacher_course_id, manual card transfer approved by a SUPER_ADMIN); the enrollment
  becomes ACTIVE only on that approval. `price_snapshot` keeps what was charged even if the course price changes later.
* teacher_course_interests — "Interesse" for upcoming courses; never an enrollment.
* teacher_reviews — one review per student and course (unique), 1–5 stars; only a student with a real enrollment writes one;
  hiding is a moderation step (row and text stay). teacher_review_reports — reports of a review (one per reporter).
* special_lessons — a teacher's one-off free live lesson (≤ 90 min), visible and joinable only after a SUPER_ADMIN approved
  it; its room is a video_rooms row with special_lesson_id (LiveKit). special_lesson_signups — "Ich nehme teil" (reminders)."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

CERT_PENDING, CERT_VERIFIED, CERT_REJECTED = "pending", "verified", "rejected"
CERT_STATUSES = (CERT_PENDING, CERT_VERIFIED, CERT_REJECTED)

COURSE_PAID, COURSE_FREE, COURSE_UPCOMING = "PAID", "FREE", "UPCOMING"
COURSE_TYPES = (COURSE_PAID, COURSE_FREE, COURSE_UPCOMING)
# the teacher's public state; AUSGEBUCHT is derived (seats full), never stored
ST_ANMELDUNG, ST_BALD, ST_AUSGEBUCHT, ST_VORBEREITUNG = "ANMELDUNG", "BALD", "AUSGEBUCHT", "VORBEREITUNG"
ST_LAUFEND, ST_ABGESCHLOSSEN, ST_ABGESAGT = "LAUFEND", "ABGESCHLOSSEN", "ABGESAGT"
COURSE_STATUSES = (ST_ANMELDUNG, ST_BALD, ST_VORBEREITUNG, ST_LAUFEND, ST_ABGESCHLOSSEN, ST_ABGESAGT)
APPROVAL_DRAFT, APPROVAL_PENDING, APPROVAL_APPROVED = "DRAFT", "PENDING", "APPROVED"
APPROVAL_REJECTED, APPROVAL_UNPUBLISHED = "REJECTED", "UNPUBLISHED"
APPROVAL_STATUSES = (APPROVAL_DRAFT, APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED, APPROVAL_UNPUBLISHED)

EN_PENDING_PAYMENT, EN_ACTIVE, EN_COMPLETED = "PENDING_PAYMENT", "ACTIVE", "COMPLETED"
EN_CANCELLED, EN_REJECTED, EN_REFUNDED = "CANCELLED", "REJECTED", "REFUNDED"
ENROLLMENT_STATUSES = (EN_PENDING_PAYMENT, EN_ACTIVE, EN_COMPLETED, EN_CANCELLED, EN_REJECTED, EN_REFUNDED)
EN_LIVE = (EN_PENDING_PAYMENT, EN_ACTIVE, EN_COMPLETED)  # hold the student's place (one per course)

REVIEW_VISIBLE, REVIEW_HIDDEN = "visible", "hidden"
REPORT_OPEN, REPORT_RESOLVED = "open", "resolved"

SL_PENDING, SL_APPROVED, SL_REJECTED, SL_CANCELLED, SL_ENDED = "PENDING", "APPROVED", "REJECTED", "CANCELLED", "ENDED"
SPECIAL_LESSON_STATUSES = (SL_PENDING, SL_APPROVED, SL_REJECTED, SL_CANCELLED, SL_ENDED)

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


def _ids(*values: str) -> str:
    return ", ".join(f"'{v}'" for v in values)


class TeacherCertificate(BaseModel):
    __tablename__ = "teacher_certificates"
    __table_args__ = (
        CheckConstraint(f"status IN ({_ids(*CERT_STATUSES)})", name="ck_teacher_certificates_status"),
        Index("ix_teacher_certificates_teacher_status", "teacher_id", "status"),
    )

    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    file_name: Mapped[str] = mapped_column(String(120), nullable=False)  # random name inside the protected folder
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # image | pdf
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=CERT_PENDING, server_default=CERT_PENDING)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class TeacherCourse(BaseModel):
    __tablename__ = "teacher_courses"
    __table_args__ = (
        CheckConstraint(f"course_type IN ({_ids(*COURSE_TYPES)})", name="ck_teacher_courses_type"),
        CheckConstraint(f"status IN ({_ids(*COURSE_STATUSES)})", name="ck_teacher_courses_status"),
        CheckConstraint(f"approval_status IN ({_ids(*APPROVAL_STATUSES)})", name="ck_teacher_courses_approval"),
        CheckConstraint("price >= 0 AND (course_type <> 'FREE' OR price = 0)", name="ck_teacher_courses_price"),
        CheckConstraint("max_students BETWEEN 1 AND 500", name="ck_teacher_courses_max_students"),
        CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_teacher_courses_dates"),
        Index("ix_teacher_courses_teacher", "teacher_id", "approval_status"),
        Index("ix_teacher_courses_catalog", "approval_status", "status"),
    )

    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(40), nullable=False, default="Deutsch", server_default="Deutsch")
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    course_type: Mapped[str] = mapped_column(String(10), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")  # UZS
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    duration_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lessons_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekdays: Mapped[list | None] = mapped_column(JSONB(none_as_null=True), nullable=True)  # ["MO", "MI", …]
    lesson_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "18:30" Tashkent time
    lesson_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, default=12, server_default="12")
    enrollment_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(14), nullable=False, default=ST_VORBEREITUNG, server_default=ST_VORBEREITUNG)
    approval_status: Mapped[str] = mapped_column(String(12), nullable=False, default=APPROVAL_DRAFT, server_default=APPROVAL_DRAFT)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    group_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("study_groups.id", ondelete="SET NULL"), nullable=True)

    teacher = relationship("User", foreign_keys=[teacher_id], lazy="joined")


class TeacherCourseEnrollment(BaseModel):
    __tablename__ = "teacher_course_enrollments"
    __table_args__ = (
        CheckConstraint(f"status IN ({_ids(*ENROLLMENT_STATUSES)})", name="ck_teacher_course_enrollments_status"),
        Index("uq_teacher_course_enrollments_live", "course_id", "student_id", unique=True,
              postgresql_where=text(f"status IN ({_ids(*EN_LIVE)})")),
        Index("ix_teacher_course_enrollments_course_status", "course_id", "status"),
        Index("ix_teacher_course_enrollments_student", "student_id"),
    )

    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teacher_courses.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)  # free | payment
    order_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True)
    price_snapshot: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student = relationship("User", foreign_keys=[student_id], lazy="joined")


class TeacherCourseInterest(BaseModel):
    __tablename__ = "teacher_course_interests"
    __table_args__ = (UniqueConstraint("course_id", "student_id", name="uq_teacher_course_interests"),)

    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teacher_courses.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TeacherReview(BaseModel):
    __tablename__ = "teacher_reviews"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_teacher_reviews_student_course"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_teacher_reviews_rating"),
        CheckConstraint(f"status IN ({_ids(REVIEW_VISIBLE, REVIEW_HIDDEN)})", name="ck_teacher_reviews_status"),
        Index("ix_teacher_reviews_teacher_status", "teacher_id", "status", "created_at"),
    )

    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teacher_courses.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=REVIEW_VISIBLE, server_default=REVIEW_VISIBLE)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hidden_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    hidden_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    student = relationship("User", foreign_keys=[student_id], lazy="joined")


class TeacherReviewReport(BaseModel):
    __tablename__ = "teacher_review_reports"
    __table_args__ = (
        UniqueConstraint("review_id", "reporter_id", name="uq_teacher_review_reports"),
        CheckConstraint(f"status IN ({_ids(REPORT_OPEN, REPORT_RESOLVED)})", name="ck_teacher_review_reports_status"),
        Index("ix_teacher_review_reports_status", "status", "created_at"),
    )

    review_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teacher_reviews.id", ondelete="CASCADE"), nullable=False)
    reporter_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=REPORT_OPEN, server_default=REPORT_OPEN)
    resolved_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SpecialLesson(BaseModel):
    __tablename__ = "special_lessons"
    __table_args__ = (
        CheckConstraint(f"status IN ({_ids(*SPECIAL_LESSON_STATUSES)})", name="ck_special_lessons_status"),
        CheckConstraint("duration_minutes BETWEEN 15 AND 90", name="ck_special_lessons_duration"),
        CheckConstraint("max_participants BETWEEN 2 AND 500", name="ck_special_lessons_max_participants"),
        Index("ix_special_lessons_status_start", "status", "starts_at"),
        Index("ix_special_lessons_teacher", "teacher_id", "starts_at"),
    )

    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(40), nullable=False, default="Deutsch", server_default="Deutsch")
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=SL_PENDING, server_default=SL_PENDING)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelled_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # the Global Chat announcement (no FK on purpose: chat messages are never deleted, and the chat stays independent)
    announcement_message_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    teacher_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # "room can be opened"
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # sign-ups: "starts soon"

    teacher = relationship("User", foreign_keys=[teacher_id], lazy="joined")


class SpecialLessonSignup(BaseModel):
    __tablename__ = "special_lesson_signups"
    __table_args__ = (UniqueConstraint("lesson_id", "user_id", name="uq_special_lesson_signups"),)

    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("special_lessons.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
