"""VIZU-Multilevel attempt lifecycle: server-authoritative timing, the
Lesen -> Hören -> Schreiben -> Sprechen flow, per-competency results, the
overall level, the attempt limit (MAX_ATTEMPTS per student, each attempt
independent) and the stored Gesamtergebnis used for "Bestes Ergebnis".

Everything time- or flow-related is decided HERE, from timestamps the
backend stamps itself — the client's clock and navigation state are never
trusted (a reload cannot restart the 20-minute timer, a skipped step
cannot be submitted out of order, a late submission cannot add answers)."""

import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.vizu_multilevel_attempt import MAX_ATTEMPTS, STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMultilevelAttempt
from app.models.vizu_multilevel_content import CEFR_LEVELS, SKILL_HOEREN, SKILL_LESEN, VizuMultilevelQuestion, VizuMultilevelTask
from app.models.vizu_multilevel_discarded import REASON_BELOW_A1, VizuMultilevelDiscardedAttempt
from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingSubmission, VizuMultilevelSpeakingTask
from app.models.vizu_multilevel_writing import VizuMultilevelWritingSubmission, VizuMultilevelWritingTask

# Order of the flow — this is also the order competencies are unlocked in.
SKILLS = ["lesen", "hoeren", "schreiben", "sprechen"]

SECTION_SECONDS = 20 * 60  # each competency: 20 minutes -> 100 minutes total
# Network latency / the student clicking "finish" at 00:00 — a submission
# arriving this long after the deadline still counts; later ones are
# treated as unanswered (0 points).
GRACE_SECONDS = 30
# An in-progress attempt untouched for this long is considered abandoned.
ABANDON_AFTER = timedelta(hours=3)

# Section statuses
LOCKED = "LOCKED"
AVAILABLE = "AVAILABLE"
RUNNING = "RUNNING"
SUBMITTED = "SUBMITTED"

# Per-competency result statuses
R_NO_CONTENT = "NO_CONTENT"
R_NOT_SUBMITTED = "NOT_SUBMITTED"
R_PENDING_REVIEW = "PENDING_REVIEW"
R_GRADED = "GRADED"

# Overall result statuses
O_NO_CONTENT = "NO_CONTENT"
O_IN_PROGRESS = "IN_PROGRESS"
O_PENDING_REVIEW = "PENDING_REVIEW"
O_FINAL = "FINAL"
O_BELOW_A1 = "BELOW_A1"

# Result level of an attempt below A1 ("Niveau unter A1"). Internal value;
# the frontend/certificate show it as "unter A1".
LEVEL_BELOW_A1 = "BELOW_A1"
# Ordering for "best level" / sorting: below A1 < A1 < ... < C1.
RESULT_LEVEL_ORDER = [LEVEL_BELOW_A1, *CEFR_LEVELS]
REASON_NO_CONTENT = "NO_CONTENT"


class SectionFlowError(Exception):
    """A request violates the competency flow (wrong order, unknown skill,
    attempt already finished). `code` is machine-readable for the API."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Attempts
# ============================================================


def get_own_attempt(db: Session, user_id: UUID, attempt_id: UUID) -> VizuMultilevelAttempt | None:
    # Owner-scoped lookup — a guessed/foreign attempt id 404s exactly like
    # a nonexistent one, never leaking another student's attempt (IDOR-safe).
    return db.scalar(
        select(VizuMultilevelAttempt).where(
            VizuMultilevelAttempt.id == attempt_id, VizuMultilevelAttempt.user_id == user_id
        )
    )


def list_attempts(db: Session, user_id: UUID) -> list[VizuMultilevelAttempt]:
    """The student's own attempts, Versuch 1, 2, 3 (owner-scoped)."""
    return list(
        db.scalars(
            select(VizuMultilevelAttempt)
            .where(VizuMultilevelAttempt.user_id == user_id)
            .order_by(VizuMultilevelAttempt.attempt_number, VizuMultilevelAttempt.started_at)
        )
    )


def get_current_attempt(db: Session, user_id: UUID) -> VizuMultilevelAttempt | None:
    """The student's latest attempt (the running one, if any)."""
    return db.scalar(
        select(VizuMultilevelAttempt)
        .where(VizuMultilevelAttempt.user_id == user_id)
        .order_by(VizuMultilevelAttempt.attempt_number.desc(), VizuMultilevelAttempt.started_at.desc())
        .limit(1)
    )


