"""A2 4. Unterricht → Hören: three independent tasks "Text 1", "Text 2",
"Text 3" instead of the old "Familie Mannsberg" task.

Each Text is an ordinary Hören task (listenings row) of A2 lesson 4 with a
stable task_key (a2-u04-hoeren-text-N): students get it through the normal
Hören endpoints (require_lesson_access, published, audio streamed privately),
and questions / answer keys can be attached later with the existing Hören
question editor. No questions are created here.

Audio goes through the A2 Audio Manager (assets.py): the same format/content
checks and SHA-256 duplicate detection, the file is a library entry linked to
exactly one Text. Replacing one Text never touches the others. New audio is
"pending"; a Text can only be switched active when its audio is on the
server and was listened to ("verified").

The old task (current edition and the "[Archiv]" first-edition copy, both in
lesson 4 and titled "… Familie Mannsberg") is removed by remove_legacy, run
through app/scripts/a2_lesson4_hoeren.py: every row, question, option, key
and audio file is written to a backup folder first (files SHA-256 checked).
A task with learner attempts or answer-key reviews is NOT deleted (its
history would cascade away): it is archived instead — "[Archiv]" title,
unpublished, hidden from students and from the current A2 lists. A physical
file is only removed when no other row of any level still references it."""

import hashlib
import json
import shutil
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.a2_audio_asset import KIND_TEXT, VERIFY_OK, A2AudioAsset
from app.models.answer_key_review import AnswerKeyReview
from app.models.lesson import Lesson
from app.models.lesson_skill import LessonSkillAttempt, ListeningQuestion
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.listening_audio_track import ListeningAudioTrack
from app.models.user import User
from app.services.a2_audio import assets
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills.admin import listening_storage

LESSON = 4
SLOTS = (1, 2, 3)
LEGACY_TITLE = "Familie Mannsberg"


def task_key(slot: int) -> str:
    return f"a2-u04-hoeren-text-{slot}"


def slot_title(slot: int) -> str:
    return f"Hören: Text {slot}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _error(code: int, detail) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def lesson(db: Session) -> Lesson:
    found = next((item for item in assets.a2_lessons(db) if item.number == LESSON), None)
    if found is None:
        raise _error(404, "A2_LESSON_4_NOT_FOUND")
    return found


def _slot_tasks(db: Session, the_lesson: Lesson) -> dict[int, Listening]:
    rows = db.scalars(select(Listening).where(Listening.lesson_id == the_lesson.id, Listening.task_key.in_([task_key(n) for n in SLOTS])))
    by_key = {row.task_key: row for row in rows}
    return {n: by_key[task_key(n)] for n in SLOTS if task_key(n) in by_key}


def _slot_task(db: Session, slot: int) -> Listening:
    if slot not in SLOTS:
        raise _error(404, "SLOT_NOT_FOUND: Text 1, 2 or 3")
    task = _slot_tasks(db, lesson(db)).get(slot)
    if task is None:
        raise _error(409, "SLOT_NOT_SET_UP: create the Text 1-3 structure first")
    return task


def _linked_asset(db: Session, task: Listening) -> A2AudioAsset | None:
    return db.scalar(select(A2AudioAsset).where(A2AudioAsset.listening_id == task.id))


# ============================================================
# admin overview
# ============================================================

