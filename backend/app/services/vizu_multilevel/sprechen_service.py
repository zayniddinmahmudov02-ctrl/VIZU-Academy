"""VIZU-Multilevel Sprechen — task list, audio submission (protected
storage, ownership-checked playback) and the final competency submit.
Teacher grading lives in services/teacher/vizu_multilevel_speaking_review_service.py."""

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

storage = ProtectedVizuMultilevelSpeakingStorage()


class SectionTimeUpError(Exception):
    """The 20-minute Sprechen window (deadline + grace) is over."""


def list_speaking_tasks(db: Session, include_inactive: bool = False) -> list[VizuMultilevelSpeakingTask]:
    query = select(VizuMultilevelSpeakingTask).order_by(VizuMultilevelSpeakingTask.order_index)
    if not include_inactive:
        query = query.where(VizuMultilevelSpeakingTask.is_active.is_(True))
    return list(db.scalars(query))


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
    if attempt.sprechen_submitted_at is not None:
        raise service.SectionFlowError("SECTION_ALREADY_SUBMITTED")
    if not service.ensure_section_open(db, attempt, "sprechen"):
        raise SectionTimeUpError()

    task = db.scalar(
        select(VizuMultilevelSpeakingTask).where(
            VizuMultilevelSpeakingTask.id == task_id, VizuMultilevelSpeakingTask.is_active.is_(True)
        )
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking task not found")

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
    await file.seek(0)

    existing = db.scalar(
        select(VizuMultilevelSpeakingSubmission).where(
            VizuMultilevelSpeakingSubmission.attempt_id == attempt.id,
            VizuMultilevelSpeakingSubmission.task_id == task_id,
        )
    )

    # UUID-based filename — the browser's filename is never a storage key.
    unique_name = f"{uuid4().hex}.{audio_format}"
    file.filename = unique_name
    await storage.upload(file, unique_name)

    if existing is not None:
        old_path = existing.storage_path
        existing.storage_path = unique_name
        existing.content_type = CONTENT_TYPE_BY_FORMAT[audio_format]
        existing.duration_seconds = duration_seconds
        existing.file_size_bytes = len(contents)
        existing.submitted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        delete_files([old_path])
        return existing

    submission = VizuMultilevelSpeakingSubmission(
        attempt_id=attempt.id,
        task_id=task_id,
        storage_path=unique_name,
        content_type=CONTENT_TYPE_BY_FORMAT[audio_format],
        duration_seconds=duration_seconds,
        file_size_bytes=len(contents),
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def submit_all(db: Session, attempt: VizuMultilevelAttempt) -> VizuMultilevelAttempt:
    """Final "Sprechen absenden" — idempotent. Works with zero recordings
    (finishing without answering). A late final submit is accepted: only
    recordings uploaded while the window was open exist (upload enforces
    that), so there is nothing to discard here."""
    if attempt.sprechen_submitted_at is not None:
        return attempt
    service.begin_submission(db, attempt, "sprechen")
    service.mark_submitted(db, attempt, "sprechen")
    return attempt
