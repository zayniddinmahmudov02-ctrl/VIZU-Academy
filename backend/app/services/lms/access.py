"""VIZU LMS lesson unlock rules — one function, used by the student LMS API
and by `require_lesson_access` (every lesson-content endpoint).

Order of checks for a student:
  1. lesson not published (draft)            -> not visible (404)
  2. access_override = LOCKED                 -> LESSON_LOCKED
  3. Premium / Angebote rule (can_access_lesson) -> PREMIUM_REQUIRED
  4. course.sequential_unlock and the previous published lesson of the
     level not completed (unless access_override = OPEN) -> LESSON_LOCKED
Staff (admin panel roles) pass every check — they review drafts and locked
lessons. With the defaults (published, no override, sequential off) this is
exactly the previous behaviour: only the Premium rule applies."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.lms import ACCESS_LOCKED, ACCESS_OPEN
from app.models.module import Module
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.services.vizu_pay.access import can_access_lesson, has_premium_bypass, is_level_coming_soon, is_level_sales_closed

REASON_DRAFT = "DRAFT"
REASON_ADMIN = "ADMIN_LOCKED"
REASON_PREMIUM = "PREMIUM_REQUIRED"
REASON_SEQUENTIAL = "PREVIOUS_LESSON_NOT_COMPLETED"
REASON_COMING_SOON = "LEVEL_COMING_SOON"
REASON_SALES_CLOSED = "LEVEL_SALES_CLOSED"  # available level, not approved for sale yet


@dataclass(frozen=True)
class LessonAccess:
    visible: bool
    unlocked: bool
    reason: str | None = None

    @property
    def http_detail(self) -> str:
        if self.reason in (REASON_PREMIUM, REASON_COMING_SOON, REASON_SALES_CLOSED):
            return self.reason
        return "LESSON_LOCKED"


def previous_published_lesson(db: Session, lesson: Lesson) -> Lesson | None:
    return db.scalar(
        select(Lesson)
        .where(Lesson.module_id == lesson.module_id, Lesson.is_published.is_(True), Lesson.number < lesson.number)
        .order_by(Lesson.number.desc())
        .limit(1)
    )


def lesson_completed(db: Session, user_id, lesson_id) -> bool:
    return bool(
        db.scalar(
            select(StudentProgress.lesson_completed).where(StudentProgress.user_id == user_id, StudentProgress.lesson_id == lesson_id)
        )
    )


def _sequential(db: Session, lesson: Lesson) -> bool:
    module = db.get(Module, lesson.module_id)
    course = db.get(Course, module.course_id) if module else None
    return bool(course and course.sequential_unlock)


def lesson_access(db: Session, user: User | None, lesson: Lesson) -> LessonAccess:
    if has_premium_bypass(user):
        return LessonAccess(visible=True, unlocked=True)
    if not lesson.is_published:
        return LessonAccess(visible=False, unlocked=False, reason=REASON_DRAFT)
    if lesson.access_override == ACCESS_LOCKED:
        return LessonAccess(visible=True, unlocked=False, reason=REASON_ADMIN)
    if is_level_coming_soon(lesson):
        return LessonAccess(visible=True, unlocked=False, reason=REASON_COMING_SOON)
    if not can_access_lesson(user, lesson):
        # a level not approved for sale: nothing to buy yet ("Tez orada"), not "Premium required"
        return LessonAccess(visible=True, unlocked=False, reason=REASON_SALES_CLOSED if is_level_sales_closed(lesson) else REASON_PREMIUM)
    if lesson.access_override != ACCESS_OPEN and user is not None and _sequential(db, lesson):
        previous = previous_published_lesson(db, lesson)
        if previous is not None and not lesson_completed(db, user.id, previous.id):
            return LessonAccess(visible=True, unlocked=False, reason=REASON_SEQUENTIAL)
    return LessonAccess(visible=True, unlocked=True)


def ensure_lesson_open(db: Session, user: User | None, lesson: Lesson) -> None:
    """Raise the HTTP error for a lesson the user may not open: 404 for a
    draft (students must not learn it exists), 403 PREMIUM_REQUIRED or
    LESSON_LOCKED otherwise."""
    from fastapi import HTTPException, status

    access = lesson_access(db, user, lesson)
    if not access.visible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if not access.unlocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=access.http_detail)
