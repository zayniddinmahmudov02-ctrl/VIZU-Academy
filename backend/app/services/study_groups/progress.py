"""Group monitoring, read from the LMS — nothing here is stored separately.

Sources:
  lessons                  lessons of the group's courses (study_group_courses)
  lesson progress          student_progress (lesson_completed, completed_at,
                           last_activity_at, total_score 0–100, competencies_*)
  skills                   student_competency_progress (+ lesson_competencies)
  submissions              student_writings, student_speakings, homework_submissions
  deadlines                study_group_tasks.due_at (group task), writings.closes_at

Every figure is computed from rows that exist. Where there is no data the
value is None — never an invented percentage or score. All data for a group
is loaded with a fixed number of queries (no per-student queries)."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission
from app.models.lesson import Lesson
from app.models.lms import PROGRESS_COMPLETED, LessonCompetency, StudentCompetencyProgress
from app.models.module import Module
from app.models.speaking import Speaking
from app.models.student_progress import StudentProgress
from app.models.student_speaking import StudentSpeaking
from app.models.student_writing import StudentWriting
from app.models.study_group import MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupMember, StudyGroupMessage, StudyGroupTask
from app.models.user import User
from app.models.writing import Writing
from app.services.study_groups.access import display_name, now
from app.services.study_groups.groups import lessons as group_lessons

ACTIVE_DAYS = 7
SKILLS = ("LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN", "GRAMMATIK", "WORTSCHATZ")

# submission status in the LMS -> monitoring status
SUBMISSION_STATUS = {
    "DRAFT": "in_progress",
    "SUBMITTED": "under_review",
    "EVALUATING": "under_review",
    "EVALUATION_FAILED": "under_review",
    "NEEDS_REVISION": "needs_revision",
    "GRADED": "accepted",
}
# task status buckets
DONE = ("completed", "completed_late")
SUBMITTED = ("under_review", "needs_revision", *DONE)
MISSING = ("not_started", "in_progress", "overdue")


@dataclass
class Data:
    group: StudyGroup
    lessons: list  # [(Lesson, Module, Course)]
    tasks: list  # [StudyGroupTask]
    students: list  # [(StudyGroupMember, User)]
    progress: dict = field(default_factory=dict)  # (user, lesson) -> StudentProgress
    submissions: dict = field(default_factory=lambda: defaultdict(list))  # user -> [dict]
    skills: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(list)))  # user -> skill -> [row]
    skill_totals: dict = field(default_factory=dict)  # skill -> lessons that teach it

    @property
    def lesson_ids(self) -> list:
        return [lesson.id for lesson, _, _ in self.lessons]

    def lesson_info(self) -> dict:
        return {str(lesson.id): (lesson, module, course) for lesson, module, course in self.lessons}


def _students(db: Session, group: StudyGroup, user_ids: list | None = None) -> list:
    stmt = (select(StudyGroupMember, User).join(User, User.id == StudyGroupMember.user_id)
            .where(StudyGroupMember.group_id == group.id, StudyGroupMember.role == MEMBER_STUDENT))
    if user_ids is not None:
        stmt = stmt.where(StudyGroupMember.user_id.in_(user_ids))
    else:
        stmt = stmt.where(StudyGroupMember.status == MEMBER_ACTIVE)
    return list(db.execute(stmt.order_by(User.first_name, User.username)).unique().all())


def load(db: Session, group: StudyGroup, user_ids: list | None = None, with_text: bool = False) -> Data:
    data = Data(group=group, lessons=group_lessons(db, group),
                tasks=list(db.scalars(select(StudyGroupTask).where(StudyGroupTask.group_id == group.id).order_by(StudyGroupTask.assigned_at))),
                students=_students(db, group, user_ids))
    uids = [u.id for _, u in data.students]
    lids = data.lesson_ids
    if not uids or not lids:
        return data
    s_uids, s_lids = [str(u) for u in uids], [str(lid) for lid in lids]

    for p in db.scalars(select(StudentProgress).where(StudentProgress.user_id.in_(s_uids), StudentProgress.lesson_id.in_(s_lids))):
        data.progress[(str(p.user_id), str(p.lesson_id))] = p

    def add(kind, sub, task, lesson_id, user_id, deadline=None, text=None):
        data.submissions[str(user_id)].append({
            "kind": kind, "id": sub.id, "lesson_id": str(lesson_id), "title": task.title, "raw_status": sub.status,
            "status": SUBMISSION_STATUS.get(sub.status, "under_review"), "submitted_at": sub.submitted_at, "score": sub.score,
            "feedback": sub.feedback, "reviewed_at": sub.reviewed_at, "deadline": deadline,
            **({"answer_text": text} if with_text else {}),
        })

    for sub, w in db.execute(select(StudentWriting, Writing).join(Writing, Writing.id == StudentWriting.writing_id)
                             .where(StudentWriting.user_id.in_(s_uids), Writing.lesson_id.in_(s_lids))):
        add("writing", sub, w, w.lesson_id, sub.user_id, w.closes_at, sub.answer_text)
    for sub, sp in db.execute(select(StudentSpeaking, Speaking).join(Speaking, Speaking.id == StudentSpeaking.speaking_id)
                              .where(StudentSpeaking.user_id.in_(uids), Speaking.lesson_id.in_(s_lids))):
        add("speaking", sub, sp, sp.lesson_id, sub.user_id)
    for sub, hw in db.execute(select(HomeworkSubmission, Homework).join(Homework, Homework.id == HomeworkSubmission.homework_id)
                              .where(HomeworkSubmission.student_id.in_(uids), Homework.lesson_id.in_(s_lids))):
        add("homework", sub, hw, hw.lesson_id, sub.student_id, None, sub.text_content)

    for row in db.scalars(select(StudentCompetencyProgress).where(StudentCompetencyProgress.user_id.in_(uids),
                                                                  StudentCompetencyProgress.lesson_id.in_(lids),
                                                                  StudentCompetencyProgress.competency.in_(SKILLS))):
        data.skills[str(row.user_id)][row.competency].append(row)
    data.skill_totals = dict(db.execute(select(LessonCompetency.kind, func.count()).where(
        LessonCompetency.lesson_id.in_(lids), LessonCompetency.is_published.is_(True), LessonCompetency.kind.in_(SKILLS))
        .group_by(LessonCompetency.kind)).all())
    return data


# ---------- per student ----------

def _lesson_status(p: StudentProgress | None) -> str:
    if p is None:
        return "not_started"
    return "completed" if p.lesson_completed else "in_progress"


def _last(*values):
    values = [v for v in values if v is not None]
    return max(values) if values else None


def task_status(task: StudyGroupTask, p: StudentProgress | None, subs: list, at: datetime) -> str:
    states = {s["status"] for s in subs}
    if "needs_revision" in states:
        return "needs_revision"
    if "under_review" in states:
        return "under_review"
    if p is not None and p.lesson_completed:
        late = task.due_at is not None and p.completed_at is not None and p.completed_at > task.due_at
        return "completed_late" if late else "completed"
    if task.due_at is not None and at > task.due_at:
        return "overdue"
    if p is not None or states:
        return "in_progress"
    return "not_started"


def _student_row(data: Data, member: StudyGroupMember, user: User, at: datetime) -> dict:
    uid = str(user.id)
    rows = [data.progress.get((uid, str(lid))) for lid in data.lesson_ids]
    done = [p for p in rows if p is not None and p.lesson_completed]
    subs = data.submissions.get(uid, [])
    by_lesson = defaultdict(list)
    for s in subs:
        by_lesson[s["lesson_id"]].append(s)
    statuses = [task_status(t, data.progress.get((uid, str(t.lesson_id))), by_lesson.get(str(t.lesson_id), []), at) for t in data.tasks]
    scores = [p.total_score for p in done if p.total_score is not None]
    graded = [s["score"] for s in subs if s["status"] == "accepted" and s["score"] is not None]
    last_activity = _last(*(p.last_activity_at or p.updated_at for p in rows if p is not None), *(s["submitted_at"] for s in subs))
    total = len(data.lesson_ids)
    return {
        "user_id": user.id, "name": display_name(user), "email": user.email, "joined_at": member.joined_at,
        "member_status": member.status, "last_activity_at": last_activity,
        "active": last_activity is not None and last_activity > at - timedelta(days=ACTIVE_DAYS),
        "lessons_completed": len(done), "lessons_total": total,
        "progress": round(len(done) / total * 100) if total else None,
        "tasks_total": len(data.tasks),
        "tasks_submitted": sum(s in SUBMITTED for s in statuses),
        "tasks_missing": sum(s in MISSING for s in statuses),
        "tasks_overdue": sum(s == "overdue" for s in statuses),
        "tasks_under_review": sum(s == "under_review" for s in statuses),
        "awaiting_review": sum(s["status"] == "under_review" for s in subs),
        "needs_revision": sum(s["status"] == "needs_revision" for s in subs),
        "average_lesson_score": round(mean(scores)) if scores else None,
        "average_grade": round(mean(graded)) if graded else None,
        "graded_count": len(graded),
    }


def student_rows(db: Session, group: StudyGroup) -> tuple[Data, list[dict]]:
    data = load(db, group)
    at = now()
    return data, [_student_row(data, m, u, at) for m, u in data.students]


FILTERS = {
    "all": lambda r: True,
    "active": lambda r: r["active"],
    "inactive": lambda r: not r["active"],
    "missing": lambda r: r["tasks_missing"] > 0,
    "overdue": lambda r: r["tasks_overdue"] > 0,
    "awaiting_review": lambda r: r["awaiting_review"] > 0,
}
SORTS = {
    "name": (lambda r: r["name"].lower(), False),
    "progress": (lambda r: (r["progress"] is None, -(r["progress"] or 0)), False),
    "progress_asc": (lambda r: (r["progress"] is None, r["progress"] or 0), False),
    "last_activity": (lambda r: (r["last_activity_at"] is None, -(r["last_activity_at"].timestamp() if r["last_activity_at"] else 0)), False),
}


def students_table(db: Session, group: StudyGroup, filter_: str = "all", sort: str = "name", search: str | None = None,
                   page: int = 1, page_size: int = 25) -> dict:
    if filter_ not in FILTERS or sort not in SORTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_filter_or_sort")
    data, rows = student_rows(db, group)
    rows = [r for r in rows if FILTERS[filter_](r)]
    if search:
        q = search.strip().lower()
        rows = [r for r in rows if q in r["name"].lower() or q in (r["email"] or "").lower()]
    rows.sort(key=SORTS[sort][0])
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    courses = sorted({(c.id, c.title, c.level) for _, _, c in data.lessons}, key=lambda c: c[2])
    return {"items": rows[(page - 1) * page_size: page * page_size], "total": len(rows), "page": page, "page_size": page_size,
            "courses": [{"id": c[0], "title": c[1], "level": c[2]} for c in courses]}


def dashboard(db: Session, group: StudyGroup) -> dict:
    data, rows = student_rows(db, group)
    n = len(rows)
    lesson_scores = [r["average_lesson_score"] for r in rows if r["average_lesson_score"] is not None]
    grades = [r["average_grade"] for r in rows if r["average_grade"] is not None]
    total_lessons = len(data.lesson_ids)
    done_all = sum(1 for r in rows if total_lessons and r["lessons_completed"] == total_lessons)
    task_lesson_ids = {str(t.lesson_id) for t in data.tasks}
    done_tasks = sum(1 for r in rows if data.tasks and r["tasks_submitted"] == len(data.tasks))
    return {
        "students": n,
        "active_students": sum(r["active"] for r in rows),
        "lessons_total": total_lessons,
        "students_completed_all_lessons": done_all if total_lessons else None,
        "students_submitted_all_tasks": done_tasks if data.tasks else None,
        "tasks": len(data.tasks),
        "tasks_submitted": sum(r["tasks_submitted"] for r in rows),
        "tasks_missing": sum(r["tasks_missing"] for r in rows),
        "tasks_overdue": sum(r["tasks_overdue"] for r in rows),
        "tasks_under_review": sum(r["tasks_under_review"] for r in rows),
        "awaiting_teacher_review": sum(r["awaiting_review"] for r in rows),
        "average_lesson_score": round(mean(lesson_scores)) if lesson_scores else None,
        "average_grade": round(mean(grades)) if grades else None,
        "overall_progress": (round(sum(r["lessons_completed"] for r in rows) / (n * total_lessons) * 100) if n and total_lessons else None),
        "last_activity_at": _last(group.last_activity_at, *(r["last_activity_at"] for r in rows)),
        "task_lessons": len(task_lesson_ids),
    }


def student_detail(db: Session, group: StudyGroup, student_id: UUID, include_text: bool = True) -> dict:
    data = load(db, group, user_ids=[student_id], with_text=include_text)
    if not data.students:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this group")
    member, user = data.students[0]
    at, uid = now(), str(user.id)
    info = data.lesson_info()
    subs = data.submissions.get(uid, [])
    by_lesson = defaultdict(list)
    for s in subs:
        lesson, _, course = info[s["lesson_id"]]
        s.update(lesson_title=lesson.title, lesson_number=lesson.number, course_level=course.level)
        by_lesson[s["lesson_id"]].append(s)

    lessons = []
    for lesson, module, course in data.lessons:
        p = data.progress.get((uid, str(lesson.id)))
        lessons.append({"id": lesson.id, "number": lesson.number, "title": lesson.title, "module": module.title, "level": course.level,
                        "course_title": course.title, "status": _lesson_status(p), "started_at": p.created_at if p else None,
                        "completed_at": p.completed_at if p else None,
                        "progress": (round(p.competencies_completed / p.competencies_total * 100)
                                     if p and p.competencies_total and p.competencies_completed is not None else (100 if p and p.lesson_completed else None)),
                        "score": p.total_score if p and p.lesson_completed else None,
                        "last_activity_at": (p.last_activity_at or p.updated_at) if p else None})

    tasks = []
    for t in data.tasks:
        lesson, module, course = info.get(str(t.lesson_id), (None, None, None))
        tasks.append({"id": t.id, "lesson_id": t.lesson_id, "title": t.title or (lesson.title if lesson else "—"),
                      "lesson_title": lesson.title if lesson else None, "module": module.title if module else None, "note": t.note,
                      "assigned_at": t.assigned_at, "due_at": t.due_at,
                      "status": task_status(t, data.progress.get((uid, str(t.lesson_id))), by_lesson.get(str(t.lesson_id), []), at),
                      "submissions": by_lesson.get(str(t.lesson_id), [])})

    skills = []
    for skill in SKILLS:
        rows = data.skills[uid].get(skill, [])
        scores = [r.score for r in rows if r.score is not None]
        skills.append({"skill": skill, "lessons_total": data.skill_totals.get(skill, 0),
                       "completed": sum(r.status == PROGRESS_COMPLETED for r in rows),
                       "average_score": round(mean(scores)) if scores else None})

    chat = db.execute(select(func.count(), func.max(StudyGroupMessage.created_at)).where(
        StudyGroupMessage.group_id == group.id, StudyGroupMessage.sender_id == user.id)).one()
    progress_rows = [p for p in (data.progress.get((uid, str(lid))) for lid in data.lesson_ids) if p is not None]
    row = _student_row(data, member, user, at)
    return {
        "student": {"id": user.id, "name": display_name(user), "email": user.email, "joined_at": member.joined_at,
                    "member_status": member.status},
        "summary": row,
        "lessons": lessons,
        "tasks": tasks,
        "submissions": sorted(subs, key=lambda s: s["submitted_at"] or datetime.min.replace(tzinfo=at.tzinfo), reverse=True),
        "skills": skills,
        "activity": {
            "last_login": user.last_login,
            "last_lesson_activity": _last(*(p.last_activity_at or p.updated_at for p in progress_rows)),
            "last_submission": _last(*(s["submitted_at"] for s in subs)),
            "recent_reviews": [{"kind": s["kind"], "title": s["title"], "score": s["score"], "reviewed_at": s["reviewed_at"]}
                               for s in sorted((s for s in subs if s["reviewed_at"]), key=lambda s: s["reviewed_at"], reverse=True)[:5]],
            "chat_messages": chat[0] or 0, "last_chat_message": chat[1],
        },
    }


def task_board(db: Session, group: StudyGroup) -> dict:
    """Every group task with per-status counts and the per-student matrix."""
    data = load(db, group)
    at = now()
    info = data.lesson_info()
    out = []
    for t in data.tasks:
        lesson, module, _ = info.get(str(t.lesson_id), (None, None, None))
        cells = []
        for member, user in data.students:
            uid = str(user.id)
            subs = [s for s in data.submissions.get(uid, []) if s["lesson_id"] == str(t.lesson_id)]
            cells.append({"user_id": user.id, "name": display_name(user),
                          "status": task_status(t, data.progress.get((uid, str(t.lesson_id))), subs, at),
                          "submissions": [{k: s[k] for k in ("kind", "id", "title", "status", "submitted_at", "score")} for s in subs]})
        counts = defaultdict(int)
        for c in cells:
            counts[c["status"]] += 1
        out.append({"id": t.id, "lesson_id": t.lesson_id, "title": t.title or (lesson.title if lesson else "—"),
                    "lesson_title": lesson.title if lesson else None, "module": module.title if module else None,
                    "note": t.note, "assigned_at": t.assigned_at, "due_at": t.due_at, "counts": dict(counts), "students": cells})
    return {"tasks": out}


def task_summary_for_student(db: Session, group: StudyGroup, user_id) -> dict:
    data = load(db, group, user_ids=[user_id])
    if not data.students or not data.tasks:
        return {"total": len(data.tasks), "done": 0, "open": len(data.tasks), "overdue": 0}
    uid = str(user_id)
    at = now()
    statuses = [task_status(t, data.progress.get((uid, str(t.lesson_id))),
                            [s for s in data.submissions.get(uid, []) if s["lesson_id"] == str(t.lesson_id)], at) for t in data.tasks]
    return {"total": len(statuses), "done": sum(s in SUBMITTED for s in statuses), "open": sum(s in MISSING for s in statuses),
            "overdue": sum(s == "overdue" for s in statuses)}
