"""VIZU-Multilevel attempt lifecycle: server-authoritative timing, the
Lesen -> Hören -> Schreiben -> Sprechen flow, per-competency results, the
overall level, and the "below A1 / incomplete attempts are not kept" rule.

Everything time- or flow-related is decided HERE, from timestamps the
backend stamps itself — the client's clock and navigation state are never
trusted (a reload cannot restart the 20-minute timer, a skipped step
cannot be submitted out of order, a late submission cannot add answers)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_multilevel_attempt import STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMultilevelAttempt
from app.models.vizu_multilevel_content import CEFR_LEVELS, SKILL_HOEREN, SKILL_LESEN, VizuMultilevelQuestion, VizuMultilevelTask
from app.models.vizu_multilevel_discarded import REASON_ABANDONED, REASON_BELOW_A1, VizuMultilevelDiscardedAttempt
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
    return list(
        db.scalars(
            select(VizuMultilevelAttempt)
            .where(VizuMultilevelAttempt.user_id == user_id)
            .order_by(VizuMultilevelAttempt.started_at.desc())
        )
    )


def create_attempt(db: Session, user_id: UUID) -> VizuMultilevelAttempt:
    """Starts a new attempt — or resumes the student's live one. A student
    never has two unfinished attempts, so unfinished attempts do not pile
    up and the timers cannot be 'reset' by starting over."""
    purge_abandoned(db)

    existing = db.scalar(
        select(VizuMultilevelAttempt)
        .where(VizuMultilevelAttempt.user_id == user_id, VizuMultilevelAttempt.status == STATUS_IN_PROGRESS)
        .order_by(VizuMultilevelAttempt.started_at.desc())
    )
    if existing is not None:
        return existing

    attempt = VizuMultilevelAttempt(user_id=user_id, status=STATUS_IN_PROGRESS)
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


def _speaking_totals(db: Session) -> tuple[int, int]:
    tasks = list(db.scalars(select(VizuMultilevelSpeakingTask).where(VizuMultilevelSpeakingTask.is_active.is_(True))))
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
    tasks = list(db.scalars(select(VizuMultilevelSpeakingTask).where(VizuMultilevelSpeakingTask.is_active.is_(True))))
    subs = {
        s.task_id: s
        for s in db.scalars(
            select(VizuMultilevelSpeakingSubmission).where(VizuMultilevelSpeakingSubmission.attempt_id == attempt_id)
        )
    }
    for task in tasks:
        sub = subs.get(task.id)
        if sub is not None and sub.teacher_score is None:
            return False
    return True


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

    # Sprechen — teacher-graded.
    task_count, max_points = _speaking_totals(db)
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
        "competencies": competencies,
        "overall": overall_result(competencies),
    }


# ============================================================
# Completion / below-A1 / abandonment
# ============================================================


def _discard(db: Session, attempt: VizuMultilevelAttempt, reason: str) -> None:
    """Removes the attempt (and, by cascade, its answers/submissions) and
    its stored recordings; keeps only an anonymous tally row."""
    from app.services.vizu_multilevel import sprechen_service

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
    paths = sprechen_service.stored_paths(db, attempt.id)
    db.delete(attempt)
    db.commit()
    sprechen_service.delete_files(paths)


def complete_attempt(db: Session, user_id: UUID, attempt_id: UUID) -> dict | None:
    """Finishes the attempt. Returns None for an unknown/foreign id.
    Otherwise `{"saved": bool, "result": {...}}`: below-A1 (or empty)
    results are returned once but NOT kept in the student's history."""
    attempt = get_own_attempt(db, user_id, attempt_id)
    if attempt is None:
        return None

    if attempt.status == STATUS_COMPLETED:
        return {"saved": True, "result": build_result(db, attempt)}

    if not all(is_submitted(attempt, s) for s in SKILLS):
        raise SectionFlowError("SECTIONS_NOT_SUBMITTED")

    result = build_result(db, attempt)
    overall = result["overall"]

    if overall["status"] == O_NO_CONTENT:
        result_attempt_id = attempt.id
        db.delete(attempt)
        db.commit()
        result["attempt_id"] = result_attempt_id
        return {"saved": False, "result": result}

    if overall["status"] == O_BELOW_A1:
        _discard(db, attempt, REASON_BELOW_A1)
        return {"saved": False, "result": result}

    attempt.status = STATUS_COMPLETED
    attempt.completed_at = _now()
    attempt.overall_level = overall["level"]
    db.commit()
    db.refresh(attempt)
    return {"saved": True, "result": result}


def refresh_overall(db: Session, attempt: VizuMultilevelAttempt) -> None:
    """Called after a teacher grades Schreiben/Sprechen: re-derives the
    overall result of an already-completed attempt. Becomes final (level
    set) when everything is graded; is discarded if it turns out below A1."""
    if attempt.status != STATUS_COMPLETED:
        return
    overall = build_result(db, attempt)["overall"]
    if overall["status"] == O_BELOW_A1:
        _discard(db, attempt, REASON_BELOW_A1)
    elif overall["status"] == O_FINAL:
        attempt.overall_level = overall["level"]
        db.commit()


def purge_abandoned(db: Session) -> int:
    """Unfinished attempts that have been idle for ABANDON_AFTER are not
    kept: each becomes an anonymous 'ABANDONED' tally row (so statistics
    stay truthful) and the attempt itself is deleted."""
    cutoff = _now() - ABANDON_AFTER
    stale = list(
        db.scalars(
            select(VizuMultilevelAttempt).where(
                VizuMultilevelAttempt.status == STATUS_IN_PROGRESS, VizuMultilevelAttempt.updated_at < cutoff
            )
        )
    )
    for attempt in stale:
        _discard(db, attempt, REASON_ABANDONED)
    return len(stale)
