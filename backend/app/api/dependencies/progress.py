from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db

from app.models.lesson import Lesson
from app.models.user import User

from app.services.vizu_pay.access import can_access_lesson


async def require_lesson_access(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """The single gate every lesson-content endpoint (video, grammar,
    vocabulary, readings, the assessment engine's lesson endpoints) goes
    through: first-3-per-level free, Premium or staff otherwise. See
    app.services.vizu_pay.access.can_access_lesson — that function is the
    actual rule; this just adapts it to FastAPI's dependency injection so
    every router applies it identically instead of reimplementing it."""

    lesson = db.get(Lesson, lesson_id)

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    if not can_access_lesson(current_user, lesson):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PREMIUM_REQUIRED",
        )

    return current_user