def create_attempt(db: Session, user_id: UUID) -> VizuMultilevelAttempt:
    """Starts Versuch n+1. Rules (SectionFlowError codes):
    * ATTEMPT_ALREADY_EXISTS — an attempt is still running: finish it first
      (it counts as one of the MAX_ATTEMPTS; there is no way to skip it).
    * MAX_ATTEMPTS_REACHED — the student already used all MAX_ATTEMPTS.
    Earlier attempts are never touched. A transaction-scoped advisory lock per
    user (plus the unique (user_id, attempt_number) constraint) makes two
    simultaneous requests unable to create two attempts."""
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"vizu-attempt:{user_id}"})
    existing = list_attempts(db, user_id)
    if any(a.status == STATUS_IN_PROGRESS for a in existing):
        db.rollback()  # releases the advisory lock
        raise SectionFlowError("ATTEMPT_ALREADY_EXISTS")
    if len(existing) >= MAX_ATTEMPTS:
        db.rollback()
        raise SectionFlowError("MAX_ATTEMPTS_REACHED")

    number = max((a.attempt_number or 0 for a in existing), default=0) + 1
    attempt = VizuMultilevelAttempt(user_id=user_id, status=STATUS_IN_PROGRESS, attempt_number=number)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


# ============================================================
# Server-authoritative section timing / flow
# ============================================================


def _started_at(attempt: VizuMultilevelAttempt, skill: str) -> datetime | None:
    return getattr(attempt, f"{skill}_started_at")


def submitted_at(attempt: VizuMultilevelAttempt, skill: str) -> datetime | None:
    return getattr(attempt, f"{skill}_submitted_at")


def is_submitted(attempt: VizuMultilevelAttempt, skill: str) -> bool:
    return submitted_at(attempt, skill) is not None


def _check_skill(skill: str) -> None:
    if skill not in SKILLS:
        raise SectionFlowError("UNKNOWN_SKILL")


def _check_previous_submitted(attempt: VizuMultilevelAttempt, skill: str) -> None:
    index = SKILLS.index(skill)
    if index > 0 and not is_submitted(attempt, SKILLS[index - 1]):
        raise SectionFlowError("PREVIOUS_SECTION_NOT_SUBMITTED")


def _deadline(attempt: VizuMultilevelAttempt, skill: str) -> datetime | None:
    started = _started_at(attempt, skill)
    return started + timedelta(seconds=SECTION_SECONDS) if started else None


def start_section(db: Session, attempt: VizuMultilevelAttempt, skill: str) -> dict:
    """Idempotent: the first call stamps the start time server-side; every
    later call (reload, second tab) returns the SAME deadline."""
    _check_skill(skill)
    if attempt.status != STATUS_IN_PROGRESS:
        raise SectionFlowError("ATTEMPT_NOT_IN_PROGRESS")
    _check_previous_submitted(attempt, skill)

    if _started_at(attempt, skill) is None and not is_submitted(attempt, skill):
        setattr(attempt, f"{skill}_started_at", _now())
        db.commit()
        db.refresh(attempt)
    return section_timing(attempt, skill)


def ensure_section_open(db: Session, attempt: VizuMultilevelAttempt, skill: str) -> bool:
    """Gate for any write inside a competency (answers, drafts, audio).
    Returns True if the section is open for writing, False if its time is
    up (deadline + grace). Raises SectionFlowError for flow violations."""
    _check_skill(skill)
    if attempt.status != STATUS_IN_PROGRESS:
        raise SectionFlowError("ATTEMPT_NOT_IN_PROGRESS")
    if is_submitted(attempt, skill):
        raise SectionFlowError("SECTION_ALREADY_SUBMITTED")
    _check_previous_submitted(attempt, skill)

    if _started_at(attempt, skill) is None:
        setattr(attempt, f"{skill}_started_at", _now())
        db.commit()
        db.refresh(attempt)
        return True
    return _now() <= _deadline(attempt, skill) + timedelta(seconds=GRACE_SECONDS)


# Every competency needs at least this many answered questions/tasks before
# it can be submitted (fewer if the competency has fewer items). Not "correct"
# — answered. The only exception is a section whose time is up.
MIN_ANSWERS = 5


def min_answers_required(total_items: int) -> int:
    return min(MIN_ANSWERS, max(total_items, 0))