def _slot_state(db: Session, slot: int, task: Listening | None) -> dict:
    out = {"slot": slot, "label": f"Text {slot}", "task_key": task_key(slot), "exists": task is not None}
    if task is None:
        return out
    asset = _linked_asset(db, task)
    path = skill_admin.listening_audio_path(task)
    in_sync = asset is not None and task.audio_storage_path == asset.storage_path
    status = "ok" if path else ("missing" if task.audio_storage_path else "none")
    verified = in_sync and asset.verification == VERIFY_OK
    blocker = None
    if status == "none":
        blocker = "Kein Audio hochgeladen"
    elif status == "missing":
        blocker = "Audiodatei fehlt auf dem Server"
    elif not in_sync:
        blocker = "Audio wurde außerhalb dieser Seite gesetzt — bitte hier neu hochladen"
    elif not verified:
        blocker = "Audio noch nicht als geprüft markiert" if asset.verification != "problem" else "Audio hat ein Problem"
    return {
        **out,
        "listening_id": task.id, "title": task.title, "is_published": task.is_published, "order_index": task.order_index,
        "question_count": len(task.questions),
        "audio": {
            "status": status, "file_name": task.audio_original_name if task.audio_storage_path else None,
            "size_bytes": task.audio_size_bytes if path else None, "duration_seconds": task.audio_duration_seconds,
            "format": Path(task.audio_storage_path or "").suffix.lstrip(".").upper() or None,
            "source": "library" if in_sync else ("task" if task.audio_storage_path else None),
        },
        "asset": None if asset is None else {
            "id": asset.id, "verification": asset.verification, "verification_note": asset.verification_note,
            "verified_at": asset.verified_at, "sha256": asset.sha256, "uploaded_at": asset.created_at, "in_sync": in_sync,
        },
        "verified": verified,
        "can_activate": blocker is None,
        "activate_blocker": blocker,
    }


def overview(db: Session) -> dict:
    the_lesson = lesson(db)
    tasks = _slot_tasks(db, the_lesson)
    return {
        "level": "A2", "lesson_id": the_lesson.id, "lesson_number": the_lesson.number, "lesson_title": the_lesson.title,
        "set_up": len(tasks) == len(SLOTS),
        "slots": [_slot_state(db, n, tasks.get(n)) for n in SLOTS],
        # the old task still visible as a current task (removal pending)
        "legacy_tasks": [{"listening_id": t.id, "title": t.title, "is_published": t.is_published}
                         for t in legacy_tasks(db, the_lesson) if assets.is_current_task(t)],
    }


def ensure_slots(db: Session, actor: User | None = None) -> list[int]:
    """Creates the missing Text tasks (drafts, no audio, no questions). Idempotent."""
    the_lesson = lesson(db)
    existing = _slot_tasks(db, the_lesson)
    missing = [n for n in SLOTS if n not in existing]
    if not missing:
        return []
    old = next((t for t in legacy_tasks(db, the_lesson) if assets.is_current_task(t)), None)
    if old is not None:
        base = old.order_index
    else:
        last = db.scalar(select(func.max(Listening.order_index)).where(Listening.lesson_id == the_lesson.id))
        base = (last or 0) + 1
    for n in missing:
        db.add(Listening(lesson_id=the_lesson.id, title=slot_title(n), task_key=task_key(n), order_index=base + n - 1, is_published=False))
    db.commit()
    write_audit(db, actor_id=str(actor.id) if actor else None, action="a2_l04_hoeren_slots_created",
                details=f"lesson={the_lesson.id}; slots={','.join(f'Text {n}' for n in missing)}")
    return missing


# ============================================================
# per Text: upload / replace, verify, activate, delete
# ============================================================

