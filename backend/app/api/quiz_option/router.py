from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user_optional, require_admin_panel_access
from app.core.security.roles import UserRole
from app.db.session import get_db

from app.models.user import User

from app.schemas.quiz_option import (
    QuizOptionCreate,
    QuizOptionUpdate,
    QuizOptionResponse,
    QuizOptionPublicResponse,
)

from app.services.quiz_option import QuizOptionService

router = APIRouter(
    prefix="/quiz-options",
    tags=["Quiz Options"],
)


@router.get("", response_model=list[QuizOptionResponse] | list[QuizOptionPublicResponse])
def get_all(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Public (unauthenticated callers included — the student player
    fetches this) but role-aware: is_correct/match_value only ever go
    out to an admin-panel caller. Grading for everyone else happens
    server-side via POST /quizzes/{quiz_id}/submit."""
    items = QuizOptionService(db).get_all()

    if current_user is not None and current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return [QuizOptionResponse.model_validate(item) for item in items]

    return [QuizOptionPublicResponse.model_validate(item) for item in items]


@router.post("", response_model=QuizOptionResponse)
def create(
    data: QuizOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return QuizOptionService(db).create(data)


@router.put("/{option_id}", response_model=QuizOptionResponse)
def update(
    option_id: str,
    data: QuizOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    item = QuizOptionService(db).update(
        option_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return item


@router.delete("/{option_id}")
def delete(
    option_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = QuizOptionService(db).delete(option_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return {"message": "Deleted"}