def ensure_attempt_active(attempt: VizuMultilevelAttempt) -> None:
    """A finished attempt can never be submitted to again."""
    if attempt.status != STATUS_IN_PROGRESS:
        raise SectionFlowError("ATTEMPT_ALREADY_COMPLETED")


def check_min_answers(attempt: VizuMultilevelAttempt, skill: str, answered: int, total: int) -> None:
    if answered < min_answers_required(total) and not section_expired(attempt, skill):
        raise SectionFlowError("MIN_ANSWERS_REQUIRED")


def missing_sections(attempt: VizuMultilevelAttempt) -> list[str]:
    return [s for s in SKILLS if not is_submitted(attempt, s)]


def availability(db: Session) -> dict:
    """How many items each competency has (no content details)."""
    counts = {
        "lesen": _published_question_count(db, SKILL_LESEN)[0],
        "hoeren": _published_question_count(db, SKILL_HOEREN)[0],
        "schreiben": _writing_totals(db)[0],
        "sprechen": _speaking_totals(db)[0],
    }
    return {**counts, "min_answers": MIN_ANSWERS, "available": any(counts.values())}


def ensure_section_open_strict(db: Session, attempt: VizuMultilevelAttempt, skill: str) -> None:
    """Like ensure_section_open, but a closed window is an error too."""
    if not ensure_section_open(db, attempt, skill):
        raise SectionFlowError("SECTION_TIME_UP")


def section_expired(attempt: VizuMultilevelAttempt, skill: str) -> bool:
    """True once the nominal 20 minutes are over (no grace)."""
    deadline = _deadline(attempt, skill)
    return deadline is not None and _now() >= deadline


def begin_submission(db: Session, attempt: VizuMultilevelAttempt, skill: str) -> bool:
    """Validates a competency's final submission. Returns True if answers
    arrived in time (and may be graded), False if the window has closed —
    in which case the caller must grade as if nothing was answered. A
    repeat submission is the caller's job to detect first (is_submitted)."""
    return ensure_section_open(db, attempt, skill)


def mark_submitted(db: Session, attempt: VizuMultilevelAttempt, skill: str) -> None:
    setattr(attempt, f"{skill}_submitted_at", _now())
    db.commit()
    db.refresh(attempt)


def section_timing(attempt: VizuMultilevelAttempt, skill: str) -> dict:
    now = _now()
    started = _started_at(attempt, skill)
    deadline = _deadline(attempt, skill)
    submitted = is_submitted(attempt, skill)
    remaining = None
    if started is not None and not submitted:
        remaining = max(0, int((deadline - now).total_seconds()))
    return {
        "skill": skill,
        "started_at": started,
        "deadline_at": deadline,
        "seconds_remaining": remaining,
        "duration_seconds": SECTION_SECONDS,
        "server_now": now,
        "submitted": submitted,
    }


def get_state(attempt: VizuMultilevelAttempt) -> dict:
    sections = []
    next_skill = None
    for skill in SKILLS:
        timing = section_timing(attempt, skill)
        if timing["submitted"]:
            status = SUBMITTED
        elif timing["started_at"] is not None:
            status = RUNNING
        elif next_skill is None:
            status = AVAILABLE
        else:
            status = LOCKED
        if status in (AVAILABLE, RUNNING) and next_skill is None:
            next_skill = skill
        sections.append({**timing, "status": status})
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "next_skill": next_skill,
        "server_now": _now(),
        "sections": sections,
    }


# ============================================================
# Results
# ============================================================


def _published_question_count(db: Session, skill_const: str) -> tuple[int, float]:
    query = (
        select(VizuMultilevelQuestion.points)
        .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
        .where(VizuMultilevelTask.skill == skill_const, VizuMultilevelTask.is_published.is_(True))
    )
    if skill_const == SKILL_LESEN:
        query = query.where(VizuMultilevelQuestion.is_active.is_(True))
    rows = db.execute(query).all()
    return len(rows), float(sum(r[0] for r in rows))


def _writing_totals(db: Session) -> tuple[int, int]:
    tasks = list(db.scalars(select(VizuMultilevelWritingTask).where(VizuMultilevelWritingTask.is_active.is_(True))))
    return len(tasks), sum(t.points for t in tasks)