async def upload(db: Session, actor: User, slot: int, file: UploadFile, duration_seconds: int | None) -> dict:
    """Uploads (or replaces) the audio of one Text. The file is checked by the
    A2 Audio Manager; the same content already in the library is reused when
    it is not linked anywhere, refused when another task plays it."""
    task = _slot_task(db, slot)
    fields = {"unterricht": LESSON, "audio_kind": KIND_TEXT, "part": slot, "duration_seconds": duration_seconds}
    reused = False
    try:
        uploaded = await assets.upload(db, actor, file, fields)
        asset_id = uploaded["id"]
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        if exc.status_code != 409 or detail.get("code") != "DUPLICATE" or not detail.get("existing_id"):
            raise
        existing = assets.get(db, UUID(detail["existing_id"]))
        if existing.listening_id == task.id:
            raise _error(409, {"code": "SAME_FILE", "message": f"Text {slot} hat diese Datei bereits."}) from None
        if existing.listening_id is not None:
            other = db.get(Listening, existing.listening_id)
            raise _error(409, {"code": "DUPLICATE", "existing_id": str(existing.id), "existing_filename": existing.original_filename,
                               "used_by": other.title if other else None}) from None
        assets.update(db, existing.id, {k: v for k, v in fields.items() if k != "duration_seconds" or v})
        asset_id, reused = existing.id, True
    previous = _linked_asset(db, task)
    assets.link(db, actor, asset_id, task.id)  # task -> draft; the previous file stays in the library, unlinked
    write_audit(db, actor_id=str(actor.id), action="a2_l04_hoeren_audio_uploaded",
                details=f"slot=Text {slot}; listening={task.id}; asset={asset_id}; reused={reused}; "
                        f"previous_asset={previous.id if previous and previous.id != asset_id else None}")
    db.refresh(task)
    return {**_slot_state(db, slot, task), "reused": reused}


def verify(db: Session, actor: User, slot: int, state: str, note: str | None) -> dict:
    task = _slot_task(db, slot)
    asset = _linked_asset(db, task)
    if asset is None or task.audio_storage_path != asset.storage_path:
        raise _error(409, "NO_LIBRARY_AUDIO: upload the audio on this page first")
    assets.verify(db, actor, asset.id, state, note)
    if state != VERIFY_OK and task.is_published:
        task.is_published = False  # an unchecked / faulty file is not shown to students
        db.commit()
    write_audit(db, actor_id=str(actor.id), action="a2_l04_hoeren_audio_verified", details=f"slot=Text {slot}; asset={asset.id}; state={state}")
    db.refresh(task)
    return _slot_state(db, slot, task)


def set_active(db: Session, actor: User, slot: int, active: bool) -> dict:
    task = _slot_task(db, slot)
    state = _slot_state(db, slot, task)
    if active and not state["can_activate"]:
        raise _error(409, f"CANNOT_ACTIVATE: {state['activate_blocker']}")
    task.is_published = bool(active)
    db.commit()
    write_audit(db, actor_id=str(actor.id), action="a2_l04_hoeren_task_active", details=f"slot=Text {slot}; listening={task.id}; active={bool(active)}")
    db.refresh(task)
    return _slot_state(db, slot, task)


async def remove_audio(db: Session, actor: User, slot: int) -> dict:
    """The Text loses its audio and becomes inactive; the library entry goes
    and the file is deleted unless something else still uses it."""
    task = _slot_task(db, slot)
    asset = _linked_asset(db, task)
    file_deleted = False
    if asset is not None:
        assets.unlink(db, asset.id)
        others = assets.file_references(db, asset.storage_path, except_asset=asset.id)
        result = await assets.remove(db, asset.id, delete_file=others == 0)
        file_deleted = result["file_deleted"]
        detail = f"asset={asset.id}; file_deleted={file_deleted}"
    elif task.audio_storage_path:
        await skill_admin.delete_listening_audio(db, task.id)
        detail = "task audio (not from the library)"
    else:
        raise _error(404, "NO_AUDIO")
    db.refresh(task)
    if task.is_published:
        task.is_published = False
        db.commit()
    write_audit(db, actor_id=str(actor.id), action="a2_l04_hoeren_audio_deleted", details=f"slot=Text {slot}; listening={task.id}; {detail}")
    return {**_slot_state(db, slot, task), "file_deleted": file_deleted}


def audio_path(db: Session, slot: int) -> tuple[Path, str]:
    task = _slot_task(db, slot)
    path = skill_admin.listening_audio_path(task)
    if path is None:
        raise _error(404, "Audio not found.")
    return path, task.audio_content_type or "audio/mpeg"


