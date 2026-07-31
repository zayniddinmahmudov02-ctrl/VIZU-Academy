from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db

from app.models.user import User

from app.schemas.video import (
    VideoResponse,
    VideoUpdate,
)

from app.services.video import VideoService

router = APIRouter(
    prefix="/admin/videos",
    tags=["Admin - Videos"],
)


@router.get(
    "",
    response_model=list[VideoResponse],
)
def list_videos(
    lesson_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = VideoService(db)

    if lesson_id is not None:
        return service.get_by_lesson(lesson_id)

    return service.get_all()


@router.post(
    "/upload",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_video(
    lesson_id: UUID = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    thumbnail_url: str | None = Form(None),
    duration_seconds: int = Form(0),
    order_index: int = Form(1),
    is_preview: bool = Form(False),
    is_published: bool = Form(False),
    file: UploadFile = File(...),
    thumbnail_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Uploads a video file via the configured storage backend and
    creates its metadata row in a single request. This is the only way a
    video's `storage_key` can be set — there is no endpoint that accepts
    a client-supplied storage key. `duration_seconds` is detected
    client-side (the browser reads it off the file before submitting)
    since there's no server-side media-inspection dependency installed."""

    service = VideoService(db)

    return await service.upload_video(
        lesson_id=lesson_id,
        file=file,
        title=title,
        description=description,
        thumbnail_url=thumbnail_url,
        thumbnail_file=thumbnail_file,
        duration_seconds=duration_seconds,
        order_index=order_index,
        is_preview=is_preview,
        is_published=is_published,
    )


@router.put(
    "/{video_id}/replace",
    response_model=VideoResponse,
)
async def replace_video(
    video_id: UUID,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Swaps the backing file for an existing video, keeping its id and
    metadata (title, order, publish state, progress rows, ...) intact."""

    service = VideoService(db)

    video = service.get(video_id)

    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    return await service.replace_video(
        video,
        file,
        duration_seconds=duration_seconds,
    )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    return service.update(
        video,
        payload.model_dump(exclude_unset=True),
    )


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

    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    await service.delete(video)
