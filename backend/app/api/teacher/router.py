from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_teacher_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.homework_submission import HomeworkGradeRequest, TeacherHomeworkSubmission
from app.schemas.mock_exam import (
    MockSpeakingSubmissionTeacherUpdate,
    MockWritingSubmissionTeacherUpdate,
    TeacherMockSpeakingItem,
    TeacherMockWritingItem,
)
from app.schemas.student_speaking import SpeakingGradeRequest, TeacherSpeakingItem
from app.schemas.student_writing import TeacherWritingItem, WritingGradeRequest
from app.schemas.teacher import TeacherOverview, TeacherStudent
from app.services.homework_submission import HomeworkSubmissionService
from app.services.mock_exam import attempt_service, teacher_review_service
from app.services.mock_exam.ai_service import AIServiceError
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


# ==========================
# Vorbereitung (Zertifikat/Modelltest) Schreiben/Sprechen review — the
# real exam-attempt submissions (app/models/mock_writing_submission.py,
# mock_speaking_submission.py), not the Assessment Engine's own
# WritingSubmission/SpeakingSubmission (see teacher_review_service.py's
# module docstring — the exam attempt flow never uses that engine).
# No TeacherAssignment/course scoping applies here: unlike Lektionen and
# Hausaufgaben, a Zertifikat/Modelltest isn't tied to any one course, so
# every teacher (or SUPER_ADMIN) sees every submission — same "no
# unrestricted admin access, but no invented per-provider assignment
# system either" tradeoff as the rest of this panel.
# ==========================


@router.get("/vorbereitung/writing", response_model=list[TeacherMockWritingItem])
def get_vorbereitung_writing_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return teacher_review_service.list_writing_for_teacher(db)


@router.post("/vorbereitung/writing/{submission_id}/ai-evaluate", response_model=TeacherMockWritingItem)
async def ai_evaluate_vorbereitung_writing(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    try:
        submission = await attempt_service.run_writing_ai_evaluation(db, submission_id)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if submission is None:
        raise HTTPException(status_code=404, detail="Writing submission not found.")
    return _find_writing_item(db, submission_id)


@router.put("/vorbereitung/writing/{submission_id}/review", response_model=TeacherMockWritingItem)
def review_vorbereitung_writing(
    submission_id: UUID,
    data: MockWritingSubmissionTeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    submission = attempt_service.update_writing_teacher_review(db, submission_id, data)
    if submission is None:
        raise HTTPException(status_code=404, detail="Writing submission not found.")
    return _find_writing_item(db, submission_id)


@router.get("/vorbereitung/speaking", response_model=list[TeacherMockSpeakingItem])
def get_vorbereitung_speaking_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return teacher_review_service.list_speaking_for_teacher(db)


@router.post("/vorbereitung/speaking/{submission_id}/ai-evaluate", response_model=TeacherMockSpeakingItem)
async def ai_evaluate_vorbereitung_speaking(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    try:
        submission = await attempt_service.run_speaking_ai_evaluation(db, submission_id)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if submission is None:
        raise HTTPException(status_code=404, detail="Speaking submission not found.")
    return _find_speaking_item(db, submission_id)


@router.put("/vorbereitung/speaking/{submission_id}/review", response_model=TeacherMockSpeakingItem)
def review_vorbereitung_speaking(
    submission_id: UUID,
    data: MockSpeakingSubmissionTeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    submission = attempt_service.update_speaking_teacher_review(db, submission_id, data)
    if submission is None:
        raise HTTPException(status_code=404, detail="Speaking submission not found.")
    return _find_speaking_item(db, submission_id)


def _find_writing_item(db: Session, submission_id: UUID) -> TeacherMockWritingItem:
    """Re-resolves the full breadcrumb row after a write, so the client
    gets back the same shape it lists with instead of a bare submission."""
    for item in teacher_review_service.list_writing_for_teacher(db):
        if item["submission"].id == submission_id:
            return item
    raise HTTPException(status_code=404, detail="Writing submission not found.")


def _find_speaking_item(db: Session, submission_id: UUID) -> TeacherMockSpeakingItem:
    for item in teacher_review_service.list_speaking_for_teacher(db):
        if item["submission"].id == submission_id:
            return item
    raise HTTPException(status_code=404, detail="Speaking submission not found.")
