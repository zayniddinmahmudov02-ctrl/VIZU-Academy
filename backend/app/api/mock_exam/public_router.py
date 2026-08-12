from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.mock_exam import (
    CertificationProviderResponse,
    MockExamLevelResponse,
    PublicKompetenzDetailResponse,
    PublicKompetenzSummary,
    PublicModelTestDetailResponse,
    PublicModelTestResponse,
)
from app.services.mock_exam import public_service

# No auth dependency at the router level — mirrors the public courses
# router (app/api/courses/router.py): browsing the Vorbereitung hierarchy
# is free/public like browsing courses, matching the existing
# access-control architecture rather than inventing a new one. Every
# query is scoped to published/active content regardless.
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
def list_public_model_tests(level_id: UUID, db: Session = Depends(get_db)):
    return public_service.get_public_model_tests(db, level_id)


@router.get("/model-tests/{model_test_id}", response_model=PublicModelTestDetailResponse)
def get_public_model_test(model_test_id: UUID, db: Session = Depends(get_db)):
    model_test = public_service.get_public_model_test(db, model_test_id)
    if model_test is None:
        raise HTTPException(status_code=404, detail="Model test not found.")

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
def get_public_kompetenz(kompetenz_id: UUID, db: Session = Depends(get_db)):
    kompetenz = public_service.get_public_kompetenz(db, kompetenz_id)
    if kompetenz is None:
        raise HTTPException(status_code=404, detail="Kompetenz not found.")
    return kompetenz