def _speaking_totals(db: Session, attempt_id: UUID | None = None) -> tuple[int, int]:
    """Sprechen = the student's 5 ladder Aufgaben (not the whole 25-variant bank)."""
    from app.services.vizu_multilevel import sprechen_service

    tasks = sprechen_service.attempt_tasks(db, attempt_id) if attempt_id else sprechen_service.assigned_tasks(db)
    return len(tasks), sum(t.points for t in tasks)


def _answered_max_points(db: Session, attempt_id: UUID, skill_const: str) -> float:
    """Max points of the questions this attempt was actually graded on
    (stable even if the admin edits content later)."""
    from app.models.vizu_multilevel_content import VizuMultilevelAnswer

    rows = db.execute(
        select(VizuMultilevelQuestion.points)
        .select_from(VizuMultilevelAnswer)
        .join(VizuMultilevelQuestion, VizuMultilevelAnswer.question_id == VizuMultilevelQuestion.id)
        .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
        .where(VizuMultilevelAnswer.attempt_id == attempt_id, VizuMultilevelTask.skill == skill_const)
    ).all()
    return float(sum(r[0] for r in rows))


def _graded_complete_writing(db: Session, attempt_id: UUID) -> bool:
    """True once every ACTIVE task either has a graded submission or was
    never answered at all (an unanswered task is simply 0 points — a
    teacher cannot grade nothing, so it must not block the result)."""
    tasks = list(db.scalars(select(VizuMultilevelWritingTask).where(VizuMultilevelWritingTask.is_active.is_(True))))
    subs = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelWritingSubmission).where(VizuMultilevelWritingSubmission.attempt_id == attempt_id)
        )
    }
    for task in tasks:
        sub = subs.get(task.id)
        if sub is not None and sub.content.strip() and sub.teacher_score is None:
            return False
    return True


def _graded_complete_speaking(db: Session, attempt_id: UUID) -> bool:
    from app.services.vizu_multilevel import sprechen_service

    return sprechen_service.is_graded_complete(db, attempt_id)


def _percentage(raw: float | None, maximum: float | None) -> float | None:
    if raw is None or not maximum:
        return None
    return round(raw / maximum * 100, 1)


def competency_results(db: Session, attempt: VizuMultilevelAttempt) -> list[dict]:
    out = []

    # Lesen / Hören — auto-graded at submit time.
    for skill, const, score, level in (
        ("lesen", SKILL_LESEN, attempt.lesen_score, attempt.lesen_level),
        ("hoeren", SKILL_HOEREN, attempt.hoeren_score, attempt.hoeren_level),
    ):
        count, live_max = _published_question_count(db, const)
        submitted = is_submitted(attempt, skill)
        if submitted:
            maximum = _answered_max_points(db, attempt.id, const) or live_max
        else:
            maximum = live_max
        has_content = count > 0 or (submitted and maximum > 0)
        if not has_content:
            out.append(_competency(skill, R_NO_CONTENT, None, None, None))
        elif not submitted:
            out.append(_competency(skill, R_NOT_SUBMITTED, None, maximum, None))
        else:
            out.append(_competency(skill, R_GRADED, float(score or 0), maximum, level))

    # Schreiben — teacher-graded.
    task_count, max_points = _writing_totals(db)
    if task_count == 0:
        out.append(_competency("schreiben", R_NO_CONTENT, None, None, None))
    elif not is_submitted(attempt, "schreiben"):
        out.append(_competency("schreiben", R_NOT_SUBMITTED, None, max_points, None))
    elif _graded_complete_writing(db, attempt.id):
        out.append(_competency("schreiben", R_GRADED, float(attempt.schreiben_score or 0), max_points, attempt.schreiben_level))
    else:
        out.append(_competency("schreiben", R_PENDING_REVIEW, attempt.schreiben_score, max_points, None))

    # Sprechen — AI-evaluated (teacher may override).
    task_count, max_points = _speaking_totals(db, attempt.id)
    if task_count == 0:
        out.append(_competency("sprechen", R_NO_CONTENT, None, None, None))
    elif not is_submitted(attempt, "sprechen"):
        out.append(_competency("sprechen", R_NOT_SUBMITTED, None, max_points, None))
    elif _graded_complete_speaking(db, attempt.id):
        out.append(_competency("sprechen", R_GRADED, float(attempt.sprechen_score or 0), max_points, attempt.sprechen_level))
    else:
        out.append(_competency("sprechen", R_PENDING_REVIEW, attempt.sprechen_score, max_points, None))

    return out


