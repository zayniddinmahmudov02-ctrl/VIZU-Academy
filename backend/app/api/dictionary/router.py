"""Wörterbuch API — logged-in students; every word state belongs to the
requesting user (never taken from the request body)."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import dictionary as service

router = APIRouter(prefix="/dictionary", tags=["Wörterbuch"])


class RandomIn(BaseModel):
    level: str = service.ALL_LEVELS


class SavedIn(BaseModel):
    saved: bool


@router.get("/meta")
def dictionary_meta(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.meta(db)


@router.get("/search")
def search(
    q: str = Query("", max_length=80),
    level: str | None = None,
    word_type: str | None = Query(None, max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=service.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.search(db, user, q, level, word_type, page, page_size)


@router.get("/entries/{word_id}")
def entry(word_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.entry_card(db, user, word_id)


@router.post("/random")
def random_five(data: RandomIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.random_five(db, user, data.level)


@router.put("/entries/{word_id}/saved")
def saved(word_id: str, data: SavedIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.set_saved(db, user, word_id, data.saved)


@router.get("/saved")
def saved_words(
    q: str = Query("", max_length=80),
    level: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=service.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.saved_words(db, user, q, level, page, page_size)
