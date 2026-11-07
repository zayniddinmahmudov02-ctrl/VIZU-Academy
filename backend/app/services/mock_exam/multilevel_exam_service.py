"""Multilevel exam mode (Vorbereitung → Multilevel, level "Multilevel B1–C1"): timed attempts, server-side scoring and
the automatic B1 / B2 / C1 result. The student never picks a level.

Flow: start an attempt (one open attempt per test and student; a finished one can be retaken, every attempt is kept)
→ open a section (Lesen, Hören, Schreiben, Sprechen; any order, one at a time) — the server sets the deadline from
Kompetenz.duration_minutes → save / change answers until the section is handed in or the deadline (+ GRACE_SECONDS)
passes → closing a section grades it on the server (Lesen / Hören: from the stored answers and keys; the client never
sends points). Schreiben / Sprechen get their 0–75 score from a teacher. Results and keys are shown only after all four
sections are closed.

Scoring (fixed by the owner): every section 0–75 (Lesen / Hören: correct / questions × 75, rounded half up), total
0–300. Section level: 0–38 NICHT_BESTANDEN, 39–49 B1, 50 = admin setting `score_50` (default UNGEKLAERT), 51–64 B2,
65–75 C1. Overall level: admin setting `overall_rule` — UNCONFIRMED (default: no official rule known, result
UNGEKLAERT), AVERAGE (average of the four scores, same bands) or LOWEST (lowest section level). Settings live in
app_settings["multilevel_scoring"]; changing them recomputes the stored results (audit log)."""

import json
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.storage.protected_local import ProtectedMockExamSpeakingStorage
from app.models.app_setting import AppSetting
from app.models.kompetenz import Kompetenz
from app.models.listening_content import ListeningContent
from app.models.mock_attempt_section import SECTION_EXPIRED, SECTION_OPEN, SECTION_SUBMITTED, MockAttemptSection
from app.models.mock_exam_level import MockExamLevel
from app.models.mock_question import TYPE_MULTIPLE_CHOICE, MockQuestion
from app.models.mock_question_answer import MockQuestionAnswer
from app.models.mock_speaking_submission import MockSpeakingSubmission
from app.models.mock_test_attempt import STATUS_GRADED, STATUS_IN_PROGRESS, STATUS_SUBMITTED, MockTestAttempt
from app.models.mock_writing_submission import MockWritingSubmission
from app.models.model_test import STATUS_PUBLISHED, ModelTest
from app.models.reading_content import ReadingContent
from app.models.speaking_task import SpeakingTask
from app.models.teil import Teil
from app.models.user import User
from app.models.writing_task import WritingTask
from app.services.mock_exam.multilevel_service import LEVEL_TITLE
from app.services.vizu_pay.access import can_access_model_test

SECTIONS = ["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"]
AUTO_SECTIONS = {"LESEN", "HOEREN"}
GRADED_SECTIONS = {"SCHREIBEN", "SPRECHEN"}
SECTION_MAX = 75
TOTAL_MAX = SECTION_MAX * len(SECTIONS)
GRACE_SECONDS = 30
DEFAULT_MINUTES = {"LESEN": 60, "HOEREN": 40, "SCHREIBEN": 60, "SPRECHEN": 15}
MAX_TEXT = 20000

NICHT_BESTANDEN, UNGEKLAERT, PENDING = "NICHT_BESTANDEN", "UNGEKLAERT", "PENDING"
SCORE_50_CHOICES = (UNGEKLAERT, "B1", "B2")
OVERALL_RULES = ("UNCONFIRMED", "AVERAGE", "LOWEST")
SETTINGS_KEY = "multilevel_scoring"
DEFAULT_SETTINGS = {"score_50": UNGEKLAERT, "overall_rule": "UNCONFIRMED"}
RANK = {NICHT_BESTANDEN: 0, "B1": 1, UNGEKLAERT: 1.5, "B2": 2, "C1": 3}

AUDIO_MAX_BYTES = 25 * 1024 * 1024
AUDIO_MIN_BYTES = 1024
AUDIO_TYPES = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "audio/x-m4a": "m4a", "audio/m4a": "m4a",
               "audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav"}
AUDIO_MEDIA = {"webm": "audio/webm", "ogg": "audio/ogg", "m4a": "audio/mp4", "mp3": "audio/mpeg", "wav": "audio/wav"}
speaking_storage = ProtectedMockExamSpeakingStorage()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


# ============================================================
# Settings, scaling, levels (pure)
# ============================================================


def get_settings(db: Session) -> dict:
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY))
    value = dict(DEFAULT_SETTINGS)
    if row is not None:
        value.update({k: v for k, v in (row.value or {}).items() if k in DEFAULT_SETTINGS})
    if value["score_50"] not in SCORE_50_CHOICES:
        value["score_50"] = UNGEKLAERT
    if value["overall_rule"] not in OVERALL_RULES:
        value["overall_rule"] = "UNCONFIRMED"
    return value


