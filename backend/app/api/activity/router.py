"""Activity heartbeats (time tracking for the Medien statistics and Kontroll). Rules: app.services.activity.tracker."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.activity import tracker

router = APIRouter(prefix="/activity", tags=["Activity"])

NO_STORE = {"Cache-Control": "private, no-store"}


class HeartbeatContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    area: Literal["COURSE", "WORTSCHATZ", "MUSIC", "FILM", "BOOK", "EXAM"]
    ref_id: UUID | None = None
    position: int | None = Field(default=None, ge=0, le=24 * 3600)


class HeartbeatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tab_id: str = Field(pattern=r"^[A-Za-z0-9_-]{6,40}$")
    active: bool = True
    final: bool = False
    contexts: list[HeartbeatContext] = Field(default_factory=list, max_length=4)


@router.post("/heartbeat")
def heartbeat(data: HeartbeatIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """get_current_user: every logged-in account may call it; only STUDENT accounts are recorded."""
    result = tracker.heartbeat(db, current_user, tab_id=data.tab_id, active=data.active, final=data.final,
                               contexts=[c.model_dump() for c in data.contexts])
    return JSONResponse(result, headers=NO_STORE)
