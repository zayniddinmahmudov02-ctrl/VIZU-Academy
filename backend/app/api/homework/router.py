from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db

from app.models.user import User

from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkResponse,
)

from app.services.homework import HomeworkService

router = APIRouter(
    prefix="/homeworks",
    tags=["Homeworks"],
)


@router.get(
    "",
    response_model=list[HomeworkResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return HomeworkService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=HomeworkResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
):
    item = HomeworkService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Homework not found",
        )

    return item


@router.post(
    "",
    response_model=HomeworkResponse,
)
def create(
    data: HomeworkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return HomeworkService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=HomeworkResponse,
)
def update(
    item_id: str,
    data: HomeworkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    item = HomeworkService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Homework not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = HomeworkService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Homework not found",
        )

    return {
        "message": "Deleted",
    }