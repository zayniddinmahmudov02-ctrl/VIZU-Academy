"""Groups & Classroom API.

Every endpoint needs a logged-in user; who may do what is decided on the
server in app.services.study_groups.access (manage = the group's teacher or
a SUPER_ADMIN, view = managers + active members, otherwise 404). Request
bodies never carry user_id / teacher_id / role for the caller — the caller
is always the token's user; teacher_id in a body is only honoured for a
SUPER_ADMIN assigning a group."""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.client_ip import client_ip
from app.db.session import get_db
from app.models.study_group import CHAT_MODES, MODES
from app.models.user import User
from app.services.study_groups import chat, groups, progress
from app.services.study_groups.access import is_manager, require_manage, require_student_member, require_view

router = APIRouter(prefix="/groups", tags=["Groups & Classroom"])


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GroupCreate(_In):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(None, max_length=2000)
    level: str = Field(pattern="^(A1|A2|B1|B2|C1)$")
    mode: str = Field("online", pattern=f"^({'|'.join(MODES)})$")
    status: str | None = Field(None, pattern="^(active|paused|archived)$")
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = Field(None, ge=1, le=1000)
    chat_mode: str = Field("open", pattern=f"^({'|'.join(CHAT_MODES)})$")
    course_ids: list[UUID] = Field(default_factory=list, max_length=10)
    teacher_id: UUID | None = None  # SUPER_ADMIN only
    code_expires_at: datetime | None = None
    code_max_uses: int | None = Field(None, ge=1, le=10000)


class GroupUpdate(_In):
    name: str | None = Field(None, min_length=2, max_length=120)
    description: str | None = Field(None, max_length=2000)
    level: str | None = Field(None, pattern="^(A1|A2|B1|B2|C1)$")
    mode: str | None = Field(None, pattern=f"^({'|'.join(MODES)})$")
    status: str | None = Field(None, pattern="^(active|paused|archived|blocked)$")
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = Field(None, ge=1, le=1000)
    course_ids: list[UUID] | None = Field(None, max_length=10)
    teacher_id: UUID | None = None  # SUPER_ADMIN only


class CodeCreate(_In):
    expires_at: datetime | None = None
    max_uses: int | None = Field(None, ge=1, le=10000)


class CodeChange(_In):
    paused: bool | None = None
    revoke: bool = False
    expires_at: datetime | None = None
    max_uses: int | None = Field(None, ge=1, le=10000)


class JoinIn(_In):
    code: str = Field(min_length=4, max_length=20)


class MessageIn(_In):
    body: str = Field(min_length=1, max_length=chat.MAX_MESSAGE)


class MessageModerate(_In):
    delete: bool = False
    pinned: bool | None = None
    reason: str | None = Field(None, max_length=200)


class ChatModeIn(_In):
    chat_mode: str = Field(pattern=f"^({'|'.join(CHAT_MODES)})$")


class AnnouncementIn(_In):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=chat.MAX_ANNOUNCEMENT)
    is_pinned: bool = False


class AnnouncementUpdate(_In):
    title: str | None = Field(None, min_length=1, max_length=200)
    body: str | None = Field(None, min_length=1, max_length=chat.MAX_ANNOUNCEMENT)
    is_pinned: bool | None = None
    archived: bool | None = None


class MemberUpdate(_In):
    remove: bool = False
    restore: bool = False
    can_post: bool | None = None


class TaskIn(_In):
    lesson_id: UUID
    title: str | None = Field(None, max_length=200)
    note: str | None = Field(None, max_length=2000)
    due_at: datetime | None = None


def _ip(request: Request) -> str | None:
    return client_ip(request)


def _fields(model: BaseModel) -> dict:
    return model.model_dump(exclude_unset=True)


# ---------- teacher / admin lists ----------

