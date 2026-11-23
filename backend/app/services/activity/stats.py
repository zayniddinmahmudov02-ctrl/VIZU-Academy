"""Read side of the activity tracking: a student's own Medien statistics, the Kontroll list of every student and one student's
activity detail (usage time, courses, music, Wortschatz, books, films, timeline).

Sources (nothing is estimated or invented; a number the platform does not record is returned as None):
* usage time = student_sessions.active_seconds (server-credited, see app.services.activity.tracker); today / week / month are
  Tashkent days; "week" = the last 7 days incl. today, "month" = the current calendar month.
* time per area / item = student_activity_events.seconds.
* songs: plays = media_play_history (every "play", also from before the time tracking existed), listening time = MUSIC events.
* books: opened = media_progress BOOK with last_opened_at or a page > 0 (opening is not reading: pages and "finished" come from
  the reader's saved position), reading time = BOOK events. films: started = media_progress FILM with a position > 0, watching
  time = FILM events, "continue" = the saved position.
* courses: published lessons of each level's main module vs. student_progress.lesson_completed (the same rule as the LMS).
* Wortschatz: learned lesson words (vocabulary_user_words.learned), saved words, repeated = dictionary words seen at least twice
  (dictionary_user_words.seen_count >= 2), finished blocks = WORTSCHATZ competencies completed (student_competency_progress).
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.course import Course
from app.models.dictionary import DictionaryUserWord
from app.models.lesson import Lesson
from app.models.lms import PROGRESS_COMPLETED, StudentCompetencyProgress
from app.models.medien import KIND_BOOK, KIND_FILM, STATUS_PUBLISHED, Film, MediaBook, MediaPlayHistory, MediaProgress, Song
from app.models.module import Module
from app.models.student_activity import (AREA_BOOK, AREA_COURSE, AREA_EXAM, AREA_FILM, AREA_MUSIC, AREA_WORTSCHATZ, MEDIA_AREAS,
                                         StudentActivityEvent, StudentSession)
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.models.vocabulary import VocabularyUserWord
from app.services.activity.tracker import TZ, local_day
from app.services.admin.student_stats import is_student
from app.services.lms.structure import LEVELS, level_course, level_lessons, main_module

DAILY_DAYS = 14
LIST_LIMIT = 50


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _latest(*values):
    found = [_aware(v) for v in values if v is not None]
    return max(found) if found else None


def display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


def _like(q: str) -> str:
    return "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# ---------------- usage time ----------------


def usage(db: Session, user_id, now: datetime | None = None) -> dict:
    now = _aware(now or _now())
    today = local_day(now)
    rows = db.execute(select(StudentSession.day, func.sum(StudentSession.active_seconds), func.max(StudentSession.last_seen_at),
                             func.min(StudentSession.started_at))
                      .where(StudentSession.user_id == user_id).group_by(StudentSession.day)).all()
    per_day = {d: int(s or 0) for d, s, _l, _f in rows}
    month_start = today.replace(day=1)
    return {
        "total_seconds": sum(per_day.values()),
        "today_seconds": per_day.get(today, 0),
        "week_seconds": sum(s for d, s in per_day.items() if today - timedelta(days=6) <= d <= today),
        "month_seconds": sum(s for d, s in per_day.items() if month_start <= d <= today),
        "active_days": sum(1 for s in per_day.values() if s > 0),
        "last_activity_at": _latest(*(r[2] for r in rows)),
        "tracking_since": min((_aware(r[3]) for r in rows), default=None),
        "timezone": str(TZ),
    }


def _area_seconds(db: Session, user_ids: list, areas=None) -> dict:
    stmt = select(StudentActivityEvent.user_id, StudentActivityEvent.area, func.sum(StudentActivityEvent.seconds)).where(
        StudentActivityEvent.user_id.in_(user_ids))
    if areas:
        stmt = stmt.where(StudentActivityEvent.area.in_(areas))
    out: dict = defaultdict(dict)
    for uid, area, seconds in db.execute(stmt.group_by(StudentActivityEvent.user_id, StudentActivityEvent.area)):
        out[uid][area] = int(seconds or 0)
    return out


def _event_items(db: Session, user_id, area: str) -> dict:
    """ref_id -> (seconds, last_seen_at) of one area."""
    rows = db.execute(select(StudentActivityEvent.ref_id, func.sum(StudentActivityEvent.seconds), func.max(StudentActivityEvent.last_seen_at))
                      .where(StudentActivityEvent.user_id == user_id, StudentActivityEvent.area == area, StudentActivityEvent.ref_id.isnot(None))
                      .group_by(StudentActivityEvent.ref_id)).all()
    return {ref: (int(s or 0), _aware(last)) for ref, s, last in rows}


# ---------------- media ----------------


def music(db: Session, user_id, *, published_only: bool = False, limit: int = LIST_LIMIT) -> dict:
    plays = {sid: (int(n), _aware(at)) for sid, n, at in db.execute(
        select(MediaPlayHistory.song_id, func.count(), func.max(MediaPlayHistory.created_at)).where(MediaPlayHistory.user_id == user_id)
        .group_by(MediaPlayHistory.song_id))}
    timed = _event_items(db, user_id, AREA_MUSIC)
    ids = set(plays) | {k for k, (s, _l) in timed.items() if s > 0}
    songs = {s.id: s for s in db.scalars(select(Song).where(Song.id.in_(ids)))} if ids else {}
    items = []
    for sid in ids:
        song = songs.get(sid)
        if song is None or (published_only and song.status != STATUS_PUBLISHED):
            continue
        n, played_at = plays.get(sid, (0, None))
        seconds, heard_at = timed.get(sid, (0, None))
        items.append({"id": sid, "title": song.title, "artist": song.artist, "duration_ms": song.duration_ms, "play_count": n,
                      "listened_seconds": seconds, "last_listened_at": _latest(played_at, heard_at)})
    recent = sorted(items, key=lambda i: i["last_listened_at"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    top = sorted(items, key=lambda i: (i["listened_seconds"], i["play_count"]), reverse=True)
    return {"songs_listened": len(items), "play_count": sum(i["play_count"] for i in items),
            "listened_seconds": sum(i["listened_seconds"] for i in items), "top": top[:5], "recent": recent[:10], "history": recent[:limit],
            "last": recent[0] if recent else None}


def _progress_rows(db: Session, user_id, kind: str) -> dict:
    return {r.content_id: r for r in db.scalars(select(MediaProgress).where(MediaProgress.user_id == user_id, MediaProgress.content_type == kind))}


def books(db: Session, user_id, *, published_only: bool = False, limit: int = LIST_LIMIT) -> dict:
    progress = _progress_rows(db, user_id, KIND_BOOK)
    timed = _event_items(db, user_id, AREA_BOOK)
    ids = {k for k, r in progress.items() if r.last_opened_at is not None or (r.position or 0) > 0} | {k for k, (s, _l) in timed.items() if s > 0}
    found = {b.id: b for b in db.scalars(select(MediaBook).where(MediaBook.id.in_(ids)))} if ids else {}
    items = []
    for bid in ids:
        book = found.get(bid)
        if book is None or (published_only and book.status != STATUS_PUBLISHED):
            continue
        row = progress.get(bid)
        seconds, read_at = timed.get(bid, (0, None))
        items.append({"id": bid, "title": book.title, "author": book.author, "page": row.position if row else None,
                      "pages": (row.total if row and row.total else book.page_count), "completed": bool(row and row.completed),
                      "reading_seconds": seconds, "last_opened_at": _latest(row.last_opened_at if row else None, read_at,
                                                                            row.updated_at if row and (row.position or 0) > 0 else None)})
    recent = sorted(items, key=lambda i: i["last_opened_at"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return {"books_opened": len(items), "books_completed": sum(1 for i in items if i["completed"]),
            "reading_seconds": sum(i["reading_seconds"] for i in items), "recent": recent[:10], "history": recent[:limit],
            "last": recent[0] if recent else None}


def films(db: Session, user_id, *, published_only: bool = False, limit: int = LIST_LIMIT) -> dict:
    progress = _progress_rows(db, user_id, KIND_FILM)
    timed = _event_items(db, user_id, AREA_FILM)
    ids = {k for k, r in progress.items() if (r.position or 0) > 0} | {k for k, (s, _l) in timed.items() if s > 0}
    found = {f.id: f for f in db.scalars(select(Film).where(Film.id.in_(ids)))} if ids else {}
    items = []
    for fid in ids:
        film = found.get(fid)
        if film is None or (published_only and film.status != STATUS_PUBLISHED):
            continue
        row = progress.get(fid)
        seconds, seen_at = timed.get(fid, (0, None))
        total = (row.total if row and row.total else None) or (film.video_duration_ms // 1000 if film.video_duration_ms else None)
        items.append({"id": fid, "title": film.title, "position_seconds": row.position if row else 0, "duration_seconds": total,
                      "completed": bool(row and row.completed), "watched_seconds": seconds,
                      "last_watched_at": _latest(row.updated_at if row and (row.position or 0) > 0 else None, seen_at)})
    recent = sorted(items, key=lambda i: i["last_watched_at"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return {"films_watched": len(items), "films_completed": sum(1 for i in items if i["completed"]),
            "watched_seconds": sum(i["watched_seconds"] for i in items), "recent": recent[:10], "history": recent[:limit],
            "continue": [i for i in recent if not i["completed"] and i["position_seconds"]][:5], "last": recent[0] if recent else None}


def daily(db: Session, user_id, areas, now: datetime | None = None, days: int = DAILY_DAYS) -> list[dict]:
    today = local_day(_aware(now or _now()))
    start = today - timedelta(days=days - 1)
    rows = db.execute(select(StudentActivityEvent.day, StudentActivityEvent.area, func.sum(StudentActivityEvent.seconds))
                      .where(StudentActivityEvent.user_id == user_id, StudentActivityEvent.day >= start, StudentActivityEvent.area.in_(areas))
                      .group_by(StudentActivityEvent.day, StudentActivityEvent.area)).all()
    per = defaultdict(dict)
    for d, area, s in rows:
        per[d][area] = int(s or 0)
    return [{"date": (start + timedelta(days=i)).isoformat(), **{a: per[start + timedelta(days=i)].get(a, 0) for a in areas}}
            for i in range(days)]


def media_overview(db: Session, user: User, now: datetime | None = None) -> dict:
    """The student's own Medien statistics (published items only)."""
    m, b, f = music(db, user.id, published_only=True), books(db, user.id, published_only=True), films(db, user.id, published_only=True)
    first = db.scalar(select(func.min(StudentActivityEvent.started_at)).where(StudentActivityEvent.user_id == user.id,
                                                                             StudentActivityEvent.area.in_(MEDIA_AREAS)))
    return {"music": m, "books": b, "films": f, "media_seconds": m["listened_seconds"] + b["reading_seconds"] + f["watched_seconds"],
            "daily": daily(db, user.id, MEDIA_AREAS, now), "tracking_since": _aware(first)}


