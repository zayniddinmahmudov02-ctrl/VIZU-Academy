"""Admin side of the lesson skills: question editing (Lesen / Hören), Hören
audio upload, task duplication, per-student results, manual score override
and re-evaluation. Every function assumes the caller already passed the
admin-panel permission check (router dependency)."""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage.protected_local import ProtectedLessonListeningStorage
from app.models.lesson_skill import (
    EVAL_KIND_SPEAKING,
    EVAL_KIND_WRITING,
    CONFIG_TYPES,
    QUESTION_TRUE_FALSE,
    QUESTION_TYPES,
    AiEvaluation,
    LessonSkillAttempt,
    ListeningOption,
    ListeningQuestion,
)
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.listening_audio_track import ListeningAudioTrack
from app.models.reading import Reading
from app.models.reading_option import ReadingOption
from app.models.reading_question import ReadingQuestion
from app.models.speaking import Speaking
from app.models.student_speaking import StudentSpeaking
from app.models.student_writing import StudentWriting
from app.models.user import User
from app.models.writing import Writing
from app.services.lesson_skills import ai_evaluation
from app.services.lesson_skills import question_types as qt
from app.services.lesson_skills.results import lesson_skill_results

listening_storage = ProtectedLessonListeningStorage()

MAX_AUDIO_BYTES = 100 * 1024 * 1024  # the book audio files reach ~27 MB
# extension -> (content type, accepted declared types)
AUDIO_FORMATS = {
    "mp3": ("audio/mpeg", {"audio/mpeg", "audio/mp3"}),
    "wav": ("audio/wav", {"audio/wav", "audio/x-wav", "audio/wave"}),
    "m4a": ("audio/mp4", {"audio/mp4", "audio/x-m4a", "audio/m4a"}),
}
ALL_AUDIO_TYPES = set().union(*(types for _, types in AUDIO_FORMATS.values()))


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Questions (shared validation)
# ============================================================


def validate_questions(items: list[dict]) -> list[dict]:
    if len(items) > 100:
        raise HTTPException(status_code=422, detail="Too many questions (max 100).")
    clean = []
    for n, q in enumerate(items, start=1):
        text_value = str(q.get("question", "")).strip()
        qtype = str(q.get("question_type", "MULTIPLE_CHOICE")).upper()
        options = q.get("options") or []
        if not text_value or len(text_value) > 2000:
            raise HTTPException(status_code=422, detail=f"Question {n}: text is required (max 2000 characters).")
        if qtype not in QUESTION_TYPES:
            raise HTTPException(status_code=422, detail=f"Question {n}: unknown type.")
        config = None
        if qtype in CONFIG_TYPES:
            try:
                config = qt.validate_config(qtype, q.get("config"))
            except qt.QuestionConfigError as exc:
                raise HTTPException(status_code=422, detail=f"Question {n}: {exc}") from None
            options = []
        elif qtype == QUESTION_TRUE_FALSE and len(options) != 2:
            raise HTTPException(status_code=422, detail=f"Question {n}: Richtig/Falsch needs exactly 2 options.")
        if qtype not in CONFIG_TYPES and not 2 <= len(options) <= 6:
            raise HTTPException(status_code=422, detail=f"Question {n}: 2-6 options are required.")
        opts = []
        for o in options:
            otext = str(o.get("text", "")).strip()
            if not otext or len(otext) > 500:
                raise HTTPException(status_code=422, detail=f"Question {n}: every option needs a text (max 500).")
            opts.append({"id": o.get("id"), "text": otext, "is_correct": bool(o.get("is_correct"))})
        if qtype not in CONFIG_TYPES and sum(o["is_correct"] for o in opts) != 1:
            raise HTTPException(status_code=422, detail=f"Question {n}: exactly one option must be correct.")
        raw_points = q.get("points", 1)
        try:
            points = int(1 if raw_points is None else raw_points)
        except (TypeError, ValueError):
            points = 0
        if not 1 <= points <= 100:
            raise HTTPException(status_code=422, detail=f"Question {n}: points must be 1-100.")
        clean.append(
            {
                "id": q.get("id"),
                "question": text_value,
                "question_type": qtype,
                "points": points,
                "explanation": (str(q.get("explanation") or "").strip() or None),
                "options": opts,
                "config": config,
            }
        )
    return clean