# ============================================================
# removal of the old "Familie Mannsberg" task (script, with backup)
# ============================================================

def legacy_tasks(db: Session, the_lesson: Lesson) -> list[Listening]:
    """Hören tasks of A2 lesson 4 about "Familie Mannsberg" — this lesson only."""
    return list(db.scalars(select(Listening).where(Listening.lesson_id == the_lesson.id, Listening.task_key.is_(None),
                                                   Listening.title.ilike(f"%{LEGACY_TITLE}%"))
                           .order_by(Listening.order_index, Listening.created_at)))


def _row(obj) -> dict:
    return {c.name: getattr(obj, c.key) for c in obj.__table__.columns}


def _json_default(value):
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _files(db: Session, task: Listening) -> list[str]:
    paths = [task.audio_storage_path] + [t.storage_path for t in task.audio_tracks]
    paths += list(db.scalars(select(ListeningAudioArchive.storage_path).where(ListeningAudioArchive.listening_id == task.id)))
    return sorted({p for p in paths if p})


def _history(db: Session, task: Listening) -> dict:
    question_ids = [q.id for q in task.questions]
    attempts = db.scalar(select(func.count()).select_from(LessonSkillAttempt).where(LessonSkillAttempt.listening_id == task.id)) or 0
    reviews = (db.scalar(select(func.count()).select_from(AnswerKeyReview).where(AnswerKeyReview.listening_question_id.in_(question_ids))) or 0) \
        if question_ids else 0
    return {"attempts": attempts, "answer_key_reviews": reviews}


def _all_references(db: Session, storage_path: str) -> int:
    count = 0
    for column in (Listening.audio_storage_path, ListeningAudioTrack.storage_path, ListeningAudioArchive.storage_path, A2AudioAsset.storage_path):
        count += db.scalar(select(func.count()).where(column == storage_path)) or 0
    return count


def plan(db: Session) -> dict:
    """Read-only: what remove_legacy would do, with a plan id."""
    the_lesson = lesson(db)
    tasks = []
    for t in legacy_tasks(db, the_lesson):
        history = _history(db, t)
        keep = bool(history["attempts"] or history["answer_key_reviews"])
        if keep and not assets.is_current_task(t) and not t.is_published:
            continue  # already archived with its history: nothing left to do
        files = []
        for rel in _files(db, t):
            path = skill_admin._stored(rel)
            files.append({"storage_path": rel, "on_disk": path is not None, "size_bytes": path.stat().st_size if path else None,
                          "references": _all_references(db, rel)})
        tasks.append({
            "listening_id": t.id, "title": t.title, "content_id": t.content_id, "is_published": t.is_published,
            "archived": not assets.is_current_task(t), "questions": len(t.questions),
            "options": sum(len(q.options) for q in t.questions), "tracks": len(t.audio_tracks), "files": files,
            "library_assets": [str(a) for a in db.scalars(select(A2AudioAsset.id).where(A2AudioAsset.listening_id == t.id))],
            **history, "action": "archive" if keep else "delete",
        })
    digest = hashlib.sha256(json.dumps([[str(t["listening_id"]), t["action"], [f["storage_path"] for f in t["files"]]] for t in tasks]).encode())
    return {"lesson_id": the_lesson.id, "lesson_number": the_lesson.number, "tasks": tasks, "plan_id": digest.hexdigest()[:12],
            "slots_missing": [n for n in SLOTS if n not in _slot_tasks(db, the_lesson)]}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _backup(db: Session, tasks: list[Listening], folder: Path) -> dict:
    """Every row of the old tasks + copies of their audio files (SHA-256 checked)."""
    (folder / "files").mkdir(parents=True, exist_ok=False)
    data = []
    files = {}
    for t in tasks:
        questions = []
        for q in t.questions:
            reviews = db.scalars(select(AnswerKeyReview).where(AnswerKeyReview.listening_question_id == q.id))
            questions.append({**_row(q), "options": [_row(o) for o in q.options], "answer_key_reviews": [_row(r) for r in reviews]})
        archives = db.scalars(select(ListeningAudioArchive).where(ListeningAudioArchive.listening_id == t.id))
        library = db.scalars(select(A2AudioAsset).where(A2AudioAsset.listening_id == t.id))
        data.append({"listening": _row(t), "questions": questions, "audio_tracks": [_row(tr) for tr in t.audio_tracks],
                     "audio_archives": [_row(a) for a in archives], "a2_audio_assets": [_row(a) for a in library], **_history(db, t)})
        for rel in _files(db, t):
            if rel in files:
                continue
            src = skill_admin._stored(rel)
            if src is None:
                files[rel] = {"on_disk": False}
                continue
            dst = folder / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            digest = _sha256(src)
            if _sha256(dst) != digest:
                raise RuntimeError(f"backup copy of {rel} does not match — nothing was changed")
            files[rel] = {"on_disk": True, "sha256": digest, "size_bytes": src.stat().st_size}
    (folder / "tasks.json").write_text(json.dumps(data, default=_json_default, ensure_ascii=False, indent=1), encoding="utf-8")
    (folder / "files.json").write_text(json.dumps(files, ensure_ascii=False, indent=1), encoding="utf-8")
    return files


