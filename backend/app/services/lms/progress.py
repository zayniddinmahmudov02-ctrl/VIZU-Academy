"""VIZU LMS progress — the one place that decides a student's state in the
ten competencies of a lesson, whether the lesson is completed, and the level
progress built from that.

Signals are read from the existing sources, never re-implemented:
  * videos: video_progress (completion threshold enforced by its service),
  * Frage des Themas / Sprechen / Schreiben: the submission + grading state
    from app.services.lesson_skills.results (GRADED counts, SUBMITTED not —
    Frage counts once submitted, it has no fixed rubric),
  * Lesen / Hören / Grammatik / Wortschatz / Übungen / Abschlusstest: the
    server-graded attempts (results.py), with the legacy VOCABULARY / LESSON
    quiz as fallback while old lessons still have them.

A competency is "tracked" when it has such a signal; only tracked, published,
available competencies decide lesson completion — opening a page or pressing
a button never completes a lesson. A competency with only text / resources is
"visited" when opened (shown to the student, not counted). If a published
lesson has no tracked competency at all, every available one must have been
visited.

Results are persisted as a snapshot (student_competency_progress +
student_progress.lesson_completed / completed_at / last_activity_at) by
sync_lesson(), which runs on every event that can change them (see
app.services.learning.lesson_progress.refresh_lesson_completion) and when the
student opens the lesson. Level lists read the snapshot."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.grammar import Grammar
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.lms import (
    COMPETENCY_ORDER,
    COMPETENCY_ORDER,
    PROGRESS_COMPLETED,
    PROGRESS_IN_PROGRESS,
    PROGRESS_NOT_STARTED,
    LearningResource,
    StudentCompetencyProgress,
)
from app.models.quiz import QUIZ_TYPE_LESSON, QUIZ_TYPE_VOCABULARY
from app.models.reading import Reading
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.models.video import Video
from app.models.video_progress import VideoProgress
from app.models.vocabulary import Vocabulary
from app.services.lesson_skills import results as skill_results
from app.services.lms import structure
from app.services.lms.access import LessonAccess, lesson_access

STATUS_LOCKED = "locked"
STATUS_NOT_AVAILABLE = "not_available"

# competency -> key in lesson_skill_results()["skills"]
SKILL_OF = {
    "WORTSCHATZ": "wortschatz",
    "GRAMMATIK": "grammatik",
    "LESEN": "lesen",
    "HOEREN": "hoeren",
    "SPRECHEN": "sprechen",
    "SCHREIBEN": "schreiben",
    "UEBUNGEN": "uebungen",
    "ABSCHLUSSTEST": "yakuniy",
}
LEGACY_QUIZ_OF = {"WORTSCHATZ": QUIZ_TYPE_VOCABULARY, "ABSCHLUSSTEST": QUIZ_TYPE_LESSON}


def competency_order_for_level(level: str | None) -> tuple[str, ...]:
    """A1 omits the introduction from the student course flow without
    changing its shared competency model or any stored lesson content."""
    if (level or "").strip().upper() == "A1":
        return tuple(kind for kind in COMPETENCY_ORDER if kind != "EINFUEHRUNG")
    return COMPETENCY_ORDER


def _now() -> datetime:
    return datetime.now(timezone.utc)


def aggregate(statuses: list[str]) -> str:
    if statuses and all(s == PROGRESS_COMPLETED for s in statuses):
        return PROGRESS_COMPLETED
    if all(s == PROGRESS_NOT_STARTED for s in statuses):
        return PROGRESS_NOT_STARTED
    return PROGRESS_IN_PROGRESS


def _skill_part(skill: dict) -> dict | None:
    if not skill.get("available"):
        return None
    raw = skill.get("status")
    if raw == skill_results.COMPLETED:
        status = PROGRESS_COMPLETED
    elif raw == skill_results.NOT_STARTED:
        status = PROGRESS_NOT_STARTED
    else:
        status = PROGRESS_IN_PROGRESS
    detail = raw if raw in (skill_results.PENDING_EVALUATION, skill_results.EVALUATION_FAILED) else None
    return {"status": status, "score": skill.get("score"), "detail": detail}


def _frage_part(skill: dict) -> dict | None:
    if not skill.get("available"):
        return None
    if skill.get("submitted"):
        return {"status": PROGRESS_COMPLETED, "score": skill.get("score"), "detail": None}
    status = PROGRESS_IN_PROGRESS if skill.get("status") == skill_results.IN_PROGRESS else PROGRESS_NOT_STARTED
    return {"status": status, "score": None, "detail": None}


def published_videos(db: Session, lesson_id) -> dict[str, list[Video]]:
    """Published videos a student can actually play — one whose file is
    missing on disk is not shown, so it cannot block the competency."""
    from app.services.video.service import stored_file_path

    out: dict[str, list[Video]] = {}
    for video in db.scalars(
        select(Video).where(Video.lesson_id == lesson_id, Video.is_published.is_(True)).order_by(Video.order_index, Video.created_at)
    ):
        if stored_file_path(video.storage_key) is None:
            continue
        out.setdefault(video.competency or "EINFUEHRUNG", []).append(video)
    return out


def _video_part(videos: list[Video], progress: dict) -> dict:
    rows = [progress.get(v.id) for v in videos]
    if all(r is not None and r.completed for r in rows):
        status = PROGRESS_COMPLETED
    elif any(r is not None and (r.completed or r.last_position > 0) for r in rows):
        status = PROGRESS_IN_PROGRESS
    else:
        status = PROGRESS_NOT_STARTED
    return {"status": status, "score": None, "detail": None}


def _legacy_quiz_part(db: Session, user_id, lesson_id, quiz_type: str) -> dict | None:
    from app.services.lesson_progress.section_gate import SectionGateService

    gate = SectionGateService(db)
    if not gate._quiz_applicable(lesson_id, quiz_type):
        return None
    done = gate._quiz_submitted(user_id, lesson_id, quiz_type)
    return {"status": PROGRESS_COMPLETED if done else PROGRESS_NOT_STARTED, "score": None, "detail": None}


def _count(db: Session, model, lesson_id, *extra) -> int:
    return db.scalar(select(func.count()).select_from(model).where(model.lesson_id == lesson_id, *extra)) or 0


def content_counts(db: Session, lesson_id) -> dict:
    """Published content per competency (what an admin has filled in)."""
    resources: dict[str | None, int] = {}
    for comp, n in db.execute(
        select(LearningResource.competency, func.count())
        .where(LearningResource.lesson_id == lesson_id, LearningResource.is_published.is_(True))
        .group_by(LearningResource.competency)
    ):
        resources[comp] = n
    return {
        "resources": resources,
        "vocabulary": _count(db, Vocabulary, lesson_id, Vocabulary.is_published.is_(True)),
        "grammar": _count(db, Grammar, lesson_id, Grammar.is_published.is_(True)),
        "readings": _count(db, Reading, lesson_id, Reading.is_published.is_(True)),
        "listenings": _count(db, Listening, lesson_id, Listening.is_published.is_(True)),
    }


def snapshot_rows(db: Session, user_id, lesson_id) -> dict[str, StudentCompetencyProgress]:
    return {
        row.competency: row
        for row in db.scalars(
            select(StudentCompetencyProgress).where(StudentCompetencyProgress.user_id == user_id, StudentCompetencyProgress.lesson_id == lesson_id)
        )
    }


def compute(db: Session, user: User, lesson: Lesson) -> dict:
    """The real per-competency state of one lesson for one student — every
    competency, hidden ones included, no lock overlay (see present())."""
    course, _ = structure.lesson_level(db, lesson)
    competency_order = competency_order_for_level(course.level if course else None)
    stored_comps = {comp.kind: comp for comp in structure.ensure_competencies(db, lesson)}
    comps = [stored_comps[kind] for kind in competency_order]
    skills = skill_results.lesson_skill_results(db, user.id, lesson.id)["skills"]
    videos = published_videos(db, lesson.id)
    all_video_ids = [v.id for vs in videos.values() for v in vs]
    vprog = {
        row.video_id: row
        for row in db.scalars(select(VideoProgress).where(VideoProgress.user_id == user.id, VideoProgress.video_id.in_(all_video_ids)))
    } if all_video_ids else {}
    counts = content_counts(db, lesson.id)
    snap = snapshot_rows(db, user.id, lesson.id)

    extra_content = {
        "WORTSCHATZ": counts["vocabulary"],
        "GRAMMATIK": counts["grammar"],
        "LESEN": counts["readings"],
        "HOEREN": counts["listenings"],
    }

    items = []
    for comp in comps:
        kind = comp.kind
        parts = []
        if kind == "EINFUEHRUNG":
            frage = _frage_part(skills["frage"])
            if frage:
                parts.append(frage)
        if kind in SKILL_OF:
            part = _skill_part(skills[SKILL_OF[kind]])
            if part is None and kind in LEGACY_QUIZ_OF:
                part = _legacy_quiz_part(db, user.id, lesson.id, LEGACY_QUIZ_OF[kind])
            if part:
                parts.append(part)
        kind_videos = videos.get(kind, [])
        if kind_videos:
            parts.append(_video_part(kind_videos, vprog))

        tracked = bool(parts)
        resources = counts["resources"].get(kind, 0)
        has_body = bool((comp.body or "").strip())
        if kind == "ZUSAMMENFASSUNG":
            # the summary always has the lesson results to show once any
            # competency is tracked (it is last, so all others are in `items`)
            extra_content[kind] = sum(1 for i in items if i["tracked"] and i["is_published"])
        available = tracked or has_body or resources > 0 or extra_content.get(kind, 0) > 0
        row = snap.get(kind)
        if not available:
            progress_status = STATUS_NOT_AVAILABLE
        elif tracked:
            progress_status = aggregate([p["status"] for p in parts])
        else:
            progress_status = PROGRESS_COMPLETED if row and row.visited_at else PROGRESS_NOT_STARTED
        scores = [p["score"] for p in parts if p["score"] is not None]
        detail = next((p["detail"] for p in parts if p["detail"]), None)
        items.append(
            {
                "kind": kind,
                "position": len(items) + 1,
                "is_published": comp.is_published,
                "body": comp.body,
                "available": available,
                "tracked": tracked,
                "counts_for_completion": False,
                "status": progress_status,
                "progress_status": progress_status,
                "detail": detail,
                "score": round(sum(scores) / len(scores)) if scores else None,
                "videos": len(kind_videos),
                "resources": resources,
                "visited_at": row.visited_at if row else None,
                "completed_at": row.completed_at if row else None,
            }
        )

    visible = [c for c in items if c["is_published"]]
    counted = [c for c in visible if c["available"] and c["tracked"]]
    if not counted:
        counted = [c for c in visible if c["available"]]
    for c in counted:
        c["counts_for_completion"] = True
    done = sum(c["progress_status"] == PROGRESS_COMPLETED for c in counted)
    completed = bool(counted) and done == len(counted)
    if completed:
        lesson_status = PROGRESS_COMPLETED
    elif any(c["progress_status"] in (PROGRESS_IN_PROGRESS, PROGRESS_COMPLETED) for c in visible):
        lesson_status = PROGRESS_IN_PROGRESS
    else:
        lesson_status = PROGRESS_NOT_STARTED
    return {
        "lesson_id": lesson.id,
        "progress_status": lesson_status,
        "completed": completed,
        "competencies_total": len(counted),
        "competencies_completed": done,
        "percent": round(100 * done / len(counted)) if counted else 0,
        "competency_order": list(competency_order),
        "competencies": items,
    }


def present(state: dict, access: LessonAccess, *, include_hidden: bool = False) -> dict:
    """What a viewer gets: hidden competencies removed (unless admin
    preview) and `status` = "locked" while the lesson is locked;
    `progress_status` keeps the real state."""
    competencies = []
    for c in state["competencies"]:
        if not c["is_published"] and not include_hidden:
            continue
        item = dict(c)
        if not access.unlocked and item["status"] != STATUS_NOT_AVAILABLE:
            item["status"] = STATUS_LOCKED
        competencies.append(item)
    return {
        **state,
        "access": {"unlocked": access.unlocked, "reason": access.reason},
        "status": state["progress_status"] if access.unlocked else STATUS_LOCKED,
        "competencies": competencies,
    }


def lesson_state(db: Session, user: User, lesson: Lesson, *, include_hidden: bool = False, access: LessonAccess | None = None) -> dict:
    return present(compute(db, user, lesson), access or lesson_access(db, user, lesson), include_hidden=include_hidden)


def is_lesson_completed(db: Session, user_id, lesson_id) -> bool:
    user = db.get(User, user_id)
    lesson = db.get(Lesson, lesson_id)
    if user is None or lesson is None:
        return False
    return compute(db, user, lesson)["completed"]


def _lock_lesson(db: Session, user_id, lesson_id) -> None:
    """Serialises snapshot writes of one student's lesson until commit:
    every writer reads "no row yet" and inserts, so two concurrent requests
    (two competencies opened at once, a visit during a quiz submit) would
    both insert and one would die on the unique constraint."""
    db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"lms_progress:{user_id}:{lesson_id}"))))


def _progress_row(db: Session, user_id, lesson_id) -> StudentProgress:
    row = db.scalar(select(StudentProgress).where(StudentProgress.user_id == user_id, StudentProgress.lesson_id == lesson_id))
    if row is None:
        row = StudentProgress(user_id=user_id, lesson_id=lesson_id)
        db.add(row)
    return row


def persist(db: Session, user_id, lesson_id, state: dict) -> None:
    """Write the snapshot of a compute() result."""
    now = _now()
    snap = snapshot_rows(db, user_id, lesson_id)
    changed = False
    for c in state["competencies"]:
        status = c["progress_status"]
        if status == STATUS_NOT_AVAILABLE:
            continue
        row = snap.get(c["kind"])
        if row is None:
            if status == PROGRESS_NOT_STARTED:
                continue
            row = StudentCompetencyProgress(user_id=user_id, lesson_id=lesson_id, competency=c["kind"], status=PROGRESS_NOT_STARTED)
            db.add(row)
        if row.status != status or row.score != c["score"]:
            row.status = status
            row.score = c["score"]
            row.last_activity_at = now
            changed = True
        if status != PROGRESS_NOT_STARTED and row.started_at is None:
            row.started_at = now
        if status == PROGRESS_COMPLETED and row.completed_at is None:
            row.completed_at = now
        elif status != PROGRESS_COMPLETED:
            row.completed_at = None
    if state["progress_status"] != PROGRESS_NOT_STARTED or changed:
        progress = _progress_row(db, user_id, lesson_id)
        if progress.lesson_completed != state["completed"]:
            progress.lesson_completed = state["completed"]
            progress.completed_at = now if state["completed"] else None
            changed = True
        if changed or progress.last_activity_at is None:
            progress.last_activity_at = now
    else:
        # untouched lesson: keep an existing row's counts current, never
        # create a row (a progress row means "the student started it")
        progress = db.scalar(select(StudentProgress).where(StudentProgress.user_id == user_id, StudentProgress.lesson_id == lesson_id))
    if progress is not None:
        progress.competencies_total = state["competencies_total"]
        progress.competencies_completed = state["competencies_completed"]


def sync_lesson(db: Session, user_id, lesson_id) -> dict | None:
    """Recompute and persist one student's lesson snapshot; returns the
    state (all competencies) or None for an unknown user / lesson."""
    user = db.get(User, user_id)
    lesson = db.get(Lesson, lesson_id)
    if user is None or lesson is None:
        return None
    _lock_lesson(db, user.id, lesson.id)
    state = compute(db, user, lesson)
    persist(db, user.id, lesson.id, state)
    db.commit()
    if state["completed"]:
        # medals hang on real completion (never on opening a lesson); awarding is idempotent
        from app.services.achievements import evaluate_safely

        evaluate_safely(db, user.id)
    return state


def record_visit(db: Session, user: User, lesson: Lesson, kind: str) -> dict:
    """The student opened a competency: visited_at (first time) — completes
    only untracked text/resource competencies, never a lesson by itself."""
    _lock_lesson(db, user.id, lesson.id)
    now = _now()
    row = snapshot_rows(db, user.id, lesson.id).get(kind)
    if row is None:
        row = StudentCompetencyProgress(user_id=user.id, lesson_id=lesson.id, competency=kind, status=PROGRESS_NOT_STARTED)
        db.add(row)
    if row.visited_at is None:
        row.visited_at = now
    row.last_activity_at = now
    db.flush()
    return sync_lesson(db, user.id, lesson.id)


# ============================================================
# Level overview (snapshot based)
# ============================================================


def level_overview(db: Session, user: User, level: str, *, include_drafts: bool = False, detail: bool = True) -> dict:
    """Level summary + lesson cards. Card counts come from the snapshot;
    with `detail`, a lesson without one is computed read-only (nothing is
    written for lessons the student has not touched)."""
    level = structure.normalize_level(level)
    course = structure.level_course(db, level)
    module = structure.main_module(db, course) if course else None
    lessons = structure.level_lessons(db, module, published_only=not include_drafts)
    ids = [lesson.id for lesson in lessons]
    progress = {
        row.lesson_id: row
        for row in db.scalars(select(StudentProgress).where(StudentProgress.user_id == user.id, StudentProgress.lesson_id.in_(ids)))
    } if ids else {}
    comp_started: dict[UUID, int] = {}
    if ids:
        for lesson_id, n in db.execute(
            select(StudentCompetencyProgress.lesson_id, func.count())
            .where(
                StudentCompetencyProgress.user_id == user.id,
                StudentCompetencyProgress.lesson_id.in_(ids),
                StudentCompetencyProgress.status.in_((PROGRESS_COMPLETED, PROGRESS_IN_PROGRESS)),
            )
            .group_by(StudentCompetencyProgress.lesson_id)
        ):
            comp_started[lesson_id] = n
    video_lessons = set(db.scalars(select(Video.lesson_id).where(Video.lesson_id.in_(ids), Video.is_published.is_(True)))) if ids else set()

    cards = []
    for lesson in lessons:
        access = lesson_access(db, user, lesson)
        row = progress.get(lesson.id)
        needs_state = (level == "A1" and row is not None) or (detail and (row is None or row.competencies_total is None))
        state = compute(db, user, lesson) if needs_state else None
        completed = state["completed"] if state is not None else bool(row and row.lesson_completed)
        started = (
            state["progress_status"] != PROGRESS_NOT_STARTED
            if state is not None
            else completed or comp_started.get(lesson.id, 0) > 0
        )
        status = STATUS_LOCKED if not access.unlocked else (PROGRESS_COMPLETED if completed else (PROGRESS_IN_PROGRESS if started else PROGRESS_NOT_STARTED))
        if state is not None:
            comp_total, comp_completed = state["competencies_total"], state["competencies_completed"]
        elif row is not None and row.competencies_total is not None:
            comp_total, comp_completed = row.competencies_total, row.competencies_completed or 0
        else:
            comp_total, comp_completed = None, None
        if completed:
            percent = 100
        elif comp_total:
            percent = round(100 * min(comp_completed, comp_total) / comp_total)
        else:
            percent = 0
        cards.append(
            {
                "id": lesson.id,
                "number": lesson.number,
                "title": lesson.title,
                "description": lesson.description,
                "duration": lesson.duration,
                "is_published": lesson.is_published,
                "has_video": lesson.id in video_lessons,
                "status": status,
                "lock_reason": access.reason,
                "completed": completed,
                "percent": percent,
                "competencies_total": comp_total,
                "competencies_completed": comp_completed,
                "completed_at": row.completed_at if row else None,
                "last_activity_at": row.last_activity_at if row else None,
            }
        )

    published = [c for c in cards if c["is_published"]]
    completed_n = sum(c["completed"] for c in published)
    last = max((c for c in published if c["last_activity_at"]), key=lambda c: c["last_activity_at"], default=None)
    if last and not last["completed"] and last["status"] != STATUS_LOCKED:
        continue_card = last
    else:
        continue_card = next((c for c in published if not c["completed"] and c["status"] != STATUS_LOCKED), None)
    return {
        "level": level,
        "course_id": course.id if course else None,
        "title": course.title if course else level,
        "sequential_unlock": bool(course and course.sequential_unlock),
        "lessons_target": structure.LEVEL_LESSON_COUNTS[level],
        "lessons_published": len(published),
        "lessons_completed": completed_n,
        "percent": round(100 * completed_n / len(published)) if published else 0,
        "last_lesson_id": last["id"] if last else None,
        "continue_lesson_id": continue_card["id"] if continue_card else None,
        "sale": level_sale(user, level),
        "lessons": cards,
    }


def level_sale(user: User, level: str) -> dict:
    """What the student sees about buying a level: available or "Tez orada",
    already owned (purchase / legacy Premium / staff), the single-level offer
    and the packages that contain the level — all from the Angebote
    configuration (Admin -> Angebote), never from the client."""
    from app.services.vizu_pay import offers as offer_config
    from app.services.vizu_pay.access import has_premium_bypass, is_user_premium, owns_level

    available = offer_config.level_available(level)
    sales = offer_config.level_sales_enabled(level)
    listed = {o["code"]: o for o in offer_config.list_offers()}

    def brief(o: dict) -> dict:
        return {k: o[k] for k in ("code", "kind", "label", "levels", "available_levels", "sales_levels", "original_price", "sale_price",
                                  "discount_percent", "purchasable", "currency")}

    # legacy Premium opens a level only once it is approved for sale (see access.can_access_lesson)
    premium_counts = sales and is_user_premium(user)
    return {
        "available": available,
        "coming_soon": not available,
        # available (free lessons open) but not approved for sale yet: buying shows "Tez orada"
        "sales_enabled": bool(available and sales),
        "sales_closed": bool(available and not sales),
        "owned": bool(has_premium_bypass(user) or (available and (premium_counts or owns_level(user, level)))),
        "free_lessons": offer_config.free_lessons() if available else 0,
        "offer": brief(listed[level]) if level in listed else None,
        "packages": [brief(o) for o in listed.values() if o["kind"] == offer_config.KIND_PACKAGE and level in o["levels"] and o["purchasable"]],
    }