def _sync_questions(db: Session, existing: list, items: list[dict], new_question, new_option) -> None:
    """Upsert by id; questions/options missing from the payload are removed."""
    by_id = {str(q.id): q for q in existing}
    keep = set()
    for order, item in enumerate(items, start=1):
        q = by_id.get(str(item["id"])) if item["id"] else None
        if q is None:
            q = new_question()
            db.add(q)
        q.question = item["question"]
        q.question_type = item["question_type"]
        q.points = item["points"]
        q.explanation = item["explanation"]
        q.config = item.get("config")
        q.order_index = order
        db.flush()
        keep.add(str(q.id))
        opt_by_id = {str(o.id): o for o in q.options}
        keep_opts = set()
        for o_order, o_item in enumerate(item["options"], start=1):
            o = opt_by_id.get(str(o_item["id"])) if o_item["id"] else None
            if o is None:
                o = new_option(q)
                db.add(o)
            o.option_text = o_item["text"]
            o.is_correct = o_item["is_correct"]
            o.order_index = o_order
            db.flush()
            keep_opts.add(str(o.id))
        for oid, o in opt_by_id.items():
            if oid not in keep_opts:
                db.delete(o)
    for qid, q in by_id.items():
        if qid not in keep:
            db.delete(q)
    db.commit()


def admin_question(q) -> dict:
    return {
        "id": q.id,
        "question": q.question,
        "question_type": q.question_type,
        "points": q.points,
        "explanation": q.explanation,
        "config": q.config,
        "options": [
            {"id": o.id, "text": o.option_text, "is_correct": o.is_correct}
            for o in sorted(q.options, key=lambda o: (o.order_index, o.created_at))
        ],
    }


def replace_reading_questions(db: Session, reading_id: UUID, items: list[dict]) -> Reading:
    reading = db.get(Reading, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Reading not found.")
    clean = validate_questions(items)
    _sync_questions(
        db,
        list(reading.questions),
        clean,
        lambda: ReadingQuestion(reading_id=reading.id, question="", is_published=True),
        lambda q: ReadingOption(question_id=q.id, option_text=""),
    )
    for q in reading.questions:  # questions follow the text's publish state
        q.is_published = True
    db.commit()
    db.refresh(reading)
    return reading


def replace_listening_questions(db: Session, listening_id: UUID, items: list[dict]) -> Listening:
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    clean = validate_questions(items)
    _sync_questions(
        db,
        list(listening.questions),
        clean,
        lambda: ListeningQuestion(listening_id=listening.id, question=""),
        lambda q: ListeningOption(question_id=q.id, option_text=""),
    )
    db.refresh(listening)
    # A1: the last missing answer key entered -> publish once the audio is there
    from app.services.lesson_skills.hoeren_pdf_import import auto_publish

    if auto_publish(db, listening) == "published":
        db.refresh(listening)
    return listening


# ============================================================
# Hören audio
# ============================================================


def _detect_audio(head: bytes) -> str | None:
    if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return "mp3"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[4:8] == b"ftyp":
        return "m4a"
    return None


async def _store_audio(file: UploadFile, expected_format: str | None = None) -> tuple[str, str]:
    """Validates and stores one uploaded audio file privately; returns
    (storage name, detected format). Same rules for the main audio and the
    extra tracks."""
    declared = (file.content_type or "").split(";")[0].strip().lower()
    head = await file.read(16)
    await file.seek(0)
    detected = _detect_audio(head)
    if expected_format and detected != expected_format.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A2 material requires {expected_format.upper()} audio.",
        )
    # the content decides: book files named .mp3 are sometimes WAV (A1-3.mp3, A1-5.mp3) and the
    # browser declares them audio/mpeg — any declared audio type is fine, the stored type is the detected one
    declared_ok = detected is not None and (declared in AUDIO_FORMATS[detected][1] or declared in ALL_AUDIO_TYPES)
    if not declared_ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_AUDIO: allowed are MP3, WAV and M4A files.")
    name = f"{uuid4().hex}.{detected}"
    try:
        await listening_storage.upload(file, name, max_bytes=MAX_AUDIO_BYTES)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AUDIO_TOO_LARGE: max 100 MB.") from None
    return name, detected


