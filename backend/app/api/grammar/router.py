from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.services.vizu_pay.access import can_access_lesson

from app.schemas.grammar import (
    GrammarCreate,
    GrammarUpdate,
    GrammarResponse,
)

from app.services.grammar import GrammarService

router = APIRouter(
    prefix="/grammars",
    tags=["Grammars"],
)


@router.get("", response_model=list[GrammarResponse])
def get_grammars(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson in the platform — bypasses per-lesson
    # free/Premium gating entirely, so this is for the admin CMS content
    # table only. Students always go through GET /grammars/lesson/{id}.
    return GrammarService(db).get_all()


@router.get("/lesson/{lesson_id}", response_model=list[GrammarResponse])
def get_lesson_grammars(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_lesson_access),
):
    """Student-facing — published-only, matching the same pattern used by
    GET /vocabularies/lesson/{lesson_id} and GET /videos/by-lesson/{lesson_id}.
    A DRAFT grammar item must never reach a student. require_lesson_access
    gates the free-3-lessons-per-level / Premium rule the same way every
    other lesson-content endpoint does."""
    return GrammarService(db).get_by_lesson(lesson_id, published_only=True)


@router.get("/{grammar_id}", response_model=GrammarResponse)
def get_grammar(
    grammar_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    grammar = GrammarService(db).get(grammar_id)

    if not grammar:
        raise HTTPException(
            status_code=404,
            detail="Grammar not found",
        )

    # Direct-by-ID access must be gated exactly like GET /lesson/{lesson_id}
    # — otherwise the free-3-lessons/Premium rule is bypassable by anyone
    # who has a grammar_id (e.g. from a free lesson's own list response).
    lesson = db.get(Lesson, grammar.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return grammar


@router.post("", response_model=GrammarResponse)
def create_grammar(
    data: GrammarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return GrammarService(db).create(data)


@router.put("/{grammar_id}", response_model=GrammarResponse)
def update_grammar(
    grammar_id: str,
    data: GrammarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    grammar = GrammarService(db).update(
        grammar_id,
        data,
    )

    if not grammar:
        raise HTTPException(
            status_code=404,
            detail="Grammar not found",
        )

    return grammar


@router.delete("/{grammar_id}")
def delete_grammar(
    grammar_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = GrammarService(db).delete(grammar_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Grammar not found",
        )

    return {
        "message": "Grammar deleted"
    }