# ---------------- courses / Wortschatz ----------------


def _level_lessons(db: Session) -> dict:
    """level -> (course, [published lessons of its main module])."""
    out = {}
    for level in LEVELS:
        course = level_course(db, level)
        lessons = level_lessons(db, main_module(db, course), published_only=True) if course else []
        if course and lessons:
            out[level] = (course, lessons)
    return out


def courses(db: Session, user_id, structure: dict | None = None) -> list[dict]:
    structure = structure if structure is not None else _level_lessons(db)
    rows = {r.lesson_id: r for r in db.scalars(select(StudentProgress).where(StudentProgress.user_id == user_id))}
    timed = _event_items(db, user_id, AREA_COURSE)
    out = []
    for level, (course, lessons) in structure.items():
        mine = [(lesson, rows[lesson.id]) for lesson in lessons if lesson.id in rows]
        seconds = sum(timed.get(lesson.id, (0, None))[0] for lesson in lessons)
        if not mine and not seconds:
            continue
        done = sum(1 for _l, r in mine if r.lesson_completed)
        last = max(mine, key=lambda lr: _latest(lr[1].last_activity_at, lr[1].updated_at), default=None)
        out.append({"course_id": course.id, "title": course.title, "level": level, "lessons_completed": done, "lessons_total": len(lessons),
                    "percent": round(done * 100 / len(lessons)), "started_at": min((_aware(r.created_at) for _l, r in mine), default=None),
                    "last_lesson": {"id": last[0].id, "number": last[0].number, "title": last[0].title,
                                    "at": _latest(last[1].last_activity_at, last[1].updated_at)} if last else None,
                    "seconds": seconds})
    return out


