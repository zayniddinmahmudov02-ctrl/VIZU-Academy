"""Admin → Team: teacher accounts, Kontroll permission, status, password reset, group / course assignment, a SUPER_ADMIN account
that also teaches (`/admin-teachers/{user_id}` PUT / DELETE).
Every route: require_super_admin. Rules: app.services.teacher.team. Answers carrying a temporary password are no-store."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.core.client_ip import client_ip
from app.db.session import get_db
from app.models.user import User
from app.services.teacher import team

router = APIRouter(prefix="/admin/team", tags=["Admin - Team"])


def _private(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


class TeacherCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(min_length=2, max_length=200)
    username: str = Field(min_length=3, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=128)
    can_access_student_control: bool = False


class TeacherUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None, max_length=255)


class ControlIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class StatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: bool


class PasswordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str | None = Field(default=None, max_length=128)


@router.get("/overview")
def overview(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.overview(db, viewer=current_user)


@router.put("/admin-teachers/{user_id}")
def add_admin_teacher(user_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                      current_user: User = Depends(require_super_admin)):
    """A SUPER_ADMIN account also teaches (Team + My Teacher); its role and rights stay. Audited."""
    _private(response)
    return team.set_admin_teaches(db, current_user, user_id, True, client_ip(request))


@router.delete("/admin-teachers/{user_id}")
def remove_admin_teacher(user_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                         current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.set_admin_teaches(db, current_user, user_id, False, client_ip(request))


@router.get("/teachers")
def list_teachers(response: Response, search: str | None = Query(None, max_length=120),
                  status: Literal["active", "inactive"] | None = None, control: Literal["yes", "no"] | None = None,
                  page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
                  db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.list_teachers(db, search=search, status=status, control=control, page=page, page_size=page_size)


@router.get("/choices")
def choices(response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.choices(db)


@router.post("/teachers", status_code=201)
def create_teacher(data: TeacherCreate, request: Request, response: Response, db: Session = Depends(get_db),
                   current_user: User = Depends(require_super_admin)):
    _private(response)
    teacher, password = team.create(db, current_user, data.model_dump(), client_ip(request))
    return {"teacher": teacher, "temporary_password": password}


@router.get("/teachers/{teacher_id}")
def get_teacher(teacher_id: UUID, response: Response, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.detail(db, teacher_id)


@router.patch("/teachers/{teacher_id}")
def update_teacher(teacher_id: UUID, data: TeacherUpdate, request: Request, response: Response, db: Session = Depends(get_db),
                   current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.update(db, current_user, teacher_id, data.model_dump(exclude_unset=True), client_ip(request))


@router.put("/teachers/{teacher_id}/control")
def set_control(teacher_id: UUID, data: ControlIn, request: Request, response: Response, db: Session = Depends(get_db),
                current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.set_control(db, current_user, teacher_id, data.enabled, client_ip(request))


@router.put("/teachers/{teacher_id}/status")
def set_status(teacher_id: UUID, data: StatusIn, request: Request, response: Response, db: Session = Depends(get_db),
               current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.set_status(db, current_user, teacher_id, data.active, client_ip(request))


@router.post("/teachers/{teacher_id}/reset-password")
def reset_password(teacher_id: UUID, data: PasswordIn, request: Request, response: Response, db: Session = Depends(get_db),
                   current_user: User = Depends(require_super_admin)):
    _private(response)
    teacher, password = team.reset_password(db, current_user, teacher_id, data.password, client_ip(request))
    return {"teacher": teacher, "temporary_password": password}


@router.put("/teachers/{teacher_id}/groups/{group_id}")
def assign_group(teacher_id: UUID, group_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                 current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.assign_group(db, current_user, teacher_id, group_id, client_ip(request))


@router.delete("/teachers/{teacher_id}/groups/{group_id}")
def remove_group(teacher_id: UUID, group_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                 current_user: User = Depends(require_super_admin)):
    """The group goes to the acting administrator (a group always has one teacher)."""
    _private(response)
    return team.remove_group(db, current_user, teacher_id, group_id, client_ip(request))


@router.put("/teachers/{teacher_id}/courses/{course_id}")
def assign_course(teacher_id: UUID, course_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                  current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.assign_course(db, current_user, teacher_id, course_id, client_ip(request))


@router.delete("/teachers/{teacher_id}/courses/{course_id}")
def remove_course(teacher_id: UUID, course_id: UUID, request: Request, response: Response, db: Session = Depends(get_db),
                  current_user: User = Depends(require_super_admin)):
    _private(response)
    return team.remove_course(db, current_user, teacher_id, course_id, client_ip(request))