def _competency(skill: str, status: str, raw: float | None, maximum: float | None, level: str | None) -> dict:
    return {
        "skill": skill,
        "status": status,
        "raw_score": raw,
        "max_score": maximum,
        "percentage": _percentage(raw, maximum),
        "level": level,
    }


def overall_result(competencies: list[dict]) -> dict:
    """Overall level = the LOWEST level among the competencies that have
    content (the weakest competency caps the overall result). A graded
    competency that did not confirm even A1 makes the whole result
    "below A1". Never invents a level while required data is missing."""
    considered = [c for c in competencies if c["status"] != R_NO_CONTENT]
    if not considered:
        return {"status": O_NO_CONTENT, "level": None}

    if any(c["status"] == R_GRADED and c["level"] is None for c in considered):
        return {"status": O_BELOW_A1, "level": None}
    if any(c["status"] == R_NOT_SUBMITTED for c in considered):
        return {"status": O_IN_PROGRESS, "level": None}
    if any(c["status"] == R_PENDING_REVIEW for c in considered):
        return {"status": O_PENDING_REVIEW, "level": None}

    lowest = min(CEFR_LEVELS.index(c["level"]) for c in considered)
    return {"status": O_FINAL, "level": CEFR_LEVELS[lowest]}


def build_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    competencies = competency_results(db, attempt)
    return {
        "attempt_id": attempt.id,
        "attempt_number": attempt.attempt_number,
        "max_attempts": MAX_ATTEMPTS,
        "competencies": competencies,
        "overall": overall_result(competencies),
    }


def round_half_up(value: float) -> int:
    """Same rounding as the result page (JS Math.round), not banker's rounding."""
    return int(math.floor(value + 0.5))


def gesamtergebnis(competencies: list[dict]) -> int:
    """Gesamtergebnis 0-100 = the average of the graded competency percentages,
    exactly as the result page and the certificate show it (unchanged rule)."""
    graded = [float(c["percentage"]) for c in competencies if c["status"] == R_GRADED and c.get("percentage") is not None]
    total = round_half_up(sum(graded) / len(graded)) if graded else 0
    return max(0, min(100, total))


def is_result_final(result: dict) -> bool:
    """Every competency with content is graded, and there is a level (A1-C1)
    or the overall result is below A1. Pending reviews -> not final yet."""
    considered = [c for c in result["competencies"] if c["status"] != R_NO_CONTENT]
    if not considered or any(c["status"] != R_GRADED for c in considered):
        return False
    return result["overall"]["status"] in (O_FINAL, O_BELOW_A1)


def result_level(attempt: VizuMultilevelAttempt) -> str | None:
    """A1..C1, BELOW_A1, or None (no final result yet / no result at all)."""
    if attempt.result_score is None:
        return None
    if attempt.overall_level:
        return attempt.overall_level
    return LEVEL_BELOW_A1 if attempt.discarded_reason == REASON_BELOW_A1 else None


def sync_result_score(db: Session, attempt: VizuMultilevelAttempt, result: dict | None = None) -> None:
    """Stores the attempt's final Gesamtergebnis (or NULL while not final).
    Only ever derived from build_result — no separate score calculation."""
    score = None
    if attempt.status == STATUS_COMPLETED and attempt.discarded_reason != REASON_NO_CONTENT:
        result = result or build_result(db, attempt)
        if is_result_final(result):
            score = gesamtergebnis(result["competencies"])
    if attempt.result_score != score:
        attempt.result_score = score
        db.commit()
        db.refresh(attempt)


def sync_missing_scores(db: Session, attempts: list[VizuMultilevelAttempt]) -> None:
    """Lazily fills result_score for finished attempts that predate the column
    or are still waiting for a review (cheap no-op once everything is final)."""
    for attempt in attempts:
        if attempt.status == STATUS_COMPLETED and attempt.result_score is None and attempt.discarded_reason != REASON_NO_CONTENT:
            sync_result_score(db, attempt)


def best_attempt(attempts: list[VizuMultilevelAttempt]) -> VizuMultilevelAttempt | None:
    """Highest Gesamtergebnis over all FINAL attempts (not just the last);
    on a tie the most recently completed one."""
    final = [a for a in attempts if a.result_score is not None]
    if not final:
        return None
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    return max(final, key=lambda a: (a.result_score, a.completed_at or epoch))


