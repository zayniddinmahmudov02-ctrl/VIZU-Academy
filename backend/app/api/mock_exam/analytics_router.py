from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.schemas.mock_exam import (
    CertificationProviderAnalytics,
    DashboardSummary,
    ModelTestAnalytics,
)
from app.services.mock_exam import analytics_service

router = APIRouter(
    prefix="/mock-exam",
    tags=["Mock Exam — Analytics"],
    dependencies=[Depends(require_admin_panel_access)],
)


@router.get("/dashboard-summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    return analytics_service.get_dashboard_summary(db)


@router.get("/model-tests/{model_test_id}/analytics", response_model=ModelTestAnalytics)
def model_test_analytics(model_test_id: UUID, db: Session = Depends(get_db)):
    result = analytics_service.get_model_test_analytics(db, model_test_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Model test not found.")
    return result


@router.get("/providers/{provider_id}/analytics", response_model=CertificationProviderAnalytics)
def provider_analytics(provider_id: UUID, db: Session = Depends(get_db)):
    result = analytics_service.get_provider_analytics(db, provider_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Certification provider not found.")
    return result
