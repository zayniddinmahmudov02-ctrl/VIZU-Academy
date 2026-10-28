"""Hooks from the existing grading services into groups.

* scoped_row: a teacher may open / grade / listen to a submission when the
  student is an active member of a (not blocked) group the teacher leads and
  that group works with the submission's course — in addition to the
  existing TeacherAssignment rule, never instead of it. A SUPER_ADMIN reaches
  every group's students. Grading itself stays in the existing services.
* after_submission / after_grading: in-app notifications. They never break
  the submission or the grade they follow (failures are only logged)."""

import logging
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.notification import TYPE_COURSE
from app.models.study_group import GROUP_BLOCKED, MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupCourse, StudyGroupMember
from app.models.user import User

log = logging.getLogger(__name__)

STATUS_LABEL = {"GRADED": "qabul qilindi / angenommen", "NEEDS_REVISION": "tuzatish kerak / Überarbeitung nötig"}


def _groups_of(db: Session, teacher_id):
    teacher = db.get(User, teacher_id)
    stmt = select(StudyGroup.id).where(StudyGroup.status != GROUP_BLOCKED)
    if teacher is None or teacher.role != UserRole.SUPER_ADMIN:
        stmt = stmt.where(StudyGroup.teacher_id == teacher_id)
    return stmt


def group_course_ids_for_teacher(db: Session, teacher_id) -> list[str]:
    return [str(c) for c in db.scalars(select(StudyGroupCourse.course_id).where(StudyGroupCourse.group_id.in_(_groups_of(db, teacher_id))).distinct())]


def teacher_reaches_student(db: Session, teacher_id, student_id, course_id) -> bool:
    return bool(db.scalar(select(exists().where(
        StudyGroupMember.group_id.in_(_groups_of(db, teacher_id)),
        StudyGroupMember.user_id == student_id, StudyGroupMember.status == MEMBER_ACTIVE, StudyGroupMember.role == MEMBER_STUDENT,
        StudyGroupMember.group_id.in_(select(StudyGroupCourse.group_id).where(StudyGroupCourse.course_id == UUID(str(course_id))))))))


def scoped_row(db: Session, repository, teacher_id, submission_id):
    """Row (submission, task, lesson, module, course, student) or None."""
    course_ids = group_course_ids_for_teacher(db, teacher_id)
    if not course_ids:
        return None
    row = repository.get_for_teacher(course_ids, submission_id)
    if row is not None and teacher_reaches_student(db, teacher_id, row[-1].id, row[4].id):
        return row
    return None


def after_submission(db: Session, student_id, lesson_id, what: str) -> None:
    try:
        from app.services.study_groups import notify

        course_id = db.scalar(select(Module.course_id).join(Lesson, Lesson.module_id == Module.id).where(Lesson.id == lesson_id))
        if course_id is not None:
            notify.submission_to_group_teachers(db, student_id, UUID(str(course_id)), what)
            db.commit()
    except Exception:  # a notification must never undo a submission
        db.rollback()
        log.exception("group notification after submission failed")


def after_grading(db: Session, student_id, title: str, status: str, score) -> None:
    try:
        from app.services.notification.service import create_notification

        label = STATUS_LABEL.get(status, status)
        create_notification(db, str(student_id), title=f"Tekshirildi / Bewertet: {title}"[:255],
                            message=f"{label}" + (f" — {score} ball" if score is not None else ""), type=TYPE_COURSE)
        db.commit()
    except Exception:
        db.rollback()
        log.exception("notification after grading failed")