def scale(raw: int, raw_max: int) -> int | None:
    """Raw points → 0–75, rounded half up; never above 75."""
    if raw_max <= 0:
        return None
    raw = max(0, min(raw, raw_max))
    return min(SECTION_MAX, (raw * SECTION_MAX * 2 + raw_max) // (2 * raw_max))


def section_level(score: int | None, score_50: str = UNGEKLAERT) -> str | None:
    if score is None:
        return None
    if not 0 <= score <= SECTION_MAX:
        raise ValueError("score must be 0–75")
    if score <= 38:
        return NICHT_BESTANDEN
    if score <= 49:
        return "B1"
    if score == 50:
        return score_50 if score_50 in SCORE_50_CHOICES else UNGEKLAERT
    if score <= 64:
        return "B2"
    return "C1"


def overall_level(scores: list[int | None], settings: dict) -> str:
    """PENDING until all four scores exist; then the configured rule (UNCONFIRMED → UNGEKLAERT)."""
    if len(scores) != len(SECTIONS) or any(s is None for s in scores):
        return PENDING
    rule = settings.get("overall_rule", "UNCONFIRMED")
    if rule == "AVERAGE":
        total = sum(scores)
        return section_level((total * 2 + len(scores)) // (2 * len(scores)), settings["score_50"])
    if rule == "LOWEST":
        return min((section_level(s, settings["score_50"]) for s in scores), key=lambda lv: RANK[lv])
    return UNGEKLAERT


# ============================================================
# Test structure
# ============================================================


def _multilevel_level_ids(db: Session) -> list[UUID]:
    return list(db.scalars(select(MockExamLevel.id).where(MockExamLevel.title == LEVEL_TITLE)))


def is_multilevel_test(db: Session, model_test: ModelTest) -> bool:
    return model_test.level_id in _multilevel_level_ids(db)


def _kompetenzen(db: Session, model_test_id: UUID) -> dict[str, Kompetenz]:
    rows = db.scalars(select(Kompetenz).where(Kompetenz.model_test_id == model_test_id).order_by(Kompetenz.sort_order))
    out: dict[str, Kompetenz] = {}
    for k in rows:
        out.setdefault(k.type, k)
    return out


def _questions(db: Session, kompetenz_id: UUID) -> list[MockQuestion]:
    reading = (select(MockQuestion).join(ReadingContent, MockQuestion.reading_content_id == ReadingContent.id)
               .join(Teil, ReadingContent.teil_id == Teil.id).where(Teil.kompetenz_id == kompetenz_id)
               .order_by(Teil.sort_order, MockQuestion.sort_order))
    listening = (select(MockQuestion).join(ListeningContent, MockQuestion.listening_content_id == ListeningContent.id)
                 .join(Teil, ListeningContent.teil_id == Teil.id).where(Teil.kompetenz_id == kompetenz_id)
                 .order_by(Teil.sort_order, MockQuestion.sort_order))
    return list(db.scalars(reading)) + list(db.scalars(listening))


def exam_gaps(db: Session, model_test_id: UUID) -> list[str]:
    """What keeps a Multilevel test from being a complete exam (used by the publish guard)."""
    komps = _kompetenzen(db, model_test_id)
    gaps = []
    for t in SECTIONS:
        k = komps.get(t)
        if k is None:
            gaps.append(f"{t}: fehlt")
            continue
        teile = db.scalar(select(func.count()).select_from(Teil).where(Teil.kompetenz_id == k.id))
        if not teile:
            gaps.append(f"{t}: keine Teile")
        elif t in AUTO_SECTIONS and not _questions(db, k.id):
            gaps.append(f"{t}: keine Fragen")
    return gaps


def _duration(k: Kompetenz) -> int:
    return k.duration_minutes if k.duration_minutes and k.duration_minutes > 0 else DEFAULT_MINUTES[k.type]


# ============================================================
# Attempts
# ============================================================


def _published_tests(db: Session) -> list[ModelTest]:
    ids = _multilevel_level_ids(db)
    if not ids:
        return []
    return list(db.scalars(select(ModelTest).where(ModelTest.level_id.in_(ids), ModelTest.status == STATUS_PUBLISHED)
                           .order_by(ModelTest.sort_order)))


def _own_attempt(db: Session, user: User, attempt_id: UUID, lock: bool = False) -> MockTestAttempt:
    query = select(MockTestAttempt).where(MockTestAttempt.id == attempt_id)
    if lock:
        query = query.with_for_update()
    attempt = db.scalar(query)
    if attempt is None or attempt.user_id != user.id:
        raise _err(404, "ATTEMPT_NOT_FOUND")  # someone else's attempt looks like a missing one
    return attempt


def list_exams(db: Session, user: User) -> list[dict]:
    out = []
    for t in _published_tests(db):
        attempts = list(db.scalars(select(MockTestAttempt).where(MockTestAttempt.model_test_id == t.id, MockTestAttempt.user_id == user.id)
                                   .order_by(MockTestAttempt.started_at.desc())))
        open_attempt = next((a for a in attempts if a.status == STATUS_IN_PROGRESS), None)
        last = next((a for a in attempts if a.status != STATUS_IN_PROGRESS), None)
        out.append({"model_test_id": t.id, "title": t.title, "number": t.sort_order, "description": t.description,
                    "is_locked": not can_access_model_test(t, user), "attempts": len(attempts),
                    "open_attempt_id": open_attempt.id if open_attempt else None,
                    "last_result": _summary(db, last) if last else None})
    return out


def start_attempt(db: Session, user: User, model_test_id: UUID) -> MockTestAttempt:
    test = db.get(ModelTest, model_test_id)
    if test is None or test.status != STATUS_PUBLISHED or not is_multilevel_test(db, test):
        raise _err(404, "EXAM_NOT_FOUND")
    if not can_access_model_test(test, user):
        raise _err(403, "PREMIUM_REQUIRED")
    if exam_gaps(db, test.id):
        raise _err(409, "EXAM_NOT_READY")
    # one open attempt per (student, test), also under concurrent clicks
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"ml-attempt:{user.id}:{test.id}"})
    existing = db.scalar(select(MockTestAttempt).where(MockTestAttempt.model_test_id == test.id, MockTestAttempt.user_id == user.id,
                                                       MockTestAttempt.status == STATUS_IN_PROGRESS))
    if existing is not None:
        db.commit()
        return existing
    attempt = MockTestAttempt(model_test_id=test.id, user_id=user.id, status=STATUS_IN_PROGRESS, max_score=TOTAL_MAX)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def _sections(db: Session, attempt: MockTestAttempt) -> dict[str, MockAttemptSection]:
    return {s.section_type: s for s in db.scalars(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id))}


