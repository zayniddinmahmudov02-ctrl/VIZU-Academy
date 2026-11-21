"""Student statistics: ONE definition of "student" for every admin number (dashboard, students list, language learners).

* There is one canonical account table, `users`. Self-registration by e-mail or phone (`auth.service.create_user`) and the
  Telegram Mini App login (`get_or_create_telegram_user`) all write it; each identity is unique (users.email, login_phone,
  telegram_id), so one row = one person and a re-registration can never add a second row (409 ACCOUNT_EXISTS / same row).
  Staff accounts are students promoted by a role change; the app never deletes users (no soft delete either).
* Student = role STUDENT and not a test account. Counted with COUNT over users.id (DISTINCT where a join could repeat a row).
* Test account = an e-mail domain reserved for documentation / testing (RFC 2606 / 6761: example.com|net|org, *.example,
  *.test, *.invalid, *.localhost) — no real person owns such an address. Shown separately, never in the student total.
  The internal placeholders of phone (`phone.vizu-deutsch.com`) and Telegram (`telegram.local`) accounts ARE real students.
* Registered (total) = every student row in any state: logging out, inactivity, a ban, a suspension or a deactivation never
  lowers it.
* Blocked = banned, deactivated or suspended right now (a subset of the total, shown separately).
* Active = not blocked AND (logged in [users.last_login] or lesson progress [student_progress.updated_at]) within ACTIVE_DAYS.
  Inactive = total − active.
* Test-takers = students with at least one FINISHED test attempt (lesson tests, Multilevel Modelltest, Stufe Bestimmung,
  legacy assessments, legacy quizzes). Lesson participants = students with at least one student_progress row. Students in
  groups = DISTINCT active student members. None of these is mixed into the total.
* New today / this month: users.created_at against the Tashkent calendar (UTC+5, no daylight saving).
Every call runs fresh PostgreSQL queries (no cache)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Select, and_, exists, func, literal, not_, or_, select, union
from sqlalchemy.orm import Session

from app.core.pagination import clamp_page_params, paginated_response
from app.core.security.roles import UserRole
from app.models.assessment_attempt import STATUS_IN_PROGRESS as ASSESSMENT_IN_PROGRESS
from app.models.assessment_attempt import AssessmentAttempt
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.lesson_skill import ATTEMPT_IN_PROGRESS, LessonSkillAttempt
from app.models.mock_test_attempt import STATUS_IN_PROGRESS as MOCK_IN_PROGRESS
from app.models.mock_test_attempt import MockTestAttempt
from app.models.module import Module
from app.models.student_progress import StudentProgress
from app.models.student_quiz import StudentQuiz
from app.models.study_group import GROUP_ACTIVE, MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupMember
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.vizu_multilevel_attempt import STATUS_COMPLETED as LEVEL_TEST_COMPLETED
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt

ACTIVE_DAYS = 30
TASHKENT = timezone(timedelta(hours=5))  # Uzbekistan has no daylight saving time
TEST_EMAIL_DOMAINS = ("example.com", "example.net", "example.org")
TEST_EMAIL_SUFFIXES = (".example", ".test", ".invalid", ".localhost")
ADMIN_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN)
OTHER_STAFF_ROLES = (UserRole.CONTENT_MANAGER, UserRole.PAYMENT_MANAGER, UserRole.SUPPORT)
LIST_STATUSES = ("all", "active", "inactive", "blocked", "test_takers", "test_accounts")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(at: datetime) -> datetime:
    """users.last_login / suspended_until are `timestamp without time zone` written in UTC."""
    return at.astimezone(timezone.utc).replace(tzinfo=None)


def tashkent_day_start(now: datetime) -> datetime:
    local = now.astimezone(TASHKENT)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def tashkent_month_start(now: datetime) -> datetime:
    return tashkent_day_start(now).replace(day=1)


# ---------- the shared rules (SQL clauses on users) ----------

def is_test_account():
    domain = func.lower(func.split_part(User.email, "@", 2))
    return or_(domain.in_(TEST_EMAIL_DOMAINS), *[domain.like(f"%{s}") for s in TEST_EMAIL_SUFFIXES])


def is_student():
    return and_(User.role == UserRole.STUDENT, not_(is_test_account()))


def is_blocked(now: datetime):
    return or_(User.is_banned.is_(True), User.is_active.is_(False),
               and_(User.suspended_until.isnot(None), User.suspended_until > _naive_utc(now)))


def is_active(now: datetime):
    since = now - timedelta(days=ACTIVE_DAYS)
    recent_progress = exists().where(StudentProgress.user_id == User.id, StudentProgress.updated_at >= since)
    # NULL-safe on purpose: "last_login >= x" is NULL for a never-logged-in student, and NOT(NULL) would drop them from "inactive"
    recent_login = and_(User.last_login.isnot(None), User.last_login >= _naive_utc(since))
    return and_(not_(is_blocked(now)), or_(recent_login, recent_progress))


def took_a_test():
    return or_(
        exists().where(LessonSkillAttempt.user_id == User.id, LessonSkillAttempt.status != ATTEMPT_IN_PROGRESS),
        exists().where(MockTestAttempt.user_id == User.id, MockTestAttempt.status != MOCK_IN_PROGRESS),
        exists().where(VizuMultilevelAttempt.user_id == User.id, VizuMultilevelAttempt.status == LEVEL_TEST_COMPLETED),
        exists().where(AssessmentAttempt.user_id == User.id, AssessmentAttempt.status != ASSESSMENT_IN_PROGRESS),
        exists().where(StudentQuiz.user_id == User.id),
    )


def joined_a_lesson():
    return exists().where(StudentProgress.user_id == User.id)


def _in_a_group():
    return exists().where(StudyGroupMember.user_id == User.id, StudyGroupMember.status == MEMBER_ACTIVE,
                          StudyGroupMember.role == MEMBER_STUDENT)


# ---------- overview ----------

def overview(db: Session, now: datetime | None = None) -> dict:
    now = now or utc_now()
    student, test = is_student(), and_(User.role == UserRole.STUDENT, is_test_account())
    today, month = tashkent_day_start(now), tashkent_month_start(now)
    row = db.execute(select(
        func.count(func.distinct(User.id)).filter(student),
        func.count(func.distinct(User.id)).filter(and_(student, is_active(now))),
        func.count(func.distinct(User.id)).filter(and_(student, is_blocked(now))),
        func.count(func.distinct(User.id)).filter(and_(student, took_a_test())),
        func.count(func.distinct(User.id)).filter(and_(student, joined_a_lesson())),
        func.count(func.distinct(User.id)).filter(and_(student, _in_a_group())),
        func.count(func.distinct(User.id)).filter(and_(student, User.created_at >= today)),
        func.count(func.distinct(User.id)).filter(and_(student, User.created_at >= month)),
        func.count(func.distinct(User.id)).filter(test),
        func.count(func.distinct(User.id)).filter(User.role == UserRole.TEACHER),
        func.count(func.distinct(User.id)).filter(User.role.in_(ADMIN_ROLES)),
        func.count(func.distinct(User.id)).filter(User.role.in_(OTHER_STAFF_ROLES)),
        func.count(func.distinct(User.id)),
    ).select_from(User)).one()
    (total, active, blocked, test_takers, participants, in_groups, today_new, month_new,
     test_accounts, teachers, admins, other_staff, accounts) = (int(v or 0) for v in row)
    groups, active_groups = db.execute(select(func.count(StudyGroup.id), func.count(StudyGroup.id).filter(StudyGroup.status == GROUP_ACTIVE))).one()
    return {
        "total_students": total,
        "active_students": active,
        "inactive_students": total - active,
        "blocked_students": blocked,
        "test_takers": test_takers,
        "lesson_participants": participants,
        "students_in_groups": in_groups,
        "total_teachers": teachers,
        "total_admins": admins,
        "total_other_staff": other_staff,
        "test_accounts": test_accounts,
        "total_accounts": accounts,
        "total_groups": int(groups or 0),
        "active_groups": int(active_groups or 0),
        "total_registrations_today": today_new,
        "total_registrations_this_month": month_new,
        "active_days": ACTIVE_DAYS,
        "timezone": "Asia/Tashkent",
        "computed_at": now,
    }


# ---------- students list ----------

def _registered_via(user: User) -> str:
    if user.telegram_id is not None:
        return "telegram"
    if user.login_phone:
        return "phone"
    return "email"


def list_students(db: Session, *, page: int = 1, page_size: int = 20, status: str = "all", search: str | None = None,
                  sort: str = "newest", now: datetime | None = None) -> dict:
    now = now or utc_now()
    base = User.role == UserRole.STUDENT
    where = {
        "all": is_student(),
        "active": and_(is_student(), is_active(now)),
        "inactive": and_(is_student(), not_(is_active(now))),
        "blocked": and_(is_student(), is_blocked(now)),
        "test_takers": and_(is_student(), took_a_test()),
        "test_accounts": and_(base, is_test_account()),
    }.get(status, is_student())
    query = select(User).where(where)
    if search and search.strip():
        like = f"%{search.strip()}%"
        query = query.where(or_(User.first_name.ilike(like), User.last_name.ilike(like), User.username.ilike(like),
                                User.email.ilike(like), User.login_phone.ilike(like), User.phone_number.ilike(like)))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    order = {"oldest": [User.created_at.asc()], "last_login": [User.last_login.desc().nullslast(), User.created_at.desc()],
             "name": [func.lower(func.coalesce(User.first_name, User.username)).asc(), User.created_at.desc()]}
    page, page_size = clamp_page_params(page, page_size)
    users = list(db.scalars(query.order_by(*order.get(sort, [User.created_at.desc()]), User.id).offset((page - 1) * page_size).limit(page_size)))
    ids = [u.id for u in users]
    flags = {}
    if ids:
        for uid, active, blocked, tested, lessons, groups in db.execute(select(
                User.id, is_active(now), is_blocked(now), took_a_test(), joined_a_lesson(),
                select(func.count(StudyGroupMember.id)).where(StudyGroupMember.user_id == User.id, StudyGroupMember.status == MEMBER_ACTIVE)
                .scalar_subquery()).where(User.id.in_(ids))):
            flags[uid] = (bool(active), bool(blocked), bool(tested), bool(lessons), int(groups or 0))
    items = []
    for u in users:
        active, blocked, tested, lessons, groups = flags.get(u.id, (False, False, False, False, 0))
        via = _registered_via(u)
        items.append({
            "id": u.id, "name": " ".join(p for p in (u.first_name, u.last_name) if p) or u.username, "username": u.username,
            "contact": u.login_phone if via == "phone" else (None if via == "telegram" else u.email), "registered_via": via,
            "created_at": u.created_at, "last_login": u.last_login, "is_active_student": active, "is_blocked": blocked,
            "took_a_test": tested, "joined_a_lesson": lessons, "groups": groups,
        })
    out = paginated_response(items, total, page, page_size)
    out["status"] = status if status in LIST_STATUSES else "all"
    return out


# ---------- language learners (the Languages admin pages) ----------

def language_student_ids(language_id: UUID) -> Select:
    """Students linked to a language: a user_languages row OR lesson progress in that language's courses (user_languages
    is not written by the current app, so progress is what links a student to the language they learn)."""
    by_choice = select(UserLanguage.user_id.label("user_id")).where(UserLanguage.language_id == language_id)
    by_progress = (select(StudentProgress.user_id.label("user_id"))
                   .join(Lesson, StudentProgress.lesson_id == Lesson.id).join(Module, Lesson.module_id == Module.id)
                   .join(Course, Module.course_id == Course.id).where(Course.language_id == language_id))
    linked = union(by_choice, by_progress).subquery()
    return select(User.id).where(User.id.in_(select(linked.c.user_id)), is_student())


def language_learner_counts(db: Session, language_id: UUID, now: datetime | None = None) -> tuple[int, int]:
    """(learners, learners active within ACTIVE_DAYS in this language)."""
    now = now or utc_now()
    since = now - timedelta(days=ACTIVE_DAYS)
    ids = language_student_ids(language_id).subquery()
    learners = db.scalar(select(func.count(func.distinct(ids.c.id)))) or 0
    recent = union(
        select(UserLanguage.user_id.label("user_id")).where(UserLanguage.language_id == language_id, UserLanguage.last_activity >= since),
        select(StudentProgress.user_id.label("user_id")).join(Lesson, StudentProgress.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id).join(Course, Module.course_id == Course.id)
        .where(Course.language_id == language_id, StudentProgress.updated_at >= since),
    ).subquery()
    active = db.scalar(select(func.count(func.distinct(ids.c.id))).where(ids.c.id.in_(select(recent.c.user_id)))) or 0
    return int(learners), int(active)


def language_learners_page(db: Session, language_id: UUID, search: str | None, page: int, page_size: int) -> dict:
    ids = language_student_ids(language_id).subquery()
    cond = [User.id.in_(select(ids.c.id))]
    if search:
        like = f"%{search}%"
        cond.append(or_(User.username.ilike(like), User.email.ilike(like)))
    total = db.scalar(select(func.count(User.id)).where(*cond)) or 0
    page, page_size = clamp_page_params(page, page_size)
    progress = (select(StudentProgress.user_id.label("user_id"), func.min(StudentProgress.created_at).label("first"),
                       func.max(StudentProgress.updated_at).label("last"))
                .join(Lesson, StudentProgress.lesson_id == Lesson.id).join(Module, Lesson.module_id == Module.id)
                .join(Course, Module.course_id == Course.id).where(Course.language_id == language_id)
                .group_by(StudentProgress.user_id).subquery())
    chosen = select(UserLanguage).where(UserLanguage.language_id == language_id).subquery()
    joined = func.least(chosen.c.joined_at, progress.c.first)  # LEAST / GREATEST skip NULLs in PostgreSQL
    last = func.greatest(chosen.c.last_activity, progress.c.last)
    rows = db.execute(
        select(User, func.coalesce(chosen.c.is_primary, literal(False)), joined, last)
        .outerjoin(chosen, chosen.c.user_id == User.id).outerjoin(progress, progress.c.user_id == User.id)
        .where(*cond).order_by(joined.desc().nullslast(), User.id).offset((page - 1) * page_size).limit(page_size)
    ).all() if total else []
    items = [{"id": u.id, "username": u.username, "email": u.email, "is_primary": bool(primary), "joined_at": j or u.created_at,
              "last_activity": la} for u, primary, j, la in rows]
    return paginated_response(items, total, page, page_size)
