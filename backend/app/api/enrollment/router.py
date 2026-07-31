from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db

from app.models.user import User

from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
)

from app.services.enrollment import (
    EnrollmentService,
)

router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"],
)


@router.get(
    "",
    response_model=list[EnrollmentResponse],
)
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return EnrollmentService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=EnrollmentResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    item = EnrollmentService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found",
        )

    return item


@router.post(
    "",
    response_model=EnrollmentResponse,
)
def create(
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return EnrollmentService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=EnrollmentResponse,
)
def update(
    item_id: str,
    data: EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    item = EnrollmentService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    deleted = EnrollmentService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found",
        )

    return {
        "message": "Deleted",
    }