def attempt_summary_item(attempt: VizuMultilevelAttempt) -> dict:
    return {
        "id": attempt.id,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "result_score": attempt.result_score,
        "result_level": result_level(attempt),
        "certificate_available": attempt.result_score is not None and result_level(attempt) is not None,
    }


def my_results(db: Session, user_id: UUID) -> dict:
    """The student's own attempts + best result. Never another student's."""
    attempts = list_attempts(db, user_id)
    sync_missing_scores(db, attempts)
    best = best_attempt(attempts)
    running = next((a for a in attempts if a.status == STATUS_IN_PROGRESS), None)
    used = len(attempts)
    return {
        "max_attempts": MAX_ATTEMPTS,
        "attempts_used": used,
        "attempts_remaining": max(0, MAX_ATTEMPTS - used),
        "can_start": running is None and used < MAX_ATTEMPTS,
        "in_progress_attempt_id": running.id if running else None,
        "attempts": [attempt_summary_item(a) for a in attempts],
        "best": attempt_summary_item(best) if best else None,
    }


# ============================================================
# Completion / below-A1 / abandonment
# ============================================================


def _discard(db: Session, attempt: VizuMultilevelAttempt, reason: str) -> None:
    """Marks a finished attempt's result as having no CEFR level (below A1).
    The attempt stays a full result ("Niveau unter A1", with certificate);
    the anonymous tally row is still written so the admin statistics keep
    counting exactly as before."""
    if attempt.discarded_reason is not None:
        return
    db.add(
        VizuMultilevelDiscardedAttempt(
            reason=reason,
            started_at=attempt.started_at,
            lesen_score=attempt.lesen_score,
            hoeren_score=attempt.hoeren_score,
            schreiben_score=attempt.schreiben_score,
            sprechen_score=attempt.sprechen_score,
        )
    )
    attempt.discarded_reason = reason
    attempt.status = STATUS_COMPLETED
    attempt.completed_at = attempt.completed_at or _now()
    db.commit()
    db.refresh(attempt)


def complete_attempt(db: Session, user_id: UUID, attempt_id: UUID) -> dict | None:
    """Finishes the attempt. Returns None for an unknown/foreign id.
    Otherwise `{"saved": bool, "result": {...}}`: every result is kept,
    below A1 included; only an attempt without any content is not a result."""
    attempt = get_own_attempt(db, user_id, attempt_id)
    if attempt is None:
        return None

    if attempt.status == STATUS_COMPLETED:
        raise SectionFlowError("ATTEMPT_ALREADY_COMPLETED")

    if missing_sections(attempt):
        raise SectionFlowError("SECTIONS_NOT_SUBMITTED")

    result = build_result(db, attempt)
    overall = result["overall"]

    if overall["status"] == O_NO_CONTENT:
        attempt.discarded_reason = REASON_NO_CONTENT
        attempt.status = STATUS_COMPLETED
        attempt.completed_at = _now()
        db.commit()
        return {"saved": False, "result": result}

    if overall["status"] == O_BELOW_A1:
        _discard(db, attempt, REASON_BELOW_A1)
        sync_result_score(db, attempt, result)
        return {"saved": True, "result": result}

    attempt.status = STATUS_COMPLETED
    attempt.completed_at = _now()
    attempt.overall_level = overall["level"]
    db.commit()
    db.refresh(attempt)
    sync_result_score(db, attempt, result)
    return {"saved": True, "result": result}


def refresh_overall(db: Session, attempt: VizuMultilevelAttempt) -> None:
    """Called after a teacher/AI grades Schreiben/Sprechen: re-derives the
    overall result of an already-completed attempt. Becomes final (level
    set) when everything is graded; is marked below A1 if it turns out so.
    The stored Gesamtergebnis follows every (re)grade."""
    if attempt.status != STATUS_COMPLETED or attempt.discarded_reason == REASON_NO_CONTENT:
        return
    result = build_result(db, attempt)
    overall = result["overall"]
    if attempt.discarded_reason is None:
        if overall["status"] == O_BELOW_A1:
            _discard(db, attempt, REASON_BELOW_A1)
        elif overall["status"] == O_FINAL:
            attempt.overall_level = overall["level"]
            db.commit()
    sync_result_score(db, attempt, result)
