"""Student endpoints of the lesson skills (A1 Modul 1 onward).

Every route requires the lesson gate (require_lesson_access: logged in +
free-3-per-level / Premium / staff) and only ever touches the caller's own
attempts. Answer keys are returned only for the caller's own SUBMITTED
attempts."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson_skill import SKILL_HOEREN, SKILL_LESEN, LessonSkillAttempt
from app.models.user import User
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import skill_tests as tests
from app.services.lesson_skills.results import lesson_skill_results

router = APIRouter(prefix="/lesson-skills", tags=["Lesson skills"])


class SubmitAnswers(BaseModel):
    attempt_id: UUID
    # {question_id: option_id}
    answers: dict[str, str] = Field(default_factory=dict, max_length=200)


class AttemptOut(BaseModel):
    id: UUID
    attempt_number: int
    status: str
    score: int | None
    correct_count: int | None
    question_count: int | None
    started_at: datetime
    submitted_at: datetime | None
    duration_seconds: int | None


class QuestionResult(BaseModel):
    question_id: UUID
    selected_option_id: str | None
    correct_option_id: UUID | None
    is_correct: bool
    points: float
    max_points: float
    explanation: str | None


class AttemptResult(BaseModel):
    attempt: AttemptOut
    results: list[QuestionResult]
    correct_count: int
    question_count: int
    points: float
    max_points: float
    score: int
    transcript: str | None = None


def _result(attempt: LessonSkillAttempt, graded: dict, transcript: str | None = None) -> dict:
    return {**{k: graded[k] for k in ("results", "correct_count", "question_count", "points", "max_points", "score")},
            "attempt": tests.attempt_item(attempt), "transcript": transcript}


def _own_attempt(db: Session, user: User, lesson_id: UUID, attempt_id: UUID, skill: str, listening_id: UUID | None = None):
    rows = [a for a in tests.attempts(db, user.id, lesson_id, skill, listening_id) if a.id == attempt_id]
    if not rows:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return rows[0]


# ============================================================
# Lesen
# ============================================================


@router.get("/{lesson_id}/lesen")
def get_lesen(lesson_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    """The lesson's published texts with their questions (no answer key)."""
    texts = []
    for reading in tests.lesen_readings(db, lesson_id):
        texts.append(
            {
                "id": reading.id,
                "title": reading.title,
                "content": reading.content,
                "questions": [tests.public_question(q) for q in tests.reading_questions(reading)],
            }
        )
    rows = tests.attempts(db, user.id, lesson_id, SKILL_LESEN)
    return {
        "lesson_id": lesson_id,
        "texts": texts,
        "question_count": sum(len(t["questions"]) for t in texts),
        "summary": tests.summary(rows),
        "attempts": [tests.attempt_item(a) for a in rows],
    }


@router.post("/{lesson_id}/lesen/start", response_model=AttemptOut)
def start_lesen(lesson_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    if not tests.lesen_questions(db, lesson_id):
        raise HTTPException(status_code=409, detail="NO_QUESTIONS")
    return tests.attempt_item(tests.start_attempt(db, user.id, lesson_id, SKILL_LESEN))


@router.post("/{lesson_id}/lesen/submit", response_model=AttemptResult)
def submit_lesen(lesson_id: UUID, data: SubmitAnswers, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    questions = tests.lesen_questions(db, lesson_id)
    attempt, graded = tests.submit_attempt(db, user.id, lesson_id, SKILL_LESEN, data.attempt_id, data.answers, questions)
    return _result(attempt, graded)


@router.get("/{lesson_id}/lesen/attempts/{attempt_id}", response_model=AttemptResult)
def review_lesen(lesson_id: UUID, attempt_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    attempt = _own_attempt(db, user, lesson_id, attempt_id, SKILL_LESEN)
    return _result(attempt, tests.review(attempt, tests.lesen_questions(db, lesson_id)))


# ============================================================
# Hören
# ============================================================


def _sorted_questions(listening) -> list:
    return sorted(listening.questions, key=lambda q: (q.order_index, q.created_at))


@router.get("/{lesson_id}/hoeren")
def get_hoeren(lesson_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    """Published Hören tasks that have audio. The transcript is only shown
    after the caller has submitted the task's test at least once."""
    tasks = []
    for listening in tests.lesson_listenings(db, lesson_id):
        if not tests.has_audio(listening):
            continue
        rows = tests.attempts(db, user.id, lesson_id, SKILL_HOEREN, listening.id)
        summary = tests.summary(rows)
        questions = _sorted_questions(listening)
        tasks.append(
            {
                "id": listening.id,
                "title": listening.title,
                "instruction": listening.instruction,
                "audio_duration_seconds": listening.audio_duration_seconds,
                # legacy tasks keep their public URL; uploaded audio is streamed via /audio
                "external_audio_url": None if listening.audio_storage_path else listening.audio_url,
                "questions": [tests.public_question(q) for q in questions],
                "transcript": listening.transcript if (not questions or summary["attempts_count"]) else None,
                "summary": summary,
                "attempts": [tests.attempt_item(a) for a in rows],
            }
        )
    return {"lesson_id": lesson_id, "tasks": tasks}


@router.get("/{lesson_id}/hoeren/{listening_id}/audio")
def stream_hoeren_audio(lesson_id: UUID, listening_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    listening = tests.published_listening(db, lesson_id, listening_id)
    path = skill_admin.listening_audio_path(listening)
    if path is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path, media_type=listening.audio_content_type or "audio/mpeg", headers={"Cache-Control": "private, no-store"})


@router.post("/{lesson_id}/hoeren/{listening_id}/start", response_model=AttemptOut)
def start_hoeren(lesson_id: UUID, listening_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    listening = tests.published_listening(db, lesson_id, listening_id)
    if not listening.questions:
        raise HTTPException(status_code=409, detail="NO_QUESTIONS")
    return tests.attempt_item(tests.start_attempt(db, user.id, lesson_id, SKILL_HOEREN, listening.id))


@router.post("/{lesson_id}/hoeren/{listening_id}/submit", response_model=AttemptResult)
def submit_hoeren(
    lesson_id: UUID, listening_id: UUID, data: SubmitAnswers, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)
):
    listening = tests.published_listening(db, lesson_id, listening_id)
    attempt, graded = tests.submit_attempt(
        db, user.id, lesson_id, SKILL_HOEREN, data.attempt_id, data.answers, _sorted_questions(listening), listening.id
    )
    return _result(attempt, graded, listening.transcript)


@router.get("/{lesson_id}/hoeren/{listening_id}/attempts/{attempt_id}", response_model=AttemptResult)
def review_hoeren(
    lesson_id: UUID, listening_id: UUID, attempt_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)
):
    listening = tests.published_listening(db, lesson_id, listening_id)
    attempt = _own_attempt(db, user, lesson_id, attempt_id, SKILL_HOEREN, listening.id)
    return _result(attempt, tests.review(attempt, _sorted_questions(listening)), listening.transcript)


# ============================================================
# Results
# ============================================================


@router.get("/{lesson_id}/results")
def my_results(lesson_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    """The caller's own Lesen / Hören / Schreiben / Sprechen results and the
    lesson's overall result (final or interim, with its method)."""
    return lesson_skill_results(db, user.id, lesson_id)
