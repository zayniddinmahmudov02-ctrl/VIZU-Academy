from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db

from app.models.user import User

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizResponse,
)

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