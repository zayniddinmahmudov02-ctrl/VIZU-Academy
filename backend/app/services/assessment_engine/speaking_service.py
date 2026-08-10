"""SPRECHEN (speaking) audio submissions and teacher review.

Reuses the same primitives as every other skill in this engine:
ProtectedLocalStorage (already built for Hören's TaskAudio — same secure,
non-public storage, just a different subfolder), attempt_service's shared
ownership/task-attempt helpers, and the universal clamp_rubric_scores()
also used by writing_service. Speaking is teacher-only in this phase (no
AI audio scoring), so there's no evaluator_type branch to worry about.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.assessment import Assessment
from app.models.assessment_task import TYPE_SPEAKING, AssessmentTask
from app.models.task_audio import ALL_AUDIO_FORMATS, CONTENT_TYPE_BY_FORMAT
from app.models.user import User
from app.models.speaking_evaluation import SpeakingEvaluation
from app.models.speaking_submission import (
    STATUS_FINAL,
    STATUS_PENDING_REVIEW,
    STATUS_REVIEWED,
    SpeakingSubmission,
)

from app.schemas.assessment_engine import (
    PendingSpeakingReviewItem,
    SpeakingEvaluationResponse,
    SpeakingResultResponse,
    SpeakingSubmissionResponse,
    WritingRubricCriterionResponse,
)

from . import attempt_service
from .audio_service import MAX_AUDIO_SIZE_BYTES, resolve_audio_format, storage
from .rubric_scoring import clamp_rubric_scores


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_speaking_task(db: Session, task_id: str) -> AssessmentTask:
    task = db.get(AssessmentTask, UUID(task_id))
    if task is None or task.task_type != TYPE_SPEAKING:
        raise HTTPException(status_code=404, detail="Speaking task not found.")
    return task


def _get_submission(db: Session, attempt_id: str, task_id: str) -> SpeakingSubmission | None:
    return db.scalars(
        select(SpeakingSubmission).where(
            SpeakingSubmission.attempt_id == UUID(attempt_id),
            SpeakingSubmission.task_id == UUID(task_id),
        )
    ).first()


def _evaluation_to_schema(evaluation: SpeakingEvaluation) -> SpeakingEvaluationResponse:
    return SpeakingEvaluationResponse(
        id=evaluation.id,
        submission_id=evaluation.submission_id,
        reviewed_by_id=evaluation.reviewed_by_id,
        rubric_scores=json.loads(evaluation.rubric_scores) if evaluation.rubric_scores else {},
        total_score=evaluation.total_score,
        feedback=evaluation.feedback,
        created_at=evaluation.created_at,
    )


# ============================================================
# Upload / re-record (Abgeben)
# ============================================================

async def upload_submission(
    db: Session,
    attempt_id: str,
    task_id: str,
    user: User,
    file: UploadFile,
    duration_seconds: int | None,
) -> SpeakingSubmission:
    attempt = attempt_service.get_owned_attempt(db, attempt_id, user)
    task = _get_speaking_task(db, task_id)
    assessment = db.get(Assessment, attempt.assessment_id)

    if attempt.locked:
        raise HTTPException(status_code=403, detail="This attempt is locked and can no longer be edited.")

    existing = _get_submission(db, attempt_id, task_id)
    if existing is not None and existing.status == STATUS_FINAL and not assessment.allow_resubmit:
        raise HTTPException(status_code=403, detail="Re-recording is not allowed for this assessment.")

    audio_format = resolve_audio_format(file.content_type)
    if audio_format not in ALL_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type '{file.content_type}'. Allowed: MP3, WAV, M4A.",
        )

    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Audio exceeds the maximum upload size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    await file.seek(0)

    # Re-record semantics: replace the previous file, same convention as
    # TaskAudio.upload_audio and WritingSubmission's content upsert.
    if existing is not None:
        await storage.delete(existing.storage_path)

    unique_name = f"{uuid4().hex}.{audio_format}"
    storage_path = f"speaking-submissions/{unique_name}"
    file.filename = unique_name
    await storage.upload(file, storage_path)

    attempt_service.get_or_create_task_attempt(db, attempt, task)

    if existing is None:
        existing = SpeakingSubmission(
            user_id=user.id,
            assessment_id=assessment.id,
            section_id=task.section_id,
            task_id=task.id,
            attempt_id=attempt.id,
        )
        db.add(existing)

    existing.storage_path = storage_path
    existing.filename = unique_name
    existing.format = audio_format
    existing.content_type = CONTENT_TYPE_BY_FORMAT[audio_format]
    existing.duration_seconds = duration_seconds
    existing.file_size_bytes = len(contents)
    existing.status = STATUS_PENDING_REVIEW
    existing.submitted_at = _now()
    existing.final_score = None

    db.commit()
    db.refresh(existing)
    return existing


# ============================================================
# Secure access + streaming
# ============================================================

def resolve_submission_audio_path(submission: SpeakingSubmission) -> Path:
    return storage.ROOT / submission.storage_path


def authorize_submission_access(db: Session, submission_id: str, user: User) -> SpeakingSubmission:
    """Per spec section 13: a student may only ever access their own audio;
    staff (super admin / teacher / other admin-panel roles) may access any
    submission for review. 404 (not 403) when the submission doesn't
    exist or doesn't belong to the caller, so a guessed ID can't be used
    to probe for existence."""
    submission = db.get(SpeakingSubmission, UUID(submission_id))
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    if submission.user_id == user.id or user.role in UserRole.ADMIN_PANEL_ROLES:
        return submission

    raise HTTPException(status_code=404, detail="Submission not found.")


# ============================================================
# Read
# ============================================================

def get_submission(db: Session, attempt_id: str, task_id: str, user: User) -> SpeakingSubmission | None:
    attempt_service.get_owned_attempt(db, attempt_id, user)
    return _get_submission(db, attempt_id, task_id)


def get_speaking_result(db: Session, attempt_id: str, task_id: str, user: User) -> SpeakingResultResponse:
    attempt = attempt_service.get_owned_attempt(db, attempt_id, user)
    assessment = db.get(Assessment, attempt.assessment_id)

    submission = _get_submission(db, attempt_id, task_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="No submission for this task.")

    evaluations = (
        [_evaluation_to_schema(e) for e in submission.evaluations] if assessment.show_feedback else []
    )
    return SpeakingResultResponse(
        submission=SpeakingSubmissionResponse.model_validate(submission),
        evaluations=evaluations,
        show_feedback=assessment.show_feedback,
    )


# ============================================================
# Teacher review
# ============================================================

def list_pending_reviews(db: Session, assessment_id: str | None = None) -> list[PendingSpeakingReviewItem]:
    query = select(SpeakingSubmission).where(
        SpeakingSubmission.status.in_([STATUS_PENDING_REVIEW, STATUS_REVIEWED])
    )
    if assessment_id:
        query = query.where(SpeakingSubmission.assessment_id == UUID(assessment_id))
    submissions = db.scalars(query.order_by(SpeakingSubmission.submitted_at)).all()

    items = []
    for submission in submissions:
        task = db.get(AssessmentTask, submission.task_id)
        student = db.get(User, submission.user_id)
        items.append(
            PendingSpeakingReviewItem(
                submission=SpeakingSubmissionResponse.model_validate(submission),
                task_title=task.title if task else "",
                student_name=student.username if student else "",
                rubric_criteria=(
                    [WritingRubricCriterionResponse.model_validate(c) for c in task.rubric_criteria] if task else []
                ),
            )
        )
    return items


def submit_teacher_review(
    db: Session,
    submission_id: str,
    teacher: User,
    rubric_scores: dict[str, int],
    feedback: str | None,
    finalize: bool,
) -> SpeakingEvaluationResponse:
    submission = db.get(SpeakingSubmission, UUID(submission_id))
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    task = db.get(AssessmentTask, submission.task_id)
    clamped, total = clamp_rubric_scores(rubric_scores, list(task.rubric_criteria), task.max_points)

    evaluation = SpeakingEvaluation(
        submission_id=submission.id,
        reviewed_by_id=teacher.id,
        rubric_scores=json.dumps(clamped),
        total_score=total,
        feedback=feedback,
    )
    db.add(evaluation)

    submission.final_score = total
    submission.status = STATUS_FINAL if finalize else STATUS_REVIEWED
    db.commit()
    db.refresh(evaluation)

    if finalize:
        attempt_service.recompute_attempt_result(db, submission.attempt_id)

    return _evaluation_to_schema(evaluation)
