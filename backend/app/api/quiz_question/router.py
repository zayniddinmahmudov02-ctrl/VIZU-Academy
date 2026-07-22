from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.quiz_question import (
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizQuestionResponse,
)

from app.services.quiz_question import (
    QuizQuestionService,
)

router = APIRouter(
    prefix="/quiz-questions",
    tags=["Quiz Questions"],
)


@router.get(
    "",
    response_model=list[QuizQuestionResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return QuizQuestionService(db).get_all()


@router.get(
    "/{question_id}",
    response_model=QuizQuestionResponse,
)
def get_one(
    question_id: str,
    db: Session = Depends(get_db),
):
    item = QuizQuestionService(db).get(question_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    return item


@router.post(
    "",
    response_model=QuizQuestionResponse,
)
def create(
    data: QuizQuestionCreate,
    db: Session = Depends(get_db),
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