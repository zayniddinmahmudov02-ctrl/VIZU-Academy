from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.model_test import ModelTest
from app.schemas.mock_exam import (
    CertificationProviderCreate,
    CertificationProviderResponse,
    CertificationProviderUpdate,
    KompetenzCreate,
    KompetenzResponse,
    KompetenzUpdate,
    MockExamLevelCreate,
    MockExamLevelResponse,
    MockExamLevelUpdate,
    ModelTestCreate,
    ModelTestResponse,
    ModelTestScoreResponse,
    ModelTestUpdate,
    TeilCreate,
    TeilResponse,
    TeilUpdate,
)
from app.services.mock_exam import hierarchy_service

router = APIRouter(
    prefix="/mock-exam",
    tags=["Mock Exam — Hierarchy"],
    dependencies=[Depends(require_super_admin)],
)


# ============================================================
# Certification Provider (Certificates)
# ============================================================


@router.get("/providers", response_model=list[CertificationProviderResponse])
def list_providers(db: Session = Depends(get_db)):
    return hierarchy_service.get_providers(db)


@router.post("/providers", response_model=CertificationProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(data: CertificationProviderCreate, db: Session = Depends(get_db)):
    return hierarchy_service.create_provider(db, data)


@router.put("/providers/{provider_id}", response_model=CertificationProviderResponse)
def update_provider(provider_id: UUID, data: CertificationProviderUpdate, db: Session = Depends(get_db)):
    provider = hierarchy_service.update_provider(db, provider_id, data)
    if provider is None:
        raise HTTPException(status_code=404, detail="Certification provider not found.")
    return provider


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: UUID, db: Session = Depends(get_db)):
    if not hierarchy_service.delete_provider(db, provider_id):
        raise HTTPException(status_code=404, detail="Certification provider not found.")


# ============================================================
# Mock Exam Level
# ============================================================


@router.get("/levels", response_model=list[MockExamLevelResponse])
def list_levels(provider_id: UUID | None = None, db: Session = Depends(get_db)):
    return hierarchy_service.get_levels(db, provider_id)


@router.post("/levels", response_model=MockExamLevelResponse, status_code=status.HTTP_201_CREATED)
def create_level(data: MockExamLevelCreate, db: Session = Depends(get_db)):
    return hierarchy_service.create_level(db, data)


@router.put("/levels/{level_id}", response_model=MockExamLevelResponse)
def update_level(level_id: UUID, data: MockExamLevelUpdate, db: Session = Depends(get_db)):
    level = hierarchy_service.update_level(db, level_id, data)
    if level is None:
        raise HTTPException(status_code=404, detail="Level not found.")
    return level


@router.delete("/levels/{level_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_level(level_id: UUID, db: Session = Depends(get_db)):
    if not hierarchy_service.delete_level(db, level_id):
        raise HTTPException(status_code=404, detail="Level not found.")


# ============================================================
# Model Test
# ============================================================


@router.get("/model-tests", response_model=list[ModelTestResponse])
def list_model_tests(level_id: UUID | None = None, db: Session = Depends(get_db)):
    return hierarchy_service.get_model_tests(db, level_id)


@router.post("/model-tests", response_model=ModelTestResponse, status_code=status.HTTP_201_CREATED)
def create_model_test(data: ModelTestCreate, db: Session = Depends(get_db)):
    return hierarchy_service.create_model_test(db, data)


@router.put("/model-tests/{model_test_id}", response_model=ModelTestResponse)
def update_model_test(model_test_id: UUID, data: ModelTestUpdate, db: Session = Depends(get_db)):
    model_test = hierarchy_service.update_model_test(db, model_test_id, data)
    if model_test is None:
        raise HTTPException(status_code=404, detail="Model test not found.")
    return model_test


@router.delete("/model-tests/{model_test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_test(model_test_id: UUID, db: Session = Depends(get_db)):
    if not hierarchy_service.delete_model_test(db, model_test_id):
        raise HTTPException(status_code=404, detail="Model test not found.")


@router.get("/model-tests/{model_test_id}/score", response_model=ModelTestScoreResponse)
def get_model_test_score(model_test_id: UUID, db: Session = Depends(get_db)):
    if db.get(ModelTest, model_test_id) is None:
        raise HTTPException(status_code=404, detail="Model test not found.")
    return hierarchy_service.calculate_model_test_score(db, model_test_id)


# ============================================================
# Kompetenz
# ============================================================


@router.get("/kompetenzen", response_model=list[KompetenzResponse])
def list_kompetenzen(model_test_id: UUID | None = None, db: Session = Depends(get_db)):
    return hierarchy_service.get_kompetenzen(db, model_test_id)


@router.post("/kompetenzen", response_model=KompetenzResponse, status_code=status.HTTP_201_CREATED)
def create_kompetenz(data: KompetenzCreate, db: Session = Depends(get_db)):
    return hierarchy_service.create_kompetenz(db, data)


@router.put("/kompetenzen/{kompetenz_id}", response_model=KompetenzResponse)
def update_kompetenz(kompetenz_id: UUID, data: KompetenzUpdate, db: Session = Depends(get_db)):
    kompetenz = hierarchy_service.update_kompetenz(db, kompetenz_id, data)
    if kompetenz is None:
        raise HTTPException(status_code=404, detail="Kompetenz not found.")
    return kompetenz


@router.delete("/kompetenzen/{kompetenz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kompetenz(kompetenz_id: UUID, db: Session = Depends(get_db)):
    if not hierarchy_service.delete_kompetenz(db, kompetenz_id):
        raise HTTPException(status_code=404, detail="Kompetenz not found.")


# ============================================================
# Teil
# ============================================================


@router.get("/teile", response_model=list[TeilResponse])
def list_teile(kompetenz_id: UUID | None = None, db: Session = Depends(get_db)):
    return hierarchy_service.get_teile(db, kompetenz_id)


@router.post("/teile", response_model=TeilResponse, status_code=status.HTTP_201_CREATED)
def create_teil(data: TeilCreate, db: Session = Depends(get_db)):
    return hierarchy_service.create_teil(db, data)


@router.put("/teile/{teil_id}", response_model=TeilResponse)
def update_teil(teil_id: UUID, data: TeilUpdate, db: Session = Depends(get_db)):
    teil = hierarchy_service.update_teil(db, teil_id, data)
    if teil is None:
        raise HTTPException(status_code=404, detail="Teil not found.")
    return teil


@router.delete("/teile/{teil_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teil(teil_id: UUID, db: Session = Depends(get_db)):
    if not hierarchy_service.delete_teil(db, teil_id):
        raise HTTPException(status_code=404, detail="Teil not found.")
