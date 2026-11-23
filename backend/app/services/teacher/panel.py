"""Teacher Panel data beyond grading: dashboard, the students of the teacher's groups and courses (Schüler), one student's
learning profile, courses, video lessons (Unterricht), group tasks (Aufgaben), materials and group messages (Nachrichten).

Scope — the same rule everywhere; a student outside it is answered with 404, exactly like one that does not exist:
* groups = study_groups whose teacher_id is the teacher (archived groups are listed as such, never counted as "Meine Gruppen");
* students = active student members of those groups + active enrollments in the teacher's assigned courses
  (teacher_assignments — the rule GET /teacher/students always had);
* courses = the courses of those groups (study_group_courses) + the assigned courses.
A SUPER_ADMIN in the Teacher Panel is scoped the same way (their own groups and assignments).
The Schüler profile shows learning data only (groups, courses, lesson progress, homework, exams, learning activity); usage
time and media are the Kontroll area's (own permission, app.services.activity.stats).
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.homework import Homework
from app.models.homework_submission import STATUS_SUBMITTED, HomeworkSubmission
from app.models.lesson import Lesson
from app.models.model_test import ModelTest
from app.models.mock_test_attempt import MockTestAttempt
from app.models.module import Module
from app.models.student_activity import AREA_COURSE, AREA_EXAM, AREA_WORTSCHATZ, StudentActivityEvent, StudentSession
from app.models.student_progress import StudentProgress
from app.models.study_group import (GROUP_ACTIVE, GROUP_ARCHIVED, MEMBER_ACTIVE, MEMBER_STUDENT, MEMBER_TEACHER, StudyGroup,
                                    StudyGroupCourse, StudyGroupMember, StudyGroupMessage, StudyGroupTask)
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.models.video_room import ROOM_ENDED, ROOM_LIVE, ROOM_SCHEDULED, VideoRoom
from app.services.activity import stats
from app.services.activity.tracker import TZ

ACTIVITY_FILTERS = ("7d", "30d", "inactive", "never")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _like(q: str) -> str:
    return "%" + q.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


class Scope:
    """Everything the teacher may see, read once per request."""

    def __init__(self, db: Session, teacher: User):
        self.teacher = teacher
        self.groups = list(db.scalars(select(StudyGroup).where(StudyGroup.teacher_id == teacher.id).order_by(StudyGroup.name)))
        self.group_ids = [g.id for g in self.groups]
        self.live_group_ids = [g.id for g in self.groups if g.status != GROUP_ARCHIVED]
        self.members: dict = defaultdict(list)  # student id -> [group]
        if self.group_ids:
            by_id = {g.id: g for g in self.groups}
            for gid, uid, joined in db.execute(select(StudyGroupMember.group_id, StudyGroupMember.user_id, StudyGroupMember.joined_at).where(
                    StudyGroupMember.group_id.in_(self.group_ids), StudyGroupMember.role == MEMBER_STUDENT,
                    StudyGroupMember.status == MEMBER_ACTIVE)):
                self.members[uid].append({"id": gid, "name": by_id[gid].name, "level": by_id[gid].level, "status": by_id[gid].status,
                                          "joined_at": _aware(joined)})
        group_courses = set(db.scalars(select(StudyGroupCourse.course_id).where(StudyGroupCourse.group_id.in_(self.live_group_ids)))) \
            if self.live_group_ids else set()
        self.assigned_course_ids = set(db.scalars(select(TeacherAssignment.course_id).where(TeacherAssignment.teacher_id == teacher.id)))
        self.course_ids = group_courses | self.assigned_course_ids
        self.courses = {c.id: c for c in db.scalars(select(Course).where(Course.id.in_(self.course_ids)))} if self.course_ids else {}
        self.enrolled: dict = defaultdict(set)  # student id -> {course id} (assigned courses only)
        if self.assigned_course_ids:
            for uid, cid in db.execute(select(Enrollment.user_id, Enrollment.course_id).where(
                    Enrollment.course_id.in_(self.assigned_course_ids), Enrollment.is_active.is_(True))):
                self.enrolled[uid].add(cid)
        self.group_courses: dict = defaultdict(set)  # group id -> {course id}
        if self.live_group_ids:
            for gid, cid in db.execute(select(StudyGroupCourse.group_id, StudyGroupCourse.course_id).where(
                    StudyGroupCourse.group_id.in_(self.live_group_ids))):
                self.group_courses[gid].add(cid)
        self.student_ids = set(self.members) | set(self.enrolled)

    def courses_of(self, student_id) -> list[dict]:
        ids = set(self.enrolled.get(student_id, set()))
        for g in self.members.get(student_id, []):
            ids |= self.group_courses.get(g["id"], set())
        return [{"id": c.id, "title": c.title, "level": c.level} for c in sorted((self.courses[i] for i in ids if i in self.courses),
                                                                               key=lambda c: (c.level, c.title))]

    def require_student(self, student_id: UUID) -> None:
        if student_id not in self.student_ids:
            raise HTTPException(status_code=404, detail="STUDENT_NOT_FOUND")


def _last_activity(db: Session, ids: list) -> dict:
    if not ids:
        return {}
    sess = dict(db.execute(select(StudentSession.user_id, func.max(StudentSession.last_seen_at)).where(StudentSession.user_id.in_(ids))
                           .group_by(StudentSession.user_id)).all())
    prog = dict(db.execute(select(StudentProgress.user_id, func.max(StudentProgress.updated_at)).where(StudentProgress.user_id.in_(ids))
                           .group_by(StudentProgress.user_id)).all())
    users = dict(db.execute(select(User.id, User.last_login).where(User.id.in_(ids))).all())
    return {uid: stats._latest(sess.get(uid), prog.get(uid), users.get(uid)) for uid in ids}


def _status(user: User, now: datetime) -> str:
    if user.is_banned or (user.suspended_until and _aware(user.suspended_until) > now):
        return "blocked"
    return "active" if user.is_active else "inactive"


# ---------------- Schüler ----------------


def students(db: Session, teacher: User, *, search: str | None = None, group_id: UUID | None = None, course_id: UUID | None = None,
             level: str | None = None, status: str | None = None, activity: str | None = None, registered_from=None, registered_to=None,
             page: int = 1, page_size: int = 25) -> dict:
    scope = Scope(db, teacher)
    now = _now()
    page, page_size = max(1, page), max(1, min(page_size, 100))
    empty = {"items": [], "total": 0, "page": page, "page_size": page_size,
             "filters": {"groups": [{"id": g.id, "name": g.name, "level": g.level} for g in scope.groups],
                         "courses": [{"id": c.id, "title": c.title, "level": c.level} for c in scope.courses.values()]}}
    if not scope.student_ids:
        return empty
    users = list(db.scalars(select(User).where(User.id.in_(scope.student_ids))))
    last = _last_activity(db, [u.id for u in users])
    rows = []
    for u in users:
        groups = scope.members.get(u.id, [])
        courses = scope.courses_of(u.id)
        levels = sorted({g["level"] for g in groups} | {c["level"] for c in courses})
        row = {"id": u.id, "name": stats.display_name(u), "email": u.email, "groups": groups, "courses": courses, "levels": levels,
               "registered_at": _aware(u.created_at), "status": _status(u, now), "last_activity_at": last.get(u.id)}
        if search and search.strip():
            q = search.strip().lower()
            if q not in row["name"].lower() and q not in (u.email or "").lower() and q not in (u.username or "").lower() and q != str(u.id):
                continue
        if group_id and not any(g["id"] == group_id for g in groups):
            continue
        if course_id and not any(c["id"] == course_id for c in courses):
            continue
        if level and level not in levels:
            continue
        if status and row["status"] != status:
            continue
        if activity in ACTIVITY_FILTERS:
            seen = row["last_activity_at"]
            if activity == "never" and seen is not None:
                continue
            if activity in ("7d", "30d") and (seen is None or seen < now - timedelta(days=7 if activity == "7d" else 30)):
                continue
            if activity == "inactive" and seen is not None and seen >= now - timedelta(days=30):
                continue
        if registered_from and row["registered_at"].astimezone(TZ).date() < registered_from:
            continue
        if registered_to and row["registered_at"].astimezone(TZ).date() > registered_to:
            continue
        rows.append(row)
    rows.sort(key=lambda r: r["name"].lower())
    return {**empty, "items": rows[(page - 1) * page_size: page * page_size], "total": len(rows)}


def student_profile(db: Session, teacher: User, student_id: UUID) -> dict:
    scope = Scope(db, teacher)
    scope.require_student(student_id)
    user = db.get(User, student_id)
    now = _now()
    homework = []
    for sub, hw, lesson in db.execute(select(HomeworkSubmission, Homework, Lesson).join(Homework, Homework.id == HomeworkSubmission.homework_id)
                                      .join(Lesson, Lesson.id == Homework.lesson_id).where(HomeworkSubmission.student_id == user.id)
                                      .order_by(HomeworkSubmission.submitted_at.desc()).limit(20)):
        homework.append({"id": sub.id, "title": hw.title, "lesson": f"Lektion {lesson.number}: {lesson.title}", "status": sub.status,
                         "score": sub.score, "max_score": hw.max_score, "submitted_at": _aware(sub.submitted_at)})
    exams = []
    for att, test in db.execute(select(MockTestAttempt, ModelTest).join(ModelTest, ModelTest.id == MockTestAttempt.model_test_id)
                                .where(MockTestAttempt.user_id == user.id).order_by(MockTestAttempt.started_at.desc()).limit(10)):
        exams.append({"id": att.id, "title": test.title, "status": att.status, "total_score": att.total_score, "max_score": att.max_score,
                      "level": att.result_level, "started_at": _aware(att.started_at), "submitted_at": _aware(att.submitted_at)})
    scored = [h for h in homework if h["score"] is not None]
    events = list(db.scalars(select(StudentActivityEvent).where(StudentActivityEvent.user_id == user.id, StudentActivityEvent.seconds > 0,
                                                               StudentActivityEvent.area.in_((AREA_COURSE, AREA_WORTSCHATZ, AREA_EXAM)))
                             .order_by(StudentActivityEvent.last_seen_at.desc()).limit(10)))
    labels = stats._labels(db, events)
    recent = [{"area": e.area, "title": labels.get(e.ref_id, {}).get("title"), "at": _aware(e.started_at), "seconds": e.seconds} for e in events]
    return {
        "student": {"id": user.id, "name": stats.display_name(user), "email": user.email, "username": user.username,
                    "registered_at": _aware(user.created_at), "status": _status(user, now), "last_login_at": _aware(user.last_login),
                    "last_activity_at": _last_activity(db, [user.id]).get(user.id)},
        "groups": scope.members.get(user.id, []),
        "courses": scope.courses_of(user.id),
        "progress": stats.courses(db, user.id),
        "homework": homework,
        "exams": exams,
        "results": {"homework_graded": len(scored), "homework_average": round(sum(h["score"] for h in scored) / len(scored)) if scored else None,
                    "exams_finished": sum(1 for e in exams if e["submitted_at"]), "best_level": next((e["level"] for e in exams if e["level"]), None)},
        "recent_activity": recent,
    }


# ---------------- dashboard & sections ----------------


def _rooms(db: Session, scope: Scope, statuses, limit: int, newest_first: bool = False) -> list[dict]:
    if not scope.group_ids:
        return []
    names = {g.id: g.name for g in scope.groups}
    order = (VideoRoom.started_at.desc().nulls_last(), VideoRoom.created_at.desc()) if newest_first else \
        (VideoRoom.scheduled_at.asc().nulls_first(), VideoRoom.created_at.asc())
    rows = db.scalars(select(VideoRoom).where(VideoRoom.group_id.in_(scope.group_ids), VideoRoom.status.in_(statuses)).order_by(*order).limit(limit))
    return [{"id": r.id, "group_id": r.group_id, "group": names.get(r.group_id), "title": r.title, "status": r.status,
             "scheduled_at": _aware(r.scheduled_at), "started_at": _aware(r.started_at), "ended_at": _aware(r.ended_at)} for r in rows]


def _task_rows(db: Session, scope: Scope, limit: int | None = None) -> list[dict]:
    if not scope.live_group_ids:
        return []
    by_id = {g.id: g for g in scope.groups}
    stmt = select(StudyGroupTask, Lesson).join(Lesson, Lesson.id == StudyGroupTask.lesson_id).where(StudyGroupTask.group_id.in_(scope.live_group_ids)) \
        .order_by(StudyGroupTask.due_at.asc().nulls_last(), StudyGroupTask.assigned_at.desc())
    if limit:
        stmt = stmt.limit(limit)
    rows = db.execute(stmt).all()
    members = defaultdict(set)
    for uid, groups in scope.members.items():
        for g in groups:
            members[g["id"]].add(uid)
    lesson_ids = {lesson.id for _t, lesson in rows}
    done = defaultdict(set)
    if lesson_ids:
        for uid, lid in db.execute(select(StudentProgress.user_id, StudentProgress.lesson_id).where(
                StudentProgress.lesson_id.in_(lesson_ids), StudentProgress.lesson_completed.is_(True))):
            done[lid].add(uid)
    out = []
    for task, lesson in rows:
        group_members = members.get(task.group_id, set())
        out.append({"id": task.id, "group_id": task.group_id, "group": by_id[task.group_id].name, "lesson_id": lesson.id,
                    "title": task.title or f"Lektion {lesson.number}: {lesson.title}", "lesson": f"Lektion {lesson.number}: {lesson.title}",
                    "note": task.note, "assigned_at": _aware(task.assigned_at), "due_at": _aware(task.due_at),
                    "students": len(group_members), "completed": len(group_members & done.get(lesson.id, set()))})
    return out


def _new_homework(db: Session, scope: Scope) -> int:
    if not scope.assigned_course_ids:
        return 0
    return db.scalar(select(func.count()).select_from(HomeworkSubmission).join(Homework, Homework.id == HomeworkSubmission.homework_id)
                     .join(Lesson, Lesson.id == Homework.lesson_id).join(Module, Module.id == Lesson.module_id)
                     .where(Module.course_id.in_(scope.assigned_course_ids), HomeworkSubmission.status == STATUS_SUBMITTED,
                            HomeworkSubmission.reviewed_at.is_(None))) or 0


def dashboard(db: Session, teacher: User) -> dict:
    scope = Scope(db, teacher)
    now = _now()
    counts = dict(db.execute(select(StudyGroupMember.group_id, func.count()).where(
        StudyGroupMember.group_id.in_(scope.group_ids), StudyGroupMember.role == MEMBER_STUDENT, StudyGroupMember.status == MEMBER_ACTIVE)
        .group_by(StudyGroupMember.group_id)).all()) if scope.group_ids else {}
    lessons_held = db.scalar(select(func.count()).select_from(VideoRoom).where(VideoRoom.group_id.in_(scope.group_ids),
                                                                                VideoRoom.status.in_((ROOM_LIVE, ROOM_ENDED)))) \
        if scope.group_ids else 0
    tasks = _task_rows(db, scope)
    recent = []
    if scope.student_ids:
        names = {u.id: stats.display_name(u) for u in db.scalars(select(User).where(User.id.in_(scope.student_ids)))}
        for row, lesson in db.execute(select(StudentProgress, Lesson).join(Lesson, Lesson.id == StudentProgress.lesson_id)
                                      .where(StudentProgress.user_id.in_(scope.student_ids)).order_by(StudentProgress.updated_at.desc()).limit(8)):
            recent.append({"student_id": row.user_id, "student": names.get(row.user_id), "lesson": f"Lektion {lesson.number}: {lesson.title}",
                           "completed": bool(row.lesson_completed), "at": _aware(row.last_activity_at or row.updated_at)})
    last = _last_activity(db, list(scope.student_ids))
    active_week = sum(1 for v in last.values() if v is not None and v >= now - timedelta(days=7))
    return {
        "stats": {"students": len(scope.student_ids), "groups": len(scope.live_group_ids), "courses": len(scope.courses),
                  "lessons": lessons_held, "lessons_upcoming": len(_rooms(db, scope, (ROOM_SCHEDULED, ROOM_LIVE), 100)),
                  "homework": len(tasks), "new_submissions": _new_homework(db, scope)},
        "groups": [{"id": g.id, "name": g.name, "level": g.level, "status": g.status, "students": counts.get(g.id, 0),
                    "capacity": g.capacity, "last_activity_at": _aware(g.last_activity_at)} for g in scope.groups if g.status != GROUP_ARCHIVED],
        "upcoming_lessons": _rooms(db, scope, (ROOM_SCHEDULED, ROOM_LIVE), 6),
        "recent_activity": recent,
        "students_activity": {"active_7d": active_week, "inactive": len(scope.student_ids) - active_week},
        "tasks_due": [t for t in tasks if t["due_at"] and t["due_at"] >= now][:5],
        "has_groups": bool(scope.groups),
    }


def courses(db: Session, teacher: User) -> list[dict]:
    scope = Scope(db, teacher)
    out = []
    for course in sorted(scope.courses.values(), key=lambda c: (c.level, c.order_index)):
        modules = [m for (m,) in db.execute(select(Module.id).where(Module.course_id == course.id))]
        lessons = db.scalar(select(func.count()).select_from(Lesson).where(Lesson.module_id.in_(modules), Lesson.is_published.is_(True))) \
            if modules else 0
        students = {uid for uid in scope.student_ids if any(c["id"] == course.id for c in scope.courses_of(uid))}
        out.append({"id": course.id, "title": course.title, "level": course.level, "lessons": lessons or 0, "students": len(students),
                    "assigned": course.id in scope.assigned_course_ids,
                    "groups": [g.name for g in scope.groups if course.id in scope.group_courses.get(g.id, set())]})
    return out


def unterricht(db: Session, teacher: User) -> dict:
    scope = Scope(db, teacher)
    return {"live": _rooms(db, scope, (ROOM_LIVE,), 10), "upcoming": _rooms(db, scope, (ROOM_SCHEDULED,), 50),
            "past": _rooms(db, scope, (ROOM_ENDED,), 30, newest_first=True),
            "groups": [{"id": g.id, "name": g.name} for g in scope.groups if g.status == GROUP_ACTIVE]}


def tasks(db: Session, teacher: User) -> list[dict]:
    return _task_rows(db, Scope(db, teacher))


def materials(db: Session, teacher: User) -> list[dict]:
    scope = Scope(db, teacher)
    out = []
    for course in sorted(scope.courses.values(), key=lambda c: (c.level, c.order_index)):
        lessons = db.execute(select(Lesson.id, Lesson.number, Lesson.title).join(Module, Module.id == Lesson.module_id)
                             .where(Module.course_id == course.id, Lesson.is_published.is_(True)).order_by(Module.order_index, Lesson.number)).all()
        out.append({"course_id": course.id, "title": course.title, "level": course.level,
                    "lessons": [{"id": lid, "number": n, "title": t} for lid, n, t in lessons]})
    return out


def messages(db: Session, teacher: User) -> list[dict]:
    scope = Scope(db, teacher)
    out = []
    for g in scope.groups:
        if g.status == GROUP_ARCHIVED:
            continue
        read_at = db.scalar(select(StudyGroupMember.last_read_at).where(StudyGroupMember.group_id == g.id, StudyGroupMember.user_id == teacher.id,
                                                                       StudyGroupMember.role == MEMBER_TEACHER))
        visible = (StudyGroupMessage.group_id == g.id, StudyGroupMessage.deleted_at.is_(None))
        last = db.scalar(select(StudyGroupMessage).where(*visible).order_by(StudyGroupMessage.created_at.desc()).limit(1))
        unread_q = select(func.count()).select_from(StudyGroupMessage).where(
            *visible, or_(StudyGroupMessage.sender_id.is_(None), StudyGroupMessage.sender_id != teacher.id))
        if read_at is not None:
            unread_q = unread_q.where(StudyGroupMessage.created_at > read_at)
        sender = db.get(User, last.sender_id) if last is not None and last.sender_id else None
        out.append({"group_id": g.id, "group": g.name, "level": g.level, "unread": db.scalar(unread_q) or 0,
                    "last_message": {"body": last.body[:140], "at": _aware(last.created_at), "sender": stats.display_name(sender) if sender else None,
                                     "kind": last.kind} if last is not None else None})
    out.sort(key=lambda r: r["last_message"]["at"] if r["last_message"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return out
