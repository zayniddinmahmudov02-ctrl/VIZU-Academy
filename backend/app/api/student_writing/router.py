from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.student_writing import (
    StudentWritingCreate,
    StudentWritingUpdate,
    StudentWritingResponse,
)

from app.services.student_writing import (
    StudentWritingService,
)

router = APIRouter(
    prefix="/student-writings",
    tags=["Student Writings"],
)


@router.get(
    "",
    response_model=list[StudentWritingResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return StudentWritingService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=StudentWritingResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
):
    item = StudentWritingService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Writing not found",
        )

    return item


@router.post(
    "",
    response_model=StudentWritingResponse,
)
def create(
    data: StudentWritingCreate,
    db: Session = Depends(get_db),
):
    return StudentWritingService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentWritingResponse,
)
def update(
    item_id: str,
    data: StudentWritingUpdate,
    db: Session = Depends(get_db),
):
    item = StudentWritingService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Writing not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
):
    deleted = StudentWritingService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student Writing not found",
        )

    return {
        "message": "Deleted"
    }