def _duration(seconds: int | None) -> int | None:
    return seconds if seconds and 0 < seconds < 6 * 3600 else None


def file_references(db: Session, storage_path: str) -> int:
    """How many Hören tasks / tracks point at this stored file."""
    from sqlalchemy import func

    return int(db.scalar(select(func.count()).select_from(Listening).where(Listening.audio_storage_path == storage_path)) or 0) \
        + int(db.scalar(select(func.count()).select_from(ListeningAudioTrack).where(ListeningAudioTrack.storage_path == storage_path)) or 0)


async def _delete_if_unused(db: Session, storage_path: str | None) -> bool:
    """Removes a stored audio file only when no task or track references it
    any more (call after the referencing row was changed and committed)."""
    if not storage_path or file_references(db, storage_path):
        return False
    await listening_storage.delete(storage_path)
    return True


async def upload_listening_audio(
    db: Session,
    listening_id: UUID,
    file: UploadFile,
    duration_seconds: int | None,
    *,
    preserve_previous: bool = False,
    replaced_by_id: UUID | None = None,
    allow_auto_publish: bool = True,
    expected_format: str | None = None,
) -> Listening:
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    if listening.a2_material_key:
        # legacy A2-mapped task: replacing keeps the old file (archived) and never auto-publishes
        preserve_previous = True
        allow_auto_publish = False
    name, detected = await _store_audio(file, expected_format)
    if listening.a2_material_key:
        listening.is_published = False
    old = listening.audio_storage_path
    if preserve_previous and old:
        db.add(
            ListeningAudioArchive(
                listening_id=listening.id,
                storage_path=old,
                original_name=listening.audio_original_name,
                content_type=listening.audio_content_type,
                size_bytes=listening.audio_size_bytes,
                duration_seconds=listening.audio_duration_seconds,
                replaced_by_id=replaced_by_id,
                archived_at=_now(),
            )
        )
    listening.audio_storage_path = name
    listening.audio_content_type = AUDIO_FORMATS[detected][0]
    listening.audio_size_bytes = (listening_storage.ROOT / name).stat().st_size
    listening.audio_original_name = (file.filename or "")[:255] or None
    listening.audio_duration_seconds = _duration(duration_seconds)
    db.commit()
    db.refresh(listening)
    if not preserve_previous:
        await _delete_if_unused(db, old)  # the replaced file — only if nothing else uses it
    # A1: audio + complete answer keys -> "Veröffentlicht" automatically
    if allow_auto_publish:
        from app.services.lesson_skills.hoeren_pdf_import import auto_publish

        if auto_publish(db, listening) == "published":
            db.refresh(listening)
    return listening


async def delete_listening_audio(db: Session, listening_id: UUID) -> Listening:
    """Removes the uploaded audio file. A Hören task cannot be published
    without audio, so it is hidden again (questions and answers are kept)."""
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    if listening.a2_material_key:
        raise HTTPException(
            status_code=409,
            detail="A2 material audio cannot be removed; replace it to preserve its archive history.",
        )
    if not listening.audio_storage_path:
        raise HTTPException(status_code=404, detail="Audio not found.")
    old = listening.audio_storage_path
    listening.audio_storage_path = None
    listening.audio_content_type = None
    listening.audio_size_bytes = None
    listening.audio_original_name = None
    listening.audio_duration_seconds = None
    if not listening.audio_url:
        listening.is_published = False
    db.commit()
    await _delete_if_unused(db, old)
    db.refresh(listening)
    return listening


