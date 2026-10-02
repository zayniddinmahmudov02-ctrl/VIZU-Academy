"""Teacher Panel — VIZU-Multilevel Schreiben review. Deliberately unscoped by
course (no `teacher_course_ids_or_none` check): VIZU-Multilevel, like
Vorbereitung, has no course concept, so any TEACHER/SUPER_ADMIN sees
every submission — same precedent as
services/mock_exam/teacher_review_service.list_writing_for_teacher."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_writing import (
    VizuMultilevelWritingCriterionScore,
    VizuMultilevelWritingSubmission,
    VizuMultilevelWritingTask,
)
from app.services.vizu_multilevel import service as flow
from app.services.vizu_multilevel.schreiben_service import PASS_THRESHOLD

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]


def _status(graded_count: int, total: int) -> str:
    if graded_count == 0:
        return "NEW"
    if graded_count < total:
        return "IN_PROGRESS"
    return "GRADED"


def list_writing_for_teacher(db: Session) -> list[dict]:
    attempts = list(
        db.scalars(
            select(VizuMultilevelAttempt)
            .where(VizuMultilevelAttempt.schreiben_submitted_at.isnot(None))
            .options(joinedload(VizuMultilevelAttempt.user))
            .order_by(VizuMultilevelAttempt.schreiben_submitted_at.desc())
        )
    )
    if not attempts:
        return []

    attempt_ids = [a.id for a in attempts]
    total_tasks_count = len(
        list(db.scalars(select(VizuMultilevelWritingTask).where(VizuMultilevelWritingTask.is_active.is_(True))))
    )

    graded_rows = db.execute(
        select(VizuMultilevelWritingSubmission.attempt_id)
        .where(
            VizuMultilevelWritingSubmission.attempt_id.in_(attempt_ids),
            VizuMultilevelWritingSubmission.teacher_score.isnot(None),
        )
    ).all()
    graded_count_by_attempt: dict[UUID, int] = {}
    for (attempt_id,) in graded_rows:
        graded_count_by_attempt[attempt_id] = graded_count_by_attempt.get(attempt_id, 0) + 1

    items = []
    for attempt in attempts:
        graded_count = graded_count_by_attempt.get(attempt.id, 0)
        user = attempt.user
        student_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
        items.append(
            {
                "attempt_id": attempt.id,
                "student_name": student_name,
                "username": user.username,
                "email": user.email,
                "schreiben_submitted_at": attempt.schreiben_submitted_at,
                "graded_count": graded_count,
                "total_tasks": total_tasks_count,
                "schreiben_score": attempt.schreiben_score,
                "max_score": total_tasks_count * 20,
                "status": _status(graded_count, total_tasks_count),
            }
        )
    return items


def get_writing_detail_for_teacher(db: Session, attempt_id: UUID) -> dict | None:
    attempt = (
        db.scalar(
            select(VizuMultilevelAttempt)
            .where(VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.schreiben_submitted_at.isnot(None))
            .options(joinedload(VizuMultilevelAttempt.user))
        )
    )
    if attempt is None:
        return None

    tasks = list(
        db.scalars(
            select(VizuMultilevelWritingTask)
            .where(VizuMultilevelWritingTask.is_active.is_(True))
            .options(joinedload(VizuMultilevelWritingTask.rubric_criteria))
            .order_by(VizuMultilevelWritingTask.order_index)
        ).unique()
    )
    submissions = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelWritingSubmission)
            .where(VizuMultilevelWritingSubmission.attempt_id == attempt_id)
            .options(joinedload(VizuMultilevelWritingSubmission.criterion_scores))
        ).unique()
    }

    user = attempt.user
    student_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username

    submission_details = []
    for task in tasks:
        submission = submissions.get(task.id)
        criterion_scores = (
            {str(cs.criterion_id): cs.score for cs in submission.criterion_scores} if submission else {}
        )
        submission_details.append(
            {
                "task_id": task.id,
                "order_index": task.order_index,
                "level": task.level,
                "title": task.title,
                "instruction": task.instruction,
                "min_words": task.min_words,
                "max_words": task.max_words,
                "image_url": task.image_url,
                "content": submission.content if submission else "",
                "word_count": submission.word_count if submission else 0,
                "rubric_criteria": [
                    {"id": c.id, "name": c.name, "max_score": c.max_score, "order_index": c.order_index}
                    for c in task.rubric_criteria
                ],
                "criterion_scores": criterion_scores,
                "teacher_score": submission.teacher_score if submission else None,
                "teacher_comment": submission.teacher_comment if submission else None,
            }
        )

    return {
        "attempt_id": attempt.id,
        "student_name": student_name,
        "username": user.username,
        "email": user.email,
        "schreiben_submitted_at": attempt.schreiben_submitted_at,
        "schreiben_score": attempt.schreiben_score,
        "schreiben_level": attempt.schreiben_level,
        "schreiben_feedback": attempt.schreiben_feedback,
        "submissions": submission_details,
    }


def _recompute_attempt(db: Session, attempt: VizuMultilevelAttempt) -> None:
    tasks = list(
        db.scalars(
            select(VizuMultilevelWritingTask)
            .where(VizuMultilevelWritingTask.is_active.is_(True))
            .order_by(VizuMultilevelWritingTask.order_index)
        )
    )
    submissions_by_task = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelWritingSubmission).where(VizuMultilevelWritingSubmission.attempt_id == attempt.id)
        )
    }

    graded_scores = [
        submissions_by_task[t.id].teacher_score
        for t in tasks
        if t.id in submissions_by_task and submissions_by_task[t.id].teacher_score is not None
    ]
    attempt.schreiben_score = sum(graded_scores) if graded_scores else None

    confirmed_level = None
    for task in tasks:
        submission = submissions_by_task.get(task.id)
        score = submission.teacher_score if submission else None
        if score is not None and score >= PASS_THRESHOLD:
            confirmed_level = task.level
        else:
            break
    attempt.schreiben_level = confirmed_level


def grade_task(
    db: Session,
    attempt_id: UUID,
    task_id: UUID,
    reviewer_id: UUID,
    criterion_scores: dict[UUID, int],
    comment: str | None,
) -> dict | None:
    attempt = db.scalar(
        select(VizuMultilevelAttempt).where(
            VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.schreiben_submitted_at.isnot(None)
        )
    )
    if attempt is None:
        return None

    submission = db.scalar(
        select(VizuMultilevelWritingSubmission).where(
            VizuMultilevelWritingSubmission.attempt_id == attempt_id, VizuMultilevelWritingSubmission.task_id == task_id
        )
    )
    if submission is None:
        return None

    existing = {
        cs.criterion_id: cs
        for cs in db.scalars(
            select(VizuMultilevelWritingCriterionScore).where(VizuMultilevelWritingCriterionScore.submission_id == submission.id)
        )
    }
    for criterion_id, score in criterion_scores.items():
        if criterion_id in existing:
            existing[criterion_id].score = score
        else:
            db.add(
                VizuMultilevelWritingCriterionScore(submission_id=submission.id, criterion_id=criterion_id, score=score)
            )

    db.flush()
    total = sum(
        cs.score
        for cs in db.scalars(
            select(VizuMultilevelWritingCriterionScore).where(VizuMultilevelWritingCriterionScore.submission_id == submission.id)
        )
    )
    submission.teacher_score = total
    submission.teacher_comment = comment
    submission.reviewed_by_id = reviewer_id
    submission.reviewed_at = datetime.now(timezone.utc)

    _recompute_attempt(db, attempt)
    db.commit()

    # Build the response BEFORE the overall refresh — which may discard a
    # below-A1 attempt (and with it the rows this detail is built from).
    detail = get_writing_detail_for_teacher(db, attempt_id)
    flow.refresh_overall(db, attempt)
    return detail


def set_feedback(db: Session, attempt_id: UUID, feedback: str | None) -> dict | None:
    attempt = db.scalar(
        select(VizuMultilevelAttempt).where(
            VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.schreiben_submitted_at.isnot(None)
        )
    )
    if attempt is None:
        return None
    attempt.schreiben_feedback = feedback
    db.commit()
    return get_writing_detail_for_teacher(db, attempt_id)
