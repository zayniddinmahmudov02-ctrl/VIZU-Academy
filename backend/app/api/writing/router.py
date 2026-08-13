from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.db.session import get_db

from app.models.lesson import Lesson
from app.models.user import User
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.writing import (
    WritingCreate,
    WritingUpdate,
    WritingResponse,
)

from app.services.writing import WritingService

router = APIRouter(
    prefix="/writings",
    tags=["Writings"],
)


@router.get("", response_model=list[WritingResponse])
def get_writings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only.
    return WritingService(db).get_all()


@router.get("/{writing_id}", response_model=WritingResponse)
def get_writing(
    writing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    writing = WritingService(db).get(writing_id)

    if not writing:
        raise HTTPException(
            status_code=404,
            detail="Writing not found",
        )

    # Direct-by-ID must not bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, writing.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return writing


@router.post("", response_model=WritingResponse)
def create_writing(
    data: WritingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return WritingService(db).create(data)


@router.put("/{writing_id}", response_model=WritingResponse)
def update_writing(
    writing_id: str,
    data: WritingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    writing = WritingService(db).update(
        writing_id,
        data,
    )

    if not writing:
        raise HTTPException(
            status_code=404,
            detail="Writing not found",
        )

    return writing


@router.delete("/{writing_id}")
def delete_writing(
    writing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = WritingService(db).delete(writing_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Writing not found",
        )

    return {
        "message": "Writing deleted"
    }