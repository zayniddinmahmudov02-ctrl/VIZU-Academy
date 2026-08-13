from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.listening import (
    ListeningCreate,
    ListeningResponse,
    ListeningUpdate,
)
from app.services.listening import ListeningService
from app.services.vizu_pay.access import can_access_lesson

router = APIRouter(
    prefix="/listenings",
    tags=["Listenings"],
)


@router.get("", response_model=list[ListeningResponse])
def get_listenings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only.
    return ListeningService(db).get_all()


@router.get("/{listening_id}", response_model=ListeningResponse)
def get_listening(
    listening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listening = ListeningService(db).get(listening_id)

    if not listening:
        raise HTTPException(
            status_code=404,
            detail="Listening not found",
        )

    # Direct-by-ID must not bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, listening.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return listening


@router.post("", response_model=ListeningResponse)
def create_listening(
    data: ListeningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return ListeningService(db).create(data)


@router.put("/{listening_id}", response_model=ListeningResponse)
def update_listening(
    listening_id: str,
    data: ListeningUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    listening = ListeningService(db).update(
        listening_id,
        data,
    )

    if not listening:
        raise HTTPException(
            status_code=404,
            detail="Listening not found",
        )

    return listening


@router.delete("/{listening_id}")
def delete_listening(
    listening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = ListeningService(db).delete(listening_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Listening not found",
        )

    return {
        "message": "Listening deleted"
    }