from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.student_quiz import (
    StudentQuizCreate,
    StudentQuizUpdate,
    StudentQuizResponse,
)

from app.services.student_quiz import (
    StudentQuizService,
)

router = APIRouter(
    prefix="/student-quizzes",
    tags=["Student Quizzes"],
)


@router.get(
    "",
    response_model=list[StudentQuizResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return StudentQuizService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=StudentQuizResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
):
    item = StudentQuizService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    return item


@router.post(
    "",
    response_model=StudentQuizResponse,
)
def create(
    data: StudentQuizCreate,
    db: Session = Depends(get_db),
):
    return StudentQuizService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentQuizResponse,
)
def update(
    item_id: str,
    data: StudentQuizUpdate,
    db: Session = Depends(get_db),
):
    item = StudentQuizService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
):
    deleted = StudentQuizService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    return {
        "message": "Deleted",
    }