"""A2 Audio Manager: upload, correct, verify, link and remove A2 audio files.

Storage: the existing private Hören storage (lesson-listening), files under
"a2-audio/<random>.<format>" — never the original name, never public. A
student reaches an A2 audio only through the existing Hören endpoint of a
lesson they may open (require_lesson_access + published task), because
linking writes the file into the Hören task (listening.audio_storage_path).
The original file name is kept separately (original_filename).

Upload checks, all on the server: the name must not name another level;
extension, declared MIME type and the file's first bytes must all say the
same format (MP3 / M4A, A2_AUDIO_FORMATS); size <= A2_AUDIO_MAX_BYTES; not
empty; not a file already in the library (SHA-256) -> 409 DUPLICATE with
the existing entry. The file name is parsed (filename.py) into Unterricht /
kind / part; values the admin sends win. Nothing is linked on upload.

Linking (link) is an explicit admin action. The target must be a current
Hören task of an A2 lesson (not an "[Archiv]" or legacy a2_material_key
task). The task's previous audio is kept: it goes to listening_audio_archives
(the existing version history), never deleted. A newly linked task is set to
draft so the admin checks audio + questions before students see it.

Removing is two separate steps: the library entry (delete) and, only on
request and only when nothing else references it, the physical file. A
linked entry cannot be removed (unlink first)."""

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.a2_audio_asset import (
    AUDIO_KINDS,
    KIND_HOEREN,
    KIND_TEXT,
    KIND_UNTERRICHT,
    VERIFY_OK,
    VERIFY_PENDING,
    VERIFY_PROBLEM,
    A2AudioAsset,
)
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.listening_audio_track import ListeningAudioTrack
from app.models.user import User
from app.services.a2_audio import filename
from app.services.lesson_skills.admin import listening_storage
from app.services.lms import structure as lms_structure

LEVEL = "A2"
STORAGE_PREFIX = "a2-audio"
ARCHIVE_PREFIX = "[Archiv]"
TITLE_MAX = 255
NOTE_MAX = 1000