def _expire_overdue(db: Session, attempt: MockTestAttempt) -> None:
    """Closes (and grades) every open section whose deadline + grace has passed."""
    now = _now()
    for s in _sections(db, attempt).values():
        if s.status == SECTION_OPEN and now > s.deadline_at + timedelta(seconds=GRACE_SECONDS):
            _close_section(db, attempt, s, SECTION_EXPIRED)


def _remaining(s: MockAttemptSection) -> int:
    return max(0, int((s.deadline_at - _now()).total_seconds()))


def attempt_view(db: Session, user: User, attempt_id: UUID) -> dict:
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    _expire_overdue(db, attempt)
    db.commit()
    komps = _kompetenzen(db, attempt.model_test_id)
    secs = _sections(db, attempt)
    test = db.get(ModelTest, attempt.model_test_id)
    any_open = any(s.status == SECTION_OPEN for s in secs.values())
    sections = []
    for t in SECTIONS:
        k, s = komps.get(t), secs.get(t)
        sections.append({"type": t, "title": k.title if k else t, "duration_minutes": _duration(k) if k else 0,
                         "status": s.status if s else "NOT_STARTED", "remaining_seconds": _remaining(s) if s and s.status == SECTION_OPEN else None,
                         "can_start": attempt.status == STATUS_IN_PROGRESS and s is None and not any_open and k is not None})
    return {"attempt_id": attempt.id, "model_test_id": attempt.model_test_id, "title": test.title if test else "",
            "status": attempt.status, "started_at": attempt.started_at, "finished": attempt.status != STATUS_IN_PROGRESS,
            "sections": sections}


def start_section(db: Session, user: User, attempt_id: UUID, section_type: str) -> MockAttemptSection:
    if section_type not in SECTIONS:
        raise _err(422, "UNKNOWN_SECTION")
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    _expire_overdue(db, attempt)
    if attempt.status != STATUS_IN_PROGRESS:
        db.commit()
        raise _err(409, "ATTEMPT_FINISHED")
    secs = _sections(db, attempt)
    if section_type in secs:
        db.commit()
        if secs[section_type].status != SECTION_OPEN:
            raise _err(409, "SECTION_CLOSED")
        return secs[section_type]
    if any(s.status == SECTION_OPEN for s in secs.values()):
        db.commit()
        raise _err(409, "OTHER_SECTION_OPEN")
    k = _kompetenzen(db, attempt.model_test_id).get(section_type)
    if k is None:
        raise _err(404, "SECTION_NOT_FOUND")
    now = _now()
    s = MockAttemptSection(attempt_id=attempt.id, kompetenz_id=k.id, section_type=section_type, status=SECTION_OPEN,
                           started_at=now, deadline_at=now + timedelta(minutes=_duration(k)))
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _open_section(db: Session, user: User, attempt_id: UUID, section_type: str) -> tuple[MockTestAttempt, MockAttemptSection]:
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    _expire_overdue(db, attempt)
    s = _sections(db, attempt).get(section_type)
    if s is None:
        db.commit()
        raise _err(409, "SECTION_NOT_STARTED")
    if s.status != SECTION_OPEN:
        db.commit()
        raise _err(409, "SECTION_CLOSED")
    return attempt, s


# ============================================================
# Paper (what the student sees) — never keys
# ============================================================


