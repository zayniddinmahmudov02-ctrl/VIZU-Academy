"""Groups: create / edit / list, join by code, members, lesson tasks."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.study_group import (
    CODE_ACTIVE,
    CODE_PAUSED,
    GROUP_ACTIVE,
    GROUP_ARCHIVED,
    GROUP_BLOCKED,
    GROUP_PAUSED,
    MEMBER_ACTIVE,
    MEMBER_LEFT,
    MEMBER_REMOVED,
    MEMBER_STUDENT,
    MEMBER_TEACHER,
    MESSAGE_SYSTEM,
    StudyGroup,
    StudyGroupCourse,
    StudyGroupJoinCode,
    StudyGroupMember,
    StudyGroupMessage,
    StudyGroupTask,
)
from app.models.user import User
from app.services.study_groups import codes, notify
from app.services.study_groups.access import (
    TEACHER_ROLES,
    audit,
    display_name,
    is_manager,
    is_super_admin,
    membership,
    now,
    require_manage,
    require_teacher_role,
)

LEVELS = ("A1", "A2", "B1", "B2", "C1")
TEACHER_SETTABLE = (GROUP_ACTIVE, GROUP_PAUSED, GROUP_ARCHIVED)
MAX_PAGE = 100


def _bad(detail: str, code: int = status.HTTP_422_UNPROCESSABLE_ENTITY) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


# ---------- serialization ----------

def _courses_by_group(db: Session, group_ids: list) -> dict:
    out = defaultdict(list)
    if group_ids:
        rows = db.execute(select(StudyGroupCourse.group_id, Course).join(Course, Course.id == StudyGroupCourse.course_id)
                          .where(StudyGroupCourse.group_id.in_(group_ids)).order_by(Course.order_index))
        for gid, course in rows:
            out[gid].append({"id": course.id, "title": course.title, "level": course.level})
    return out


def _student_counts(db: Session, group_ids: list) -> dict:
    if not group_ids:
        return {}
    return dict(db.execute(select(StudyGroupMember.group_id, func.count()).where(
        StudyGroupMember.group_id.in_(group_ids), StudyGroupMember.status == MEMBER_ACTIVE, StudyGroupMember.role == MEMBER_STUDENT)
        .group_by(StudyGroupMember.group_id)).all())


def summaries(db: Session, groups: list[StudyGroup]) -> list[dict]:
    ids = [g.id for g in groups]
    courses, counts = _courses_by_group(db, ids), _student_counts(db, ids)
    return [{
        "id": g.id, "name": g.name, "description": g.description, "level": g.level, "mode": g.mode, "status": g.status,
        "start_date": g.start_date, "end_date": g.end_date, "capacity": g.capacity, "chat_mode": g.chat_mode,
        "teacher": {"id": g.teacher_id, "name": display_name(g.teacher)},
        "courses": courses.get(g.id, []), "student_count": counts.get(g.id, 0),
        "last_activity_at": g.last_activity_at, "created_at": g.created_at,
    } for g in groups]


def summary(db: Session, group: StudyGroup) -> dict:
    return summaries(db, [group])[0]


# ---------- create / edit ----------

def _validate_courses(db: Session, course_ids: list[UUID], level: str) -> list[Course]:
    courses = list(db.scalars(select(Course).where(Course.id.in_(course_ids)))) if course_ids else []
    if len(courses) != len(set(course_ids)):
        raise _bad("unknown_course")
    if any((c.level or "").upper() != level for c in courses):
        raise _bad("course_level_mismatch")
    return courses


def _validate_fields(data: dict, current: StudyGroup | None = None) -> None:
    level = data.get("level", current.level if current else None)
    if level not in LEVELS:
        raise _bad("invalid_level")
    start = data.get("start_date", current.start_date if current else None)
    end = data.get("end_date", current.end_date if current else None)
    if start and end and end < start:
        raise _bad("end_before_start")


def _teacher_for(db: Session, actor: User, teacher_id: UUID | None) -> UUID:
    if teacher_id is None or teacher_id == actor.id:
        require_teacher_role(actor)
        return actor.id
    if not is_super_admin(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an administrator can assign another teacher")
    teacher = db.get(User, teacher_id)
    if teacher is None or teacher.role not in TEACHER_ROLES:
        raise _bad("not_a_teacher")
    return teacher.id


def _set_teacher_member(db: Session, group: StudyGroup) -> None:
    """The teacher has a member row (role teacher) for chat read state."""
    for m in db.scalars(select(StudyGroupMember).where(StudyGroupMember.group_id == group.id, StudyGroupMember.role == MEMBER_TEACHER)):
        if m.user_id != group.teacher_id:
            m.status, m.left_at = MEMBER_LEFT, now()
    m = membership(db, group.id, group.teacher_id)
    if m is None:
        db.add(StudyGroupMember(group_id=group.id, user_id=group.teacher_id, role=MEMBER_TEACHER, status=MEMBER_ACTIVE, joined_at=now()))
    else:
        m.role, m.status, m.left_at = MEMBER_TEACHER, MEMBER_ACTIVE, None


def create(db: Session, actor: User, data: dict) -> tuple[dict, str]:
    teacher_id = _teacher_for(db, actor, data.pop("teacher_id", None))
    course_ids = data.pop("course_ids", []) or []
    _validate_fields(data)
    _validate_courses(db, course_ids, data["level"])
    if data.get("status") not in (None, *TEACHER_SETTABLE):
        raise _bad("invalid_status")
    expires_at, max_uses = data.pop("code_expires_at", None), data.pop("code_max_uses", None)
    group = StudyGroup(**data, teacher_id=teacher_id, created_by=actor.id, last_activity_at=now())
    db.add(group)
    db.flush()
    for cid in course_ids:
        db.add(StudyGroupCourse(group_id=group.id, course_id=cid))
    _set_teacher_member(db, group)
    plain = codes.create(db, group, actor.id, expires_at=expires_at, max_uses=max_uses)
    audit(db, group.id, actor.id, "group.create", "group", group.id, {"name": group.name, "teacher_id": str(teacher_id)})
    db.commit()
    db.refresh(group)
    return summary(db, group), plain


def update(db: Session, actor: User, group_id: UUID, data: dict) -> dict:
    group = require_manage(db, actor, group_id)
    new_status = data.get("status")
    if new_status is not None:
        if new_status == GROUP_BLOCKED or group.status == GROUP_BLOCKED:
            if not is_super_admin(actor):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an administrator can block or unblock")
        elif new_status not in TEACHER_SETTABLE:
            raise _bad("invalid_status")
    if "teacher_id" in data:
        teacher_id = data.pop("teacher_id")
        if teacher_id is not None and teacher_id != group.teacher_id:
            group.teacher_id = _teacher_for(db, actor, teacher_id)
            _set_teacher_member(db, group)
    course_ids = data.pop("course_ids", None)
    _validate_fields(data, group)
    level = data.get("level", group.level)
    if course_ids is not None:
        _validate_courses(db, course_ids, level)
        db.execute(StudyGroupCourse.__table__.delete().where(StudyGroupCourse.group_id == group.id,
                                                              StudyGroupCourse.course_id.notin_(course_ids or [None])))
        have = set(db.scalars(select(StudyGroupCourse.course_id).where(StudyGroupCourse.group_id == group.id)))
        for cid in course_ids:
            if cid not in have:
                db.add(StudyGroupCourse(group_id=group.id, course_id=cid))
    elif "level" in data:
        current = list(db.scalars(select(StudyGroupCourse.course_id).where(StudyGroupCourse.group_id == group.id)))
        _validate_courses(db, current, level)
    if data.get("capacity") is not None and data["capacity"] < _student_counts(db, [group.id]).get(group.id, 0):
        raise _bad("capacity_below_members")
    changed = {}
    for key, value in data.items():
        if getattr(group, key) != value:
            changed[key] = str(value)
            setattr(group, key, value)
    audit(db, group.id, actor.id, "group.update", "group", group.id, {"changed": sorted(changed), **({"status": changed["status"]} if "status" in changed else {})})
    db.commit()
    db.refresh(group)
    return summary(db, group)


# ---------- lists ----------

def _page(page: int, size: int) -> tuple[int, int]:
    return max(page, 1), min(max(size, 1), MAX_PAGE)


def list_groups(db: Session, actor: User, scope: str, *, search: str | None = None, level: str | None = None, status_: str | None = None,
                teacher_id: UUID | None = None, course_id: UUID | None = None, created_from: date | None = None,
                created_to: date | None = None, page: int = 1, page_size: int = 20) -> dict:
    """scope "teaching": the actor's own groups; "all": every group (SUPER_ADMIN only)."""
    page, page_size = _page(page, page_size)
    stmt = select(StudyGroup)
    if scope == "all":
        if not is_super_admin(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
        if teacher_id:
            stmt = stmt.where(StudyGroup.teacher_id == teacher_id)
    else:
        require_teacher_role(actor)
        stmt = stmt.where(StudyGroup.teacher_id == actor.id)
    if search:
        stmt = stmt.where(StudyGroup.name.ilike(f"%{search.strip()[:80].replace('%', '').replace('_', '')}%"))
    if level:
        stmt = stmt.where(StudyGroup.level == level)
    if status_:
        stmt = stmt.where(StudyGroup.status == status_)
    if course_id:
        stmt = stmt.where(StudyGroup.id.in_(select(StudyGroupCourse.group_id).where(StudyGroupCourse.course_id == course_id)))
    if created_from:
        stmt = stmt.where(StudyGroup.created_at >= datetime.combine(created_from, datetime.min.time()))
    if created_to:
        stmt = stmt.where(StudyGroup.created_at < datetime.combine(created_to + timedelta(days=1), datetime.min.time()))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    groups = list(db.scalars(stmt.order_by(StudyGroup.status != GROUP_ACTIVE, StudyGroup.last_activity_at.desc().nulls_last())
                             .offset((page - 1) * page_size).limit(page_size)).unique())
    items = summaries(db, groups)
    if is_super_admin(actor) or scope == "teaching":
        current = {c.group_id: c for c in db.scalars(select(StudyGroupJoinCode).where(
            StudyGroupJoinCode.group_id.in_([g.id for g in groups] or [None]), StudyGroupJoinCode.status.in_((CODE_ACTIVE, CODE_PAUSED))))}
        for item in items:
            item["code"] = codes.describe(current.get(item["id"]))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def admin_stats(db: Session, actor: User) -> dict:
    if not is_super_admin(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    by_status = dict(db.execute(select(StudyGroup.status, func.count()).group_by(StudyGroup.status)).all())
    students = db.scalar(select(func.count(func.distinct(StudyGroupMember.user_id))).where(
        StudyGroupMember.status == MEMBER_ACTIVE, StudyGroupMember.role == MEMBER_STUDENT))
    teachers = db.scalar(select(func.count(func.distinct(StudyGroup.teacher_id))).where(StudyGroup.status != GROUP_ARCHIVED))
    messages = db.scalar(select(func.count()).select_from(StudyGroupMessage).where(StudyGroupMessage.created_at > now() - timedelta(days=7)))
    return {"groups": sum(by_status.values()), "by_status": by_status, "students": students or 0, "teachers": teachers or 0,
            "messages_7d": messages or 0}


def my_groups(db: Session, user: User) -> list[dict]:
    """Groups the user belongs to as a student, with unread chat counts and the last message."""
    rows = list(db.execute(select(StudyGroup, StudyGroupMember).join(StudyGroupMember, StudyGroupMember.group_id == StudyGroup.id)
                           .where(StudyGroupMember.user_id == user.id, StudyGroupMember.status == MEMBER_ACTIVE,
                                  StudyGroupMember.role == MEMBER_STUDENT, StudyGroup.status != GROUP_BLOCKED)
                           .order_by(StudyGroup.last_activity_at.desc().nulls_last())).unique())
    from app.services.study_groups import chat, progress

    items = summaries(db, [g for g, _ in rows])
    for item, (group, member) in zip(items, rows):
        item["unread"] = chat.unread_count(db, group.id, user.id, member.last_read_at)
        item["last_message"] = chat.last_message(db, group.id)
        item["tasks"] = progress.task_summary_for_student(db, group, user.id)
    return items


def options(db: Session, actor: User) -> dict:
    require_teacher_role(actor)
    courses = [{"id": c.id, "title": c.title, "level": c.level} for c in db.scalars(select(Course).where(Course.is_active.is_(True))
                                                                                     .order_by(Course.order_index))]
    teachers = []
    if is_super_admin(actor):
        teachers = [{"id": u.id, "name": display_name(u), "email": u.email}
                    for u in db.scalars(select(User).where(User.role.in_(TEACHER_ROLES)).order_by(User.email))]
    return {"levels": list(LEVELS), "courses": courses, "teachers": teachers}


# ---------- join codes ----------

def code_info(db: Session, actor: User, group_id: UUID) -> dict | None:
    group = require_manage(db, actor, group_id, write=False)
    return codes.describe(codes.current(db, group.id))


def regenerate_code(db: Session, actor: User, group_id: UUID, expires_at=None, max_uses: int | None = None) -> dict:
    group = require_manage(db, actor, group_id)
    plain = codes.create(db, group, actor.id, expires_at=expires_at, max_uses=max_uses)
    audit(db, group.id, actor.id, "code.regenerate", "group", group.id, {"expires_at": str(expires_at) if expires_at else None, "max_uses": max_uses})
    db.commit()
    return {"code": plain, **(codes.describe(codes.current(db, group.id)) or {})}


def change_code(db: Session, actor: User, group_id: UUID, data: dict) -> dict | None:
    group = require_manage(db, actor, group_id)
    code = codes.current(db, group.id)
    if code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active code")
    if data.get("revoke"):
        codes.revoke_all(db, group.id)
        audit(db, group.id, actor.id, "code.revoke", "group", group.id)
    else:
        kwargs = {k: data[k] for k in ("expires_at", "max_uses") if k in data}
        codes.set_state(code, paused=data.get("paused"), **kwargs)
        audit(db, group.id, actor.id, "code.update", "group", group.id, {"paused": data.get("paused"), **{k: str(v) for k, v in kwargs.items()}})
    db.commit()
    return codes.describe(codes.current(db, group.id))


def _resolve_code(db: Session, user: User, code: str, ip: str | None, lock: bool = False) -> tuple[StudyGroup, StudyGroupJoinCode]:
    codes.check_rate(db, user.id, ip)
    jc = codes.lookup(db, code)
    if jc is None or jc.status == "revoked":
        codes.record_failure(db, user.id, ip)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid_code")
    # the row lock serialises joins of one group (capacity, code use count)
    group = (db.scalar(select(StudyGroup).where(StudyGroup.id == jc.group_id).with_for_update(of=StudyGroup)) if lock
             else db.get(StudyGroup, jc.group_id))
    if lock:
        db.refresh(jc, with_for_update=True)
    if jc.status == CODE_PAUSED:
        raise _bad("code_paused", status.HTTP_409_CONFLICT)
    if jc.expires_at is not None and jc.expires_at <= now():
        raise _bad("code_expired", status.HTTP_410_GONE)
    if jc.max_uses is not None and jc.use_count >= jc.max_uses:
        raise _bad("code_used_up", status.HTTP_409_CONFLICT)
    if group.status != GROUP_ACTIVE:
        raise _bad("group_closed", status.HTTP_409_CONFLICT)
    return group, jc


def preview(db: Session, user: User, code: str, ip: str | None) -> dict:
    group, _ = _resolve_code(db, user, code, ip)
    item = summary(db, group)
    m = membership(db, group.id, user.id)
    return {"id": group.id, "name": group.name, "level": group.level, "teacher": item["teacher"], "courses": item["courses"],
            "student_count": item["student_count"], "capacity": group.capacity,
            "already_member": m is not None and m.status == MEMBER_ACTIVE and m.role == MEMBER_STUDENT}


def join(db: Session, user: User, code: str, ip: str | None) -> dict:
    group, jc = _resolve_code(db, user, code, ip, lock=True)
    if group.teacher_id == user.id:
        raise _bad("own_group", status.HTTP_409_CONFLICT)
    m = membership(db, group.id, user.id)
    if m is not None and m.status == MEMBER_ACTIVE:
        db.rollback()
        return {"group": summary(db, group), "already_member": True}
    if m is not None and m.status == MEMBER_REMOVED:
        raise _bad("removed_by_teacher", status.HTTP_403_FORBIDDEN)
    if group.capacity is not None and _student_counts(db, [group.id]).get(group.id, 0) >= group.capacity:
        raise _bad("group_full", status.HTTP_409_CONFLICT)
    if m is None:
        db.add(StudyGroupMember(group_id=group.id, user_id=user.id, role=MEMBER_STUDENT, status=MEMBER_ACTIVE, joined_at=now(), last_read_at=now()))
    else:
        m.status, m.left_at, m.joined_at, m.role = MEMBER_ACTIVE, None, now(), MEMBER_STUDENT
    jc.use_count += 1
    group.last_activity_at = now()
    db.add(StudyGroupMessage(group_id=group.id, sender_id=None, kind=MESSAGE_SYSTEM, body=f"{display_name(user)} guruhga qo‘shildi."))
    audit(db, group.id, user.id, "member.join", "user", user.id)
    notify.to_teacher(db, group, f"{group.name}: yangi a’zo / neues Mitglied", f"{display_name(user)} guruhga qo‘shildi.", "students")
    db.commit()
    return {"group": summary(db, group), "already_member": False}


# ---------- members ----------

def members(db: Session, viewer: User, group: StudyGroup) -> list[dict]:
    manager = is_manager(viewer, group)
    stmt = select(StudyGroupMember).where(StudyGroupMember.group_id == group.id)
    if not manager:
        stmt = stmt.where(StudyGroupMember.status == MEMBER_ACTIVE)
    rows = db.scalars(stmt.order_by(StudyGroupMember.role.desc(), StudyGroupMember.joined_at)).unique()
    out = []
    for m in rows:
        item = {"user_id": m.user_id, "name": display_name(m.user), "role": m.role, "joined_at": m.joined_at}
        if manager:
            item.update(email=m.user.email, status=m.status, can_post=m.can_post, left_at=m.left_at)
        out.append(item)
    return out


def update_member(db: Session, actor: User, group_id: UUID, user_id: UUID, data: dict) -> dict:
    group = require_manage(db, actor, group_id)
    m = membership(db, group.id, user_id)
    if m is None or m.role != MEMBER_STUDENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if data.get("remove"):
        if m.status == MEMBER_ACTIVE:
            m.status, m.left_at = MEMBER_REMOVED, now()
            audit(db, group.id, actor.id, "member.remove", "user", user_id)
    elif data.get("restore"):
        if m.status != MEMBER_ACTIVE:
            if group.capacity is not None and _student_counts(db, [group.id]).get(group.id, 0) >= group.capacity:
                raise _bad("group_full", status.HTTP_409_CONFLICT)
            m.status, m.left_at = MEMBER_ACTIVE, None
            audit(db, group.id, actor.id, "member.restore", "user", user_id)
    if "can_post" in data and data["can_post"] is not None:
        m.can_post = bool(data["can_post"])
        audit(db, group.id, actor.id, "member.can_post", "user", user_id, {"can_post": m.can_post})
    db.commit()
    return {"user_id": m.user_id, "status": m.status, "can_post": m.can_post}


def leave(db: Session, user: User, group_id: UUID) -> None:
    m = membership(db, group_id, user.id)
    if m is None or m.status != MEMBER_ACTIVE or m.role != MEMBER_STUDENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    m.status, m.left_at = MEMBER_LEFT, now()
    audit(db, group_id, user.id, "member.leave", "user", user.id)
    db.commit()


# ---------- lessons and tasks ----------

def group_course_ids(db: Session, group_id) -> list:
    return list(db.scalars(select(StudyGroupCourse.course_id).where(StudyGroupCourse.group_id == group_id)))


def lessons(db: Session, group: StudyGroup) -> list[tuple[Lesson, Module, Course]]:
    """Published lessons of the group's courses, in course order."""
    course_ids = [str(c) for c in group_course_ids(db, group.id)]
    if not course_ids:
        return []
    return list(db.execute(
        select(Lesson, Module, Course).join(Module, Module.id == Lesson.module_id).join(Course, Course.id == Module.course_id)
        .where(Module.course_id.in_(course_ids), Lesson.is_published.is_(True))
        .order_by(Course.order_index, Module.order_index, Module.number, Lesson.number)).all())


def lesson_list(db: Session, viewer: User, group: StudyGroup) -> list[dict]:
    tasks = {t.lesson_id: t for t in db.scalars(select(StudyGroupTask).where(StudyGroupTask.group_id == group.id))}
    return [{"id": lesson.id, "number": lesson.number, "title": lesson.title, "module": module.title, "course_id": course.id,
             "course_title": course.title, "level": course.level,
             "task": ({"id": tasks[lesson.id].id, "due_at": tasks[lesson.id].due_at} if lesson.id in tasks else None)}
            for lesson, module, course in lessons(db, group)]


def save_task(db: Session, actor: User, group_id: UUID, data: dict) -> dict:
    group = require_manage(db, actor, group_id)
    lesson_id = data["lesson_id"]
    if lesson_id not in {lesson.id for lesson, _, _ in lessons(db, group)}:
        raise _bad("lesson_not_in_group_courses")
    task = db.scalar(select(StudyGroupTask).where(StudyGroupTask.group_id == group.id, StudyGroupTask.lesson_id == lesson_id))
    created = task is None
    if created:
        task = StudyGroupTask(group_id=group.id, lesson_id=lesson_id, assigned_at=now(), created_by=actor.id)
        db.add(task)
    due_changed = created or task.due_at != data.get("due_at")
    task.title, task.note, task.due_at = data.get("title"), data.get("note"), data.get("due_at")
    db.flush()
    audit(db, group.id, actor.id, "task.create" if created else "task.update", "task", task.id, {"lesson_id": str(lesson_id), "due_at": str(task.due_at) if task.due_at else None})
    if due_changed:
        lesson = db.get(Lesson, lesson_id)
        due = f" — muddat: {task.due_at:%d.%m.%Y %H:%M}" if task.due_at else ""
        notify.to_students(db, group, f"{group.name}: {'yangi vazifa' if created else 'vazifa muddati'} / Aufgabe",
                           f"{task.title or lesson.title}{due}", "tasks")
    group.last_activity_at = now()
    db.commit()
    return {"id": task.id, "lesson_id": task.lesson_id, "title": task.title, "note": task.note, "due_at": task.due_at, "assigned_at": task.assigned_at}


def delete_task(db: Session, actor: User, group_id: UUID, task_id: UUID) -> None:
    group = require_manage(db, actor, group_id)
    task = db.scalar(select(StudyGroupTask).where(StudyGroupTask.id == task_id, StudyGroupTask.group_id == group.id))
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    audit(db, group.id, actor.id, "task.delete", "task", task.id, {"lesson_id": str(task.lesson_id)})
    db.delete(task)
    db.commit()


def audit_log(db: Session, actor: User, group_id: UUID, page: int = 1, page_size: int = 50) -> dict:
    from app.models.study_group import StudyGroupAuditLog

    group = require_manage(db, actor, group_id, write=False)
    page, page_size = _page(page, page_size)
    stmt = select(StudyGroupAuditLog).where(StudyGroupAuditLog.group_id == group.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = list(db.scalars(stmt.order_by(StudyGroupAuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))
    actors = {u.id: display_name(u) for u in db.scalars(select(User).where(User.id.in_({r.actor_id for r in rows if r.actor_id} or {None})))}
    return {"items": [{"id": r.id, "action": r.action, "actor": actors.get(r.actor_id), "target_type": r.target_type, "target_id": r.target_id,
                       "meta": r.meta, "created_at": r.created_at} for r in rows], "total": total, "page": page, "page_size": page_size}
