from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_mock import VizuMockAttemptResponse
from app.services.vizu_mock import service

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
