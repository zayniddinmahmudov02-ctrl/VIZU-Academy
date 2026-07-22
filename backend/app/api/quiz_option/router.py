from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.quiz_option import (
    QuizOptionCreate,
    QuizOptionUpdate,
    QuizOptionResponse,
)

from app.services.quiz_option import QuizOptionService

router = APIRouter(
    prefix="/quiz-options",
    tags=["Quiz Options"],
)


@router.get("", response_model=list[QuizOptionResponse])
def get_all(db: Session = Depends(get_db)):
    return QuizOptionService(db).get_all()


@router.post("", response_model=QuizOptionResponse)
def create(
    data: QuizOptionCreate,
    db: Session = Depends(get_db),
):
    return QuizOptionService(db).create(data)


@router.put("/{option_id}", response_model=QuizOptionResponse)
def update(
    option_id: str,
    data: QuizOptionUpdate,
    db: Session = Depends(get_db),
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
):
    deleted = QuizOptionService(db).delete(option_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return {"message": "Deleted"}