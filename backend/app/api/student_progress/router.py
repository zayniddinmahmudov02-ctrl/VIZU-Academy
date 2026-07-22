from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.student_progress import (
    StudentProgressCreate,
    StudentProgressUpdate,
    StudentProgressResponse,
)

from app.services.student_progress import (
    StudentProgressService,
)

router = APIRouter(
    prefix="/student-progress",
    tags=["Student Progress"],
)


@router.get(
    "",
    response_model=list[StudentProgressResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return StudentProgressService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=StudentProgressResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
):
    item = StudentProgressService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Progress not found",
        )

    return item


@router.post(
    "",
    response_model=StudentProgressResponse,
)
def create(
    data: StudentProgressCreate,
    db: Session = Depends(get_db),
):
    return StudentProgressService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentProgressResponse,
)
def update(
    item_id: str,
    data: StudentProgressUpdate,
    db: Session = Depends(get_db),
):
    item = StudentProgressService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Progress not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
):
    deleted = StudentProgressService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Progress not found",
        )

    return {
        "message": "Deleted"
    }