from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    get_current_user,
    require_admin_panel_access,
)
from app.core.audit import write_audit
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
from app.services.video.service import log_missing_file, stored_file_path, video_media_type


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

    if path is None:
        # the row is fine, the bytes are not where storage_key says —
        # logged with the absolute expected path (journalctl), reported as
        # its own error code instead of a generic "not found"
        log_missing_file(video)
        raise HTTPException(status_code=404, detail="VIDEO_FILE_MISSING")

    return FileResponse(path=path, media_type=video_media_type(path), headers={"Cache-Control": "private, no-store"})


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

    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    # Only the fields the client sent; NOT NULL columns can't be cleared.
    # (Passing the schema object itself made the repository fail with a 500.)
    changes = payload.model_dump(exclude_unset=True)
    for field in ("title", "duration_seconds", "order_index", "is_preview", "is_published"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=422, detail=f"{field} must not be null")

    updated = service.update(
        video,
        changes,
    )
    write_audit(db, actor_id=current_user.id, action="video_updated", details=f"video={video_id} fields={','.join(sorted(changes))}")
    return updated


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


# ==================================================
# Subtitles (VIZU LMS) — WebVTT next to the video file in protected storage
# ==================================================

MAX_SUBTITLE_BYTES = 2 * 1024 * 1024


@router.post("/{video_id}/subtitles")
async def upload_subtitles(
    video_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Attach / replace the video's WebVTT subtitles (.vtt, max 2 MB)."""
    service = VideoService(db)
    video = service.get(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    data = await file.read(MAX_SUBTITLE_BYTES + 1)
    if len(data) > MAX_SUBTITLE_BYTES:
        raise HTTPException(status_code=413, detail="SUBTITLES_TOO_LARGE: max 2 MB")
    if not data.lstrip(b"\xef\xbb\xbf").startswith(b"WEBVTT"):
        raise HTTPException(status_code=400, detail="UNSUPPORTED_SUBTITLES: WebVTT (.vtt) files only")
    key = f"videos/{video.lesson_id}/subtitles/{uuid4().hex}.vtt"
    path = service.video_storage.ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    old_key = video.subtitle_key
    video.subtitle_key = key
    db.commit()
    if old_key:
        await service.video_storage.delete(old_key)
    write_audit(db, actor_id=current_user.id, action="video_subtitles_uploaded", details=f"video={video_id} bytes={len(data)}")
    return {"video_id": video.id, "has_subtitles": True}


@router.delete("/{video_id}/subtitles", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtitles(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)
    video = service.get(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    old_key = video.subtitle_key
    video.subtitle_key = None
    db.commit()
    if old_key:
        await service.video_storage.delete(old_key)
    write_audit(db, actor_id=current_user.id, action="video_subtitles_deleted", details=f"video={video_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{video_id}/subtitles")
def stream_subtitles(video_id: UUID, token: str, db: Session = Depends(get_db)):
    """Same signed stream token as GET /{video_id}/stream (a <track> element
    can't send a Bearer header either)."""
    try:
        token_video_id = decode_video_stream_token(token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired stream token")
    if token_video_id != str(video_id):
        raise HTTPException(status_code=403, detail="Token does not authorize this video")
    service = VideoService(db)
    video = service.get(video_id)
    if video is None or not video.is_published or not video.subtitle_key:
        raise HTTPException(status_code=404, detail="Subtitles not found")
    path = stored_file_path(video.subtitle_key)
    if path is None:
        raise HTTPException(status_code=404, detail="Subtitles file missing on disk")
    return FileResponse(path=path, media_type="text/vtt", headers={"Cache-Control": "private, no-store"})
