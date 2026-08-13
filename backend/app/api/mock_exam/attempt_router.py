from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.core.security.roles import UserRole
from app.db.session import get_db
from app.models.mock_test_attempt import MockTestAttempt
from app.models.user import User
from app.schemas.mock_exam import (
    MockQuestionAnswerCreate,
    MockQuestionAnswerResponse,
    MockSpeakingSubmissionCreate,
    MockSpeakingSubmissionResponse,
    MockSpeakingSubmissionTeacherUpdate,
    MockTestAttemptCreate,
    MockTestAttemptResponse,
    MockWritingSubmissionCreate,
    MockWritingSubmissionResponse,
    MockWritingSubmissionTeacherUpdate,
)
from app.services.mock_exam import attempt_service
from app.services.mock_exam.ai_service import AIServiceError

router = APIRouter(prefix="/mock-exam", tags=["Mock Exam — Attempts & Submissions"])


def _is_staff(user: User) -> bool:
    return user.role in UserRole.ADMIN_PANEL_ROLES


def _ensure_owner_or_staff(attempt: MockTestAttempt, current_user: User) -> None:
    if attempt.user_id != current_user.id and not _is_staff(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this attempt.")


# ============================================================
# Attempts
# ============================================================


@router.get("/attempts", response_model=list[MockTestAttemptResponse])
def list_attempts(
    model_test_id: UUID | None = None,
    user_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return attempt_service.get_attempts(db, model_test_id, user_id)


@router.post("/attempts", response_model=MockTestAttemptResponse, status_code=status.HTTP_201_CREATED)
def create_attempt(
    data: MockTestAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attempt_service.create_attempt(db, current_user, data)


@router.get("/attempts/{attempt_id}", response_model=MockTestAttemptResponse)
def get_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = attempt_service.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    _ensure_owner_or_staff(attempt, current_user)
    return attempt


@router.post("/attempts/{attempt_id}/finalize", response_model=MockTestAttemptResponse)
def finalize_attempt(
    attempt_id: UUID,
    time_spent_seconds: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = attempt_service.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    _ensure_owner_or_staff(attempt, current_user)
    return attempt_service.finalize_attempt(db, attempt_id, time_spent_seconds)


# ============================================================
# Question Answers
# ============================================================


@router.post("/question-answers", response_model=MockQuestionAnswerResponse, status_code=status.HTTP_201_CREATED)
def submit_question_answer(
    data: MockQuestionAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = attempt_service.get_attempt(db, data.attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    _ensure_owner_or_staff(attempt, current_user)
    return attempt_service.submit_question_answer(db, data)


# ============================================================
# Writing Submissions
# ============================================================


@router.get("/writing-submissions", response_model=list[MockWritingSubmissionResponse])
def list_writing_submissions(
    attempt_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return attempt_service.get_writing_submissions(db, attempt_id)


@router.post("/writing-submissions", response_model=MockWritingSubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_writing_submission(
    data: MockWritingSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = attempt_service.get_attempt(db, data.attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    _ensure_owner_or_staff(attempt, current_user)
    return attempt_service.create_writing_submission(db, data)


@router.post("/writing-submissions/{submission_id}/ai-evaluate", response_model=MockWritingSubmissionResponse)
async def evaluate_writing_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        submission = await attempt_service.run_writing_ai_evaluation(db, submission_id)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if submission is None:
        raise HTTPException(status_code=404, detail="Writing submission not found.")
    return submission


@router.put("/writing-submissions/{submission_id}/teacher-review", response_model=MockWritingSubmissionResponse)
def review_writing_submission(
    submission_id: UUID,
    data: MockWritingSubmissionTeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    submission = attempt_service.update_writing_teacher_review(db, submission_id, data)
    if submission is None:
        raise HTTPException(status_code=404, detail="Writing submission not found.")
    return submission


# ============================================================
# Speaking Submissions
# ============================================================


@router.get("/speaking-submissions", response_model=list[MockSpeakingSubmissionResponse])
def list_speaking_submissions(
    attempt_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return attempt_service.get_speaking_submissions(db, attempt_id)


@router.post("/speaking-submissions", response_model=MockSpeakingSubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_speaking_submission(
    data: MockSpeakingSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = attempt_service.get_attempt(db, data.attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    _ensure_owner_or_staff(attempt, current_user)
    return attempt_service.create_speaking_submission(db, data)


@router.post("/speaking-submissions/{submission_id}/ai-evaluate", response_model=MockSpeakingSubmissionResponse)
async def evaluate_speaking_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        submission = await attempt_service.run_speaking_ai_evaluation(db, submission_id)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if submission is None:
        raise HTTPException(status_code=404, detail="Speaking submission not found.")
    return submission


@router.put("/speaking-submissions/{submission_id}/teacher-review", response_model=MockSpeakingSubmissionResponse)
def review_speaking_submission(
    submission_id: UUID,
    data: MockSpeakingSubmissionTeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    submission = attempt_service.update_speaking_teacher_review(db, submission_id, data)
    if submission is None:
        raise HTTPException(status_code=404, detail="Speaking submission not found.")
    return submission
