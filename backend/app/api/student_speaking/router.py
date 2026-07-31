from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user

from app.core.security.roles import UserRole

from app.db.session import get_db

from app.models.user import User

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


def _ensure_owner_or_admin(
    item_user_id: str,
    current_user: User,
):
    if (
        item_user_id != str(current_user.id)
        and current_user.role not in UserRole.ADMIN_PANEL_ROLES
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this student speaking",
        )


@router.get(
    "",
    response_model=list[StudentSpeakingResponse],
)
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = StudentSpeakingService(db).get_all()

    if current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return items

    return [
        item
        for item in items
        if item.user_id == str(current_user.id)
    ]


@router.get(
    "/{item_id}",
    response_model=StudentSpeakingResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = StudentSpeakingService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    _ensure_owner_or_admin(item.user_id, current_user)

    return item


@router.post(
    "",
    response_model=StudentSpeakingResponse,
)
def create(
    data: StudentSpeakingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owner_or_admin(data.user_id, current_user)

    return StudentSpeakingService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentSpeakingResponse,
)
def update(
    item_id: str,
    data: StudentSpeakingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = StudentSpeakingService(db).get(item_id)

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    _ensure_owner_or_admin(existing.user_id, current_user)

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
    current_user: User = Depends(get_current_user),
):
    existing = StudentSpeakingService(db).get(item_id)

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    _ensure_owner_or_admin(existing.user_id, current_user)

    deleted = StudentSpeakingService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student Speaking not found",
        )

    return {
        "message": "Student Speaking deleted"
    }