def _stored(storage_path: str | None) -> Path | None:
    if not storage_path:
        return None
    path = (listening_storage.ROOT / storage_path).resolve()
    root = listening_storage.ROOT.resolve()
    return path if root in path.parents and path.exists() else None


def listening_audio_path(listening: Listening) -> Path | None:
    return _stored(listening.audio_storage_path)


# ============================================================
# Extra labelled audio tracks (e.g. "Audio von Alisa" / "Audio von Alex")
# ============================================================

LABEL_MAX = 120


def _clean_label(label: str | None) -> str | None:
    text = " ".join(str(label or "").split())[:LABEL_MAX]
    return text or None


def _reject_a2_extra_track_edit(db: Session, listening_id: UUID) -> None:
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    if listening.a2_material_key:
        raise HTTPException(
            status_code=409,
            detail="Each A2 audio material has its own task; manage its main audio in Media Management.",
        )


def track_audio_path(track: ListeningAudioTrack) -> Path | None:
    return _stored(track.storage_path)


def tracks_state(listening: Listening) -> str:
    """ok (every extra track has its file) | file_missing — 'ok' when there are none."""
    return "ok" if all(track_audio_path(t) is not None for t in listening.audio_tracks) else "file_missing"


def _track(db: Session, listening_id: UUID, track_id: UUID) -> ListeningAudioTrack:
    track = db.get(ListeningAudioTrack, track_id)
    if track is None or str(track.listening_id) != str(listening_id):
        raise HTTPException(status_code=404, detail="Audio track not found.")
    return track


def set_audio_label(db: Session, listening_id: UUID, label: str | None) -> Listening:
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    listening.audio_label = _clean_label(label)
    db.commit()
    db.refresh(listening)
    return listening


async def upload_audio_track(db: Session, listening_id: UUID, label: str, file: UploadFile, duration_seconds: int | None,
                             track_id: UUID | None = None) -> ListeningAudioTrack:
    """New track (track_id None) or replace the file of an existing one. The
    old file is removed only after the new one is stored — and only because
    every track owns its file (copies get their own file, see duplicate)."""
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    _reject_a2_extra_track_edit(db, listening_id)
    clean = _clean_label(label)
    track = _track(db, listening_id, track_id) if track_id else None
    if track is None and not clean:
        raise HTTPException(status_code=422, detail="LABEL_REQUIRED: e.g. „Audio von Alex“.")
    name, detected = await _store_audio(file)
    old = track.storage_path if track else None
    if track is None:
        track = ListeningAudioTrack(listening_id=listening.id, label=clean,
                                    order_index=max([t.order_index for t in listening.audio_tracks] or [0]) + 1)
        db.add(track)
    elif clean:
        track.label = clean
    track.storage_path = name
    track.content_type = AUDIO_FORMATS[detected][0]
    track.size_bytes = (listening_storage.ROOT / name).stat().st_size
    track.original_name = (file.filename or "")[:255] or None
    track.duration_seconds = _duration(duration_seconds)
    db.commit()
    db.refresh(track)
    if old and old != name:
        await _delete_if_unused(db, old)
    # A1: every slot filled + complete verified keys -> "Veröffentlicht" (same rule as the main audio)
    from app.services.lesson_skills.hoeren_pdf_import import auto_publish

    db.refresh(listening)
    auto_publish(db, listening)
    return track


async def clear_audio_track_file(db: Session, listening_id: UUID, track_id: UUID) -> ListeningAudioTrack:
    """Removes only the FILE of a track — the slot (label, order) stays, ready
    for a new upload (A1 L14 „Text von Alisa“ / „Text von Alex“). A task with
    an empty slot is incomplete, so it is hidden again (questions are kept)."""
    _reject_a2_extra_track_edit(db, listening_id)
    track = _track(db, listening_id, track_id)
    if not track.storage_path:
        raise HTTPException(status_code=404, detail="Audio not found.")
    old = track.storage_path
    track.storage_path = None
    track.content_type = None
    track.size_bytes = None
    track.original_name = None
    track.duration_seconds = None
    listening = db.get(Listening, listening_id)
    if listening is not None and not listening.audio_url:
        listening.is_published = False
    db.commit()
    await _delete_if_unused(db, old)
    db.refresh(track)
    return track