def completed_counts(db: Session, user_ids: list, structure: dict) -> dict:
    """user -> (lessons completed, courses completed) over the published level lessons."""
    lesson_level = {lesson.id: level for level, (_c, lessons) in structure.items() for lesson in lessons}
    per = defaultdict(lambda: defaultdict(int))
    total_done = defaultdict(int)
    for uid, lid in db.execute(select(StudentProgress.user_id, StudentProgress.lesson_id)
                               .where(StudentProgress.user_id.in_(user_ids), StudentProgress.lesson_completed.is_(True))):
        total_done[uid] += 1
        if lid in lesson_level:
            per[uid][lesson_level[lid]] += 1
    return {uid: (total_done.get(uid, 0), sum(1 for level, n in per[uid].items() if n >= len(structure[level][1]))) for uid in user_ids}


def vocabulary(db: Session, user_id) -> dict:
    seconds, last_event = db.execute(select(func.coalesce(func.sum(StudentActivityEvent.seconds), 0), func.max(StudentActivityEvent.last_seen_at))
                                     .where(StudentActivityEvent.user_id == user_id, StudentActivityEvent.area == AREA_WORTSCHATZ)).one()
    learned, saved_lesson, last_lesson = db.execute(select(
        func.count().filter(VocabularyUserWord.learned.is_(True)), func.count().filter(VocabularyUserWord.saved.is_(True)),
        func.max(func.greatest(VocabularyUserWord.learned_at, VocabularyUserWord.saved_at)))
        .where(VocabularyUserWord.user_id == user_id)).one()
    saved_dict, repeated, last_dict = db.execute(select(
        func.count().filter(DictionaryUserWord.saved.is_(True)), func.count().filter(DictionaryUserWord.seen_count >= 2),
        func.max(func.greatest(DictionaryUserWord.last_seen_at, DictionaryUserWord.saved_at)))
        .where(DictionaryUserWord.user_id == user_id)).one()
    blocks, last_block = db.execute(select(func.count(), func.max(StudentCompetencyProgress.completed_at)).where(
        StudentCompetencyProgress.user_id == user_id, StudentCompetencyProgress.competency == "WORTSCHATZ",
        StudentCompetencyProgress.status == PROGRESS_COMPLETED)).one()
    return {"seconds": int(seconds or 0), "words_learned": int(learned or 0), "words_saved": int(saved_lesson or 0) + int(saved_dict or 0),
            "words_repeated": int(repeated or 0), "blocks_completed": int(blocks or 0),
            "last_activity_at": _latest(last_event, last_lesson, last_dict, last_block)}


