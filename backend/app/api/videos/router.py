from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    get_current_user,
    require_admin_panel_access,
)
from app.core.security.jwt import decode_video_stream_token
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


@router.get("/{video_id}/stream")
def stream_video(
    video_id: UUID,
    token: str,
    db: Session = Depends(get_db),
):
    """The only place video bytes are ever served from — not a public
    URL, not the /uploads static mount. A native <video> element can't
    send an Authorization header, so this is gated by the short-lived
    signed token GET /videos/{id} (or /by-lesson/{lesson_id}) embeds in
    the URL it returns, instead of the usual Bearer-token dependency —
    same trust model as an S3/CloudFront presigned URL. FileResponse
    handles Range/206 requests natively, so seeking keeps working."""

    try:
        token_video_id = decode_video_stream_token(token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired stream token")

    if token_video_id != str(video_id):
        raise HTTPException(status_code=403, detail="Token does not authorize this video")

    service = VideoService(db)
    video = service.get(video_id)

    if video is None or not video.is_published or not video.storage_key:
        raise HTTPException(status_code=404, detail="Video not found")

    path = service.resolve_video_path(video)

    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file missing on disk")

    return FileResponse(path=path, media_type="video/mp4")


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
