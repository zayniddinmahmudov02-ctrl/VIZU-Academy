"""Per-lesson skill results: Lesen, Hören, Schreiben, Sprechen.

Overall = weighted average of the REQUIRED skills the lesson actually has.
Default (course.result_config NULL): equal weights, all four required —
(Lesen + Hören + Schreiben + Sprechen) / 4. Admins can change weights and
which skills are required per course (level). It is FINAL only when every
required skill is graded; until then an INTERIM value is reported with the
exact method — a skill that is not done yet is never counted as 0."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson_skill import SKILL_HOEREN, SKILL_LESEN
from app.models.speaking import Speaking
from app.models.student_speaking import StudentSpeaking
from app.models.student_writing import StudentWriting
from app.models.writing import Writing
from app.services.lesson_skills import skill_tests as tests

NOT_AVAILABLE = "not_available"
NOT_STARTED = "not_started"
IN_PROGRESS = "in_progress"
PENDING_EVALUATION = "pending_evaluation"
EVALUATION_FAILED = "evaluation_failed"
COMPLETED = "completed"

SUBMISSION_STATUS = {
    None: NOT_STARTED,
    "DRAFT": IN_PROGRESS,
    "NEEDS_REVISION": IN_PROGRESS,
    "SUBMITTED": PENDING_EVALUATION,
    "EVALUATING": PENDING_EVALUATION,
    "EVALUATION_FAILED": EVALUATION_FAILED,
    "GRADED": COMPLETED,
}


SKILL_KEYS = ("lesen", "hoeren", "schreiben", "sprechen")
DEFAULT_RESULT_CONFIG = {"weights": {k: 25 for k in SKILL_KEYS}, "required": list(SKILL_KEYS)}


def _mean(values: list[int]) -> int | None:
    return tests.round_half_up(sum(values) / len(values)) if values else None


def validate_result_config(config) -> dict:
    """{"weights": {skill: 0-100}, "required": [skill, ...]}; raises ValueError."""
    if config is None:
        return {"weights": dict(DEFAULT_RESULT_CONFIG["weights"]), "required": list(SKILL_KEYS)}
    if not isinstance(config, dict):
        raise ValueError("result_config must be an object")
    weights = config.get("weights") or {}
    required = config.get("required")
    if not isinstance(weights, dict) or not isinstance(required, list):
        raise ValueError("result_config needs 'weights' and 'required'")
    clean_w = {}
    for k in SKILL_KEYS:
        try:
            w = int(weights.get(k, 25))
        except (TypeError, ValueError):
            raise ValueError(f"weight of {k} must be a number") from None
        if not 0 <= w <= 100:
            raise ValueError(f"weight of {k} must be 0-100")
        clean_w[k] = w
    clean_r = [k for k in SKILL_KEYS if k in required]
    if not clean_r:
        raise ValueError("at least one skill must be required")
    if any(clean_w[k] == 0 for k in clean_r):
        raise ValueError("a required skill needs a weight above 0")
    return {"weights": clean_w, "required": clean_r}


def lesson_result_config(db: Session, lesson_id: UUID) -> dict:
    from app.models.course import Course
    from app.models.lesson import Lesson
    from app.models.module import Module

    lesson = db.get(Lesson, lesson_id)
    module = db.get(Module, lesson.module_id) if lesson else None
    course = db.get(Course, module.course_id) if module else None
    try:
        return validate_result_config(course.result_config if course else None)
    except ValueError:
        return validate_result_config(None)


def _lesen(db: Session, user_id: UUID, lesson_id: UUID) -> dict:
    if not tests.lesen_questions(db, lesson_id):
        return {"available": False, "status": NOT_AVAILABLE, "score": None}
    s = tests.summary(tests.attempts(db, user_id, lesson_id, SKILL_LESEN))
    status = COMPLETED if s["best_score"] is not None else (IN_PROGRESS if s["in_progress_attempt_id"] else NOT_STARTED)
    return {
        "available": True,
        "status": status,
        "score": s["best_score"],
        "attempts": s["attempts_count"],
        "last_score": s["last_score"],
        "submitted_at": s["last_submitted_at"],
        "can_retry": True,
    }


def _hoeren(db: Session, user_id: UUID, lesson_id: UUID) -> dict:
    listenings = [lst for lst in tests.lesson_listenings(db, lesson_id) if lst.questions and tests.has_audio(lst)]
    if not listenings:
        return {"available": False, "status": NOT_AVAILABLE, "score": None}
    tasks, bests, attempts_total, last = [], [], 0, None
    for lst in listenings:
        s = tests.summary(tests.attempts(db, user_id, lesson_id, SKILL_HOEREN, lst.id))
        attempts_total += s["attempts_count"]
        if s["best_score"] is not None:
            bests.append(s["best_score"])
        if s["last_submitted_at"] and (last is None or s["last_submitted_at"] > last):
            last = s["last_submitted_at"]
        tasks.append({"id": lst.id, "title": lst.title, "best_score": s["best_score"], "attempts": s["attempts_count"]})
    done = len(bests) == len(listenings)
    return {
        "available": True,
        "status": COMPLETED if done else (IN_PROGRESS if bests or attempts_total else NOT_STARTED),
        "score": _mean(bests),
        "interim": not done and bool(bests),
        "attempts": attempts_total,
        "submitted_at": last,
        "tasks": tasks,
        "can_retry": True,
    }


def _graded_tasks(task_rows, subs_by_task: dict) -> dict:
    if not task_rows:
        return {"available": False, "status": NOT_AVAILABLE, "score": None}
    tasks, scores, statuses = [], [], []
    submitted_at = evaluated_at = None
    for task in task_rows:
        sub = subs_by_task.get(str(task.id))
        state = SUBMISSION_STATUS.get(sub.status if sub else None, IN_PROGRESS)
        statuses.append(state)
        if state == COMPLETED and sub.score is not None:
            scores.append(max(0, min(100, sub.score)))
        if sub and sub.submitted_at and (submitted_at is None or sub.submitted_at > submitted_at):
            submitted_at = sub.submitted_at
        if sub and sub.evaluated_at and (evaluated_at is None or sub.evaluated_at > evaluated_at):
            evaluated_at = sub.evaluated_at
        attempts_used = (sub.attempt_count or (1 if sub and sub.submitted_at else 0)) if sub else 0
        tasks.append(
            {
                "id": task.id,
                "title": task.title,
                "status": state,
                "score": sub.score if (sub and state == COMPLETED) else None,
                "attempts": attempts_used,
                "max_attempts": task.max_attempts,
                "ai_evaluation": task.ai_evaluation_enabled,
                "can_resubmit": bool(task.ai_evaluation_enabled and state in (COMPLETED, EVALUATION_FAILED, IN_PROGRESS, NOT_STARTED) and attempts_used < task.max_attempts),
            }
        )
    if all(s == COMPLETED for s in statuses):
        status = COMPLETED
    elif any(s == PENDING_EVALUATION for s in statuses):
        status = PENDING_EVALUATION
    elif any(s == EVALUATION_FAILED for s in statuses):
        status = EVALUATION_FAILED
    elif all(s == NOT_STARTED for s in statuses):
        status = NOT_STARTED
    else:
        status = IN_PROGRESS
    return {
        "available": True,
        "status": status,
        "score": _mean(scores),
        "interim": status != COMPLETED and bool(scores),
        "attempts": sum(t["attempts"] for t in tasks),
        "submitted_at": submitted_at,
        "evaluated_at": evaluated_at,
        "tasks": tasks,
        "can_retry": any(t["can_resubmit"] for t in tasks),
    }


def _schreiben(db: Session, user_id: UUID, lesson_id: UUID) -> dict:
    rows = list(db.scalars(select(Writing).where(Writing.lesson_id == lesson_id, Writing.is_published.is_(True)).order_by(Writing.order_index)))
    subs = {
        str(s.writing_id): s
        for s in db.scalars(select(StudentWriting).where(StudentWriting.user_id == user_id, StudentWriting.writing_id.in_([w.id for w in rows])))
    } if rows else {}
    return _graded_tasks(rows, subs)


def _sprechen(db: Session, user_id: UUID, lesson_id: UUID) -> dict:
    rows = list(db.scalars(select(Speaking).where(Speaking.lesson_id == lesson_id, Speaking.is_published.is_(True)).order_by(Speaking.order_index)))
    subs = {
        str(s.speaking_id): s
        for s in db.scalars(select(StudentSpeaking).where(StudentSpeaking.user_id == user_id, StudentSpeaking.speaking_id.in_([s.id for s in rows])))
    } if rows else {}
    return _graded_tasks(rows, subs)


SKILL_NAMES = {"lesen": "Lesen", "hoeren": "Hören", "schreiben": "Schreiben", "sprechen": "Sprechen"}


def overall(skills: dict, config: dict | None = None) -> dict:
    config = config or validate_result_config(None)
    weights, required_keys = config["weights"], config["required"]
    required = {k: v for k, v in skills.items() if v["available"] and k in required_keys}
    base = {"weights": {k: weights[k] for k in required}, "required": list(required)}
    if not required:
        return {"status": NOT_AVAILABLE, "score": None, "method": None, "graded_skills": 0, "required_skills": 0, **base}
    graded = {k: v for k, v in required.items() if v["status"] == COMPLETED and v["score"] is not None}
    n, m = len(graded), len(required)
    equal = len({weights[k] for k in required}) == 1

    def weighted(items: dict) -> int:
        total = sum(weights[k] for k in items)
        return tests.round_half_up(sum(v["score"] * weights[k] for k, v in items.items()) / total)

    def formula(items) -> str:
        names = [SKILL_NAMES.get(k, k) for k in items]
        if equal:
            return f"({' + '.join(names)}) / {len(names)}"
        total = sum(weights[k] for k in items)
        return f"({' + '.join(f'{SKILL_NAMES.get(k, k)}×{weights[k]}' for k in items)}) / {total}"

    if n == m:
        return {"status": "final", "score": weighted(graded), "method": formula(required), "graded_skills": n, "required_skills": m, **base}
    if n == 0:
        return {"status": NOT_STARTED, "score": None, "method": None, "graded_skills": 0, "required_skills": m, **base}
    return {
        "status": "interim",
        "score": weighted(graded),
        "method": f"interim: {formula(graded)} — {n} of {m} required skills graded",
        "graded_skills": n,
        "required_skills": m,
        **base,
    }


def lesson_skill_results(db: Session, user_id: UUID, lesson_id: UUID) -> dict:
    skills = {
        "lesen": _lesen(db, user_id, lesson_id),
        "hoeren": _hoeren(db, user_id, lesson_id),
        "schreiben": _schreiben(db, user_id, lesson_id),
        "sprechen": _sprechen(db, user_id, lesson_id),
    }
    return {"lesson_id": lesson_id, "skills": skills, "overall": overall(skills, lesson_result_config(db, lesson_id))}
