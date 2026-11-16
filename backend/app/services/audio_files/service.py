"""Central audio service: upload, probe, trim and delete audio files — used by Media Management and Multilevel Audio.

Rules
- Files live in the private lesson-listening storage under random names; nothing here returns a storage path or URL.
- An upload is an ORIGINAL and is never changed or removed by a trim: a trim is a new TRIMMED row (source_id) cut from
  the original with ffmpeg (argument list, no shell, timeout, temp file inside the storage root, same format as the
  source: MP3 re-encoded with libmp3lame -q:a 2, WAV as PCM, M4A as AAC 192k). Trimming again cuts from the original.
- Accepted: MP3, WAV, M4A by content (magic bytes) and declared type, max 100 MB, duration read with ffprobe.
- Only an unused TRIMMED file is ever deleted from disk; originals are kept."""

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audio_file import KIND_ORIGINAL, KIND_TRIMMED, AudioFile
from app.models.user import User
from app.services.lesson_skills import admin as skill_admin

MAX_BYTES = skill_admin.MAX_AUDIO_BYTES
MIN_TRIM_MS = 500
MAX_DURATION_MS = 6 * 3600 * 1000
PROCESS_TIMEOUT = 300

_CODEC = {"mp3": ["-c:a", "libmp3lame", "-q:a", "2"], "wav": ["-c:a", "pcm_s16le"], "m4a": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]}


# Where the tools live when the service's own PATH does not contain them: the production systemd unit sets PATH to the virtualenv
# only (so `shutil.which("ffmpeg")` found nothing although /usr/bin/ffmpeg exists — every audio / video upload then failed).
_FALLBACK_DIRS = ("/usr/bin", "/usr/local/bin", "/opt/homebrew/bin", "/snap/bin", "/bin")


