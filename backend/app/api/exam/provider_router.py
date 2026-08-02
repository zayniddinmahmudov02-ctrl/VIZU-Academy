from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.exam_provider import ExamProvider
from app.models.user import User
from app.schemas.exam import (
    ExamProviderCreate,
    ExamProviderResponse,
    ExamProviderUpdate,
)

router = APIRouter(
    prefix="/exam-providers",
    tags=["Exams"],
)


@router.get(
    "",
    response_model=list[ExamProviderResponse],
)
def list_providers(
    db: Session = Depends(get_db),
):
    return db.scalars(select(ExamProvider)).all()


@router.post(
    "",
    response_model=ExamProviderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_provider(
    payload: ExamProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    existing = db.scalar(
        select(ExamProvider).where(ExamProvider.code == payload.code)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An exam provider with this code already exists.",
        )

    provider = ExamProvider(**payload.model_dump())

    db.add(provider)
    db.commit()
    db.refresh(provider)

    return provider


@router.put(
    "/{provider_id}",
    response_model=ExamProviderResponse,
)
def update_provider(
    provider_id: str,
    payload: ExamProviderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    provider = db.get(ExamProvider, provider_id)

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam provider not found.",
        )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(provider, key, value)

    db.commit()
    db.refresh(provider)

    return provider


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    provider = db.get(ExamProvider, provider_id)

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam provider not found.",
        )

    db.delete(provider)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This provider still has exams assigned to it. Delete those exams first.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