async def remove_legacy(db: Session, backup_root: Path, confirm: str, actor: User | None = None) -> dict:
    """Backup, then: delete (no history) or archive (history) each old task,
    remove the files nothing references any more, create the Text 1-3 tasks."""
    current = plan(db)
    if confirm != current["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {current['plan_id']} — nothing was changed")
    actions = {str(t["listening_id"]): t["action"] for t in current["tasks"]}
    tasks = [t for t in legacy_tasks(db, lesson(db)) if str(t.id) in actions]
    folder = backup_root / f"a2-l04-hoeren-{_now().strftime('%Y%m%d-%H%M%S-%f')}-{current['plan_id']}"
    files = _backup(db, tasks, folder) if tasks else {}
    touched_files = set(files)
    done = []
    actor_id = str(actor.id) if actor else None
    # the Text tasks take the old task's place in the lesson before it goes
    created = ensure_slots(db, actor)
    for t in tasks:
        task_id, title = str(t.id), t.title
        action = actions[task_id]
        assets.release_task(db, t)
        if action == "archive":
            if assets.is_current_task(t):
                t.title = f"{assets.ARCHIVE_PREFIX} {t.title}"[: assets.TITLE_MAX]
            t.is_published = False
        else:
            for row in db.scalars(select(ListeningAudioArchive).where(ListeningAudioArchive.listening_id == t.id)):
                db.delete(row)
            db.delete(t)  # questions, options, key reviews and extra tracks cascade
        db.commit()
        done.append({"listening_id": task_id, "title": title, "action": action})
        write_audit(db, actor_id=actor_id, action=f"a2_l04_legacy_task_{'archived' if action == 'archive' else 'deleted'}",
                    details=f"listening={task_id}; title={title}; backup={folder}")
    removed_files, kept_files = [], []
    for rel in sorted(touched_files):
        if not files[rel].get("on_disk"):
            continue
        refs = _all_references(db, rel)
        if refs:
            kept_files.append({"storage_path": rel, "references": refs})
            continue
        await listening_storage.delete(rel)
        removed_files.append(rel)
    if removed_files:
        write_audit(db, actor_id=actor_id, action="a2_l04_legacy_audio_deleted",
                    details=f"files={','.join(removed_files)}; backup={folder}")
    report = {"plan_id": current["plan_id"], "backup": str(folder), "tasks": done, "files_removed": removed_files,
              "files_kept": kept_files, "slots_created": created}
    if tasks:
        (folder / "report.json").write_text(json.dumps(report, default=_json_default, ensure_ascii=False, indent=1), encoding="utf-8")
    return report
