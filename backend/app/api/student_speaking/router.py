from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.student_speaking import (
    StudentSpeakingCreate,
    StudentSpeakingUpdate,
    StudentSpeakingResponse,
)

from app.services.student_speaking import (
    StudentSpeakingService,
)

router = APIRouter(
    prefix="/student-speakings",
    tags=["Student Speakings"],
)


@router.get(
    "",
    response_model=list[StudentSpeakingResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return StudentSpeakingService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=StudentSpeakingResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
):
    item = StudentSpeakingService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    return item


@router.post(
    "",
    response_model=StudentSpeakingResponse,
)
def create(
    data: StudentSpeakingCreate,
    db: Session = Depends(get_db),
):
    return StudentSpeakingService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentSpeakingResponse,
)
def update(
    item_id: str,
    data: StudentSpeakingUpdate,
    db: Session = Depends(get_db),
):
    item = StudentSpeakingService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
):
    deleted = StudentSpeakingService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    return {
        "message": "Student Speaking deleted"
    }