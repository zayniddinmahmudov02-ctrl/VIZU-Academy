from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_teacher_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.homework_submission import HomeworkGradeRequest, TeacherHomeworkSubmission
from app.schemas.student_speaking import SpeakingGradeRequest, TeacherSpeakingItem
from app.schemas.student_writing import TeacherWritingItem, WritingGradeRequest
from app.schemas.teacher import TeacherOverview, TeacherStudent
from app.services.homework_submission import HomeworkSubmissionService
from app.services.student_speaking import StudentSpeakingService
from app.services.student_writing import StudentWritingService
from app.services.teacher import TeacherService

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher Panel"],
)


@router.get("/overview", response_model=TeacherOverview)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return TeacherService(db).overview(current_user.id)


@router.get("/students", response_model=list[TeacherStudent])
def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return TeacherService(db).list_students(current_user.id)


# ==========================
# Homework grading (see app/models/homework_submission.py)
# ==========================
# Every method below is scoped through TeacherAssignment inside
# HomeworkSubmissionService — a submission belonging to a course this
# teacher isn't assigned to 404s exactly like one that doesn't exist,
# never a 403 (IDOR-safe, same principle as BookService).


@router.get("/homework", response_model=list[TeacherHomeworkSubmission])
def get_homework_submissions(
    status: str | None = None,
    course_id: str | None = None,
    level: str | None = None,
    lesson_id: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return HomeworkSubmissionService(db).list_for_teacher(
        current_user.id,
        status_filter=status,
        course_id=course_id,
        level=level,
        lesson_id=lesson_id,
        search=search,
    )


@router.get("/homework/{submission_id}", response_model=TeacherHomeworkSubmission)
def get_homework_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return HomeworkSubmissionService(db).get_for_teacher(current_user.id, submission_id)


@router.patch("/homework/{submission_id}/grade", response_model=TeacherHomeworkSubmission)
def grade_homework_submission(
    submission_id: UUID,
    data: HomeworkGradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return HomeworkSubmissionService(db).grade(
        current_user.id,
        submission_id,
        score=data.score,
        feedback=data.feedback,
        new_status=data.status,
    )


# ==========================
# Schreiben (legacy Writing) grading (see app/models/student_writing.py)
# ==========================


@router.get("/writing", response_model=list[TeacherWritingItem])
def get_writing_submissions(
    status: str | None = None,
    course_id: str | None = None,
    level: str | None = None,
    lesson_id: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return StudentWritingService(db).list_for_teacher(
        current_user.id, status_filter=status, course_id=course_id, level=level, lesson_id=lesson_id, search=search
    )


@router.get("/writing/{submission_id}", response_model=TeacherWritingItem)
def get_writing_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return StudentWritingService(db).get_for_teacher(current_user.id, submission_id)


@router.patch("/writing/{submission_id}/grade", response_model=TeacherWritingItem)
def grade_writing_submission(
    submission_id: UUID,
    data: WritingGradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return StudentWritingService(db).grade(
        current_user.id, submission_id, score=data.score, feedback=data.feedback, new_status=data.status
    )


# ==========================
# Sprechen (legacy Speaking) grading (see app/models/student_speaking.py)
# ==========================


@router.get("/speaking", response_model=list[TeacherSpeakingItem])
def get_speaking_submissions(
    status: str | None = None,
    course_id: str | None = None,
    level: str | None = None,
    lesson_id: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return StudentSpeakingService(db).list_for_teacher(
        current_user.id, status_filter=status, course_id=course_id, level=level, lesson_id=lesson_id, search=search
    )


@router.get("/speaking/{submission_id}", response_model=TeacherSpeakingItem)
def get_speaking_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return StudentSpeakingService(db).get_for_teacher(current_user.id, submission_id)


@router.patch("/speaking/{submission_id}/grade", response_model=TeacherSpeakingItem)
def grade_speaking_submission(
    submission_id: UUID,
    data: SpeakingGradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return StudentSpeakingService(db).grade(
        current_user.id, submission_id, score=data.score, feedback=data.feedback, new_status=data.status
    )