@router.get("/options")
def options(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.options(db, user)


@router.get("/teaching")
def teaching(search: str | None = Query(None, max_length=80), level: str | None = None, status: str | None = None,
             course_id: UUID | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.list_groups(db, user, "teaching", search=search, level=level, status_=status, course_id=course_id,
                              page=page, page_size=page_size)


@router.get("/admin/all")
def admin_all(search: str | None = Query(None, max_length=80), level: str | None = None, status: str | None = None,
              teacher_id: UUID | None = None, course_id: UUID | None = None, created_from: date | None = None,
              created_to: date | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.list_groups(db, user, "all", search=search, level=level, status_=status, teacher_id=teacher_id, course_id=course_id,
                              created_from=created_from, created_to=created_to, page=page, page_size=page_size)


@router.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.admin_stats(db, user)


@router.post("", status_code=201)
def create_group(data: GroupCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, code = groups.create(db, user, data.model_dump())
    return {"group": group, "code": code}


# ---------- student ----------

@router.get("/my")
def my_groups(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.my_groups(db, user)


@router.post("/join/preview")
def join_preview(data: JoinIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.preview(db, user, data.code, _ip(request))


@router.post("/join")
def join(data: JoinIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.join(db, user, data.code, _ip(request))


# ---------- one group ----------

@router.get("/{group_id}")
def group_detail(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, member = require_view(db, user, group_id)
    manager = is_manager(user, group)
    out = groups.summary(db, group)
    out["viewer"] = {"is_manager": manager, "can_post": chat.can_post(group, user, member),
                     "unread": chat.unread_count(db, group.id, user.id, member.last_read_at) if member else 0}
    if manager:
        out["code"] = groups.code_info(db, user, group.id)
    return out


@router.patch("/{group_id}")
def update_group(group_id: UUID, data: GroupUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.update(db, user, group_id, _fields(data))


@router.post("/{group_id}/leave", status_code=204)
def leave_group(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    groups.leave(db, user, group_id)


@router.post("/{group_id}/code")
def regenerate_code(group_id: UUID, data: CodeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.regenerate_code(db, user, group_id, data.expires_at, data.max_uses)


@router.patch("/{group_id}/code")
def change_code(group_id: UUID, data: CodeChange, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.change_code(db, user, group_id, _fields(data))


@router.get("/{group_id}/members")
def members(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, _ = require_view(db, user, group_id)
    return groups.members(db, user, group)


@router.patch("/{group_id}/members/{user_id}")
def update_member(group_id: UUID, user_id: UUID, data: MemberUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.update_member(db, user, group_id, user_id, _fields(data))


# chat

@router.get("/{group_id}/messages")
def messages(group_id: UUID, before: datetime | None = None, after: datetime | None = None, limit: int = Query(50, ge=1, le=100),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, member = require_view(db, user, group_id)
    return chat.list_messages(db, user, group, member, before=before, after=after, limit=limit)


@router.post("/{group_id}/messages", status_code=201)
def post_message(group_id: UUID, data: MessageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, member = require_view(db, user, group_id)
    return chat.post_message(db, user, group, member, data.body)


@router.post("/{group_id}/read", status_code=204)
def mark_read(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _, member = require_view(db, user, group_id)
    chat.mark_read(db, member)


@router.patch("/{group_id}/messages/{message_id}")
def moderate(group_id: UUID, message_id: UUID, data: MessageModerate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return chat.moderate_message(db, user, group_id, message_id, _fields(data))


@router.put("/{group_id}/chat")
def chat_mode(group_id: UUID, data: ChatModeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return chat.set_chat_mode(db, user, group_id, data.chat_mode)


# announcements

@router.get("/{group_id}/announcements")
def announcements(group_id: UUID, include_archived: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, _ = require_view(db, user, group_id)
    return chat.list_announcements(db, user, group, include_archived)


@router.post("/{group_id}/announcements", status_code=201)
def create_announcement(group_id: UUID, data: AnnouncementIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return chat.save_announcement(db, user, group_id, data.model_dump())


@router.patch("/{group_id}/announcements/{announcement_id}")
def update_announcement(group_id: UUID, announcement_id: UUID, data: AnnouncementUpdate, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    return chat.save_announcement(db, user, group_id, _fields(data), announcement_id)


# lessons, tasks, monitoring

@router.get("/{group_id}/lessons")
def lessons(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, _ = require_view(db, user, group_id)
    return groups.lesson_list(db, user, group)


@router.put("/{group_id}/tasks")
def save_task(group_id: UUID, data: TaskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.save_task(db, user, group_id, data.model_dump())


@router.delete("/{group_id}/tasks/{task_id}", status_code=204)
def delete_task(group_id: UUID, task_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    groups.delete_task(db, user, group_id, task_id)


@router.get("/{group_id}/tasks")
def task_board(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return progress.task_board(db, require_manage(db, user, group_id, write=False))


@router.get("/{group_id}/dashboard")
def dashboard(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return progress.dashboard(db, require_manage(db, user, group_id, write=False))


@router.get("/{group_id}/students")
def students(group_id: UUID, filter: str = "all", sort: str = "name", search: str | None = Query(None, max_length=80),
             page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group = require_manage(db, user, group_id, write=False)
    return progress.students_table(db, group, filter, sort, search, page, page_size)


@router.get("/{group_id}/students/{student_id}")
def student(group_id: UUID, student_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group = require_manage(db, user, group_id, write=False)
    require_student_member(db, group, student_id)
    return progress.student_detail(db, group, student_id)


@router.get("/{group_id}/me")
def my_progress(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group, member = require_view(db, user, group_id)
    if member is None or member.role != "student":
        return None
    return progress.student_detail(db, group, user.id)


@router.get("/{group_id}/audit")
def audit_log(group_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
              db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return groups.audit_log(db, user, group_id, page, page_size)
