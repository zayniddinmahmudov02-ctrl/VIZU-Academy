from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db

from app.models.user import User

from app.repositories.student_progress import StudentProgressRepository


async def require_video_completed(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Gate for lesson-activity endpoints that come after the video in
    the lesson flow (Video -> Vocabulary -> Grammar -> ... -> Quiz).
    Requires the caller be authenticated (so we know whose progress to
    check) and that they've completed this lesson's video, matching the
    "students must complete the video first" requirement server-side —
    not just in the frontend nav."""

    repository = StudentProgressRepository(db)

    progress = repository.get_by_user_and_lesson(
        str(current_user.id),
        str(lesson_id),
    )

    if progress is None or not progress.video_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete the video first",
        )

    return current_user
