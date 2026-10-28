"""Who may see / manage a study group — every endpoint goes through here.

* manage: the group's teacher or a SUPER_ADMIN (a blocked group is read-only
  for its teacher; only a SUPER_ADMIN changes it).
* view:   managers + active members.
Anything else gets 404, never 403 — a guessed group id must not even
confirm that the group exists."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.study_group import (
    GROUP_BLOCKED,
    MEMBER_ACTIVE,
    MEMBER_STUDENT,
    StudyGroup,
    StudyGroupAuditLog,
    StudyGroupMember,
)
from app.models.user import User

TEACHER_ROLES = (UserRole.TEACHER, UserRole.SUPER_ADMIN)


def now() -> datetime:
    return datetime.now(timezone.utc)


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")


def is_super_admin(user: User) -> bool:
    return user.role == UserRole.SUPER_ADMIN


def is_manager(user: User, group: StudyGroup) -> bool:
    return is_super_admin(user) or (user.role == UserRole.TEACHER and group.teacher_id == user.id)


def membership(db: Session, group_id, user_id) -> StudyGroupMember | None:
    return db.scalar(select(StudyGroupMember).where(StudyGroupMember.group_id == group_id, StudyGroupMember.user_id == user_id))


def active_membership(db: Session, group_id, user_id) -> StudyGroupMember | None:
    m = membership(db, group_id, user_id)
    return m if m is not None and m.status == MEMBER_ACTIVE else None


def get_group(db: Session, group_id: UUID) -> StudyGroup:
    group = db.get(StudyGroup, group_id)
    if group is None:
        raise not_found()
    return group


def require_view(db: Session, user: User, group_id: UUID) -> tuple[StudyGroup, StudyGroupMember | None]:
    group = get_group(db, group_id)
    if is_manager(user, group):
        return group, active_membership(db, group.id, user.id)
    member = active_membership(db, group.id, user.id)
    if member is None or group.status == GROUP_BLOCKED:
        raise not_found()
    return group, member


def require_manage(db: Session, user: User, group_id: UUID, write: bool = True) -> StudyGroup:
    group = get_group(db, group_id)
    if not is_manager(user, group):
        raise not_found()
    if write and group.status == GROUP_BLOCKED and not is_super_admin(user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group is blocked by an administrator")
    return group


def require_teacher_role(user: User) -> None:
    if user.role not in TEACHER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")


def require_student_member(db: Session, group: StudyGroup, student_id: UUID) -> StudyGroupMember:
    """The student must be (or have been) a student member of this group."""
    m = membership(db, group.id, student_id)
    if m is None or m.role != MEMBER_STUDENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this group")
    return m


def audit(db: Session, group_id, actor_id, action: str, target_type: str | None = None, target_id=None, meta: dict | None = None) -> None:
    db.add(StudyGroupAuditLog(group_id=group_id, actor_id=actor_id, action=action, target_type=target_type,
                              target_id=str(target_id) if target_id is not None else None, meta=meta))


def display_name(user: User | None) -> str:
    if user is None:
        return "—"
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username