def rename_audio_track(db: Session, listening_id: UUID, track_id: UUID, label: str) -> ListeningAudioTrack:
    _reject_a2_extra_track_edit(db, listening_id)
    track = _track(db, listening_id, track_id)
    clean = _clean_label(label)
    if not clean:
        raise HTTPException(status_code=422, detail="LABEL_REQUIRED")
    track.label = clean
    db.commit()
    db.refresh(track)
    return track


async def delete_audio_track(db: Session, listening_id: UUID, track_id: UUID) -> None:
    """Removes the track row and its file (unless another task / track uses the same file)."""
    _reject_a2_extra_track_edit(db, listening_id)
    track = _track(db, listening_id, track_id)
    old = track.storage_path
    db.delete(track)
    db.commit()
    await _delete_if_unused(db, old)


def audio_tracks_public(listening: Listening) -> list[dict]:
    """The task's audio as an ordered list: the main audio first, then the
    extra tracks — only entries whose file exists. No storage paths."""
    out = []
    if listening_audio_path(listening) is not None:
        out.append({"id": "main", "label": listening.audio_label, "duration_seconds": listening.audio_duration_seconds})
    for t in listening.audio_tracks:
        if track_audio_path(t) is not None:
            out.append({"id": str(t.id), "label": t.label, "duration_seconds": t.duration_seconds})
    return out


def audio_tracks_admin(listening: Listening) -> list[dict]:
    """Admin view of every audio slot (also the empty / missing ones)."""
    main_path = listening_audio_path(listening)
    out = [{"id": "main", "label": listening.audio_label, "file_name": listening.audio_original_name if listening.audio_storage_path else None,
            "size_bytes": listening.audio_size_bytes if main_path else None, "duration_seconds": listening.audio_duration_seconds,
            "file_status": "ok" if main_path else ("missing" if listening.audio_storage_path else ("external" if listening.audio_url else "none"))}]
    for t in listening.audio_tracks:
        path = track_audio_path(t)
        out.append({"id": str(t.id), "label": t.label, "file_name": t.original_name, "size_bytes": t.size_bytes if path else None,
                    "duration_seconds": t.duration_seconds, "file_status": "ok" if path else ("missing" if t.storage_path else "none")})
    return out


# ============================================================
# Duplicate
# ============================================================


def _copy_title(title: str) -> str:
    return f"{title} (Kopie)"[:255]


def duplicate_reading(db: Session, reading_id: UUID) -> Reading:
    src = db.get(Reading, reading_id)
    if src is None:
        raise HTTPException(status_code=404, detail="Reading not found.")
    copy = Reading(lesson_id=src.lesson_id, title=_copy_title(src.title), content=src.content, order_index=src.order_index + 1, is_published=False,
                   image_url=src.image_url)
    db.add(copy)
    db.flush()
    for q in src.questions:
        nq = ReadingQuestion(reading_id=copy.id, question=q.question, explanation=q.explanation, order_index=q.order_index,
                             is_published=q.is_published, question_type=q.question_type, points=q.points, config=q.config)
        db.add(nq)
        db.flush()
        for o in q.options:
            db.add(ReadingOption(question_id=nq.id, option_text=o.option_text, is_correct=o.is_correct, order_index=o.order_index))
    db.commit()
    db.refresh(copy)
    return copy


