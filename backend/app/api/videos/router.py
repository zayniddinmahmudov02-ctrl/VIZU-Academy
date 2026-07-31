from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    get_current_user,
    require_admin_panel_access,
)
from app.db.session import get_db

from app.models.user import User

from app.schemas.video import (
    VideoCreate,
    VideoResponse,
    VideoStreamResponse,
    VideoUpdate,
)

from app.services.video import VideoService


router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)


@router.get(
    "/",
    response_model=list[VideoResponse],
)
def get_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # VideoResponse carries storage_key — an internal storage path, never
    # meant to reach a browser — so this listing is admin-only. Students
    # get playback exclusively through GET /videos/{id} (or
    # /videos/by-lesson/{lesson_id}), which return a playable URL and
    # nothing else.
    service = VideoService(db)
    return service.get_all()


@router.get(
    "/{video_id}",
    response_model=VideoStreamResponse,
)
def get_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student playback endpoint. Verifies the requester is authenticated
    and has access (free preview, active premium, or active enrollment in
    the video's course), then returns a playable URL. Never returns the
    storage_key or any other internal field."""

    service = VideoService(db)

    video, video_url = service.generate_streaming_url(
        video_id,
        current_user,
    )

    return VideoStreamResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        video_url=video_url,
    )


@router.get(
    "/by-lesson/{lesson_id}",
    response_model=VideoStreamResponse,
)
def get_lesson_video(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student playback endpoint for "the video for this lesson" — the
    first activity in every lesson. Same access gate as GET
    /videos/{video_id}, just resolved from a lesson instead of a video
    id."""

    service = VideoService(db)

    video, video_url = service.get_lesson_playback(
        lesson_id,
        current_user,
    )

    return VideoStreamResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        video_url=video_url,
    )


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[VideoResponse],
)
def get_lesson_videos(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Same reasoning as get_videos() above — VideoResponse exposes
    # storage_key, so this stays admin-only.
    service = VideoService(db)
    return service.get_by_lesson(
        lesson_id,
    )


@router.post(
    "/",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_video(
    payload: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)
    return service.create(payload.model_dump())


@router.put(
    "/{video_id}",
    response_model=VideoResponse,
)
def update_video(
    video_id: UUID,
    payload: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)

    video = service.get(video_id)

    return service.update(
        video,
        payload,
    )


@router.patch(
    "/{video_id}/publish",
    response_model=VideoResponse,
)
def publish_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)

    video = service.get(video_id)

    return service.publish(video)


@router.patch(
    "/{video_id}/unpublish",
    response_model=VideoResponse,
)
def unpublish_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)

    video = service.get(video_id)

    return service.unpublish(video)


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)

    video = service.get(video_id)

    await service.delete(video)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
