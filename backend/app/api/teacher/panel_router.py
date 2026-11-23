"""Teacher Panel sections (dashboard, Schüler, Kurse, Unterricht, Aufgaben, Materialien, Nachrichten, Einstellungen) and the
read-only Kontroll area. Every route: require_teacher_panel_access (TEACHER or SUPER_ADMIN, own password set); Kontroll also
require_student_control (the Kontroll permission). Scoping rules: app.services.teacher.panel; Kontroll: app.services.activity.stats."""

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_student_control, require_teacher_panel_access
from app.core.audit import write_audit
from app.core.client_ip import client_ip
from app.db.session import get_db
from app.models.user import User
from app.services.activity import stats
from app.services.teacher import panel, team
from app.services.teacher.team import USERNAME_RE

router = APIRouter(prefix="/teacher", tags=["Teacher Panel"])
kontroll_router = APIRouter(prefix="/teacher/kontroll", tags=["Teacher Panel - Kontroll"])

NO_STORE = "private, no-store"


def _private(response: Response) -> None:
    response.headers["Cache-Control"] = NO_STORE


@router.get("/me")
def teacher_me(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    team.profile(db, current_user)
    return {"id": current_user.id, "name": team.display_name(current_user), "username": current_user.username, "role": current_user.role,
            "can_access_student_control": team.can_access_control(db, current_user)}


class UsernameIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=50)


@router.put("/me/username")
def change_username(data: UsernameIn, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    """A teacher changes the own login name (unique, 3–50 of a–z 0–9 _ . -)."""
    name = data.username.strip().lower()
    if not USERNAME_RE.match(name):
        raise HTTPException(status_code=422, detail="USERNAME_INVALID: 3–50 Zeichen, nur a–z, 0–9, _ . -")
    if name != current_user.username:
        if db.scalar(select(User.id).where(func.lower(User.username) == name, User.id != current_user.id)) is not None:
            raise HTTPException(status_code=409, detail="USERNAME_TAKEN")
        old = current_user.username
        current_user.username = name
        db.commit()
        write_audit(db, current_user.id, "teacher_username_changed", current_user.id, f"{old} -> {name}", client_ip(request))
    return {"username": current_user.username}


@router.get("/dashboard")
def dashboard(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    return panel.dashboard(db, current_user)


@router.get("/roster")
def roster(response: Response, search: str | None = Query(None, max_length=120), group_id: UUID | None = None, course_id: UUID | None = None,
           level: Literal["A1", "A2", "B1", "B2", "C1"] | None = None, status: Literal["active", "inactive", "blocked"] | None = None,
           activity: Literal["7d", "30d", "inactive", "never"] | None = None, registered_from: date | None = None,
           registered_to: date | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
           db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    """Every student of the teacher's groups and assigned courses, once (several groups are listed in the row)."""
    _private(response)
    return panel.students(db, current_user, search=search, group_id=group_id, course_id=course_id, level=level, status=status,
                          activity=activity, registered_from=registered_from, registered_to=registered_to, page=page, page_size=page_size)


@router.get("/roster/{student_id}")
def roster_student(student_id: UUID, response: Response, db: Session = Depends(get_db),
                   current_user: User = Depends(require_teacher_panel_access)):
    """Learning profile of one student in the teacher's scope (else 404)."""
    _private(response)
    return panel.student_profile(db, current_user, student_id)


@router.get("/courses")
def teacher_courses(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    return panel.courses(db, current_user)


@router.get("/video-lessons")
def video_lessons(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    return panel.unterricht(db, current_user)


@router.get("/tasks")
def group_tasks(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    return panel.tasks(db, current_user)


@router.get("/materials")
def materials(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    return panel.materials(db, current_user)


@router.get("/messages")
def messages(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_panel_access)):
    _private(response)
    return panel.messages(db, current_user)


# ---------------- Kontroll (read only: GET routes only) ----------------


@kontroll_router.get("/students")
def kontroll_students(response: Response, search: str | None = Query(None, max_length=120),
                      sort: Literal["registered", "name", "usage", "last_activity"] = "registered",
                      page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
                      db: Session = Depends(get_db), current_user: User = Depends(require_student_control)):
    _private(response)
    return stats.kontroll_list(db, page=page, page_size=page_size, search=search, sort=sort)


@kontroll_router.get("/students/{student_id}")
def kontroll_student(student_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                     current_user: User = Depends(require_student_control)):
    """One student's activity. Every opened detail is written to audit_logs (who looked at whom)."""
    _private(response)
    data = stats.kontroll_detail(db, student_id)
    write_audit(db, current_user.id, "kontroll_student_viewed", student_id, None, client_ip(request))
    return data


@kontroll_router.get("/students/{student_id}/timeline")
def kontroll_timeline(student_id: UUID, response: Response, day: date | None = None, db: Session = Depends(get_db),
                      current_user: User = Depends(require_student_control)):
    _private(response)
    stats._student_or_404(db, student_id)
    return stats.timeline(db, student_id, day)
