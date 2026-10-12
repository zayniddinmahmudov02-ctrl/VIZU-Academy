from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db

from app.models.lesson import Lesson
from app.models.reading import Reading
from app.models.user import User

from app.schemas.reading_question import ReadingQuestionResponse

from app.services.reading_question import (
    ReadingQuestionService,
)
from app.services.lms.access import ensure_lesson_open

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
    current_user: User = Depends(require_admin_panel_access),
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
    if lesson is None:
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")
    ensure_lesson_open(db, current_user, lesson)

    return item