def _paper(db: Session, kompetenz: Kompetenz, with_keys: bool = False) -> list[dict]:
    teile = db.scalars(select(Teil).where(Teil.kompetenz_id == kompetenz.id).order_by(Teil.sort_order))
    out = []
    for teil in teile:
        rc, lc, wt, st = teil.reading_content, teil.listening_content, teil.writing_task, teil.speaking_task
        content = rc or lc
        questions = []
        for q in (content.questions if content else []):
            questions.append({"id": q.id, "question_type": q.question_type, "question_text": q.question_text, "points": q.points,
                              "options": [{"id": o.id, "option_text": o.option_text, **({"is_correct": o.is_correct} if with_keys else {})}
                                          for o in q.options]})
        kind = "reading" if rc else "listening" if lc else "writing" if wt else "speaking" if st else "empty"
        out.append({"id": teil.id, "kind": kind, "title": teil.title, "instructions": teil.instructions, "description": teil.description,
                    "text": rc.text if rc else None, "image_url": (rc.image_url if rc else None) or (lc.image_url if lc else None),
                    "audio_url": (lc.audio_url or None) if lc else None,
                    "writing_task": {"id": wt.id, "task_text": wt.task_text, "word_limit": wt.word_limit, "image_url": wt.image_url,
                                     **({"evaluation_rubric": wt.evaluation_rubric} if with_keys else {})} if wt else None,
                    "speaking_task": {"id": st.id, "task_text": st.task_text, "image_url": st.image_url,
                                      "preparation_time_seconds": st.preparation_time_seconds, "speaking_time_seconds": st.speaking_time_seconds,
                                      "max_recording_duration_seconds": st.max_recording_duration_seconds} if st else None,
                    "questions": questions})
    return out


def section_paper(db: Session, user: User, attempt_id: UUID, section_type: str) -> dict:
    attempt, s = _open_section(db, user, attempt_id, section_type)
    db.commit()
    k = db.get(Kompetenz, s.kompetenz_id)
    answers = {a.question_id: json.loads(a.answer_data or "[]") for a in
               db.scalars(select(MockQuestionAnswer).where(MockQuestionAnswer.attempt_id == attempt.id))}
    writings = {w.writing_task_id: w.answer_text for w in
                db.scalars(select(MockWritingSubmission).where(MockWritingSubmission.attempt_id == attempt.id))}
    recordings = {r.speaking_task_id: r.submitted_at for r in
                  db.scalars(select(MockSpeakingSubmission).where(MockSpeakingSubmission.attempt_id == attempt.id))}
    return {"attempt_id": attempt.id, "section_type": section_type, "title": k.title, "remaining_seconds": _remaining(s),
            "deadline_at": s.deadline_at, "teile": _paper(db, k),
            "answers": {str(q): [str(v) for v in ids] for q, ids in answers.items()},
            "writings": {str(t): v for t, v in writings.items()},
            "recordings": {str(t): v for t, v in recordings.items()}}


def admin_preview(db: Session, model_test_id: UUID) -> dict:
    test = db.get(ModelTest, model_test_id)
    if test is None:
        raise _err(404, "MODEL_TEST_NOT_FOUND")
    komps = _kompetenzen(db, test.id)
    return {"model_test_id": test.id, "title": test.title, "status": test.status, "gaps": exam_gaps(db, test.id),
            "sections": [{"type": t, "title": komps[t].title, "duration_minutes": _duration(komps[t]), "teile": _paper(db, komps[t], with_keys=True)}
                         if t in komps else {"type": t, "title": t, "duration_minutes": 0, "teile": []} for t in SECTIONS]}


# ============================================================
# Answers (saved, changeable until the section closes)
# ============================================================


def _section_question(db: Session, s: MockAttemptSection, question_id: UUID) -> MockQuestion:
    q = next((q for q in _questions(db, s.kompetenz_id) if q.id == question_id), None)
    if q is None:
        raise _err(404, "QUESTION_NOT_IN_SECTION")
    return q


def save_answer(db: Session, user: User, attempt_id: UUID, section_type: str, question_id: UUID, option_ids: list[UUID]) -> dict:
    attempt, s = _open_section(db, user, attempt_id, section_type)
    q = _section_question(db, s, question_id)
    own = {o.id for o in q.options}
    if not set(option_ids) <= own:
        raise _err(422, "OPTION_NOT_IN_QUESTION")
    if len(set(option_ids)) > 1 and q.question_type != TYPE_MULTIPLE_CHOICE:
        raise _err(422, "ONLY_ONE_OPTION")
    data = json.dumps(sorted({str(o) for o in option_ids}))
    stmt = pg_insert(MockQuestionAnswer).values(id=uuid4(), attempt_id=attempt.id, question_id=q.id, answer_data=data,
                                                is_correct=None, points_earned=0)
    db.execute(stmt.on_conflict_do_update(constraint="uq_mock_question_answers_attempt_question",
                                          set_={"answer_data": data, "is_correct": None, "points_earned": 0, "updated_at": func.now()}))
    db.commit()
    return {"question_id": q.id, "option_ids": json.loads(data), "remaining_seconds": _remaining(s)}