# ---------------- timeline ----------------


def _labels(db: Session, events: list[StudentActivityEvent]) -> dict:
    by_area = defaultdict(set)
    for e in events:
        if e.ref_id is not None:
            by_area[e.area].add(e.ref_id)
    labels: dict = {}
    lesson_ids = by_area[AREA_COURSE] | by_area[AREA_WORTSCHATZ]
    if lesson_ids:
        for lesson, level in db.execute(select(Lesson, Course.level).join(Module, Module.id == Lesson.module_id)
                                        .join(Course, Course.id == Module.course_id).where(Lesson.id.in_(lesson_ids))):
            labels[lesson.id] = {"level": level, "lesson_number": lesson.number, "title": f"{level} Kurs — Lektion {lesson.number}"}
    for area, model in ((AREA_MUSIC, Song), (AREA_FILM, Film), (AREA_BOOK, MediaBook)):
        if by_area[area]:
            for item in db.scalars(select(model).where(model.id.in_(by_area[area]))):
                labels[item.id] = {"title": item.title + (f" — {item.artist}" if area == AREA_MUSIC and item.artist else "")}
    return labels


def timeline(db: Session, user_id, day: date | None = None) -> dict:
    days = [d for (d,) in db.execute(select(StudentActivityEvent.day).where(StudentActivityEvent.user_id == user_id)
                                     .group_by(StudentActivityEvent.day).order_by(StudentActivityEvent.day.desc()).limit(60))]
    day = day or (days[0] if days else None)
    if day is None:
        return {"day": None, "days": [], "items": []}
    events = list(db.scalars(select(StudentActivityEvent).where(StudentActivityEvent.user_id == user_id, StudentActivityEvent.day == day)
                             .order_by(StudentActivityEvent.started_at)))
    labels = _labels(db, events)
    items = []
    for e in events:
        if e.seconds <= 0:
            continue
        label = labels.get(e.ref_id, {})
        items.append({"id": e.id, "area": e.area, "ref_id": e.ref_id, "started_at": _aware(e.started_at), "ended_at": _aware(e.last_seen_at),
                      "time": _aware(e.started_at).astimezone(TZ).strftime("%H:%M"), "seconds": e.seconds,
                      "title": label.get("title"), "level": label.get("level"), "lesson_number": label.get("lesson_number")})
    return {"day": day.isoformat(), "days": [d.isoformat() for d in days], "items": items}


