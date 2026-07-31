from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db

from app.models.user import User

from app.schemas.video_progress import (
    VideoProgressCompleteRequest,
    VideoProgressResponse,
    VideoProgressUpdateRequest,
)

from app.services.video_progress import VideoProgressService


router = APIRouter(
    prefix="/videos",
    tags=["Video Progress"],
)


@router.get(
    "/progress/{lesson_id}",
    response_model=VideoProgressResponse,
)
def get_progress(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume state for the current user's watch of this lesson's video —
    zeroed defaults if they haven't started it yet."""

    service = VideoProgressService(db)

    return service.get_for_lesson(
        current_user,
        lesson_id,
    )


@router.post(
    "/progress",
    response_model=VideoProgressResponse,
)
def update_progress(
    payload: VideoProgressUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reports playback position. The server clamps forward jumps to real
    elapsed time — the response reflects what was actually accepted, not
    necessarily what was sent, so the player can snap back if clamped."""

    service = VideoProgressService(db)

    return service.update_progress(
        current_user,
        payload.video_id,
        payload.position,
        ended=payload.ended,
    )


@router.post(
    "/complete",
    response_model=VideoProgressResponse,
)
def complete_progress(
    payload: VideoProgressCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marks the video watched — only accepted if the server's own
    recorded watch_percent already meets the completion threshold (or the
    player reported the end event). Also unlocks the rest of the lesson
    by flipping StudentProgress.video_completed."""

    service = VideoProgressService(db)

    return service.complete_progress(
        current_user,
        payload.video_id,
        ended=payload.ended,
    )
