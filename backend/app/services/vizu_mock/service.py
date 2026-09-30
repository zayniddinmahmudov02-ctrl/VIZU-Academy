from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_mock_attempt import STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMockAttempt


def create_attempt(db: Session, user_id: UUID) -> VizuMockAttempt:
    attempt = VizuMockAttempt(user_id=user_id, status=STATUS_IN_PROGRESS)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def list_attempts(db: Session, user_id: UUID) -> list[VizuMockAttempt]:
    return list(
        db.scalars(
            select(VizuMockAttempt)
            .where(VizuMockAttempt.user_id == user_id)
            .order_by(VizuMockAttempt.started_at.desc())
        )
    )


def get_own_attempt(db: Session, user_id: UUID, attempt_id: UUID) -> VizuMockAttempt | None:
    # Owner-scoped lookup — a guessed/foreign attempt id 404s exactly like
    # a nonexistent one, never leaking another student's attempt (same
    # IDOR-safe convention used throughout the student-facing API).
    return db.scalar(
        select(VizuMockAttempt).where(VizuMockAttempt.id == attempt_id, VizuMockAttempt.user_id == user_id)
    )


def complete_attempt(db: Session, user_id: UUID, attempt_id: UUID) -> VizuMockAttempt | None:
    attempt = get_own_attempt(db, user_id, attempt_id)
    if attempt is None:
        return None
    if attempt.status != STATUS_COMPLETED:
        attempt.status = STATUS_COMPLETED
        attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(attempt)
    return attempt
