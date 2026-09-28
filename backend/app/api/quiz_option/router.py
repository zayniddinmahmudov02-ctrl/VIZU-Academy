from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user_optional
from app.core.security.roles import UserRole
from app.db.session import get_db

from app.models.user import User

from app.schemas.quiz_option import (
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