def find_tool(name: str) -> str | None:
    """Path of `ffmpeg` / `ffprobe`: the <NAME>_BIN environment variable (a full path or a name), then PATH, then the usual system folders."""
    configured = os.environ.get(f"{name.upper()}_BIN")
    for candidate in ([configured] if configured else []) + [name]:
        found = shutil.which(candidate)
        if found:
            return found
    for folder in _FALLBACK_DIRS:
        path = os.path.join(folder, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def _bin(name: str) -> str:
    found = find_tool(name)
    if not found:
        raise HTTPException(status_code=503, detail="AUDIO_TOOL_MISSING: audio processing is not available on this server.")
    return found


def _storage_root() -> Path:
    return skill_admin.listening_storage.ROOT


def path_of(audio: AudioFile | None) -> Path | None:
    """The stored file when it exists inside the storage root, else None."""
    if audio is None or audio.deleted_at is not None:
        return None
    return skill_admin._stored(audio.storage_path)


def _probe_seconds(path: Path) -> float | None:
    if find_tool("ffprobe"):
        out = subprocess.run([_bin("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                             capture_output=True, text=True, timeout=60, check=True).stdout
        return float(json.loads(out)["format"]["duration"])
    # no ffprobe: ffmpeg itself reports "Duration: HH:MM:SS.xx" (it exits 1 without an output file, which is expected)
    err = subprocess.run([_bin("ffmpeg"), "-nostdin", "-i", str(path)], capture_output=True, text=True, timeout=60).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def probe_duration_ms(path: Path) -> int | None:
    try:
        seconds = _probe_seconds(path)
    except (subprocess.SubprocessError, KeyError, ValueError, OSError):
        return None
    if seconds is None:
        return None
    ms = round(seconds * 1000)
    return ms if 0 < ms < MAX_DURATION_MS else None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def serialize(audio: AudioFile | None) -> dict | None:
    if audio is None:
        return None
    return {"id": audio.id, "kind": audio.kind, "source_id": audio.source_id, "original_name": audio.original_name,
            "content_type": audio.content_type, "size_bytes": audio.size_bytes, "duration_ms": audio.duration_ms,
            "trim_start_ms": audio.trim_start_ms, "trim_end_ms": audio.trim_end_ms,
            "file_status": "ok" if path_of(audio) else "missing", "created_at": audio.created_at}


async def store_original(db: Session, file: UploadFile, user: User | None) -> AudioFile:
    name, detected = await skill_admin._store_audio(file)
    path = _storage_root() / name
    duration = probe_duration_ms(path)
    if duration is None:  # not decodable audio (or ffprobe cannot read it): do not keep it
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="UNSUPPORTED_AUDIO: the file could not be read as audio.")
    audio = AudioFile(storage_path=name, kind=KIND_ORIGINAL, original_name=(file.filename or "")[:255] or None,
                      content_type=skill_admin.AUDIO_FORMATS[detected][0], size_bytes=path.stat().st_size, duration_ms=duration,
                      sha256=_sha256(path), created_by_id=user.id if user else None)
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def get_active(db: Session, audio_id: UUID) -> AudioFile:
    audio = db.get(AudioFile, audio_id)
    if audio is None or audio.deleted_at is not None:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_FOUND")
    return audio


def _cut(src: Path, dst: Path, fmt: str, start_ms: int, end_ms: int) -> None:
    cmd = [_bin("ffmpeg"), "-nostdin", "-v", "error", "-y", "-ss", f"{start_ms / 1000:.3f}", "-to", f"{end_ms / 1000:.3f}", "-i", str(src),
           "-vn", "-map_metadata", "-1", *_CODEC[fmt], "-f", {"mp3": "mp3", "wav": "wav", "m4a": "ipod"}[fmt], str(dst)]
    try:
        subprocess.run(cmd, capture_output=True, timeout=PROCESS_TIMEOUT, check=True)
    except subprocess.TimeoutExpired:
        dst.unlink(missing_ok=True)
        raise HTTPException(status_code=504, detail="AUDIO_PROCESSING_TIMEOUT: trimming took too long.") from None
    except (subprocess.CalledProcessError, OSError):
        dst.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="AUDIO_PROCESSING_FAILED: the audio could not be trimmed.") from None


async def trim(db: Session, source_id: UUID, start_ms: int, end_ms: int, user: User | None) -> AudioFile:
    """A new TRIMMED file cut from the ORIGINAL `source_id` (a trimmed id resolves to its original); the original stays."""
    source = get_active(db, source_id)
    if source.kind == KIND_TRIMMED and source.source_id:
        source = get_active(db, source.source_id)
    src = path_of(source)
    if src is None:
        raise HTTPException(status_code=409, detail="AUDIO_FILE_MISSING: the original file is not on the server.")
    total = source.duration_ms or probe_duration_ms(src) or 0
    if not (0 <= start_ms < end_ms) or (total and end_ms > total + 50):
        raise HTTPException(status_code=422, detail="INVALID_RANGE: start must be before end and inside the audio.")
    if end_ms - start_ms < MIN_TRIM_MS:
        raise HTTPException(status_code=422, detail="RANGE_TOO_SHORT: the selection must be at least 0.5 seconds.")
    fmt = src.suffix.lstrip(".").lower()
    name = f"{uuid4().hex}.{fmt}"
    dst = _storage_root() / name
    await asyncio.to_thread(_cut, src, dst, fmt, start_ms, min(end_ms, total) if total else end_ms)
    duration = probe_duration_ms(dst)
    if duration is None or not dst.stat().st_size:
        dst.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="AUDIO_PROCESSING_FAILED: the trimmed file is empty.")
    base = (source.original_name or "audio").rsplit(".", 1)[0]
    audio = AudioFile(storage_path=name, kind=KIND_TRIMMED, source_id=source.id, trim_start_ms=start_ms, trim_end_ms=end_ms,
                      original_name=f"{base}-trim.{fmt}"[:255], content_type=source.content_type, size_bytes=dst.stat().st_size,
                      duration_ms=duration, sha256=_sha256(dst), created_by_id=user.id if user else None)
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def references(db: Session, audio: AudioFile) -> int:
    """Rows that still use this file: trims cut from it, Multilevel Hören Teile playing it and Hören sections playing it as their shared audio."""
    from sqlalchemy import func

    from app.models.kompetenz import Kompetenz
    from app.models.listening_content import ListeningContent

    return int(db.scalar(select(func.count()).select_from(AudioFile).where(AudioFile.source_id == audio.id, AudioFile.deleted_at.is_(None))) or 0) \
        + int(db.scalar(select(func.count()).select_from(ListeningContent).where(ListeningContent.audio_file_id == audio.id)) or 0) \
        + int(db.scalar(select(func.count()).select_from(Kompetenz).where(Kompetenz.audio_file_id == audio.id)) or 0)


async def discard(db: Session, audio: AudioFile | None) -> None:
    """Remove a TRIMMED file nobody uses (call after the referencing row changed and committed). ORIGINALS are never
    removed here: they stay so a slot can be re-trimmed or restored."""
    if audio is None or audio.kind != KIND_TRIMMED or references(db, audio):
        return
    try:
        await skill_admin.listening_storage.delete(audio.storage_path)
    except OSError:
        raise HTTPException(status_code=500, detail="AUDIO_FILE_DELETE_FAILED: the file could not be removed.") from None
    audio.deleted_at = datetime.now(timezone.utc)
    db.commit()
