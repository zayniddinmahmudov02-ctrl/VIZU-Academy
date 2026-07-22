from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.listening import (
    ListeningCreate,
    ListeningResponse,
    ListeningUpdate,
)
from app.services.listening import ListeningService

router = APIRouter(
    prefix="/listenings",
    tags=["Listenings"],
)


@router.get("", response_model=list[ListeningResponse])
def get_listenings(
    db: Session = Depends(get_db),
):
    return ListeningService(db).get_all()


@router.get("/{listening_id}", response_model=ListeningResponse)
def get_listening(
    listening_id: str,
    db: Session = Depends(get_db),
):
    listening = ListeningService(db).get(listening_id)

    if not listening:
        raise HTTPException(
            status_code=404,
            detail="Listening not found",
        )

    return listening


@router.post("", response_model=ListeningResponse)
def create_listening(
    data: ListeningCreate,
    db: Session = Depends(get_db),
):
    return ListeningService(db).create(data)


@router.put("/{listening_id}", response_model=ListeningResponse)
def update_listening(
    listening_id: str,
    data: ListeningUpdate,
    db: Session = Depends(get_db),
):
    listening = ListeningService(db).update(
        listening_id,
        data,
    )

    if not listening:
        raise HTTPException(
            status_code=404,
            detail="Listening not found",
        )

    return listening


@router.delete("/{listening_id}")
def delete_listening(
    listening_id: str,
    db: Session = Depends(get_db),
):
    deleted = ListeningService(db).delete(listening_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Listening not found",
        )

    return {
        "message": "Listening deleted"
    }