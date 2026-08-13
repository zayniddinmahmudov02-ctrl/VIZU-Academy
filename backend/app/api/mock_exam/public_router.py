from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.mock_exam import (
    CertificationProviderResponse,
    MockExamLevelResponse,
    PublicKompetenzDetailResponse,
    PublicKompetenzSummary,
    PublicModelTestDetailResponse,
    PublicModelTestResponse,
)
from app.services.mock_exam import public_service
from app.services.vizu_pay.access import can_access_model_test

# No mandatory-login dependency at the router level — mirrors the public
# courses router (app/api/courses/router.py): browsing the Vorbereitung
# hierarchy is visible to anonymous visitors, same as browsing courses.
# get_current_user_optional is used only where Premium status changes the
# response (locking, content access) — every query stays scoped to
# published/active content regardless of who's asking.
router = APIRouter(
    prefix="/mock-exam/public",
    tags=["Mock Exam — Public (Vorbereitung)"],
)


@router.get("/providers", response_model=list[CertificationProviderResponse])
def list_public_providers(db: Session = Depends(get_db)):
    return public_service.get_public_providers(db)


@router.get("/levels", response_model=list[MockExamLevelResponse])
def list_public_levels(provider_id: UUID, db: Session = Depends(get_db)):
    return public_service.get_public_levels(db, provider_id)


@router.get("/model-tests", response_model=list[PublicModelTestResponse])
def list_public_model_tests(
    level_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Every model test in the level is listed regardless of lock state —
    only PublicModelTestResponse.is_locked changes. The actual content gate
    is enforced in get_public_model_test/get_public_kompetenz below, and
    again when starting an attempt (attempt_service.create_attempt) — this
    listing endpoint is presentation only."""
    tests = public_service.get_public_model_tests(db, level_id)
    return [
        PublicModelTestResponse(
            id=t.id,
            level_id=t.level_id,
            title=t.title,
            description=t.description,
            sort_order=t.sort_order,
            is_locked=not can_access_model_test(t, current_user),
        )
        for t in tests
    ]


@router.get("/model-tests/{model_test_id}", response_model=PublicModelTestDetailResponse)
def get_public_model_test(
    model_test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    model_test = public_service.get_public_model_test(db, model_test_id)
    if model_test is None:
        raise HTTPException(status_code=404, detail="Model test not found.")

    if not can_access_model_test(model_test, current_user):
        raise HTTPException(
            status_code=403,
            detail="PREMIUM_REQUIRED",
        )

    return PublicModelTestDetailResponse(
        id=model_test.id,
        level_id=model_test.level_id,
        title=model_test.title,
        description=model_test.description,
        kompetenzen=[
            PublicKompetenzSummary(
                id=k.id,
                type=k.type,
                title=k.title,
                has_content=len(k.teile) > 0,
            )
            for k in model_test.kompetenzen
        ],
    )


@router.get("/kompetenzen/{kompetenz_id}", response_model=PublicKompetenzDetailResponse)
def get_public_kompetenz(
    kompetenz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    kompetenz = public_service.get_public_kompetenz(db, kompetenz_id)
    if kompetenz is None:
        raise HTTPException(status_code=404, detail="Kompetenz not found.")

    if not can_access_model_test(kompetenz.model_test, current_user):
        raise HTTPException(
            status_code=403,
            detail="PREMIUM_REQUIRED",
        )

    return kompetenz
