from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage.protected_local import ProtectedLocalStorage
from app.models.assessment import Assessment, STATUS_PUBLISHED, TYPE_MOCK_TEST
from app.models.assessment_attempt import AssessmentAttempt
from app.models.assessment_task import AssessmentTask
from app.models.task_attempt import TaskAttempt
from app.models.task_audio import ALL_AUDIO_FORMATS, CONTENT_TYPE_BY_FORMAT, TaskAudio
from app.models.user import User
from app.core.security.roles import UserRole

from . import attempt_service

MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # 50MB — generous for a single listening task's clip

EXTENSION_BY_CONTENT_TYPE = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/m4a": "m4a",
}

storage = ProtectedLocalStorage()


def _get_task(db: Session, task_id: str) -> AssessmentTask:
    task = db.get(AssessmentTask, UUID(task_id))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


# ============================================================
# Admin — upload / replace / delete
# ============================================================

async def upload_audio(
    db: Session,
    task_id: str,
    file: UploadFile,
    duration_seconds: int | None,
) -> TaskAudio:
    task = _get_task(db, task_id)

    audio_format = EXTENSION_BY_CONTENT_TYPE.get(file.content_type or "")
    if audio_format not in ALL_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type '{file.content_type}'. Allowed: MP3, WAV, M4A.",
        )

    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Audio exceeds the maximum upload size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    await file.seek(0)

    # Replace semantics: a new upload always removes the previous file for
    # this task first, matching "upload / replace" being the same action
    # from the admin's point of view.
    existing = db.scalars(select(TaskAudio).where(TaskAudio.task_id == task.id)).first()
    if existing is not None:
        await storage.delete(existing.storage_path)
        db.delete(existing)
        db.flush()

    unique_name = f"{uuid4().hex}.{audio_format}"
    storage_path = f"assessment-audio/{unique_name}"

    file.filename = unique_name
    await storage.upload(file, storage_path)

    audio = TaskAudio(
        task_id=task.id,
        storage_path=storage_path,
        filename=file.filename,
        format=audio_format,
        content_type=CONTENT_TYPE_BY_FORMAT[audio_format],
        duration_seconds=duration_seconds,
        file_size_bytes=len(contents),
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


async def delete_audio(db: Session, task_id: str) -> bool:
    task = _get_task(db, task_id)
    audio = db.scalars(select(TaskAudio).where(TaskAudio.task_id == task.id)).first()
    if audio is None:
        return False

    await storage.delete(audio.storage_path)
    db.delete(audio)
    db.commit()
    return True


def get_audio_record(db: Session, task_id: str) -> TaskAudio | None:
    return db.scalars(select(TaskAudio).where(TaskAudio.task_id == UUID(task_id))).first()


# ============================================================
# Secure access + streaming
# ============================================================

def resolve_audio_path(audio: TaskAudio) -> Path:
    return storage.ROOT / audio.storage_path


def _user_has_attempt(db: Session, assessment_id: UUID, user_id: UUID) -> bool:
    return (
        db.scalars(
            select(AssessmentAttempt.id).where(
                AssessmentAttempt.assessment_id == assessment_id,
                AssessmentAttempt.user_id == user_id,
            )
        ).first()
        is not None
    )


def authorize_audio_access(db: Session, task_id: str, user: User) -> TaskAudio:
    """The single gate every audio-serving/play-tracking endpoint goes
    through. Raises 404 for "doesn't exist or you can't know it exists"
    (never leaks whether a DRAFT task has audio), 403 for "exists, you're
    just not allowed". Super admins always pass (they need to preview
    unpublished work); everyone else must go through a published
    assessment, and — for MOCK_TEST specifically — must already have an
    attempt on it, per spec: "Mock Test audio endpointlari attempt bilan
    bog'lanishi kerak"."""

    task = _get_task(db, task_id)
    audio = db.scalars(select(TaskAudio).where(TaskAudio.task_id == task.id)).first()
    if audio is None:
        raise HTTPException(status_code=404, detail="No audio for this task.")

    if user.role in (UserRole.SUPER_ADMIN,):
        return audio

    section = task.section
    assessment = db.get(Assessment, section.assessment_id) if section else None
    if assessment is None or assessment.status != STATUS_PUBLISHED:
        raise HTTPException(status_code=404, detail="No audio for this task.")

    if assessment.assessment_type == TYPE_MOCK_TEST and not _user_has_attempt(db, assessment.id, user.id):
        raise HTTPException(status_code=403, detail="Start the test before accessing its audio.")

    return audio


# ============================================================
# Play count — server-side enforcement, never trust the frontend
# ============================================================

def _get_or_create_task_attempt(db: Session, task: AssessmentTask, user: User) -> TaskAttempt:
    section = task.section
    assessment_id = section.assessment_id

    attempt = db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.assessment_id == assessment_id, AssessmentAttempt.user_id == user.id)
        .order_by(AssessmentAttempt.started_at.desc())
    ).first()
    if attempt is None:
        raise HTTPException(status_code=403, detail="Start an attempt before playing audio.")

    return attempt_service.get_or_create_task_attempt(db, attempt, task)


def get_play_status(db: Session, task_id: str, user: User) -> dict:
    task = _get_task(db, task_id)
    authorize_audio_access(db, task_id, user)
    task_attempt = _get_or_create_task_attempt(db, task, user)

    limit = task.audio_play_limit
    plays_used = task_attempt.audio_play_count
    remaining = None if limit is None else max(limit - plays_used, 0)

    return {
        "task_id": task_id,
        "play_limit": limit,
        "plays_used": plays_used,
        "plays_remaining": remaining,
        "can_play": limit is None or plays_used < limit,
        "allow_pause": task.allow_pause,
        "allow_seek": task.allow_seek,
        "allow_replay": task.allow_replay,
        "allow_speed_change": task.allow_speed_change,
    }


def register_play(db: Session, task_id: str, user: User) -> dict:
    """Called once per actual playback start. Increments and re-checks —
    the frontend disables its button using get_play_status, but this is
    the check that actually matters."""
    task = _get_task(db, task_id)
    authorize_audio_access(db, task_id, user)
    task_attempt = _get_or_create_task_attempt(db, task, user)

    if task_attempt.assessment_attempt.locked:
        raise HTTPException(status_code=403, detail="This attempt is locked; audio can no longer be played.")

    limit = task.audio_play_limit
    if limit is not None and task_attempt.audio_play_count >= limit:
        raise HTTPException(status_code=403, detail="Audio play limit reached for this task.")

    task_attempt.audio_play_count += 1
    db.commit()

    return get_play_status(db, task_id, user)
