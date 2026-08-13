from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.db.session import get_db

from app.models.lesson import Lesson
from app.models.reading import Reading
from app.models.user import User
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.reading_question import (
    ReadingQuestionCreate,
    ReadingQuestionUpdate,
    ReadingQuestionResponse,
)

from app.services.reading_question import (
    ReadingQuestionService,
)

router = APIRouter(
    prefix="/reading-questions",
    tags=["Reading Questions"],
)


@router.get(
    "",
    response_model=list[ReadingQuestionResponse],
)
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every reading — admin CMS content table only.
    return ReadingQuestionService(db).get_all()


@router.get(
    "/{question_id}",
    response_model=ReadingQuestionResponse,
)
def get_one(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = ReadingQuestionService(db).get(question_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    # Direct-by-ID must not bypass the free-3-lessons/Premium rule that
    # gates the parent reading's lesson.
    reading = db.get(Reading, item.reading_id)
    lesson = db.get(Lesson, reading.lesson_id) if reading else None
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return item


@router.post(
    "",
    response_model=ReadingQuestionResponse,
)
def create(
    data: ReadingQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return ReadingQuestionService(db).create(data)


@router.put(
    "/{question_id}",
    response_model=ReadingQuestionResponse,
)
def update(
    question_id: str,
    data: ReadingQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    item = ReadingQuestionService(db).update(
        question_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    return item


@router.delete("/{question_id}")
def delete(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = ReadingQuestionService(db).delete(
        question_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    return {
        "message": "Deleted",
    }
