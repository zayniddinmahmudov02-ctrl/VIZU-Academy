from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user

from app.db.session import get_db

from app.models.user import User

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
    current_user: User = Depends(get_current_user),
):
    return ExamService(db).get_all()


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
)
def get_one(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
