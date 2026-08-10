"""SCHREIBEN (writing) submissions, AI evaluation, and teacher review.

Reuses the same engine primitives as every other skill: AssessmentAttempt
for ownership/locking, attempt_service.get_or_create_task_attempt() for the
per-task score snapshot row, attempt_service.recompute_attempt_result() to
fold a (possibly much later) evaluation into the attempt's totals. The only
genuinely new piece is the DRAFT -> SUBMITTED -> PENDING_REVIEW/GRADED
state machine and the AI/teacher scoring itself.
"""

import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_task import (
    EVAL_MODE_AI_AND_TEACHER,
    EVAL_MODE_AI_ONLY,
    TYPE_WRITING,
    AssessmentTask,
)
from app.models.user import User
from app.models.writing_evaluation import EVALUATOR_AI, EVALUATOR_TEACHER, WritingEvaluation
from app.models.writing_submission import (
    STATUS_DRAFT,
    STATUS_GRADED,
    STATUS_PENDING_REVIEW,
    STATUS_SUBMITTED,
    WritingSubmission,
)

from app.schemas.assessment_engine import (
    PendingWritingReviewItem,
    WritingEvaluationResponse,
    WritingResultResponse,
    WritingRubricCriterionResponse,
    WritingSubmissionResponse,
)

from app.services.mock_exam import ai_service

from . import attempt_service
from .rubric_scoring import clamp_rubric_scores


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w])


def _get_writing_task(db: Session, task_id: str) -> AssessmentTask:
    task = db.get(AssessmentTask, UUID(task_id))
    if task is None or task.task_type != TYPE_WRITING:
        raise HTTPException(status_code=404, detail="Writing task not found.")
    return task


def _get_submission(db: Session, attempt_id: str, task_id: str) -> WritingSubmission | None:
    return db.scalars(
        select(WritingSubmission).where(
            WritingSubmission.attempt_id == UUID(attempt_id),
            WritingSubmission.task_id == UUID(task_id),
        )
    ).first()


def _evaluation_to_schema(evaluation: WritingEvaluation) -> WritingEvaluationResponse:
    return WritingEvaluationResponse(
        id=evaluation.id,
        submission_id=evaluation.submission_id,
        evaluator_type=evaluation.evaluator_type,
        reviewed_by_id=evaluation.reviewed_by_id,
        rubric_scores=json.loads(evaluation.rubric_scores) if evaluation.rubric_scores else {},
        total_score=evaluation.total_score,
        feedback=evaluation.feedback,
        strengths=evaluation.strengths,
        errors=json.loads(evaluation.errors) if evaluation.errors else [],
        suggestions=json.loads(evaluation.suggestions) if evaluation.suggestions else [],
        created_at=evaluation.created_at,
    )


# ============================================================
# Save (Speichern) / Submit (Abgeben)
# ============================================================

def save_draft(db: Session, attempt_id: str, task_id: str, user: User, content: str) -> WritingSubmission:
    attempt = attempt_service.get_owned_attempt(db, attempt_id, user)
    task = _get_writing_task(db, task_id)
    assessment = db.get(Assessment, attempt.assessment_id)

    if attempt.locked:
        raise HTTPException(status_code=403, detail="This attempt is locked and can no longer be edited.")

    submission = _get_submission(db, attempt_id, task_id)
    if submission is not None and submission.status != STATUS_DRAFT and not assessment.allow_edit:
        raise HTTPException(status_code=403, detail="Editing is not allowed for this assessment.")

    # Ensures a TaskAttempt snapshot row exists for this task, same as
    # every other task-type's first interaction — without it, this task
    # would silently be excluded from the attempt's score totals.
    attempt_service.get_or_create_task_attempt(db, attempt, task)

    if submission is None:
        submission = WritingSubmission(
            user_id=user.id,
            assessment_id=assessment.id,
            section_id=task.section_id,
            task_id=task.id,
            attempt_id=attempt.id,
            status=STATUS_DRAFT,
        )
        db.add(submission)

    submission.content = content
    submission.word_count = _word_count(content)
    submission.character_count = len(content)
    db.commit()
    db.refresh(submission)
    return submission


async def submit_submission(db: Session, attempt_id: str, task_id: str, user: User) -> WritingSubmission:
    attempt = attempt_service.get_owned_attempt(db, attempt_id, user)
    task = _get_writing_task(db, task_id)
    assessment = db.get(Assessment, attempt.assessment_id)

    if attempt.locked:
        raise HTTPException(status_code=403, detail="This attempt is locked and can no longer be edited.")

    submission = _get_submission(db, attempt_id, task_id)
    if submission is None or not submission.content.strip():
        raise HTTPException(status_code=400, detail="Save a draft with some content before submitting.")
    if submission.status != STATUS_DRAFT and not assessment.allow_resubmit:
        raise HTTPException(status_code=403, detail="Resubmission is not allowed for this assessment.")

    word_count = _word_count(submission.content)
    if task.min_words is not None and word_count < task.min_words:
        raise HTTPException(
            status_code=400, detail=f"At least {task.min_words} words are required (currently {word_count})."
        )
    if task.max_words is not None and word_count > task.max_words:
        raise HTTPException(
            status_code=400, detail=f"No more than {task.max_words} words are allowed (currently {word_count})."
        )

    submission.status = STATUS_SUBMITTED
    submission.submitted_at = _now()
    db.commit()

    if task.evaluation_mode in (EVAL_MODE_AI_ONLY, EVAL_MODE_AI_AND_TEACHER):
        try:
            await _run_ai_evaluation(db, submission, task)
        except ai_service.AIServiceError:
            # AI unreachable/misconfigured — don't lose the submission,
            # just fall back to manual grading.
            submission.status = STATUS_PENDING_REVIEW
            db.commit()
    else:
        submission.status = STATUS_PENDING_REVIEW
        db.commit()

    db.refresh(submission)
    return submission


