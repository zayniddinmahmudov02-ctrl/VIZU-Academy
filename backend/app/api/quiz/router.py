from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, get_current_user
from app.api.dependencies.progress import require_lesson_access
from app.core.security.roles import UserRole
from app.db.session import get_db

from app.models.quiz import QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON, Quiz
from app.models.user import User

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizResponse,
)

from app.services.lesson_progress import SectionGateService
from app.services.quiz import QuizService

router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
)


@router.get(
    "",
    response_model=list[QuizResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return QuizService(db).get_all()


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[QuizResponse],
)
def get_lesson_quizzes(
    lesson_id: str,
    quiz_type: str | None = None,
    published_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    __: User = Depends(require_lesson_access),
):
    """Optionally filtered by quiz_type (GRAMMAR/LESSON) — the lesson
    player uses this to fetch the mid-lesson Grammatik Quiz and the
    end-of-lesson Lesson Quiz as two distinct requests. Each is gated by
    the sequential lesson progression (Grammatik must be viewed before
    Grammatik Quiz; Sprechen must be submitted before Lesson Quiz) —
    admin/staff bypass, same as every other section gate."""
    if quiz_type in (QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON) and current_user.role not in UserRole.ADMIN_PANEL_ROLES:
        section = "grammatik_quiz" if quiz_type == QUIZ_TYPE_GRAMMAR else "lesson_quiz"
        if not SectionGateService(db).is_unlocked(current_user.id, UUID(lesson_id), section):
            raise HTTPException(status_code=403, detail="LESSON_SECTION_LOCKED")

    query = db.query(Quiz).filter(Quiz.lesson_id == lesson_id)
    if quiz_type:
        query = query.filter(Quiz.quiz_type == quiz_type)
    if published_only:
        query = query.filter(Quiz.is_published.is_(True))
    return query.order_by(Quiz.order_index).all()


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse,
)
def get_one(
    quiz_id: str,
    db: Session = Depends(get_db),
):
    quiz = QuizService(db).get(quiz_id)

    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return quiz


@router.post(
    "",
    response_model=QuizResponse,
)
def create(
    data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return QuizService(db).create(data)


@router.put(
    "/{quiz_id}",
    response_model=QuizResponse,
)
def update(
    quiz_id: str,
    data: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    quiz = QuizService(db).update(
        quiz_id,
        data,
    )

    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return quiz


@router.delete("/{quiz_id}")
def delete(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = QuizService(db).delete(
        quiz_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    return {
        "message": "Deleted",
    }