from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
)

from app.services.exam import (
    ExamService,
)

router = APIRouter(
    prefix="/exams",
    tags=["Exams"],
)


@router.get(
    "",
    response_model=list[ExamResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return ExamService(db).get_all()


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
)
def get_one(
    exam_id: str,
    db: Session = Depends(get_db),
):

    exam = ExamService(db).get(exam_id)

    if not exam:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    return exam


@router.post(
    "",
    response_model=ExamResponse,
)
def create(
    data: ExamCreate,
    db: Session = Depends(get_db),
):
    return ExamService(db).create(data)


@router.put(
    "/{exam_id}",
    response_model=ExamResponse,
)
def update(
    exam_id: str,
    data: ExamUpdate,
    db: Session = Depends(get_db),
):

    exam = ExamService(db).update(
        exam_id,
        data,
    )

    if not exam:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    return exam


@router.delete("/{exam_id}")
def delete(
    exam_id: str,
    db: Session = Depends(get_db),
):

    deleted = ExamService(db).delete(
        exam_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    return {
        "message": "Deleted",
    }