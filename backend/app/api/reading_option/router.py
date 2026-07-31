from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db

from app.models.user import User

from app.schemas.reading_option import (
    ReadingOptionCreate,
    ReadingOptionUpdate,
    ReadingOptionResponse,
)

from app.services.reading_option import ReadingOptionService

router = APIRouter(
    prefix="/reading-options",
    tags=["Reading Options"],
)


@router.get("", response_model=list[ReadingOptionResponse])
def get_all(db: Session = Depends(get_db)):
    return ReadingOptionService(db).get_all()


@router.get("/{option_id}", response_model=ReadingOptionResponse)
def get_one(
    option_id: str,
    db: Session = Depends(get_db),
):
    item = ReadingOptionService(db).get(option_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return item


@router.post("", response_model=ReadingOptionResponse)
def create(
    data: ReadingOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return ReadingOptionService(db).create(data)


@router.put("/{option_id}", response_model=ReadingOptionResponse)
def update(
    option_id: str,
    data: ReadingOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    item = ReadingOptionService(db).update(
        option_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return item


@router.delete("/{option_id}")
def delete(
    option_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = ReadingOptionService(db).delete(option_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return {"message": "Deleted"}
