from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.speaking import (
    SpeakingCreate,
    SpeakingResponse,
    SpeakingUpdate,
)
from app.services.speaking import SpeakingService

router = APIRouter(
    prefix="/speakings",
    tags=["Speakings"],
)


@router.get("", response_model=list[SpeakingResponse])
def get_speakings(
    db: Session = Depends(get_db),
):
    return SpeakingService(db).get_all()


@router.get("/{speaking_id}", response_model=SpeakingResponse)
def get_speaking(
    speaking_id: str,
    db: Session = Depends(get_db),
):
    speaking = SpeakingService(db).get(speaking_id)

    if not speaking:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    return speaking


@router.post("", response_model=SpeakingResponse)
def create_speaking(
    data: SpeakingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return SpeakingService(db).create(data)


@router.put("/{speaking_id}", response_model=SpeakingResponse)
def update_speaking(
    speaking_id: str,
    data: SpeakingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    speaking = SpeakingService(db).update(
        speaking_id,
        data,
    )

    if not speaking:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    return speaking


@router.delete("/{speaking_id}")
def delete_speaking(
    speaking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = SpeakingService(db).delete(speaking_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    return {
        "message": "Speaking deleted"
    }
