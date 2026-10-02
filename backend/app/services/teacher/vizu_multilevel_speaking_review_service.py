"""Teacher Panel — VIZU-Multilevel Sprechen review. Unscoped by course like
the Schreiben review (VIZU-Multilevel has no course concept): any
TEACHER / admin-panel role sees every submitted attempt."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingSubmission, VizuMultilevelSpeakingTask
from app.services.vizu_multilevel import service as flow
from app.services.vizu_multilevel import sprechen_service

# Same "kamida 12/20" rule as Schreiben, expressed as a ratio of the
# Aufgabe's own points so it stays correct if an admin changes `points`.
PASS_NUMERATOR = 3
PASS_DENOMINATOR = 5


def _student_name(user) -> str:
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username


def _active_tasks(db: Session) -> list[VizuMultilevelSpeakingTask]:
    return list(
        db.scalars(
            select(VizuMultilevelSpeakingTask)
            .where(VizuMultilevelSpeakingTask.is_active.is_(True))
            .order_by(VizuMultilevelSpeakingTask.order_index)
        )
    )


def _status(graded: int, total: int) -> str:
    if graded == 0:
        return "NEW"
    if graded < total:
        return "IN_PROGRESS"
    return "GRADED"


def list_speaking_for_teacher(db: Session) -> list[dict]:
    attempts = list(
        db.scalars(
            select(VizuMultilevelAttempt)
            .where(VizuMultilevelAttempt.sprechen_submitted_at.isnot(None))
            .options(joinedload(VizuMultilevelAttempt.user))
            .order_by(VizuMultilevelAttempt.sprechen_submitted_at.desc())
        )
    )
    if not attempts:
        return []

    tasks = _active_tasks(db)
    subs = list(
        db.scalars(
            select(VizuMultilevelSpeakingSubmission).where(
                VizuMultilevelSpeakingSubmission.attempt_id.in_([a.id for a in attempts])
            )
        )
    )
    total_by_attempt: dict[UUID, int] = {}
    graded_by_attempt: dict[UUID, int] = {}
    for sub in subs:
        total_by_attempt[sub.attempt_id] = total_by_attempt.get(sub.attempt_id, 0) + 1
        if sub.teacher_score is not None:
            graded_by_attempt[sub.attempt_id] = graded_by_attempt.get(sub.attempt_id, 0) + 1

    items = []
    for attempt in attempts:
        total = total_by_attempt.get(attempt.id, 0)
        graded = graded_by_attempt.get(attempt.id, 0)
        user = attempt.user
        items.append(
            {
                "attempt_id": attempt.id,
                "student_name": _student_name(user),
                "username": user.username,
                "email": user.email,
                "sprechen_submitted_at": attempt.sprechen_submitted_at,
                "graded_count": graded,
                "total_submissions": total,
                "sprechen_score": attempt.sprechen_score,
                "max_score": sum(t.points for t in tasks),
                "status": _status(graded, total),
            }
        )
    return items


def get_speaking_detail_for_teacher(db: Session, attempt_id: UUID) -> dict | None:
    attempt = db.scalar(
        select(VizuMultilevelAttempt)
        .where(VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.sprechen_submitted_at.isnot(None))
        .options(joinedload(VizuMultilevelAttempt.user))
    )
    if attempt is None:
        return None

    subs = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelSpeakingSubmission).where(VizuMultilevelSpeakingSubmission.attempt_id == attempt_id)
        )
    }
    user = attempt.user
    return {
        "attempt_id": attempt.id,
        "student_name": _student_name(user),
        "username": user.username,
        "email": user.email,
        "sprechen_submitted_at": attempt.sprechen_submitted_at,
        "sprechen_score": attempt.sprechen_score,
        "sprechen_level": attempt.sprechen_level,
        "sprechen_feedback": attempt.sprechen_feedback,
        "submissions": [
            {
                "submission_id": subs[t.id].id if t.id in subs else None,
                "task_id": t.id,
                "order_index": t.order_index,
                "level": t.level,
                "title": t.title,
                "instruction": t.instruction,
                "points": t.points,
                "duration_seconds": subs[t.id].duration_seconds if t.id in subs else None,
                "has_audio": t.id in subs,
                "teacher_score": subs[t.id].teacher_score if t.id in subs else None,
                "teacher_comment": subs[t.id].teacher_comment if t.id in subs else None,
            }
            for t in _active_tasks(db)
        ],
    }


def get_audio(db: Session, attempt_id: UUID, submission_id: UUID) -> tuple[Path, str] | None:
    sub = db.scalar(
        select(VizuMultilevelSpeakingSubmission).where(
            VizuMultilevelSpeakingSubmission.id == submission_id,
            VizuMultilevelSpeakingSubmission.attempt_id == attempt_id,
        )
    )
    if sub is None:
        return None
    return sprechen_service.resolve_audio_path(sub), sub.content_type


def _recompute_attempt(db: Session, attempt: VizuMultilevelAttempt) -> None:
    tasks = _active_tasks(db)
    subs = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelSpeakingSubmission).where(VizuMultilevelSpeakingSubmission.attempt_id == attempt.id)
        )
    }
    graded = [subs[t.id].teacher_score for t in tasks if t.id in subs and subs[t.id].teacher_score is not None]
    attempt.sprechen_score = sum(graded) if graded else None

    confirmed = None
    for task in tasks:
        sub = subs.get(task.id)
        score = sub.teacher_score if sub else None
        if score is not None and score * PASS_DENOMINATOR >= PASS_NUMERATOR * task.points:
            confirmed = task.level
        else:
            break
    attempt.sprechen_level = confirmed


def grade_task(
    db: Session, attempt_id: UUID, task_id: UUID, reviewer_id: UUID, score: int, comment: str | None
) -> dict | None | str:
    """Returns the refreshed detail; None if the attempt/submission does
    not exist; the string "INVALID_SCORE" if the score is out of range."""
    attempt = db.scalar(
        select(VizuMultilevelAttempt).where(
            VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.sprechen_submitted_at.isnot(None)
        )
    )
    if attempt is None:
        return None
    task = db.scalar(select(VizuMultilevelSpeakingTask).where(VizuMultilevelSpeakingTask.id == task_id))
    sub = db.scalar(
        select(VizuMultilevelSpeakingSubmission).where(
            VizuMultilevelSpeakingSubmission.attempt_id == attempt_id,
            VizuMultilevelSpeakingSubmission.task_id == task_id,
        )
    )
    if task is None or sub is None:
        return None
    if score < 0 or score > task.points:
        return "INVALID_SCORE"

    sub.teacher_score = score
    sub.teacher_comment = comment
    sub.reviewed_by_id = reviewer_id
    sub.reviewed_at = datetime.now(timezone.utc)
    _recompute_attempt(db, attempt)
    db.commit()

    # Build the response BEFORE the overall refresh — which may discard a
    # below-A1 attempt (and with it the rows this detail is built from).
    detail = get_speaking_detail_for_teacher(db, attempt_id)
    flow.refresh_overall(db, attempt)
    return detail


def set_feedback(db: Session, attempt_id: UUID, feedback: str | None) -> dict | None:
    attempt = db.scalar(
        select(VizuMultilevelAttempt).where(
            VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.sprechen_submitted_at.isnot(None)
        )
    )
    if attempt is None:
        return None
    attempt.sprechen_feedback = feedback
    db.commit()
    return get_speaking_detail_for_teacher(db, attempt_id)
