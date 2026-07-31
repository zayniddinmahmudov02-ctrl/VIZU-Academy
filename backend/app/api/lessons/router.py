from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.lesson import (
    LessonCreate,
    LessonDetail,
    LessonListItem,
    LessonResponse,
    LessonUpdate,
)
from app.services.lesson import (
    LessonService,
    get_all_lessons,
    get_lesson_detail,
    get_lessons_for_module,
)

router = APIRouter(
    prefix="/lessons",
    tags=["Lessons"],
)


@router.get(
    "",
    response_model=list[LessonListItem],
)
def list_all_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_lessons(db, str(current_user.id))


@router.get(
    "/module/{module_id}",
    response_model=list[LessonResponse],
)
def list_lessons_by_module(
    module_id: UUID,
    db: Session = Depends(get_db),
):
    return get_lessons_for_module(db, str(module_id))


@router.get(
    "/{lesson_id}",
    response_model=LessonDetail,
)
def get_lesson(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = get_lesson_detail(db, str(lesson_id), str(current_user.id))

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found",
        )

    return lesson


@router.post(
    "",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    data: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return LessonService(db).create(data)


@router.put(
    "/{lesson_id}",
    response_model=LessonResponse,
)
def update_lesson(
    lesson_id: UUID,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    lesson = LessonService(db).update(str(lesson_id), data)

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found",
        )

    return lesson


@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lesson(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = LessonService(db).delete(str(lesson_id))

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