def save_writing(db: Session, user: User, attempt_id: UUID, writing_task_id: UUID, answer_text: str) -> dict:
    attempt, s = _open_section(db, user, attempt_id, "SCHREIBEN")
    task = db.get(WritingTask, writing_task_id)
    teil = db.get(Teil, task.teil_id) if task else None
    if task is None or teil is None or teil.kompetenz_id != s.kompetenz_id:
        raise _err(404, "TASK_NOT_IN_SECTION")
    answer_text = (answer_text or "")[:MAX_TEXT]
    words = len(re.findall(r"\S+", answer_text))
    stmt = pg_insert(MockWritingSubmission).values(id=uuid4(), attempt_id=attempt.id, writing_task_id=task.id, answer_text=answer_text,
                                                   word_count=words, time_spent_seconds=0)
    db.execute(stmt.on_conflict_do_update(constraint="uq_mock_writing_submissions_attempt_task",
                                          set_={"answer_text": answer_text, "word_count": words, "updated_at": func.now(), "submitted_at": func.now()}))
    db.commit()
    return {"writing_task_id": task.id, "word_count": words, "remaining_seconds": _remaining(s)}


def _audio_kind(head: bytes) -> str | None:
    if head[:4] == b"\x1aE\xdf\xa3":
        return "webm"
    if head[:4] == b"OggS":
        return "ogg"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[4:8] == b"ftyp":
        return "m4a"
    if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return "mp3"
    return None


