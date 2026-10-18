"""Admin: Lösung — answer keys of the Lesen and Hören tasks (A1–C1).
Read: every admin-panel role. Edit / verify / publish: content editors
(SUPER_ADMIN, ADMIN, CONTENT_MANAGER) — enforced here, not only in the UI.
Students never reach these routes; the student APIs keep hiding the key."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_content_editor
from app.db.session import get_db
from app.models.user import User
from app.services.lesson_skills import loesung

router = APIRouter(prefix="/admin/loesung", tags=["Admin - Lösung"])

Kind = Literal["lesen", "hoeren"]


class OptionIn(BaseModel):
    id: UUID
    text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class QuestionKeyIn(BaseModel):
    options: list[OptionIn] | None = None
    config: dict | None = None
    explanation: str | None = Field(default=None, max_length=2000)
    review: Literal["verified", "needs_review", "unverified"] | None = None
    note: str | None = Field(default=None, max_length=2000)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/overview")
def overview(
    level: Literal["A1", "A2", "B1", "B2", "C1"] | None = None,
    lesson_id: UUID | None = None,
    section: Kind | None = None,
    status: Literal["complete", "missing", "needs_review", "missing_audio", "ready", "published", "draft"] | None = None,
    publication: Literal["draft", "published"] | None = None,
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    return loesung.overview(db, level=level, lesson_id=lesson_id, section=section, state=status, publication=publication, search=q)


@router.get("/{kind}/{task_id}")
def task_detail(kind: Kind, task_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """The Aufgabe with text / audio info, every question WITH its key and
    review state, the validation report and the neighbouring Aufgaben."""
    return loesung.detail(db, kind, task_id)


@router.put("/{kind}/{task_id}/questions/{question_id}")
def save_question(kind: Kind, task_id: UUID, question_id: UUID, payload: QuestionKeyIn, request: Request, db: Session = Depends(get_db),
                  user: User = Depends(require_content_editor)):
    data = payload.model_dump(exclude_unset=True)
    if "options" in data and data["options"] is not None:
        data["options"] = [{"id": str(o["id"]), "text": o["text"], "is_correct": o["is_correct"]} for o in data["options"]]
    return loesung.save_question(db, kind, task_id, question_id, data, user, _ip(request))


@router.post("/{kind}/{task_id}/publish")
def publish(kind: Kind, task_id: UUID, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """409 NOT_READY_TO_PUBLISH with the list of problems, otherwise the
    existing publish (ReadingService.publish / ListeningService.update)."""
    return loesung.publish(db, kind, task_id, user, _ip(request))
