from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.speaking import (
    SpeakingCreate,
    SpeakingResponse,
    SpeakingUpdate,
)
from app.services.speaking import SpeakingService
from app.services.vizu_pay.access import can_access_lesson

router = APIRouter(
    prefix="/speakings",
    tags=["Speakings"],
)


@router.get("", response_model=list[SpeakingResponse])
def get_speakings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only.
    return SpeakingService(db).get_all()


@router.get("/lesson/{lesson_id}", response_model=list[SpeakingResponse])
def get_lesson_speakings(
    lesson_id: str,
    db: Session = Depends(get_db),
    __: User = Depends(require_lesson_access),
):
    """Student-facing, published-only — Sprechen's source of truth (the
    Assessment Engine's Sprechen implementation is no longer used by the
    student frontend; see lesson-sections.ts)."""
    return SpeakingService(db).get_by_lesson(lesson_id, published_only=True)


@router.get("/{speaking_id}", response_model=SpeakingResponse)
def get_speaking(
    speaking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    speaking = SpeakingService(db).get(speaking_id)

    if not speaking:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    # Direct-by-ID must not bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, speaking.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

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
