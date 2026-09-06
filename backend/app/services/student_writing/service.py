from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.student_writing import STATUS_DRAFT, STATUS_SUBMITTED, StudentWriting
from app.models.user import User
from app.models.writing import Writing
from app.repositories.student_writing import (
    StudentWritingRepository,
)
from app.repositories.teacher_assignment import TeacherAssignmentRepository
from app.schemas.student_writing import (
    StudentWritingCreate,
    StudentWritingUpdate,
    TeacherWritingItem,
)


def _display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w])


class StudentWritingService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = StudentWritingRepository(db)
        self.assignments = TeacherAssignmentRepository(db)

    # ==========================
    # Legacy generic CRUD (unchanged — see app/api/student_writing/router.py)
    # ==========================

    def get_all(self):
        return self.repository.get_all()

    def get(self, item_id: str):
        return self.repository.get(item_id)

    def create(
        self,
        data: StudentWritingCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: StudentWritingUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        item_id: str,
    ):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True

    # ==========================
    # Real student submission workflow
    # ==========================

    def submit(self, user_id: UUID, writing_id: UUID, answer_text: str, submit_final: bool) -> StudentWriting:
        writing = self.db.get(Writing, writing_id)
        if writing is None or not writing.is_published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing task not found")

        if submit_final:
            words = _word_count(answer_text)
            if words < writing.min_words:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mindestens {writing.min_words} Wörter erforderlich (aktuell: {words}).",
                )
            if words > writing.max_words:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximal {writing.max_words} Wörter erlaubt (aktuell: {words}).",
                )

        existing = self.repository.get_by_user_and_writing(user_id, writing_id)

        # A GRADED submission is final — the student can no longer overwrite
        # it by simply calling submit again; only a teacher setting
        # NEEDS_REVISION reopens it (see grade()).
        if existing is not None and existing.status == "GRADED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This submission has already been graded and can no longer be edited.",
            )

        new_status = STATUS_SUBMITTED if submit_final else STATUS_DRAFT

        if existing is not None:
            existing.answer_text = answer_text
            existing.status = new_status
            if submit_final:
                existing.submitted_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = StudentWriting(
            user_id=str(user_id),
            writing_id=str(writing_id),
            answer_text=answer_text,
            status=new_status,
            submitted_at=datetime.now(timezone.utc) if submit_final else None,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_own(self, user_id: UUID, writing_id: UUID) -> StudentWriting | None:
        return self.repository.get_by_user_and_writing(user_id, writing_id)

    # ==========================
    # Teacher grading (IDOR-scoped via TeacherAssignment)
    # ==========================

    def _to_teacher_item(self, row) -> TeacherWritingItem:
        submission, writing, lesson, _module, course, student = row
        return TeacherWritingItem(
            id=submission.id,
            student_id=student.id,
            student_name=_display_name(student),
            student_email=student.email,
            course_title=course.title,
            course_level=course.level,
            lesson_title=lesson.title,
            lesson_number=lesson.number,
            writing_title=writing.title,
            min_words=writing.min_words,
            max_words=writing.max_words,
            answer_text=submission.answer_text,
            status=submission.status,
            submitted_at=submission.submitted_at,
            score=submission.score,
            feedback=submission.feedback,
            reviewed_at=submission.reviewed_at,
        )

    def list_for_teacher(
        self,
        teacher_id: UUID,
        status_filter: str | None = None,
        course_id: str | None = None,
        level: str | None = None,
        lesson_id: str | None = None,
        search: str | None = None,
    ) -> list[TeacherWritingItem]:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        rows = self.repository.list_for_teacher(
            course_ids, status=status_filter, course_id=course_id, level=level, lesson_id=lesson_id, search=search
        )
        return [self._to_teacher_item(row) for row in rows]

    def get_for_teacher(self, teacher_id: UUID, submission_id: UUID) -> TeacherWritingItem:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        row = self.repository.get_for_teacher(course_ids, submission_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        return self._to_teacher_item(row)

    def grade(self, teacher_id: UUID, submission_id: UUID, score: int, feedback: str, new_status: str) -> TeacherWritingItem:
        # Re-checks the same IDOR scope before writing — a guessed id for
        # an unassigned course must never succeed, even if the caller
        # somehow already knew the id.
        self.get_for_teacher(teacher_id, submission_id)

        item = self.repository.get(str(submission_id))
        item.score = score
        item.feedback = feedback
        item.status = new_status
        item.reviewed_by_id = teacher_id
        item.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)

        return self._to_teacher_item(
            (item, item.writing, item.writing.lesson, item.writing.lesson.module, item.writing.lesson.module.course, item.user)
        )
