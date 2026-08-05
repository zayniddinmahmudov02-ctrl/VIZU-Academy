from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.language import (
    LanguageCreate,
    LanguageLearnersResponse,
    LanguageResponse,
    LanguageSettingsResponse,
    LanguageSettingsUpdate,
    LanguageStatistics,
    LanguageUpdate,
)
from app.services.language import (
    create_language,
    delete_language,
    get_language,
    get_language_learners,
    get_language_statistics,
    get_languages,
    get_or_create_language_settings,
    update_language,
    update_language_settings,
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
def get_language_endpoint(
    language_id: UUID,
    db: Session = Depends(get_db),
):
    language = get_language(db, language_id)

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
def delete_language_endpoint(
    language_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Soft delete — raises 404/409 itself (missing / still in use / default).
    delete_language(db, language_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.get(
    "/{language_id}/statistics",
    response_model=LanguageStatistics,
)
def get_language_statistics_endpoint(
    language_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    stats = get_language_statistics(db, language_id)

    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    return stats


@router.get(
    "/{language_id}/learners",
    response_model=LanguageLearnersResponse,
)
def get_language_learners_endpoint(
    language_id: UUID,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    result = get_language_learners(db, language_id, search, page, page_size)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    return result


@router.get(
    "/{language_id}/settings",
    response_model=LanguageSettingsResponse,
)
def get_language_settings_endpoint(
    language_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    settings = get_or_create_language_settings(db, language_id)

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    return settings


@router.put(
    "/{language_id}/settings",
    response_model=LanguageSettingsResponse,
)
def update_language_settings_endpoint(
    language_id: UUID,
    payload: LanguageSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    settings = update_language_settings(db, language_id, payload)

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found.",
        )

    return settings
