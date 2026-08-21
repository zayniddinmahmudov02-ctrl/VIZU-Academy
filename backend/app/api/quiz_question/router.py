import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user_optional, require_admin_panel_access
from app.core.security.roles import UserRole
from app.db.session import get_db

from app.models.quiz_question import QuizQuestion
from app.models.user import User

from app.schemas.quiz_question import (
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizQuestionResponse,
    QuizQuestionPublicResponse,
)

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
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Same public-but-role-aware shape as GET /quiz-options —
    correct_text_answer (CLOZE_TEXT/SENTENCE_COMPLETION) only ever
    goes out to an admin-panel caller."""
    items = QuizQuestionService(db).get_all()

    if current_user is not None and current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return [QuizQuestionResponse.model_validate(item) for item in items]

    return [_to_public(item) for item in items]


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

    return _to_public(item)


@router.post(
    "",
    response_model=QuizQuestionResponse,
)
def create(
    data: QuizQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return QuizQuestionService(db).create(data)


@router.put(
    "/{question_id}",
    response_model=QuizQuestionResponse,
)
def update(
    question_id: str,
    data: QuizQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    item = QuizQuestionService(db).update(
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
    deleted = QuizQuestionService(db).delete(
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