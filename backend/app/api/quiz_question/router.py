import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user_optional
from app.core.security.roles import UserRole
from app.db.session import get_db

from app.models.quiz_question import QuizQuestion
from app.models.user import User

from app.schemas.quiz_question import (
    QuizQuestionResponse,
    QuizQuestionPublicResponse,
)

from app.services.quiz import student_view
from app.services.quiz_question import (
    QuizQuestionService,
)

router = APIRouter(
    prefix="/quiz-questions",
    tags=["Quiz Questions"],
)


def _to_public(item: QuizQuestion) -> QuizQuestionPublicResponse:
    pool = None
    if item.question_type == "MATCHING":
        pool = [o.match_value or "" for o in item.options]
        random.shuffle(pool)

    return QuizQuestionPublicResponse(
        id=item.id,
        quiz_id=item.quiz_id,
        question=item.question,
        question_type=item.question_type,
        explanation=item.explanation,
        points=item.points,
        order_index=item.order_index,
        is_published=item.is_published,
        match_value_pool=pool,
    )


@router.get(
    "",
    response_model=list[QuizQuestionResponse] | list[QuizQuestionPublicResponse],
)
def get_all(
    quiz_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Role-aware: an admin-panel caller gets every question with
    correct_text_answer; everyone else only the published questions of
    published quizzes in lessons they may open (free first lesson /
    purchase — app.services.quiz.student_view), never a key. `quiz_id`
    narrows it to one quiz (403 PREMIUM_REQUIRED for a closed lesson)."""
    if current_user is not None and current_user.role in UserRole.ADMIN_PANEL_ROLES:
        items = QuizQuestionService(db).get_all()
        if quiz_id is not None:
            items = [item for item in items if str(item.quiz_id) == str(quiz_id)]
        return [QuizQuestionResponse.model_validate(item) for item in items]

    return [_to_public(item) for item in student_view.visible_questions(db, current_user, quiz_id)]


@router.get(
    "/{question_id}",
    response_model=QuizQuestionResponse | QuizQuestionPublicResponse,
)
def get_one(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    item = QuizQuestionService(db).get(question_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    if current_user is not None and current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return QuizQuestionResponse.model_validate(item)

    student_view.ensure_question_open(db, current_user, item)
    return _to_public(item)
