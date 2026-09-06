from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.homework import Homework
from app.models.homework_submission import STATUS_SUBMITTED, HomeworkSubmission
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.course import Course
from app.models.user import User


class HomeworkSubmissionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get(self, submission_id: UUID) -> HomeworkSubmission | None:
        return self.db.query(HomeworkSubmission).filter(HomeworkSubmission.id == submission_id).first()

    def get_by_student_and_homework(self, student_id: UUID, homework_id: UUID) -> HomeworkSubmission | None:
        return (
            self.db.query(HomeworkSubmission)
            .filter(
                HomeworkSubmission.student_id == student_id,
                HomeworkSubmission.homework_id == homework_id,
            )
            .first()
        )

    def upsert(self, student_id: UUID, homework_id: UUID, text_content: str) -> HomeworkSubmission:
        """One row per (student, homework) — a resubmission (including
        after NEEDS_REVISION) updates the existing row in place rather
        than creating a second one. Always resets status to SUBMITTED;
        score/feedback from a prior review are deliberately left
        untouched until the teacher grades it again."""
        existing = self.get_by_student_and_homework(student_id, homework_id)
        now = datetime.now(timezone.utc)

        if existing is not None:
            existing.text_content = text_content
            existing.status = STATUS_SUBMITTED
            existing.submitted_at = now
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = HomeworkSubmission(
            student_id=student_id,
            homework_id=homework_id,
            text_content=text_content,
            status=STATUS_SUBMITTED,
            submitted_at=now,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def grade(self, item: HomeworkSubmission, reviewer_id: UUID, score: int, feedback: str, status: str) -> HomeworkSubmission:
        item.score = score
        item.feedback = feedback
        item.status = status
        item.reviewed_by_id = reviewer_id
        item.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item

    def _base_teacher_query(self, course_ids: list[str]):
        return (
            self.db.query(HomeworkSubmission, Homework, Lesson, Module, Course, User)
            .join(Homework, Homework.id == HomeworkSubmission.homework_id)
            .join(Lesson, Lesson.id == Homework.lesson_id)
            .join(Module, Module.id == Lesson.module_id)
            .join(Course, Course.id == Module.course_id)
            .join(User, User.id == HomeworkSubmission.student_id)
            .filter(Module.course_id.in_(course_ids))
        )

    def list_for_teacher(
        self,
        course_ids: list[str],
        status: str | None = None,
        course_id: str | None = None,
        level: str | None = None,
        lesson_id: str | None = None,
        search: str | None = None,
    ):
        if not course_ids:
            return []

        query = self._base_teacher_query(course_ids)

        if status is not None:
            query = query.filter(HomeworkSubmission.status == status)
        if course_id is not None:
            query = query.filter(Course.id == course_id)
        if level is not None:
            query = query.filter(Course.level == level)
        if lesson_id is not None:
            query = query.filter(Lesson.id == lesson_id)
        if search:
            like = f"%{search.lower()}%"
            query = query.filter(
                (User.email.ilike(like))
                | (User.username.ilike(like))
                | (User.first_name.ilike(like))
                | (User.last_name.ilike(like))
            )

        return query.order_by(HomeworkSubmission.submitted_at.desc()).all()

    def get_for_teacher(self, course_ids: list[str], submission_id: UUID):
        """A single row, scoped exactly like list_for_teacher — returns
        None (never the row) if the submission's course isn't one of the
        teacher's assigned courses, so the router can 404 without ever
        distinguishing "doesn't exist" from "not yours" (same IDOR
        principle as BookService.get_downloadable_book)."""
        if not course_ids:
            return None
        return self._base_teacher_query(course_ids).filter(HomeworkSubmission.id == submission_id).first()
