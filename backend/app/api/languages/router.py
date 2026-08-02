from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.language import Language
from app.models.user import User
from app.schemas.language import (
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
)
from app.services.language import (
    create_language,
    get_languages,
    update_language,
)

router = APIRouter(
    prefix="/languages",
    tags=["Languages"],
)


@router.get(
    "/",
    response_model=list[LanguageResponse],
)
def list_languages(
    db: Session = Depends(get_db),
):
    return get_languages(db)


@router.get(
    "/{language_id}",
    response_model=LanguageResponse,
)
def get_language(
    language_id: UUID,
    db: Session = Depends(get_db),
):
    language = db.get(Language, language_id)

    if language is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    return language


@router.post(
    "/",
    response_model=LanguageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_language_endpoint(
    payload: LanguageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return create_language(
        db,
        payload,
    )


@router.put(
    "/{language_id}",
    response_model=LanguageResponse,
)
def update_language_endpoint(
    language_id: UUID,
    payload: LanguageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    language = update_language(
        db,
        language_id,
        payload,
    )

    if language is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    return language


@router.delete(
    "/{language_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_language(
    language_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    language = db.get(Language, language_id)

    if language is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    db.delete(language)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