def duplicate_listening(db: Session, listening_id: UUID) -> Listening:
    src = db.get(Listening, listening_id)
    if src is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    copy = Listening(
        lesson_id=src.lesson_id, title=_copy_title(src.title), audio_url=src.audio_url, transcript=src.transcript,
        instruction=src.instruction, order_index=src.order_index + 1, is_published=False,
        audio_content_type=src.audio_content_type, audio_size_bytes=src.audio_size_bytes,
        audio_duration_seconds=src.audio_duration_seconds, audio_original_name=src.audio_original_name, audio_label=src.audio_label,
    )
    source_path = listening_audio_path(src)
    if source_path is not None:
        name = f"{uuid4().hex}{source_path.suffix}"
        shutil.copyfile(source_path, listening_storage.ROOT / name)
        copy.audio_storage_path = name
    db.add(copy)
    db.flush()
    for t in src.audio_tracks:  # every track of the copy gets its own file
        path = track_audio_path(t)
        name = None
        if path is not None:
            name = f"{uuid4().hex}{path.suffix}"
            shutil.copyfile(path, listening_storage.ROOT / name)
        db.add(ListeningAudioTrack(listening_id=copy.id, label=t.label, order_index=t.order_index, storage_path=name,
                                   content_type=t.content_type, size_bytes=t.size_bytes, duration_seconds=t.duration_seconds,
                                   original_name=t.original_name))
    for q in src.questions:
        nq = ListeningQuestion(listening_id=copy.id, question=q.question, question_type=q.question_type, points=q.points,
                               explanation=q.explanation, order_index=q.order_index, config=q.config)
        db.add(nq)
        db.flush()
        for o in q.options:
            db.add(ListeningOption(question_id=nq.id, option_text=o.option_text, is_correct=o.is_correct, order_index=o.order_index))
    db.commit()
    db.refresh(copy)
    return copy


_TASK_COPY_FIELDS = {
    Writing: ("lesson_id", "instruction", "min_words", "max_words", "order_index", "ai_evaluation_enabled", "ai_instructions",
              "feedback_language", "max_score", "rubric", "max_attempts", "helper_words", "image_url", "opens_at", "closes_at",
              "text_type", "audience", "time_limit_minutes"),
    Speaking: ("lesson_id", "topic", "instruction", "sample_answer", "keywords", "preparation_time", "speaking_time", "order_index",
               "ai_evaluation_enabled", "ai_instructions", "feedback_language", "max_score", "rubric", "max_attempts", "min_duration_seconds",
               "response_type", "questions", "speech_goal"),
}


def duplicate_task(db: Session, model, task_id: UUID):
    src = db.get(model, task_id)
    if src is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    copy = model(title=_copy_title(src.title), is_published=False, **{f: getattr(src, f) for f in _TASK_COPY_FIELDS[model]})
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


# ============================================================
# Results
# ============================================================


def lesson_students(db: Session, lesson_id: UUID) -> list[dict]:
    """Every student with any Lesen/Hören attempt or Schreiben/Sprechen
    submission in this lesson, with their skill results."""
    user_ids = set(db.scalars(select(LessonSkillAttempt.user_id).where(LessonSkillAttempt.lesson_id == lesson_id)))
    writing_ids = list(db.scalars(select(Writing.id).where(Writing.lesson_id == lesson_id)))
    speaking_ids = list(db.scalars(select(Speaking.id).where(Speaking.lesson_id == lesson_id)))
    if writing_ids:
        user_ids |= set(db.scalars(select(StudentWriting.user_id).where(StudentWriting.writing_id.in_(writing_ids))))
    if speaking_ids:
        user_ids |= set(db.scalars(select(StudentSpeaking.user_id).where(StudentSpeaking.speaking_id.in_(speaking_ids))))
    rows = []
    for user in db.scalars(select(User).where(User.id.in_([u for u in user_ids if u]))):
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
        rows.append({"user_id": user.id, "student_name": name, "email": user.email, **lesson_skill_results(db, user.id, lesson_id)})
    rows.sort(key=lambda r: r["student_name"].lower())
    return rows


