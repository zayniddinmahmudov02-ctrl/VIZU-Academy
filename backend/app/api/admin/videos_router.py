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
    order_index: int = Form(1),
    is_preview: bool = Form(False),
    is_published: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Uploads a video file directly to Cloudflare R2 and creates its
    metadata row in a single request. This is the only way a video's
    `storage_key` can be set — there is no endpoint that accepts a
    client-supplied storage key."""

    service = VideoService(db)

    return service.upload_video(
        lesson_id=lesson_id,
        file=file,
        title=title,
        description=description,
        thumbnail_url=thumbnail_url,
        order_index=order_index,
        is_preview=is_preview,
        is_published=is_published,
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
def delete_video(
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

    service.delete(video)
