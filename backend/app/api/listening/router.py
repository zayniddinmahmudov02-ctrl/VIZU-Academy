from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.listening import (
    ListeningCreate,
    ListeningResponse,
    ListeningUpdate,
)
from app.services.listening import ListeningService
from app.core.security.roles import UserRole
from app.services.lms.access import ensure_lesson_open

def _student_view(listening) -> ListeningResponse:
    """A Hören task with questions is a test: its transcript is shown only
    after a submitted attempt (GET /lesson-skills/.../hoeren), never here."""
    view = ListeningResponse.model_validate(listening)
    return view.model_copy(update={"transcript": None}) if listening.questions else view


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


@router.get("/lesson/{lesson_id}", response_model=list[ListeningResponse])
def get_lesson_listenings(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    __: User = Depends(require_lesson_access),
):
    """Student-facing, published-only — Hören's source of truth (the
    Assessment Engine's Hören implementation is no longer used by the
    student frontend; see lesson-sections.ts). A Listening row with no
    real audio_url yet simply isn't published, so it never reaches this
    endpoint — the frontend never has to fabricate a player for missing
    audio."""
    return [_student_view(item) for item in ListeningService(db).get_by_lesson(lesson_id, published_only=True)]


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
    if lesson is None:
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")
    ensure_lesson_open(db, current_user, lesson)

    if current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return listening
    if not listening.is_published:
        raise HTTPException(status_code=404, detail="Listening not found")
    return _student_view(listening)


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