def _history(db: Session, kind: str, submission_id: UUID) -> list[dict]:
    return [
        {"id": e.id, "source": e.source, "status": e.status, "score": e.score, "error": e.error, "model": e.model,
         "actor_id": e.actor_id, "created_at": e.created_at, "result": e.result}
        for e in db.scalars(
            select(AiEvaluation).where(AiEvaluation.kind == kind, AiEvaluation.submission_id == submission_id).order_by(AiEvaluation.created_at)
        )
    ]


def _submission_item(db: Session, kind: str, sub, task) -> dict:
    user = sub.user
    name = (f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username) if user else "—"
    item = {
        "id": sub.id,
        "kind": kind,
        "task_id": task.id,
        "task_title": task.title,
        "user_id": sub.user_id,
        "student_name": name,
        "status": sub.status,
        "score": sub.score,
        "ai_score": sub.ai_score,
        "feedback": sub.feedback,
        "ai_evaluation": sub.ai_evaluation,
        "evaluation_error": sub.evaluation_error,
        "attempt_count": sub.attempt_count,
        "submitted_at": sub.submitted_at,
        "evaluated_at": sub.evaluated_at,
        "reviewed_at": sub.reviewed_at,
        "history": _history(db, kind, sub.id),
    }
    if kind == EVAL_KIND_WRITING:
        item["answer_text"] = sub.answer_text
    else:
        item["transcript"] = sub.transcript
        item["duration_seconds"] = sub.duration_seconds
        item["has_audio"] = bool(sub.storage_path)
    return item


def lesson_submissions(db: Session, lesson_id: UUID) -> list[dict]:
    out = []
    for task in db.scalars(select(Writing).where(Writing.lesson_id == lesson_id).order_by(Writing.order_index)):
        for sub in db.scalars(select(StudentWriting).where(StudentWriting.writing_id == task.id, StudentWriting.status != "DRAFT")):
            out.append(_submission_item(db, EVAL_KIND_WRITING, sub, task))
    for task in db.scalars(select(Speaking).where(Speaking.lesson_id == lesson_id).order_by(Speaking.order_index)):
        for sub in db.scalars(select(StudentSpeaking).where(StudentSpeaking.speaking_id == task.id)):
            out.append(_submission_item(db, EVAL_KIND_SPEAKING, sub, task))
    out.sort(key=lambda r: r["submitted_at"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return out


def _load_submission(db: Session, kind: str, submission_id: UUID):
    model, task_model, fk = (StudentWriting, Writing, "writing_id") if kind == EVAL_KIND_WRITING else (StudentSpeaking, Speaking, "speaking_id")
    sub = db.get(model, submission_id)
    if sub is None or (kind == EVAL_KIND_WRITING and sub.status == "DRAFT"):
        raise HTTPException(status_code=404, detail="Submission not found.")
    return sub, db.get(task_model, getattr(sub, fk))


def override_score(db: Session, kind: str, submission_id: UUID, actor: User, score: int, feedback: str | None, reason: str | None) -> dict:
    sub, task = _load_submission(db, kind, submission_id)
    ai_evaluation.record_override(db, kind, sub, actor.id, score, reason)
    sub.score = score
    if feedback is not None:
        sub.feedback = feedback
    sub.status = "GRADED"
    sub.reviewed_by_id = actor.id
    sub.reviewed_at = _now()
    db.commit()
    db.refresh(sub)
    return _submission_item(db, kind, sub, task)


def request_reevaluation(db: Session, kind: str, submission_id: UUID) -> object:
    """Puts the submission back to pending (SUBMITTED) so the AI runs again.
    A run that is still in progress is left alone."""
    sub, task = _load_submission(db, kind, submission_id)
    if not task.ai_evaluation_enabled:
        raise HTTPException(status_code=409, detail="AI_EVALUATION_DISABLED")
    if sub.status == ai_evaluation.STATUS_EVALUATING:
        raise HTTPException(status_code=409, detail="EVALUATION_IN_PROGRESS")
    if kind == EVAL_KIND_SPEAKING:
        sub.transcript = None  # transcribe again as well
    sub.status = ai_evaluation.STATUS_SUBMITTED
    db.commit()
    return sub
