from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.assessment import Assessment, STATUS_PUBLISHED
from app.models.assessment_attempt import (
    STATUS_GRADED,
    STATUS_IN_PROGRESS,
    AssessmentAttempt,
)
from app.models.assessment_result import AssessmentResult
from app.models.assessment_task import AssessmentTask
from app.models.section_result import SectionResult
from app.models.task_attempt import TaskAttempt
from app.models.task_question import TaskQuestion
from app.models.user import User

from app.schemas.assessment_engine import AnswerSubmit

from .scoring import get_handler


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ============================================================
# Start
# ============================================================

def start_attempt(db: Session, assessment_id: str, user: User) -> AssessmentAttempt:
    assessment = db.get(Assessment, UUID(assessment_id))
    if assessment is None or assessment.status != STATUS_PUBLISHED:
        raise HTTPException(status_code=404, detail="Assessment not found or not published.")

    existing = db.scalars(
        select(AssessmentAttempt)
        .where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == user.id,
            AssessmentAttempt.status == STATUS_IN_PROGRESS,
        )
        .order_by(AssessmentAttempt.started_at.desc())
    ).first()
    if existing is not None:
        return existing

    attempt_count = db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.assessment_id == assessment.id,
            AssessmentAttempt.user_id == user.id,
        )
    )

    if attempt_count > 0 and not assessment.allow_retry:
        raise HTTPException(status_code=403, detail="Retries are not allowed for this assessment.")

    if assessment.attempt_limit is not None and attempt_count >= assessment.attempt_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Attempt limit reached ({assessment.attempt_limit}).",
        )

    attempt = AssessmentAttempt(
        assessment_id=assessment.id,
        user_id=user.id,
        status=STATUS_IN_PROGRESS,
        attempt_number=attempt_count + 1,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def _get_owned_attempt(db: Session, attempt_id: str, user: User) -> AssessmentAttempt:
    attempt = db.get(AssessmentAttempt, UUID(attempt_id))
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    if attempt.user_id != user.id:
        raise HTTPException(status_code=403, detail="This attempt does not belong to you.")
    return attempt


# ============================================================
# Answer
# ============================================================

def submit_answer(db: Session, attempt_id: str, user: User, data: AnswerSubmit) -> Answer:
    attempt = _get_owned_attempt(db, attempt_id, user)
    assessment = db.get(Assessment, attempt.assessment_id)

    if attempt.locked:
        raise HTTPException(status_code=403, detail="This attempt is locked and can no longer be edited.")
    if attempt.status != STATUS_IN_PROGRESS and not assessment.allow_edit:
        raise HTTPException(status_code=403, detail="Editing answers is not allowed for this assessment.")

    question = db.get(TaskQuestion, UUID(data.question_id))
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    task = db.get(AssessmentTask, question.task_id)

    task_attempt = db.scalars(
        select(TaskAttempt).where(
            TaskAttempt.assessment_attempt_id == attempt.id,
            TaskAttempt.task_id == task.id,
        )
    ).first()
    if task_attempt is None:
        task_attempt = TaskAttempt(
            assessment_attempt_id=attempt.id,
            task_id=task.id,
            max_score=task.max_points,
        )
        db.add(task_attempt)
        db.flush()

    handler = get_handler(task.task_type)
    is_correct, points_earned = handler.score(question, data.answer_data)

    answer = db.scalars(
        select(Answer).where(
            Answer.task_attempt_id == task_attempt.id,
            Answer.question_id == question.id,
        )
    ).first()

    if answer is None:
        answer = Answer(task_attempt_id=task_attempt.id, question_id=question.id)
        db.add(answer)

    answer.answer_data = data.answer_data
    answer.is_correct = is_correct
    answer.points_earned = points_earned

    db.commit()
    db.refresh(answer)
    return answer


# ============================================================
# Submit / Finalize / Score
# ============================================================

def submit_attempt(db: Session, attempt_id: str, user: User) -> AssessmentAttempt:
    attempt = _get_owned_attempt(db, attempt_id, user)
    assessment = db.get(Assessment, attempt.assessment_id)

    if attempt.locked:
        raise HTTPException(status_code=403, detail="This attempt is already locked.")

    _score_and_finalize(db, attempt, assessment)

    attempt.status = STATUS_GRADED
    attempt.submitted_at = _now()
    # Per policy: once submitted, the attempt's answers are locked unless
    # the assessment explicitly allows resubmission (re-opening the same
    # attempt to change answers) — this is the "Mock Test finished ->
    # answers can no longer change" rule from the spec, expressed as data
    # rather than a special-cased status check scattered across the code.
    attempt.locked = not assessment.allow_resubmit

    db.commit()
    db.refresh(attempt)
    return attempt


def _score_and_finalize(db: Session, attempt: AssessmentAttempt, assessment: Assessment) -> None:
    """Computes and persists SectionResult rows + one AssessmentResult for
    this attempt, from the TaskAttempt/Answer rows already scored
    incrementally in submit_answer(). Re-running this (e.g. on an allowed
    resubmit) replaces the previous results rather than duplicating them."""

    db.query(SectionResult).filter(SectionResult.assessment_attempt_id == attempt.id).delete()
    db.query(AssessmentResult).filter(AssessmentResult.assessment_attempt_id == attempt.id).delete()

    task_attempts = db.scalars(
        select(TaskAttempt).where(TaskAttempt.assessment_attempt_id == attempt.id)
    ).all()

    for ta in task_attempts:
        earned = db.scalar(
            select(func.coalesce(func.sum(Answer.points_earned), 0)).where(Answer.task_attempt_id == ta.id)
        )
        ta.score = int(earned)
        ta.status = STATUS_GRADED

    db.flush()

    section_totals: dict[UUID, list[int]] = {}
    for ta in task_attempts:
        task = db.get(AssessmentTask, ta.task_id)
        section_totals.setdefault(task.section_id, [0, 0])
        section_totals[task.section_id][0] += ta.score
        section_totals[task.section_id][1] += ta.max_score

    total_score = 0
    max_score = 0
    for section_id, (score, max_s) in section_totals.items():
        percentage = round((score / max_s) * 100, 2) if max_s else 0.0
        db.add(
            SectionResult(
                assessment_attempt_id=attempt.id,
                section_id=section_id,
                section_score=score,
                max_section_score=max_s,
                percentage=percentage,
            )
        )
        total_score += score
        max_score += max_s

    overall_percentage = round((total_score / max_score) * 100, 2) if max_score else 0.0
    db.add(
        AssessmentResult(
            assessment_attempt_id=attempt.id,
            total_score=total_score,
            max_score=max_score,
            percentage=overall_percentage,
        )
    )


def get_result(db: Session, attempt_id: str, user: User) -> dict:
    attempt = _get_owned_attempt(db, attempt_id, user)
    assessment = db.get(Assessment, attempt.assessment_id)

    result = db.scalars(
        select(AssessmentResult).where(AssessmentResult.assessment_attempt_id == attempt.id)
    ).first()
    if result is None:
        raise HTTPException(status_code=409, detail="This attempt has not been submitted yet.")

    section_results = db.scalars(
        select(SectionResult).where(SectionResult.assessment_attempt_id == attempt.id)
    ).all()

    return {
        "attempt_id": str(attempt.id),
        "total_score": result.total_score,
        "max_score": result.max_score,
        "percentage": result.percentage,
        "section_results": [
            {
                "section_id": str(sr.section_id),
                "section_score": sr.section_score,
                "max_section_score": sr.max_section_score,
                "percentage": sr.percentage,
            }
            for sr in section_results
        ],
        "show_correct_answers": assessment.show_correct_answers,
        "show_feedback": assessment.show_feedback,
    }
