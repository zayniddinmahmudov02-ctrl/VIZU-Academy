from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.services.vizu_multilevel import service
from app.models.vizu_multilevel_writing import STATUS_DRAFT, STATUS_SUBMITTED, VizuMultilevelWritingSubmission, VizuMultilevelWritingTask

# "kamida 12/20" — a Schreiben Aufgabe counts as passed once its teacher-
# assigned score reaches at least 12 of its 20 max points (see the
# module's own spec, section 18). One task = one level here (unlike
# Lesen/Hören's multi-task-per-level aggregation), so no separate
# breakdown-aggregation step is needed.
PASS_THRESHOLD = 12


class WritingAlreadySubmittedError(Exception):
    """Raised when a draft save or final submit is attempted on an
    attempt whose Schreiben module has already been finally submitted —
    content is frozen from that point on (see VizuMultilevelAttempt
    .schreiben_submitted_at's own docstring)."""


class SectionTimeUpError(Exception):
    """The 20-minute Schreiben window (deadline + grace, server clock) is
    over — no more drafts are accepted."""


MAX_CONTENT_CHARS = 20000


def list_writing_tasks(db: Session) -> list[VizuMultilevelWritingTask]:
    return list(
        db.scalars(select(VizuMultilevelWritingTask).where(VizuMultilevelWritingTask.is_active.is_(True)).order_by(VizuMultilevelWritingTask.order_index))
    )


def get_own_submissions(db: Session, attempt_id: UUID) -> list[VizuMultilevelWritingSubmission]:
    return list(
        db.scalars(select(VizuMultilevelWritingSubmission).where(VizuMultilevelWritingSubmission.attempt_id == attempt_id))
    )


def _count_words(text: str) -> int:
    return len([w for w in text.split() if w])


def save_draft(db: Session, attempt: VizuMultilevelAttempt, task_id: UUID, content: str) -> VizuMultilevelWritingSubmission:
    if attempt.schreiben_submitted_at is not None:
        raise WritingAlreadySubmittedError()
    if not service.ensure_section_open(db, attempt, "schreiben"):
        raise SectionTimeUpError()

    task = db.scalar(
        select(VizuMultilevelWritingTask).where(
            VizuMultilevelWritingTask.id == task_id, VizuMultilevelWritingTask.is_active.is_(True)
        )
    )
    if task is None:
        raise LookupError("Writing task not found.")
    content = content[:MAX_CONTENT_CHARS]

    submission = db.scalar(
        select(VizuMultilevelWritingSubmission).where(
            VizuMultilevelWritingSubmission.attempt_id == attempt.id, VizuMultilevelWritingSubmission.task_id == task_id
        )
    )
    if submission is None:
        submission = VizuMultilevelWritingSubmission(attempt_id=attempt.id, task_id=task_id)
        db.add(submission)

    submission.content = content
    submission.word_count = _count_words(content)
    submission.status = STATUS_DRAFT
    submission.saved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission


def submit_all(db: Session, attempt: VizuMultilevelAttempt) -> VizuMultilevelAttempt:
    """Final "Schreiben absenden" — freezes every saved draft as SUBMITTED
    and stamps the attempt. Idempotent: a repeat call is a no-op that
    just returns the already-submitted attempt (never re-stamps the
    timestamp or raises)."""
    service.ensure_attempt_active(attempt)
    if attempt.schreiben_submitted_at is not None:
        # A second final submission is rejected (answers are locked).
        raise service.SectionFlowError("SECTION_ALREADY_SUBMITTED")

    # Stamps the section start if it was never opened (finishing without
    # answering), and enforces the Lesen -> Hören -> Schreiben order. A
    # late final submit is still accepted: it only freezes drafts that
    # were saved while the window was open (save_draft enforces that).
    service.begin_submission(db, attempt, "schreiben")

    now = datetime.now(timezone.utc)
    submissions = get_own_submissions(db, attempt.id)
    written = sum(1 for sub in submissions if sub.content.strip())
    service.check_min_answers(attempt, "schreiben", written, len(list_writing_tasks(db)))
    for submission in submissions:
        submission.status = STATUS_SUBMITTED
        submission.submitted_at = now

    attempt.schreiben_submitted_at = now
    # Queue every Aufgabe for the server-side AI evaluation (run in the
    # background by the router; see schreiben_evaluation_service).
    from app.services.vizu_multilevel import schreiben_evaluation_service

    schreiben_evaluation_service.mark_pending(db, attempt.id)
    db.commit()
    db.refresh(attempt)
    return attempt
