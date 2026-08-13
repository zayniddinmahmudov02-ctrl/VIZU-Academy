from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access, require_video_completed
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.reading import (
    ReadingCreate,
    ReadingResponse,
    ReadingUpdate,
)

from app.services.reading import ReadingService


router = APIRouter(
    prefix="/readings",
    tags=["Readings"],
)


@router.get(
    "/",
    response_model=list[ReadingResponse],
)
def get_readings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only; students
    # always go through GET /readings/lesson/{id}.
    service = ReadingService(db)

    return service.get_all()


@router.get(
    "/{reading_id}",
    response_model=ReadingResponse,
)
def get_reading(
    reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReadingService(db)
    reading = service.get(reading_id)

    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    # Same gate as GET /readings/lesson/{lesson_id} — direct-by-ID must not
    # bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, reading.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return reading


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[ReadingResponse],
)
def get_lesson_readings(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_video_completed),
    __: object = Depends(require_lesson_access),
):
    """Requires the caller to have completed this lesson's video first,
    and (require_lesson_access) that they have access to this lesson at
    all under the free-3-lessons / Premium rule."""

    service = ReadingService(db)

    return service.get_by_lesson(
        lesson_id,
    )


@router.post(
    "/",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reading(
    payload: ReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = ReadingService(db)

    return service.create(payload.model_dump())


@router.put(
    "/{reading_id}",
    response_model=ReadingResponse,
)
def update_reading(
    reading_id: UUID,
    payload: ReadingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = ReadingService(db)

    reading = service.get(reading_id)

    return service.update(
        reading,
        payload.model_dump(exclude_unset=True),
    )


@router.patch(
    "/{reading_id}/publish",
    response_model=ReadingResponse,
)
def publish_reading(
    reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = ReadingService(db)

    reading = service.get(reading_id)

    return service.publish(reading)


@router.patch(
    "/{reading_id}/unpublish",
    response_model=ReadingResponse,
)
def unpublish_reading(
    reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = ReadingService(db)

    reading = service.get(reading_id)

    return service.unpublish(reading)


@router.delete(
    "/{reading_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reading(
    reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    service = ReadingService(db)

    reading = service.get(reading_id)

    service.delete(reading)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )