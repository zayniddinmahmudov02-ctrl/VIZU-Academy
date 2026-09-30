from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_mock_attempt import VizuMockAttempt
from app.models.vizu_mock_writing import STATUS_DRAFT, STATUS_SUBMITTED, VizuMockWritingSubmission, VizuMockWritingTask

# "kamida 12/20" — a Schreiben Aufgabe counts as passed once its teacher-
# assigned score reaches at least 12 of its 20 max points (see the
# module's own spec, section 18). One task = one level here (unlike
# Lesen/Hören's multi-task-per-level aggregation), so no separate
# breakdown-aggregation step is needed.
PASS_THRESHOLD = 12


class WritingAlreadySubmittedError(Exception):
    """Raised when a draft save or final submit is attempted on an
    attempt whose Schreiben module has already been finally submitted —
    content is frozen from that point on (see VizuMockAttempt
    .schreiben_submitted_at's own docstring)."""


def list_writing_tasks(db: Session) -> list[VizuMockWritingTask]:
    return list(
        db.scalars(select(VizuMockWritingTask).where(VizuMockWritingTask.is_active.is_(True)).order_by(VizuMockWritingTask.order_index))
    )


def get_own_submissions(db: Session, attempt_id: UUID) -> list[VizuMockWritingSubmission]:
    return list(
        db.scalars(select(VizuMockWritingSubmission).where(VizuMockWritingSubmission.attempt_id == attempt_id))
    )


def _count_words(text: str) -> int:
    return len([w for w in text.split() if w])


def save_draft(db: Session, attempt: VizuMockAttempt, task_id: UUID, content: str) -> VizuMockWritingSubmission:
    if attempt.schreiben_submitted_at is not None:
        raise WritingAlreadySubmittedError()

    submission = db.scalar(
        select(VizuMockWritingSubmission).where(
            VizuMockWritingSubmission.attempt_id == attempt.id, VizuMockWritingSubmission.task_id == task_id
        )
    )
    if submission is None:
        submission = VizuMockWritingSubmission(attempt_id=attempt.id, task_id=task_id)
        db.add(submission)

    submission.content = content
    submission.word_count = _count_words(content)
    submission.status = STATUS_DRAFT
    submission.saved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission


def submit_all(db: Session, attempt: VizuMockAttempt) -> VizuMockAttempt:
    """Final "Schreiben absenden" — freezes every saved draft as SUBMITTED
    and stamps the attempt. Idempotent: a repeat call is a no-op that
    just returns the already-submitted attempt (never re-stamps the
    timestamp or raises)."""
    if attempt.schreiben_submitted_at is not None:
        return attempt

    now = datetime.now(timezone.utc)
    submissions = get_own_submissions(db, attempt.id)
    for submission in submissions:
        submission.status = STATUS_SUBMITTED
        submission.submitted_at = now

    attempt.schreiben_submitted_at = now
    db.commit()
    db.refresh(attempt)
    return attempt
