from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User

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
):
    return GrammarService(db).get_all()


@router.get("/{grammar_id}", response_model=GrammarResponse)
def get_grammar(
    grammar_id: str,
    db: Session = Depends(get_db),
):
    grammar = GrammarService(db).get(grammar_id)

    if not grammar:
        raise HTTPException(
            status_code=404,
            detail="Grammar not found",
        )

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