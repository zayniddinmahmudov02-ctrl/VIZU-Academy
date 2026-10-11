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
    QUESTION_TRUE_FALSE,
    QUESTION_TYPES,
    AiEvaluation,
    LessonSkillAttempt,
    ListeningOption,
    ListeningQuestion,
)
from app.models.listening import Listening
from app.models.reading import Reading
from app.models.reading_option import ReadingOption
from app.models.reading_question import ReadingQuestion
from app.models.speaking import Speaking
from app.models.student_speaking import StudentSpeaking
from app.models.student_writing import StudentWriting
from app.models.user import User
from app.models.writing import Writing
from app.services.lesson_skills import ai_evaluation
from app.services.lesson_skills.results import lesson_skill_results

listening_storage = ProtectedLessonListeningStorage()

MAX_AUDIO_BYTES = 25 * 1024 * 1024
# extension -> (content type, accepted declared types)
AUDIO_FORMATS = {
    "mp3": ("audio/mpeg", {"audio/mpeg", "audio/mp3"}),
    "wav": ("audio/wav", {"audio/wav", "audio/x-wav", "audio/wave"}),
    "m4a": ("audio/mp4", {"audio/mp4", "audio/x-m4a", "audio/m4a"}),
}


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
        if qtype == QUESTION_TRUE_FALSE and len(options) != 2:
            raise HTTPException(status_code=422, detail=f"Question {n}: Richtig/Falsch needs exactly 2 options.")
        if not 2 <= len(options) <= 6:
            raise HTTPException(status_code=422, detail=f"Question {n}: 2-6 options are required.")
        opts = []
        for o in options:
            otext = str(o.get("text", "")).strip()
            if not otext or len(otext) > 500:
                raise HTTPException(status_code=422, detail=f"Question {n}: every option needs a text (max 500).")
            opts.append({"id": o.get("id"), "text": otext, "is_correct": bool(o.get("is_correct"))})
        if sum(o["is_correct"] for o in opts) != 1:
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


async def upload_listening_audio(db: Session, listening_id: UUID, file: UploadFile, duration_seconds: int | None) -> Listening:
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    declared = (file.content_type or "").split(";")[0].strip().lower()
    head = await file.read(16)
    await file.seek(0)
    detected = _detect_audio(head)
    if detected is None or declared not in AUDIO_FORMATS[detected][1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNSUPPORTED_AUDIO: allowed are MP3, WAV and M4A files.")
    name = f"{uuid4().hex}.{detected}"
    try:
        await listening_storage.upload(file, name, max_bytes=MAX_AUDIO_BYTES)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AUDIO_TOO_LARGE: max 25 MB.") from None
    if listening.audio_storage_path:
        await listening_storage.delete(listening.audio_storage_path)
    listening.audio_storage_path = name
    listening.audio_content_type = AUDIO_FORMATS[detected][0]
    listening.audio_size_bytes = (listening_storage.ROOT / name).stat().st_size
    listening.audio_original_name = (file.filename or "")[:255] or None
    listening.audio_duration_seconds = duration_seconds if duration_seconds and 0 < duration_seconds < 6 * 3600 else None
    db.commit()
    db.refresh(listening)
    return listening


def listening_audio_path(listening: Listening) -> Path | None:
    if not listening.audio_storage_path:
        return None
    path = (listening_storage.ROOT / listening.audio_storage_path).resolve()
    root = listening_storage.ROOT.resolve()
    return path if root in path.parents and path.exists() else None


# ============================================================
# Duplicate
# ============================================================


def _copy_title(title: str) -> str:
    return f"{title} (Kopie)"[:255]


def duplicate_reading(db: Session, reading_id: UUID) -> Reading:
    src = db.get(Reading, reading_id)
    if src is None:
        raise HTTPException(status_code=404, detail="Reading not found.")
    copy = Reading(lesson_id=src.lesson_id, title=_copy_title(src.title), content=src.content, order_index=src.order_index + 1, is_published=False)
    db.add(copy)
    db.flush()
    for q in src.questions:
        nq = ReadingQuestion(reading_id=copy.id, question=q.question, explanation=q.explanation, order_index=q.order_index,
                             is_published=q.is_published, question_type=q.question_type, points=q.points)
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
        audio_duration_seconds=src.audio_duration_seconds, audio_original_name=src.audio_original_name,
    )
    source_path = listening_audio_path(src)
    if source_path is not None:
        name = f"{uuid4().hex}{source_path.suffix}"
        shutil.copyfile(source_path, listening_storage.ROOT / name)
        copy.audio_storage_path = name
    db.add(copy)
    db.flush()
    for q in src.questions:
        nq = ListeningQuestion(listening_id=copy.id, question=q.question, question_type=q.question_type, points=q.points,
                               explanation=q.explanation, order_index=q.order_index)
        db.add(nq)
        db.flush()
        for o in q.options:
            db.add(ListeningOption(question_id=nq.id, option_text=o.option_text, is_correct=o.is_correct, order_index=o.order_index))
    db.commit()
    db.refresh(copy)
    return copy


_TASK_COPY_FIELDS = {
    Writing: ("lesson_id", "instruction", "min_words", "max_words", "order_index", "ai_evaluation_enabled", "ai_instructions",
              "feedback_language", "max_score", "rubric", "max_attempts", "helper_words", "image_url", "opens_at", "closes_at"),
    Speaking: ("lesson_id", "topic", "instruction", "sample_answer", "keywords", "preparation_time", "speaking_time", "order_index",
               "ai_evaluation_enabled", "ai_instructions", "feedback_language", "max_score", "rubric", "max_attempts", "min_duration_seconds"),
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
