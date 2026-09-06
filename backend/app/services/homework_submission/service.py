from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.homework import Homework
from app.models.user import User
from app.repositories.homework_submission import HomeworkSubmissionRepository
from app.repositories.teacher_assignment import TeacherAssignmentRepository
from app.schemas.homework_submission import HomeworkSubmissionResponse, TeacherHomeworkSubmission


def _display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


class HomeworkSubmissionService:
    """Student submit flow + Teacher grading flow for Homework — see
    app/models/homework_submission.py for why this is a new table rather
    than a field bolted onto Homework itself (Homework is the admin-
    authored task; this is the student's answer to it, one-to-many).

    Every teacher-facing method is scoped through TeacherAssignment
    (app/models/teacher_assignment.py) — a teacher with no assignment for
    a submission's course gets exactly the same 404 as a submission that
    doesn't exist at all, never a 403 that would confirm it exists (same
    IDOR principle as BookService.get_downloadable_book).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = HomeworkSubmissionRepository(db)
        self.assignments = TeacherAssignmentRepository(db)

    # ==========================
    # Student
    # ==========================

    def submit(self, student_id: UUID, homework_id: UUID, text_content: str) -> HomeworkSubmissionResponse:
        homework = self.db.query(Homework).filter(Homework.id == homework_id).first()
        if homework is None or not homework.is_published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")

        item = self.repository.upsert(student_id, homework_id, text_content)
        return HomeworkSubmissionResponse.model_validate(item)

    def get_own(self, student_id: UUID, homework_id: UUID) -> HomeworkSubmissionResponse | None:
        item = self.repository.get_by_student_and_homework(student_id, homework_id)
        if item is None:
            return None
        return HomeworkSubmissionResponse.model_validate(item)

    # ==========================
    # Teacher
    # ==========================

    def _to_teacher_schema(self, row) -> TeacherHomeworkSubmission:
        submission, homework, lesson, _module, course, student = row
        return TeacherHomeworkSubmission(
            id=submission.id,
            student_id=student.id,
            student_name=_display_name(student),
            student_email=student.email,
            course_title=course.title,
            course_level=course.level,
            lesson_title=lesson.title,
            lesson_number=lesson.number,
            homework_title=homework.title,
            text_content=submission.text_content,
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
    ) -> list[TeacherHomeworkSubmission]:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        rows = self.repository.list_for_teacher(
            course_ids,
            status=status_filter,
            course_id=course_id,
            level=level,
            lesson_id=lesson_id,
            search=search,
        )
        return [self._to_teacher_schema(row) for row in rows]

    def get_for_teacher(self, teacher_id: UUID, submission_id: UUID) -> TeacherHomeworkSubmission:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        row = self.repository.get_for_teacher(course_ids, submission_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        return self._to_teacher_schema(row)

    def grade(
        self,
        teacher_id: UUID,
        submission_id: UUID,
        score: int,
        feedback: str,
        new_status: str,
    ) -> TeacherHomeworkSubmission:
        # Re-checks the same IDOR scope as get_for_teacher before writing
        # anything — a teacher who merely guesses another course's
        # submission id still gets 404, never a write.
        self.get_for_teacher(teacher_id, submission_id)

        item = self.repository.get(submission_id)
        graded = self.repository.grade(item, teacher_id, score, feedback, new_status)
        return self._to_teacher_schema(
            (
                graded,
                graded.homework,
                graded.homework.lesson,
                graded.homework.lesson.module,
                graded.homework.lesson.module.course,
                graded.student,
            )
        )