# ---------------- Kontroll ----------------

SORTS = ("registered", "name", "usage", "last_activity")


def _student_or_404(db: Session, student_id: UUID) -> User:
    user = db.get(User, student_id)
    if user is None or user.role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="STUDENT_NOT_FOUND")
    return user


def _status(user: User, now: datetime) -> str:
    if user.is_banned or (user.suspended_until and _aware(user.suspended_until) > now):
        return "blocked"
    return "active" if user.is_active else "inactive"


def kontroll_list(db: Session, *, page: int = 1, page_size: int = 25, search: str | None = None, sort: str = "registered") -> dict:
    page, page_size = max(1, page), max(1, min(page_size, 100))
    now = _now()
    sess = (select(StudentSession.user_id.label("uid"), func.sum(StudentSession.active_seconds).label("secs"),
                   func.max(StudentSession.last_seen_at).label("last")).group_by(StudentSession.user_id).subquery())
    base = select(User, sess.c.secs, sess.c.last).outerjoin(sess, sess.c.uid == User.id).where(is_student())
    if search and search.strip():
        q = search.strip()
        conds = [User.email.ilike(_like(q), escape="\\"), User.username.ilike(_like(q), escape="\\"),
                 func.concat_ws(" ", User.first_name, User.last_name).ilike(_like(q), escape="\\")]
        try:
            conds.append(User.id == UUID(q))
        except ValueError:
            pass
        base = base.where(or_(*conds))
    order = {"name": (func.lower(func.coalesce(User.first_name, User.username)).asc(), User.created_at.desc()),
             "usage": (sess.c.secs.desc().nulls_last(), User.created_at.desc()),
             "last_activity": (sess.c.last.desc().nulls_last(), User.created_at.desc())}.get(sort, (User.created_at.desc(),))
    total = db.scalar(select(func.count()).select_from(base.order_by(None).subquery())) or 0
    rows = db.execute(base.order_by(*order).limit(page_size).offset((page - 1) * page_size)).all()
    ids = [u.id for u, _s, _l in rows]
    structure = _level_lessons(db)
    done = completed_counts(db, ids, structure) if ids else {}
    areas = _area_seconds(db, ids, (AREA_MUSIC, AREA_WORTSCHATZ, AREA_BOOK, AREA_FILM)) if ids else {}
    progress_last = dict(db.execute(select(StudentProgress.user_id, func.max(StudentProgress.updated_at))
                                    .where(StudentProgress.user_id.in_(ids)).group_by(StudentProgress.user_id)).all()) if ids else {}
    opened = defaultdict(lambda: {KIND_BOOK: set(), KIND_FILM: set()})
    if ids:
        for uid, kind, cid in db.execute(select(MediaProgress.user_id, MediaProgress.content_type, MediaProgress.content_id).where(
                MediaProgress.user_id.in_(ids), or_(MediaProgress.position > 0,
                                                    and_(MediaProgress.content_type == KIND_BOOK, MediaProgress.last_opened_at.isnot(None))))):
            opened[uid][kind].add(cid)
        for uid, area, ref in db.execute(select(StudentActivityEvent.user_id, StudentActivityEvent.area, StudentActivityEvent.ref_id).where(
                StudentActivityEvent.user_id.in_(ids), StudentActivityEvent.area.in_((AREA_BOOK, AREA_FILM)), StudentActivityEvent.seconds > 0)
                .group_by(StudentActivityEvent.user_id, StudentActivityEvent.area, StudentActivityEvent.ref_id)):
            opened[uid][KIND_BOOK if area == AREA_BOOK else KIND_FILM].add(ref)
    items = []
    for user, secs, last in rows:
        lessons_done, courses_done = done.get(user.id, (0, 0))
        a = areas.get(user.id, {})
        items.append({"id": user.id, "name": display_name(user), "email": user.email, "registered_at": _aware(user.created_at),
                      "status": _status(user, now), "usage_seconds": int(secs or 0),
                      "last_activity_at": _latest(last, user.last_login, progress_last.get(user.id)),
                      "courses_completed": courses_done, "lessons_completed": lessons_done,
                      "music_seconds": a.get(AREA_MUSIC, 0), "vocabulary_seconds": a.get(AREA_WORTSCHATZ, 0),
                      "books_viewed": len(opened[user.id][KIND_BOOK]), "films_viewed": len(opened[user.id][KIND_FILM])})
    return {"items": items, "total": total, "page": page, "page_size": page_size, "sort": sort if sort in SORTS else "registered"}


def kontroll_detail(db: Session, student_id: UUID, now: datetime | None = None) -> dict:
    user = _student_or_404(db, student_id)
    now = _aware(now or _now())
    general = usage(db, user.id, now)
    general["last_login_at"] = _aware(user.last_login)
    general["last_activity_at"] = _latest(general["last_activity_at"], user.last_login)
    areas = _area_seconds(db, [user.id]).get(user.id, {})
    return {
        "student": {"id": user.id, "name": display_name(user), "email": user.email, "username": user.username,
                    "registered_at": _aware(user.created_at), "status": _status(user, now)},
        "general": general,
        "area_seconds": {a: areas.get(a, 0) for a in (AREA_COURSE, AREA_WORTSCHATZ, AREA_MUSIC, AREA_BOOK, AREA_FILM, AREA_EXAM)},
        "courses": courses(db, user.id),
        "music": music(db, user.id),
        "vocabulary": vocabulary(db, user.id),
        "books": books(db, user.id),
        "films": films(db, user.id),
        "daily": daily(db, user.id, (AREA_COURSE, AREA_WORTSCHATZ, AREA_MUSIC, AREA_BOOK, AREA_FILM, AREA_EXAM), now),
    }
