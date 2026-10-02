"""VIZU-Multilevel Hören audio: one protected audio file per Aufgabe (1-5).

Reuses the project's audio conventions — the accepted formats / MIME map
of the Assessment Engine's audio_service and the protected local storage
mechanism — with a dedicated root. Files are named by UUID (the browser's
filename is never a storage key) and are never reachable through a public
URL; they are streamed only through authenticated endpoints (an exam
attempt that has opened Hören for students, any admin-panel role for
preview)."""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage.protected_local import ProtectedVizuMultilevelHoerenStorage
from app.models.task_audio import ALL_AUDIO_FORMATS, CONTENT_TYPE_BY_FORMAT
from app.models.vizu_multilevel_audio import VizuMultilevelAudio
from app.services.assessment_engine.audio_service import resolve_audio_format

AUFGABE_NUMBERS = (1, 2, 3, 4, 5)
MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024

storage = ProtectedVizuMultilevelHoerenStorage()


def _slot(aufgabe_number: int, audio: VizuMultilevelAudio | None) -> dict:
    return {
        "aufgabe_number": aufgabe_number,
        "audio_id": audio.id if audio else None,
        "has_audio": audio is not None,
        "file_name": audio.file_name if audio else None,
        "content_type": audio.content_type if audio else None,
        "duration_seconds": audio.duration_seconds if audio else None,
        "is_active": audio.is_active if audio else False,
        "updated_at": audio.updated_at if audio else None,
    }


def _active_by_number(db: Session) -> dict[int, VizuMultilevelAudio]:
    rows = db.scalars(
        select(VizuMultilevelAudio).where(
            VizuMultilevelAudio.aufgabe_number.isnot(None),
            VizuMultilevelAudio.storage_path.isnot(None),
            VizuMultilevelAudio.is_active.is_(True),
        )
    )
    return {a.aufgabe_number: a for a in rows}


def list_slots(db: Session) -> list[dict]:
    by_number = _active_by_number(db)
    return [_slot(n, by_number.get(n)) for n in AUFGABE_NUMBERS]


def numbers_with_audio(db: Session) -> set[int]:
    return set(_active_by_number(db))


def _delete_file(path: str | None) -> None:
    if path:
        try:
            (storage.ROOT / path).unlink(missing_ok=True)
        except OSError:
            pass


def get_by_id(db: Session, audio_id: UUID) -> VizuMultilevelAudio | None:
    return db.scalar(select(VizuMultilevelAudio).where(VizuMultilevelAudio.id == audio_id))


def get_for_aufgabe(db: Session, aufgabe_number: int) -> VizuMultilevelAudio | None:
    return _active_by_number(db).get(aufgabe_number)


def resolve_path(audio: VizuMultilevelAudio) -> Path:
    return storage.ROOT / (audio.storage_path or "")


async def _store(file: UploadFile) -> tuple[str, str, int]:
    audio_format = resolve_audio_format(file.content_type)
    if audio_format not in ALL_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio type '{file.content_type}'. Allowed: MP3, WAV, M4A, WebM, OGG.",
        )
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The audio file is empty.")
    if len(contents) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio exceeds the maximum upload size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    await file.seek(0)
    unique_name = f"{uuid4().hex}.{audio_format}"
    file.filename = unique_name
    await storage.upload(file, unique_name)
    return unique_name, CONTENT_TYPE_BY_FORMAT[audio_format], len(contents)


async def upload(
    db: Session, aufgabe_number: int, file: UploadFile, duration_seconds: int | None
) -> VizuMultilevelAudio:
    """Creates the Aufgabe's audio, or REPLACES the previous one (the old
    file is removed from storage) — students only ever get the latest."""
    if aufgabe_number not in AUFGABE_NUMBERS:
        raise HTTPException(status_code=422, detail="Aufgabe must be 1-5.")

    original_name = (file.filename or "audio")[:255]
    stored_name, content_type, _size = await _store(file)

    existing = db.scalar(select(VizuMultilevelAudio).where(VizuMultilevelAudio.aufgabe_number == aufgabe_number))
    old_path = None
    if existing is None:
        existing = VizuMultilevelAudio(aufgabe_number=aufgabe_number, title=f"Hören Aufgabe {aufgabe_number}")
        db.add(existing)
    else:
        old_path = existing.storage_path

    existing.file_name = original_name
    existing.storage_path = stored_name
    existing.content_type = content_type
    existing.duration_seconds = duration_seconds
    existing.is_active = True
    db.commit()
    db.refresh(existing)
    if old_path and old_path != stored_name:
        _delete_file(old_path)
    return existing


async def replace(
    db: Session, audio_id: UUID, file: UploadFile, duration_seconds: int | None
) -> VizuMultilevelAudio | None:
    audio = get_by_id(db, audio_id)
    if audio is None or audio.aufgabe_number is None:
        return None
    return await upload(db, audio.aufgabe_number, file, duration_seconds)


def delete(db: Session, audio_id: UUID) -> bool:
    audio = get_by_id(db, audio_id)
    if audio is None:
        return False
    path = audio.storage_path
    db.delete(audio)
    db.commit()
    _delete_file(path)
    return True