# ============================================================
# AI evaluation — backend-only; the frontend never supplies a score
# ============================================================

async def _run_ai_evaluation(db: Session, submission: WritingSubmission, task: AssessmentTask) -> None:
    criteria = list(task.rubric_criteria)
    if not criteria:
        submission.status = STATUS_PENDING_REVIEW
        db.commit()
        return

    result = await ai_service.evaluate_writing_rubric(
        task_text=task.content or task.instructions or task.title,
        answer_text=submission.content,
        criteria=[{"name": c.name, "max_score": c.max_score} for c in criteria],
        image_url=task.image_url,
    )

    # Never trust the AI's own arithmetic or range — clamp_rubric_scores
    # re-derives both per-criterion and total from scratch.
    clamped_scores, total = clamp_rubric_scores(result.get("criterion_scores") or {}, criteria, task.max_points)

    feedback_parts = []
    if result.get("vocabulary_feedback"):
        feedback_parts.append(f"Wortschatz: {result['vocabulary_feedback']}")
    if result.get("structure_feedback"):
        feedback_parts.append(f"Aufbau: {result['structure_feedback']}")
    if result.get("task_completion_feedback"):
        feedback_parts.append(f"Aufgabenbewältigung: {result['task_completion_feedback']}")

    evaluation = WritingEvaluation(
        submission_id=submission.id,
        evaluator_type=EVALUATOR_AI,
        rubric_scores=json.dumps(clamped_scores),
        total_score=total,
        feedback="\n".join(feedback_parts) or None,
        strengths=result.get("strengths"),
        errors=json.dumps(result.get("grammar_errors") or []),
        suggestions=json.dumps(result.get("improvement_suggestions") or []),
    )
    db.add(evaluation)

    submission.final_score = total
    submission.status = STATUS_GRADED if task.evaluation_mode == EVAL_MODE_AI_ONLY else STATUS_PENDING_REVIEW
    db.commit()

    attempt_service.recompute_attempt_result(db, submission.attempt_id)


# ============================================================
# Teacher review
# ============================================================

def submit_teacher_review(
    db: Session,
    submission_id: str,
    teacher: User,
    rubric_scores: dict[str, int],
    feedback: str | None,
) -> WritingEvaluationResponse:
    submission = db.get(WritingSubmission, UUID(submission_id))
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")

    task = db.get(AssessmentTask, submission.task_id)
    clamped, total = clamp_rubric_scores(rubric_scores, list(task.rubric_criteria), task.max_points)

    evaluation = WritingEvaluation(
        submission_id=submission.id,
        evaluator_type=EVALUATOR_TEACHER,
        reviewed_by_id=teacher.id,
        rubric_scores=json.dumps(clamped),
        total_score=total,
        feedback=feedback,
    )
    db.add(evaluation)

    submission.final_score = total
    submission.status = STATUS_GRADED
    db.commit()
    db.refresh(evaluation)

    attempt_service.recompute_attempt_result(db, submission.attempt_id)
    return _evaluation_to_schema(evaluation)


def list_pending_reviews(db: Session, assessment_id: str | None = None) -> list[PendingWritingReviewItem]:
    query = select(WritingSubmission).where(WritingSubmission.status == STATUS_PENDING_REVIEW)
    if assessment_id:
        query = query.where(WritingSubmission.assessment_id == UUID(assessment_id))
    submissions = db.scalars(query.order_by(WritingSubmission.submitted_at)).all()

    items = []
    for submission in submissions:
        task = db.get(AssessmentTask, submission.task_id)
        student = db.get(User, submission.user_id)
        ai_evaluation = next((e for e in submission.evaluations if e.evaluator_type == EVALUATOR_AI), None)
        items.append(
            PendingWritingReviewItem(
                submission=WritingSubmissionResponse.model_validate(submission),
                task_title=task.title if task else "",
                student_name=student.username if student else "",
                rubric_criteria=(
                    [WritingRubricCriterionResponse.model_validate(c) for c in task.rubric_criteria] if task else []
                ),
                ai_evaluation=_evaluation_to_schema(ai_evaluation) if ai_evaluation else None,
            )
        )
    return items


# ============================================================
# Read
# ============================================================

def get_submission(db: Session, attempt_id: str, task_id: str, user: User) -> WritingSubmission | None:
    attempt_service.get_owned_attempt(db, attempt_id, user)
    return _get_submission(db, attempt_id, task_id)


def get_writing_result(db: Session, attempt_id: str, task_id: str, user: User) -> WritingResultResponse:
    attempt = attempt_service.get_owned_attempt(db, attempt_id, user)
    assessment = db.get(Assessment, attempt.assessment_id)

    submission = _get_submission(db, attempt_id, task_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="No submission for this task.")

    evaluations = (
        [_evaluation_to_schema(e) for e in submission.evaluations] if assessment.show_feedback else []
    )
    return WritingResultResponse(
        submission=WritingSubmissionResponse.model_validate(submission),
        evaluations=evaluations,
        show_feedback=assessment.show_feedback,
    )
