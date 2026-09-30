from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_mock import (
    VizuMockAttemptResponse,
    VizuMockHoerenResult,
    VizuMockHoerenSubmitRequest,
    VizuMockHoerenTaskPublic,
    VizuMockLesenResult,
    VizuMockLesenSubmitRequest,
    VizuMockTaskPublic,
)
from app.services.vizu_mock import hoeren_service, lesen_service, service

router = APIRouter(prefix="/vizu-mock", tags=["VIZU-Mock"])


@router.post("/attempts", response_model=VizuMockAttemptResponse, status_code=201)
def create_attempt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_attempt(db, current_user.id)


@router.get("/attempts", response_model=list[VizuMockAttemptResponse])
def list_my_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_attempts(db, current_user.id)


@router.get("/attempts/{attempt_id}", response_model=VizuMockAttemptResponse)
def get_my_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = service.get_own_attempt(db, current_user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return attempt


@router.post("/attempts/{attempt_id}/complete", response_model=VizuMockAttemptResponse)
def complete_my_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = service.complete_attempt(db, current_user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return attempt


# ============================================================
# Lesen — real content, real grading (Hören/Schreiben/Sprechen are still
# framework-only, see the attempt model's docstring)
# ============================================================


@router.get("/lesen/tasks", response_model=list[VizuMockTaskPublic])
def get_lesen_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return lesen_service.list_lesen_tasks(db)


@router.post("/attempts/{attempt_id}/lesen/submit", response_model=VizuMockLesenResult)
def submit_lesen_answers(
    attempt_id: UUID,
    data: VizuMockLesenSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = service.get_own_attempt(db, current_user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return lesen_service.submit_lesen(db, attempt, data.answers)


@router.get("/attempts/{attempt_id}/lesen/result", response_model=VizuMockLesenResult)
def get_lesen_result(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = service.get_own_attempt(db, current_user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return lesen_service.get_lesen_result(db, attempt)


# ============================================================
# Hören — real content, real grading (Schreiben/Sprechen are still
# framework-only, see the attempt model's docstring)
# ============================================================


@router.get("/hoeren/tasks", response_model=list[VizuMockHoerenTaskPublic])
def get_hoeren_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return hoeren_service.list_hoeren_tasks(db)


@router.post("/attempts/{attempt_id}/hoeren/submit", response_model=VizuMockHoerenResult)
def submit_hoeren_answers(
    attempt_id: UUID,
    data: VizuMockHoerenSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = service.get_own_attempt(db, current_user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return hoeren_service.submit_hoeren(db, attempt, data.answers)


@router.get("/attempts/{attempt_id}/hoeren/result", response_model=VizuMockHoerenResult)
def get_hoeren_result(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = service.get_own_attempt(db, current_user.id, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return hoeren_service.get_hoeren_result(db, attempt)