async def upload_recording(db: Session, user: User, attempt_id: UUID, speaking_task_id: UUID, file: UploadFile) -> dict:
    attempt, s = _open_section(db, user, attempt_id, "SPRECHEN")
    task = db.get(SpeakingTask, speaking_task_id)
    teil = db.get(Teil, task.teil_id) if task else None
    if task is None or teil is None or teil.kompetenz_id != s.kompetenz_id:
        raise _err(404, "TASK_NOT_IN_SECTION")
    declared = AUDIO_TYPES.get((file.content_type or "").split(";")[0].strip().lower())
    data = await file.read(AUDIO_MAX_BYTES + 1)
    if len(data) > AUDIO_MAX_BYTES:
        raise _err(413, "AUDIO_TOO_LARGE")
    if len(data) < AUDIO_MIN_BYTES:
        raise _err(422, "EMPTY_RECORDING")
    kind = _audio_kind(data[:16])
    if declared is None or kind is None or declared != kind:  # declared MIME and file content must agree
        raise _err(415, "UNSUPPORTED_AUDIO")
    name = f"{attempt.id}/{uuid4().hex}.{kind}"
    target = speaking_storage._inside_root(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    old = db.scalar(select(MockSpeakingSubmission).where(MockSpeakingSubmission.attempt_id == attempt.id,
                                                         MockSpeakingSubmission.speaking_task_id == task.id))
    old_name = old.audio_url if old else None
    if old is None:
        db.add(MockSpeakingSubmission(attempt_id=attempt.id, speaking_task_id=task.id, audio_url=name))
    else:
        old.audio_url = name
        old.submitted_at = _now()
    db.commit()
    if old_name and old_name != name:
        try:
            speaking_storage._inside_root(old_name).unlink(missing_ok=True)
        except (OSError, ValueError):
            pass
    return {"speaking_task_id": task.id, "saved": True, "remaining_seconds": _remaining(s)}


def recording_file(db: Session, viewer: User, submission_id: UUID, staff: bool):
    sub = db.get(MockSpeakingSubmission, submission_id)
    if sub is None:
        raise _err(404, "RECORDING_NOT_FOUND")
    attempt = db.get(MockTestAttempt, sub.attempt_id)
    if not staff and (attempt is None or attempt.user_id != viewer.id):
        raise _err(404, "RECORDING_NOT_FOUND")
    try:
        path = speaking_storage._inside_root(sub.audio_url)
    except ValueError:
        raise _err(404, "RECORDING_NOT_FOUND")
    if not path.is_file():
        raise _err(404, "RECORDING_NOT_FOUND")
    return path, AUDIO_MEDIA.get(path.suffix.lstrip("."), "application/octet-stream")


# ============================================================
# Closing sections, grading, results
# ============================================================


def _grade_auto(db: Session, attempt: MockTestAttempt, s: MockAttemptSection, settings: dict) -> None:
    questions = _questions(db, s.kompetenz_id)
    answers = {a.question_id: a for a in db.scalars(select(MockQuestionAnswer).where(MockQuestionAnswer.attempt_id == attempt.id))}
    raw = raw_max = 0
    for q in questions:
        raw_max += q.points
        a = answers.get(q.id)
        if a is None:
            continue
        try:
            chosen = {str(v) for v in json.loads(a.answer_data or "[]")}
        except ValueError:
            chosen = set()
        correct = {str(o.id) for o in q.options if o.is_correct}
        a.is_correct = bool(chosen) and chosen == correct
        a.points_earned = q.points if a.is_correct else 0
        raw += a.points_earned
    s.raw_points, s.raw_max = raw, raw_max
    s.score = scale(raw, raw_max)
    s.level = section_level(s.score, settings["score_50"])


def _has_work(db: Session, attempt: MockTestAttempt, s: MockAttemptSection) -> bool:
    teil_ids = select(Teil.id).where(Teil.kompetenz_id == s.kompetenz_id)
    if s.section_type == "SCHREIBEN":
        return bool(db.scalar(select(func.count()).select_from(MockWritingSubmission)
                              .join(WritingTask, MockWritingSubmission.writing_task_id == WritingTask.id)
                              .where(MockWritingSubmission.attempt_id == attempt.id, WritingTask.teil_id.in_(teil_ids),
                                     func.length(func.trim(MockWritingSubmission.answer_text)) > 0)))
    return bool(db.scalar(select(func.count()).select_from(MockSpeakingSubmission)
                          .join(SpeakingTask, MockSpeakingSubmission.speaking_task_id == SpeakingTask.id)
                          .where(MockSpeakingSubmission.attempt_id == attempt.id, SpeakingTask.teil_id.in_(teil_ids))))


def finish_attempt(db: Session, user: User, attempt_id: UUID) -> dict:
    """"Prüfung beenden": closes the open section and marks every section never started as closed with nothing
    answered (0 points). Idempotent."""
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    _expire_overdue(db, attempt)
    if attempt.status == STATUS_IN_PROGRESS:
        secs = _sections(db, attempt)
        for s in secs.values():
            if s.status == SECTION_OPEN:
                _close_section(db, attempt, s, SECTION_SUBMITTED)
        komps = _kompetenzen(db, attempt.model_test_id)
        now = _now()
        for t in SECTIONS:
            if t not in _sections(db, attempt) and t in komps:
                s = MockAttemptSection(attempt_id=attempt.id, kompetenz_id=komps[t].id, section_type=t, status=SECTION_OPEN,
                                       started_at=now, deadline_at=now)
                db.add(s)
                db.flush()
                _close_section(db, attempt, s, SECTION_EXPIRED)
    db.commit()
    return {"attempt_id": attempt.id, "status": attempt.status}


def _close_section(db: Session, attempt: MockTestAttempt, s: MockAttemptSection, status: str) -> None:
    if s.status != SECTION_OPEN:
        return
    s.status = status
    s.submitted_at = min(_now(), s.deadline_at)
    settings = get_settings(db)
    if s.section_type in AUTO_SECTIONS:
        _grade_auto(db, attempt, s, settings)
    elif not _has_work(db, attempt, s):
        # nothing written / recorded: there is nothing to grade — 0 points, no teacher needed
        s.raw_points, s.raw_max, s.score = 0, None, 0
        s.level = section_level(0, settings["score_50"])
    db.flush()
    secs = _sections(db, attempt)
    if all(t in secs and secs[t].status != SECTION_OPEN for t in SECTIONS) and attempt.status == STATUS_IN_PROGRESS:
        attempt.status = STATUS_SUBMITTED
        attempt.submitted_at = _now()
        attempt.time_spent_seconds = int(sum((x.submitted_at - x.started_at).total_seconds() for x in secs.values()))
    _recompute(db, attempt, settings, secs)


def _recompute(db: Session, attempt: MockTestAttempt, settings: dict, secs: dict | None = None) -> None:
    secs = secs if secs is not None else _sections(db, attempt)
    if attempt.status == STATUS_IN_PROGRESS:
        return
    for s in secs.values():
        if s.score is not None:
            s.level = section_level(s.score, settings["score_50"])
    scores = [secs[t].score if t in secs else None for t in SECTIONS]
    attempt.result_level = overall_level(scores, settings)
    attempt.result_rule = settings["overall_rule"]
    attempt.max_score = TOTAL_MAX
    if attempt.result_level == PENDING:
        attempt.total_score = None
        attempt.status = STATUS_SUBMITTED
    else:
        attempt.total_score = sum(scores)
        attempt.status = STATUS_GRADED


def submit_section(db: Session, user: User, attempt_id: UUID, section_type: str) -> dict:
    """Idempotent: a second submit of a closed section changes nothing."""
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    _expire_overdue(db, attempt)
    s = _sections(db, attempt).get(section_type)
    if s is None:
        db.commit()
        raise _err(409, "SECTION_NOT_STARTED")
    _close_section(db, attempt, s, SECTION_SUBMITTED)
    db.commit()
    return {"section_type": section_type, "status": s.status, "attempt_status": attempt.status}


def _summary(db: Session, attempt: MockTestAttempt) -> dict:
    secs = _sections(db, attempt)
    return {"attempt_id": attempt.id, "status": attempt.status, "started_at": attempt.started_at, "submitted_at": attempt.submitted_at,
            "total_score": attempt.total_score, "max_score": TOTAL_MAX, "result_level": attempt.result_level,
            "sections": {t: ({"score": secs[t].score, "level": secs[t].level, "status": secs[t].status} if t in secs else None) for t in SECTIONS}}


def results(db: Session, user: User, attempt_id: UUID) -> dict:
    attempt = _own_attempt(db, user, attempt_id, lock=True)
    _expire_overdue(db, attempt)
    db.commit()
    if attempt.status == STATUS_IN_PROGRESS:
        raise _err(409, "EXAM_NOT_FINISHED")
    return _result_detail(db, attempt, include_review=True)


def _result_detail(db: Session, attempt: MockTestAttempt, include_review: bool) -> dict:
    secs = _sections(db, attempt)
    test = db.get(ModelTest, attempt.model_test_id)
    komps = _kompetenzen(db, attempt.model_test_id)
    out = _summary(db, attempt) | {"title": test.title if test else "", "duration_seconds": attempt.time_spent_seconds,
                                   "result_rule": attempt.result_rule}
    sections = []
    for t in SECTIONS:
        s = secs.get(t)
        item = {"type": t, "title": komps[t].title if t in komps else t, "score": s.score if s else None, "max": SECTION_MAX,
                "level": s.level if s else None, "status": s.status if s else "NOT_STARTED",
                "raw_points": s.raw_points if s else None, "raw_max": s.raw_max if s else None,
                "awaiting_grading": bool(s and t in GRADED_SECTIONS and s.score is None), "feedback": s.feedback if s else None}
        if include_review and s and t in AUTO_SECTIONS and t in komps:
            answers = {a.question_id: a for a in db.scalars(select(MockQuestionAnswer).where(MockQuestionAnswer.attempt_id == attempt.id))}
            item["review"] = [{"question_id": q.id, "question_text": q.question_text,
                               "chosen": [str(v) for v in json.loads(answers[q.id].answer_data or "[]")] if q.id in answers else [],
                               "correct": [str(o.id) for o in q.options if o.is_correct],
                               "options": [{"id": o.id, "option_text": o.option_text} for o in q.options],
                               "is_correct": bool(answers[q.id].is_correct) if q.id in answers else False}
                              for q in _questions(db, komps[t].id)]
        sections.append(item)
    out["sections"] = sections
    return out


def history(db: Session, user: User) -> list[dict]:
    ids = _multilevel_level_ids(db)
    if not ids:
        return []
    rows = db.execute(select(MockTestAttempt, ModelTest.title).join(ModelTest, MockTestAttempt.model_test_id == ModelTest.id)
                      .where(MockTestAttempt.user_id == user.id, ModelTest.level_id.in_(ids)).order_by(MockTestAttempt.started_at.desc())).all()
    return [_summary(db, a) | {"title": title, "duration_seconds": a.time_spent_seconds} for a, title in rows]


# ============================================================
# Staff: attempts, grading Schreiben / Sprechen, statistics, settings
# ============================================================


def admin_attempts(db: Session, model_test_id: UUID | None = None, status: str | None = None, limit: int = 200) -> list[dict]:
    ids = _multilevel_level_ids(db)
    if not ids:
        return []
    query = (select(MockTestAttempt, ModelTest.title, User.username, User.email).join(ModelTest, MockTestAttempt.model_test_id == ModelTest.id)
             .join(User, MockTestAttempt.user_id == User.id).where(ModelTest.level_id.in_(ids)))
    if model_test_id:
        query = query.where(MockTestAttempt.model_test_id == model_test_id)
    if status:
        query = query.where(MockTestAttempt.status == status)
    rows = db.execute(query.order_by(MockTestAttempt.started_at.desc()).limit(min(max(limit, 1), 500))).all()
    return [_summary(db, a) | {"title": title, "username": username, "email": email, "duration_seconds": a.time_spent_seconds}
            for a, title, username, email in rows]


def admin_attempt_detail(db: Session, attempt_id: UUID) -> dict:
    attempt = db.get(MockTestAttempt, attempt_id)
    if attempt is None or db.get(ModelTest, attempt.model_test_id).level_id not in _multilevel_level_ids(db):
        raise _err(404, "ATTEMPT_NOT_FOUND")
    _expire_overdue(db, attempt)
    db.commit()
    detail = _result_detail(db, attempt, include_review=True)
    user = db.get(User, attempt.user_id)
    detail["username"] = user.username if user else None
    detail["email"] = user.email if user else None
    tasks = {}
    for w in db.scalars(select(MockWritingSubmission).where(MockWritingSubmission.attempt_id == attempt.id)):
        task = db.get(WritingTask, w.writing_task_id)
        teil = db.get(Teil, task.teil_id) if task else None
        tasks.setdefault("writings", []).append({"teil": teil.title if teil else "", "task_text": task.task_text if task else "",
                                                 "word_limit": task.word_limit if task else None, "rubric": task.evaluation_rubric if task else None,
                                                 "answer_text": w.answer_text, "word_count": w.word_count})
    for r in db.scalars(select(MockSpeakingSubmission).where(MockSpeakingSubmission.attempt_id == attempt.id)):
        task = db.get(SpeakingTask, r.speaking_task_id)
        teil = db.get(Teil, task.teil_id) if task else None
        tasks.setdefault("recordings", []).append({"submission_id": r.id, "teil": teil.title if teil else "",
                                                   "task_text": task.task_text if task else "", "submitted_at": r.submitted_at})
    detail["writings"] = sorted(tasks.get("writings", []), key=lambda x: x["teil"])
    detail["recordings"] = sorted(tasks.get("recordings", []), key=lambda x: x["teil"])
    return detail


def grade_section(db: Session, grader: User, attempt_id: UUID, section_type: str, score: int, feedback: str | None) -> dict:
    if section_type not in GRADED_SECTIONS:
        raise _err(422, "SECTION_AUTO_GRADED")
    if not 0 <= score <= SECTION_MAX:
        raise _err(422, "SCORE_OUT_OF_RANGE")
    attempt = db.scalar(select(MockTestAttempt).where(MockTestAttempt.id == attempt_id).with_for_update())
    if attempt is None:
        raise _err(404, "ATTEMPT_NOT_FOUND")
    _expire_overdue(db, attempt)
    s = _sections(db, attempt).get(section_type)
    if s is None or s.status == SECTION_OPEN:
        db.commit()
        raise _err(409, "SECTION_NOT_CLOSED")
    settings = get_settings(db)
    s.score, s.feedback, s.graded_by, s.graded_at = score, (feedback or None), grader.id, _now()
    s.level = section_level(score, settings["score_50"])
    _recompute(db, attempt, settings)
    db.commit()
    write_audit(db, actor_id=str(grader.id), action="multilevel_section_graded", target_user_id=str(attempt.user_id),
                details=f"attempt={attempt.id}; section={section_type}; score={score}")
    return admin_attempt_detail(db, attempt.id)


def statistics(db: Session) -> dict:
    ids = _multilevel_level_ids(db)
    if not ids:
        return {"attempts": 0, "finished": 0, "graded": 0, "sections": {}, "levels": {}, "tests": []}
    base = select(MockTestAttempt).join(ModelTest, MockTestAttempt.model_test_id == ModelTest.id).where(ModelTest.level_id.in_(ids))
    attempts = list(db.scalars(base))
    secs = list(db.scalars(select(MockAttemptSection).where(MockAttemptSection.attempt_id.in_([a.id for a in attempts])))) if attempts else []
    by_type: dict[str, list[int]] = {t: [] for t in SECTIONS}
    for s in secs:
        if s.score is not None:
            by_type[s.section_type].append(s.score)
    levels: dict[str, int] = {}
    for a in attempts:
        if a.result_level:
            levels[a.result_level] = levels.get(a.result_level, 0) + 1
    tests = {}
    for a in attempts:
        tests.setdefault(a.model_test_id, []).append(a)
    titles = {t.id: t.title for t in db.scalars(select(ModelTest).where(ModelTest.id.in_(list(tests))))} if tests else {}
    return {"attempts": len(attempts), "finished": sum(1 for a in attempts if a.status != STATUS_IN_PROGRESS),
            "graded": sum(1 for a in attempts if a.status == STATUS_GRADED),
            "sections": {t: {"count": len(v), "average": round(sum(v) / len(v), 1) if v else None} for t, v in by_type.items()},
            "levels": levels,
            "tests": sorted(({"model_test_id": k, "title": titles.get(k, ""), "attempts": len(v),
                              "average_total": (round(sum(a.total_score for a in v if a.total_score is not None) / n, 1)
                                                if (n := sum(1 for a in v if a.total_score is not None)) else None)} for k, v in tests.items()),
                            key=lambda x: x["title"])}


def update_settings(db: Session, actor: User, score_50: str, overall_rule: str) -> dict:
    if score_50 not in SCORE_50_CHOICES or overall_rule not in OVERALL_RULES:
        raise _err(422, "INVALID_SETTING")
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY).with_for_update())
    value = {"score_50": score_50, "overall_rule": overall_rule}
    if row is None:
        db.add(AppSetting(key=SETTINGS_KEY, value=value, updated_by=actor.id))
    else:
        row.value, row.updated_by = value, actor.id
    db.flush()
    settings = get_settings(db)
    ids = _multilevel_level_ids(db)
    changed = 0
    if ids:
        for a in db.scalars(select(MockTestAttempt).join(ModelTest, MockTestAttempt.model_test_id == ModelTest.id)
                            .where(ModelTest.level_id.in_(ids), MockTestAttempt.status != STATUS_IN_PROGRESS).with_for_update(of=MockTestAttempt)):
            before = a.result_level
            _recompute(db, a, settings)
            changed += int(before != a.result_level)
    db.commit()
    write_audit(db, actor_id=str(actor.id), action="multilevel_scoring_settings",
                details=f"score_50={score_50}; overall_rule={overall_rule}; results_changed={changed}")
    return settings | {"results_changed": changed}
