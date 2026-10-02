"""VIZU-Multilevel Sprechen — which 5 Aufgaben a student gets, audio answers
(protected storage, ownership-checked playback), the final competency
submit and the Sprechen score/level.

Task selection (ladder): Aufgabe n is the bank variant of Aufgabe type n at
level LADDER[n-1] (A1, A2, B1, B2, C1). If that variant is inactive, the
active variant of the same Aufgabe with the nearest level is used. Once an
attempt has answered an Aufgabe, that answer's task stays the attempt's task
(admin edits never re-shuffle a running/finished attempt).

Each answer is saved ONCE (re-recording happens in the browser before
"Antwort speichern"), in Aufgabe order, then processed server-side
(speech-to-text + AI evaluation, see sprechen_evaluation_service).
Teacher overrides live in services/teacher/vizu_multilevel_speaking_review_service.py."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage.protected_local import ProtectedVizuMultilevelSpeakingStorage
from app.models.task_audio import ALL_AUDIO_FORMATS, CONTENT_TYPE_BY_FORMAT
from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingSubmission, VizuMultilevelSpeakingTask
from app.services.assessment_engine.audio_service import resolve_audio_format
from app.services.vizu_multilevel import service

MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024
MIN_AUDIO_SIZE_BYTES = 1024  # anything smaller is not a real recording

LADDER = ["A1", "A2", "B1", "B2", "C1"]
SLOTS = range(1, len(LADDER) + 1)
MAX_TOTAL = 100

# Pipeline states (VizuMultilevelSpeakingSubmission.status).
PROCESSING = "PROCESSING"
TRANSCRIBED = "TRANSCRIBED"
EVALUATING = "EVALUATING"
EVALUATED = "EVALUATED"
FAILED = "FAILED"

# Sprechen total (0-100) -> CEFR level. None = below A1.
LEVEL_THRESHOLDS = [(90, "C1"), (75, "B2"), (60, "B1"), (40, "A2"), (20, "A1")]

storage = ProtectedVizuMultilevelSpeakingStorage()


class SectionTimeUpError(Exception):
    """The 20-minute Sprechen window (deadline + grace) is over."""


def level_for_score(total: int | None) -> str | None:
    if total is None:
        return None
    for minimum, level in LEVEL_THRESHOLDS:
        if total >= minimum:
            return level
    return None


# ============================================================
# Task selection
# ============================================================


def list_speaking_tasks(db: Session, include_inactive: bool = False) -> list[VizuMultilevelSpeakingTask]:
    """The whole bank (admin use)."""
    query = select(VizuMultilevelSpeakingTask).order_by(VizuMultilevelSpeakingTask.order_index, VizuMultilevelSpeakingTask.level)
    if not include_inactive:
        query = query.where(VizuMultilevelSpeakingTask.is_active.is_(True))
    return list(db.scalars(query))


def _pick(variants: list[VizuMultilevelSpeakingTask], target: str) -> VizuMultilevelSpeakingTask | None:
    if not variants:
        return None
    rank = {level: i for i, level in enumerate(LADDER)}
    return min(variants, key=lambda t: (abs(rank.get(t.level, 99) - rank[target]), rank.get(t.level, 99)))


def assigned_tasks(db: Session) -> list[VizuMultilevelSpeakingTask]:
    """The 5 Aufgaben a new student gets (ladder A1 -> C1)."""
    active = list_speaking_tasks(db)
    chosen = []
    for slot in SLOTS:
        task = _pick([t for t in active if t.order_index == slot], LADDER[slot - 1])
        if task is not None:
            chosen.append(task)
    return chosen


def attempt_tasks(db: Session, attempt_id: UUID) -> list[VizuMultilevelSpeakingTask]:
    """The attempt's 5 Aufgaben: the task already answered in a slot wins,
    otherwise the current ladder task."""
    answered = {
        s.task.order_index: s.task
        for s in db.scalars(
            select(VizuMultilevelSpeakingSubmission).where(VizuMultilevelSpeakingSubmission.attempt_id == attempt_id)
        )
        if s.task is not None
    }
    current = {t.order_index: t for t in assigned_tasks(db)}
    return [answered.get(slot) or current[slot] for slot in SLOTS if slot in answered or slot in current]


# ============================================================
# Submissions
# ============================================================


def get_own_submissions(db: Session, attempt_id: UUID) -> list[VizuMultilevelSpeakingSubmission]:
    return list(
        db.scalars(
            select(VizuMultilevelSpeakingSubmission).where(VizuMultilevelSpeakingSubmission.attempt_id == attempt_id)
        )
    )


def get_own_submission(db: Session, attempt_id: UUID, submission_id: UUID) -> VizuMultilevelSpeakingSubmission | None:
    return db.scalar(
        select(VizuMultilevelSpeakingSubmission).where(
            VizuMultilevelSpeakingSubmission.id == submission_id,
            VizuMultilevelSpeakingSubmission.attempt_id == attempt_id,
        )
    )


def stored_paths(db: Session, attempt_id: UUID) -> list[str]:
    return [s.storage_path for s in get_own_submissions(db, attempt_id)]


def delete_files(paths: list[str]) -> None:
    for path in paths:
        try:
            (storage.ROOT / path).unlink(missing_ok=True)
        except OSError:
            pass


def resolve_audio_path(submission: VizuMultilevelSpeakingSubmission) -> Path:
    return storage.ROOT / submission.storage_path


async def upload_recording(
    db: Session,
    attempt: VizuMultilevelAttempt,
    task_id: UUID,
    file: UploadFile,
    duration_seconds: int | None,
) -> VizuMultilevelSpeakingSubmission:
    """Saves one Aufgabe's answer (status PROCESSING — the caller schedules
    the speech-to-text / evaluation pipeline)."""
    if attempt.sprechen_submitted_at is not None:
        raise service.SectionFlowError("SECTION_ALREADY_SUBMITTED")
    if not service.ensure_section_open(db, attempt, "sprechen"):
        raise SectionTimeUpError()

    tasks = attempt_tasks(db, attempt.id)
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking task not found")

    existing = {s.task_id for s in get_own_submissions(db, attempt.id)}
    if task_id in existing:
        # Saved answers are final — another Aufgabe can never overwrite them.
        raise service.SectionFlowError("ANSWER_ALREADY_SAVED")
    if any(t.order_index < task.order_index and t.id not in existing for t in tasks):
        raise service.SectionFlowError("PREVIOUS_TASK_REQUIRED")

    audio_format = resolve_audio_format(file.content_type)
    if audio_format not in ALL_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio type '{file.content_type}'. Allowed: MP3, WAV, M4A, WebM, OGG.",
        )
    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio exceeds the maximum upload size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    if len(contents) < MIN_AUDIO_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMPTY_RECORDING")
    if duration_seconds is not None:
        duration_seconds = max(0, min(int(duration_seconds), task.max_seconds + 5))
    await file.seek(0)

    # UUID-based filename — the browser's filename is never a storage key.
    unique_name = f"{uuid4().hex}.{audio_format}"
    file.filename = unique_name
    await storage.upload(file, unique_name)

    submission = VizuMultilevelSpeakingSubmission(
        attempt_id=attempt.id,
        task_id=task_id,
        storage_path=unique_name,
        content_type=CONTENT_TYPE_BY_FORMAT[audio_format],
        duration_seconds=duration_seconds,
        file_size_bytes=len(contents),
        submitted_at=datetime.now(timezone.utc),
        status=PROCESSING,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def submit_all(db: Session, attempt: VizuMultilevelAttempt) -> VizuMultilevelAttempt:
    """Final "Sprechen abschließen" — idempotent. Needs an answer for every
    Aufgabe (server-checked; only a section whose time ran out may finish
    with fewer, like every other VIZU-Multilevel section)."""
    service.ensure_attempt_active(attempt)
    if attempt.sprechen_submitted_at is not None:
        return attempt
    service.begin_submission(db, attempt, "sprechen")
    service.check_min_answers(
        attempt, "sprechen", len(get_own_submissions(db, attempt.id)), len(attempt_tasks(db, attempt.id))
    )
    service.mark_submitted(db, attempt, "sprechen")
    return attempt


# ============================================================
# Score / level
# ============================================================


def effective_score(submission: VizuMultilevelSpeakingSubmission | None) -> int | None:
    """Teacher override if a teacher graded it, otherwise the AI score."""
    if submission is None:
        return None
    if submission.teacher_score is not None:
        return submission.teacher_score
    return submission.ai_score


def recompute_attempt(db: Session, attempt: VizuMultilevelAttempt) -> None:
    """Sprechen score = sum of the 5 Aufgaben (unanswered = 0); level from
    the 0-100 table once every answered Aufgabe has a score."""
    tasks = attempt_tasks(db, attempt.id)
    subs = {s.task_id: s for s in get_own_submissions(db, attempt.id)}
    scores = [effective_score(subs.get(t.id)) for t in tasks]
    answered = [t for t in tasks if t.id in subs]
    if not answered:
        attempt.sprechen_score = 0 if attempt.sprechen_submitted_at else None
        attempt.sprechen_level = None
        return
    complete = all(effective_score(subs[t.id]) is not None for t in answered)
    attempt.sprechen_score = sum(s for s in scores if s is not None) if complete else None
    attempt.sprechen_level = level_for_score(attempt.sprechen_score) if complete else None


def is_graded_complete(db: Session, attempt_id: UUID) -> bool:
    subs = {s.task_id: s for s in get_own_submissions(db, attempt_id)}
    return all(effective_score(subs[t.id]) is not None for t in attempt_tasks(db, attempt_id) if t.id in subs)
