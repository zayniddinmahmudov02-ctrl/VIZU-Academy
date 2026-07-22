from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.lesson import LessonDetail, LessonListItem, LessonResponse
from app.services.lesson import get_all_lessons, get_lesson_detail, get_lessons_for_module

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
