from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user_optional
from app.core.security.roles import UserRole
from app.db.session import get_db

from app.models.user import User

from app.schemas.quiz_option import (
    QuizOptionResponse,
    QuizOptionPublicResponse,
)

from app.services.quiz import student_view
from app.services.quiz_option import QuizOptionService

router = APIRouter(
    prefix="/quiz-options",
    tags=["Quiz Options"],
)


@router.get("", response_model=list[QuizOptionResponse] | list[QuizOptionPublicResponse])
def get_all(
    quiz_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Role-aware: is_correct/match_value only ever go out to an
    admin-panel caller. Everyone else gets only the options of published
    questions in lessons they may open (free first lesson / purchase —
    app.services.quiz.student_view); `quiz_id` narrows it to one quiz.
    Grading happens server-side via POST /quizzes/{quiz_id}/submit."""
    if current_user is not None and current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return [QuizOptionResponse.model_validate(item) for item in QuizOptionService(db).get_all()]

    return [QuizOptionPublicResponse.model_validate(item) for item in student_view.visible_options(db, current_user, quiz_id)]