# format -> (stored content type, accepted declared MIME types)
FORMATS = {
    "mp3": ("audio/mpeg", {"audio/mpeg", "audio/mp3"}),
    "m4a": ("audio/mp4", {"audio/mp4", "audio/x-m4a", "audio/m4a"}),
}
# ISO-BMFF brands of audio files (an M4V / video MP4 brand is not accepted)
M4A_BRANDS = {b"M4A ", b"M4B ", b"mp42", b"mp41", b"isom", b"iso2", b"dash"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _error(code: int, detail) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def allowed_formats() -> list[str]:
    wanted = [f.strip().lower() for f in (settings.A2_AUDIO_FORMATS or "").split(",") if f.strip()]
    return [f for f in wanted if f in FORMATS]


def detect_format(head: bytes) -> str | None:
    """MP3 (ID3 tag or an MPEG audio frame header) or M4A (ftyp box with an
    audio brand) — from the bytes, not the name."""
    if head[:3] == b"ID3":
        return "mp3"
    if len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0 and (head[1] & 0x06) != 0 and (head[1] & 0x18) != 0x08:
        return "mp3"  # frame sync, a real layer (ADTS/AAC has layer 00), not the reserved MPEG version
    if head[4:8] == b"ftyp" and head[8:12] in M4A_BRANDS:
        return "m4a"
    return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def stored_path(asset: A2AudioAsset) -> Path | None:
    root = listening_storage.ROOT.resolve()
    path = (listening_storage.ROOT / asset.storage_path).resolve()
    return path if root in path.parents and path.is_file() else None


def _max_unterricht() -> int:
    return lms_structure.LEVEL_LESSON_COUNTS[LEVEL]


def _clean_fields(data: dict) -> dict:
    out = {}
    if "unterricht" in data:
        n = data["unterricht"]
        if n is not None and not (isinstance(n, int) and 1 <= n <= _max_unterricht()):
            raise _error(422, f"UNTERRICHT_OUT_OF_RANGE: 1-{_max_unterricht()}")
        out["unterricht"] = n
    if "audio_kind" in data:
        kind = (data["audio_kind"] or None) and str(data["audio_kind"]).upper()
        if kind is not None and kind not in AUDIO_KINDS:
            raise _error(422, f"INVALID_AUDIO_KIND: {', '.join(AUDIO_KINDS)}")
        out["audio_kind"] = kind
    if "part" in data:
        p = data["part"]
        if p is not None and not (isinstance(p, int) and 1 <= p <= 99):
            raise _error(422, "PART_OUT_OF_RANGE: 1-99")
        out["part"] = p
    if "title" in data and data["title"] is not None:
        title = " ".join(str(data["title"]).split())[:TITLE_MAX]
        if not title:
            raise _error(422, "TITLE_REQUIRED")
        out["title"] = title
    if "sort_order" in data and data["sort_order"] is not None:
        if not isinstance(data["sort_order"], int) or not 0 <= data["sort_order"] <= 10_000:
            raise _error(422, "SORT_ORDER_OUT_OF_RANGE")
        out["sort_order"] = data["sort_order"]
    if "duration_seconds" in data:
        d = data["duration_seconds"]
        out["duration_seconds"] = d if isinstance(d, int) and 0 < d < 6 * 3600 else None
    return out


# ---------- A2 Hören tasks (the only link targets) ----------

def is_current_task(listening: Listening) -> bool:
    """A Hören task of the current A2 edition — not an archived first-edition
    copy and not a legacy A2-mapped task (those belong to the old archive)."""
    return not (listening.title or "").startswith(ARCHIVE_PREFIX) and not listening.a2_material_key


def a2_lessons(db: Session) -> list[Lesson]:
    course = lms_structure.level_course(db, LEVEL)
    module = lms_structure.main_module(db, course) if course else None
    return lms_structure.level_lessons(db, module)


def a2_tasks(db: Session, lessons: list[Lesson] | None = None) -> list[tuple[Listening, Lesson]]:
    lessons = a2_lessons(db) if lessons is None else lessons
    by_id = {lesson.id: lesson for lesson in lessons}
    if not by_id:
        return []
    rows = db.scalars(select(Listening).where(Listening.lesson_id.in_(list(by_id))).order_by(Listening.order_index, Listening.created_at))
    return [(t, by_id[UUID(str(t.lesson_id))]) for t in rows if is_current_task(t)]


def _task_lesson(db: Session, listening: Listening) -> Lesson | None:
    """The listening's lesson if it is an A2 lesson, else None."""
    lesson = db.get(Lesson, listening.lesson_id)
    course, _ = lms_structure.lesson_level(db, lesson) if lesson else (None, None)
    return lesson if course is not None and course.level == LEVEL else None


def suggestion(asset: A2AudioAsset, tasks: list[tuple[Listening, Lesson]], linked_ids: set) -> dict | None:
    """A link the file name suggests — only when exactly one task fits. The
    admin still has to confirm it (link)."""
    if asset.listening_id is not None or asset.unterricht is None:
        return None
    in_lesson = [(t, lesson) for t, lesson in tasks if lesson.number == asset.unterricht and t.id not in linked_ids]
    if asset.audio_kind == KIND_TEXT:
        # "Text N" only fits a task that is explicitly Text N (task_key, A2 4. Unterricht — lesson4_hoeren.py); never guessed otherwise
        fits = [(t, lesson) for t, lesson in in_lesson if asset.part is not None and (t.task_key or "").endswith(f"-text-{asset.part}")]
        reason = f"Dateiname: {asset.unterricht}. Unterricht, Text {asset.part}"
    elif asset.part is not None:
        fits = [(t, lesson) for t, lesson in in_lesson if (t.content_id or "").endswith(f"-hoeren-{asset.part:02d}")]
        reason = f"Dateiname: {asset.unterricht}. Unterricht, Teil {asset.part}"
    elif asset.audio_kind in (KIND_HOEREN, KIND_UNTERRICHT):
        fits = in_lesson if len(in_lesson) == 1 else []
        reason = f"Dateiname: {asset.unterricht}. Unterricht — einzige Hören-Aufgabe der Lektion"
    else:
        fits = []
    if len(fits) != 1:
        return None
    task, lesson = fits[0]
    return {"listening_id": task.id, "title": task.title, "lesson_number": lesson.number, "reason": reason}


# ---------- serialisation ----------

def serialize(asset: A2AudioAsset, db: Session, tasks: list[tuple[Listening, Lesson]] | None = None, linked_ids: set | None = None) -> dict:
    path = stored_path(asset)
    linked = None
    if asset.listening is not None:
        lesson = db.get(Lesson, asset.listening.lesson_id)
        linked = {"listening_id": asset.listening.id, "title": asset.listening.title, "lesson_number": lesson.number if lesson else None,
                  "is_published": asset.listening.is_published,
                  # the task still plays this file (someone may have replaced the task's audio elsewhere)
                  "in_sync": asset.listening.audio_storage_path == asset.storage_path}
    return {
        "id": asset.id, "level": asset.level, "unterricht": asset.unterricht, "audio_kind": asset.audio_kind, "part": asset.part,
        "title": asset.title, "original_filename": asset.original_filename, "parsed": asset.parsed,
        "audio_format": asset.audio_format.upper(), "content_type": asset.content_type, "size_bytes": asset.size_bytes,
        "sha256": asset.sha256, "duration_seconds": asset.duration_seconds, "sort_order": asset.sort_order,
        "file_status": "ok" if path else "missing",
        "verification": asset.verification, "verification_note": asset.verification_note, "verified_at": asset.verified_at,
        "linked": linked,
        "link_mismatch": bool(linked and linked["lesson_number"] is not None and asset.unterricht != linked["lesson_number"]),
        "suggestion": suggestion(asset, tasks, linked_ids or set()) if tasks is not None else None,
        "created_at": asset.created_at, "updated_at": asset.updated_at,
    }


def _all(db: Session) -> list[A2AudioAsset]:
    return list(db.scalars(select(A2AudioAsset).order_by(A2AudioAsset.unterricht.nulls_last(), A2AudioAsset.sort_order,
                                                         A2AudioAsset.created_at)).unique())


def list_assets(db: Session) -> list[dict]:
    tasks = a2_tasks(db)
    assets = _all(db)
    linked_ids = {a.listening_id for a in assets if a.listening_id}
    return [serialize(a, db, tasks, linked_ids) for a in assets]


def get(db: Session, asset_id: UUID) -> A2AudioAsset:
    asset = db.get(A2AudioAsset, asset_id)
    if asset is None:
        raise _error(404, "A2_AUDIO_NOT_FOUND")
    return asset


def _one(db: Session, asset: A2AudioAsset) -> dict:
    tasks = a2_tasks(db)
    linked_ids = set(db.scalars(select(A2AudioAsset.listening_id).where(A2AudioAsset.listening_id.is_not(None), A2AudioAsset.id != asset.id)))
    return serialize(asset, db, tasks, linked_ids)


# ---------- upload ----------

async def upload(db: Session, actor: User, file: UploadFile, fields: dict | None = None) -> dict:
    original = " ".join((file.filename or "").split())[:TITLE_MAX]
    if not original:
        raise _error(422, "FILENAME_REQUIRED")
    parsed = filename.parse(original)
    if parsed["other_level"]:
        raise _error(422, f"FILENAME_OTHER_LEVEL: {parsed['other_level']} — only A2 audio belongs here")
    formats = allowed_formats()
    ext = Path(original).suffix.lower().lstrip(".")
    if ext not in formats:
        raise _error(400, f"UNSUPPORTED_AUDIO: allowed are {', '.join(f.upper() for f in formats)}")
    declared = (file.content_type or "").split(";")[0].strip().lower()
    if declared not in FORMATS[ext][1]:
        raise _error(400, f"UNSUPPORTED_MIME: {declared or 'none'} is not a {ext.upper()} type")
    head = await file.read(16)
    await file.seek(0)
    detected = detect_format(head)
    if detected is None:
        raise _error(400, "NOT_AUDIO: the file content is not MP3 or M4A")
    if detected != ext:
        raise _error(400, f"EXTENSION_MISMATCH: the content is {detected.upper()}, the name says .{ext}")

    explicit = _clean_fields(fields or {})
    name = f"{STORAGE_PREFIX}/{uuid4().hex}.{detected}"
    try:
        await listening_storage.upload(file, name, max_bytes=settings.A2_AUDIO_MAX_BYTES)
    except ValueError:
        raise _error(413, f"AUDIO_TOO_LARGE: max {settings.A2_AUDIO_MAX_BYTES // (1024 * 1024)} MB") from None
    path = listening_storage.ROOT / name
    size = path.stat().st_size
    if size == 0:
        await listening_storage.delete(name)
        raise _error(400, "EMPTY_FILE")
    digest = await asyncio.to_thread(_sha256, path)
    existing = db.scalar(select(A2AudioAsset).where(A2AudioAsset.sha256 == digest))
    if existing is not None:
        await listening_storage.delete(name)  # our own fresh copy; the existing entry is untouched
        raise _error(409, {"code": "DUPLICATE", "existing_id": str(existing.id), "existing_title": existing.title,
                           "existing_filename": existing.original_filename})

    values = {"unterricht": parsed["unterricht"], "audio_kind": parsed["audio_kind"], "part": parsed["part"], "title": parsed["title"]}
    values.update({k: v for k, v in explicit.items() if k in values})
    if values["unterricht"] is not None and not 1 <= values["unterricht"] <= _max_unterricht():
        values["unterricht"] = None  # "A2 15.Unterricht": no such lesson, the admin assigns it
    last = db.scalar(select(func.max(A2AudioAsset.sort_order)).where(A2AudioAsset.unterricht == values["unterricht"])) if values["unterricht"] else None
    asset = A2AudioAsset(
        level=LEVEL, **values, original_filename=original, parsed=parsed, storage_path=name, content_type=FORMATS[detected][0],
        audio_format=detected, size_bytes=size, sha256=digest, duration_seconds=explicit.get("duration_seconds"),
        sort_order=explicit.get("sort_order", (last or 0) + 1), verification=VERIFY_PENDING, uploaded_by=actor.id,
    )
    db.add(asset)
    try:
        db.commit()
    except IntegrityError:  # the same file uploaded twice at the same moment
        db.rollback()
        await listening_storage.delete(name)
        raise _error(409, {"code": "DUPLICATE"}) from None
    db.refresh(asset)
    return _one(db, asset)


# ---------- corrections, verification ----------

def update(db: Session, asset_id: UUID, data: dict) -> dict:
    asset = get(db, asset_id)
    for key, value in _clean_fields(data).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return _one(db, asset)


def verify(db: Session, actor: User, asset_id: UUID, state: str, note: str | None) -> dict:
    asset = get(db, asset_id)
    if state not in (VERIFY_OK, VERIFY_PROBLEM, VERIFY_PENDING):
        raise _error(422, "INVALID_VERIFICATION")
    note = (note or "").strip()[:NOTE_MAX] or None
    if state == VERIFY_OK and stored_path(asset) is None:
        raise _error(409, "FILE_MISSING: a file that is not in storage cannot be verified")
    if state == VERIFY_PROBLEM and not note:
        raise _error(422, "NOTE_REQUIRED: say what is wrong")
    asset.verification, asset.verification_note = state, note
    asset.verified_at, asset.verified_by = (None, None) if state == VERIFY_PENDING else (_now(), actor.id)
    db.commit()
    db.refresh(asset)
    return _one(db, asset)


# ---------- linking ----------

def _clear_task_audio(listening: Listening) -> None:
    listening.audio_storage_path = None
    listening.audio_content_type = None
    listening.audio_size_bytes = None
    listening.audio_original_name = None
    listening.audio_duration_seconds = None
    if not listening.audio_url:
        listening.is_published = False


def link(db: Session, actor: User, asset_id: UUID, listening_id: UUID) -> dict:
    asset = get(db, asset_id)
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise _error(404, "LISTENING_NOT_FOUND")
    lesson = _task_lesson(db, listening)
    if lesson is None:
        raise _error(422, "NOT_AN_A2_TASK: only Hören tasks of A2 lessons can be linked")
    if not is_current_task(listening):
        raise _error(409, "ARCHIVED_TASK: archived / legacy A2 tasks are part of the old archive")
    if asset.verification == VERIFY_PROBLEM:
        raise _error(409, "ASSET_HAS_PROBLEM: fix or replace the file first")
    if stored_path(asset) is None:
        raise _error(409, "FILE_MISSING")
    if asset.listening_id == listening.id and listening.audio_storage_path == asset.storage_path:
        return _one(db, asset)
    # the file moves away from its previous task
    if asset.listening_id is not None and asset.listening_id != listening.id:
        previous = db.get(Listening, asset.listening_id)
        if previous is not None and previous.audio_storage_path == asset.storage_path:
            _clear_task_audio(previous)
    # the task's other library file (if any) is released, it stays in the library
    for other in db.scalars(select(A2AudioAsset).where(A2AudioAsset.listening_id == listening.id, A2AudioAsset.id != asset.id)):
        other.listening_id, other.linked_at, other.linked_by = None, None, None
    db.flush()
    old = listening.audio_storage_path
    if old and old != asset.storage_path:
        in_library = db.scalar(select(A2AudioAsset.id).where(A2AudioAsset.storage_path == old).limit(1)) is not None
        if not in_library:  # keep the task's earlier audio in its version history — nothing is deleted
            db.add(ListeningAudioArchive(listening_id=listening.id, storage_path=old, original_name=listening.audio_original_name,
                                         content_type=listening.audio_content_type, size_bytes=listening.audio_size_bytes,
                                         duration_seconds=listening.audio_duration_seconds, replaced_by_id=actor.id, archived_at=_now()))
    listening.audio_storage_path = asset.storage_path
    listening.audio_content_type = asset.content_type
    listening.audio_size_bytes = asset.size_bytes
    listening.audio_original_name = asset.original_filename
    listening.audio_duration_seconds = asset.duration_seconds
    listening.is_published = False  # new audio: the admin checks audio + questions, then publishes
    asset.listening_id, asset.linked_at, asset.linked_by = listening.id, _now(), actor.id
    db.commit()
    db.refresh(asset)
    return _one(db, asset)


def unlink(db: Session, asset_id: UUID) -> dict:
    """The task stops playing this file (and goes back to draft); the file stays in the library."""
    asset = get(db, asset_id)
    if asset.listening_id is None:
        raise _error(409, "NOT_LINKED")
    listening = db.get(Listening, asset.listening_id)
    if listening is not None and listening.audio_storage_path == asset.storage_path:
        _clear_task_audio(listening)
    asset.listening_id, asset.linked_at, asset.linked_by = None, None, None
    db.commit()
    db.refresh(asset)
    return _one(db, asset)


def release_task(db: Session, listening: Listening) -> None:
    """Called when a task's audio is replaced or removed through the Hören
    endpoints: the library entry stays, only its link is dropped (no commit)."""
    for asset in db.scalars(select(A2AudioAsset).where(A2AudioAsset.listening_id == listening.id)):
        asset.listening_id, asset.linked_at, asset.linked_by = None, None, None


# ---------- removal (entry and file are separate decisions) ----------

def file_references(db: Session, storage_path: str, except_asset: UUID | None = None) -> int:
    """Everything that still points at a stored file: Hören tasks of every
    level, extra tracks, archived versions and other library entries."""
    count = 0
    for column in (Listening.audio_storage_path, ListeningAudioTrack.storage_path, ListeningAudioArchive.storage_path):
        count += db.scalar(select(func.count()).where(column == storage_path)) or 0
    q = select(func.count()).select_from(A2AudioAsset).where(A2AudioAsset.storage_path == storage_path)
    if except_asset is not None:
        q = q.where(A2AudioAsset.id != except_asset)
    return count + (db.scalar(q) or 0)


async def remove(db: Session, asset_id: UUID, delete_file: bool) -> dict:
    asset = get(db, asset_id)
    if asset.listening_id is not None:
        raise _error(409, "ASSET_LINKED: unlink it from the Hören task first")
    path = asset.storage_path
    file_deleted = False
    if delete_file:
        others = file_references(db, path, except_asset=asset.id)
        if others:
            raise _error(409, f"FILE_IN_USE: {others} other reference(s) — the file is kept, nothing was changed")
        try:
            await listening_storage.delete(path)  # file first: never "deleted" while it is still there
        except OSError:
            raise _error(500, "AUDIO_FILE_DELETE_FAILED: nothing was changed") from None
        file_deleted = True
    db.delete(asset)
    db.commit()
    return {"id": asset_id, "file_deleted": file_deleted, "file_kept": not file_deleted}


# ---------- manifest ----------

def manifest(db: Session) -> dict:
    """The A2 audio manifest from the real data: every library file per
    Unterricht, every current Hören task and whether it has audio. Nothing
    is assumed from a screenshot or a fixed list."""
    lessons = a2_lessons(db)
    tasks = a2_tasks(db, lessons)
    assets = list_assets(db)
    by_listening = {a["linked"]["listening_id"]: a for a in assets if a["linked"]}
    from app.services.lesson_skills.admin import listening_audio_path

    task_rows = []
    for t, lesson in tasks:
        asset = by_listening.get(t.id)
        has_file = listening_audio_path(t) is not None
        task_rows.append({"listening_id": t.id, "lesson_number": lesson.number, "lesson_title": lesson.title, "title": t.title,
                          "content_id": t.content_id, "order_index": t.order_index, "is_published": t.is_published,
                          "has_audio": has_file or bool(t.audio_url), "audio_source": "library" if asset else ("other" if has_file else None),
                          "asset_id": asset["id"] if asset else None, "audio_label": t.audio_label})
    count = lambda pred: sum(1 for a in assets if pred(a))  # noqa: E731
    return {
        "level": LEVEL, "generated_at": _now(),
        "counts": {
            "files": len(assets), "size_bytes": sum(a["size_bytes"] for a in assets),
            "by_format": {f.upper(): count(lambda a, f=f: a["audio_format"] == f.upper()) for f in FORMATS},
            "by_kind": {k: count(lambda a, k=k: a["audio_kind"] == k) for k in AUDIO_KINDS} | {"UNSET": count(lambda a: a["audio_kind"] is None)},
            "verified": count(lambda a: a["verification"] == VERIFY_OK), "problem": count(lambda a: a["verification"] == VERIFY_PROBLEM),
            "pending": count(lambda a: a["verification"] == VERIFY_PENDING), "linked": count(lambda a: a["linked"] is not None),
            "unlinked": count(lambda a: a["linked"] is None), "missing_file": count(lambda a: a["file_status"] != "ok"),
            "no_unterricht": count(lambda a: a["unterricht"] is None),
            "tasks": len(task_rows), "tasks_with_audio": sum(1 for r in task_rows if r["has_audio"]),
            "tasks_without_audio": sum(1 for r in task_rows if not r["has_audio"]),
        },
        "lessons": [{"number": lesson.number, "title": lesson.title, "is_published": lesson.is_published,
                     "assets": [a for a in assets if a["unterricht"] == lesson.number],
                     "tasks": [r for r in task_rows if r["lesson_number"] == lesson.number]} for lesson in lessons],
        "unassigned": [a for a in assets if a["unterricht"] is None],
        "missing_audio": [r for r in task_rows if not r["has_audio"]],
    }
