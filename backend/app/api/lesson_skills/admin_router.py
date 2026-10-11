"""Admin endpoints of the lesson skills — Lesen / Hören questions and answer
keys, Hören audio, duplication, per-student results, AI review, manual score
override and re-evaluation. Admin-panel roles only (backend-enforced)."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.lesson_skill import EVAL_KIND_SPEAKING, EVAL_KIND_WRITING
from app.models.listening import Listening
from app.models.reading import Reading
from app.models.speaking import Speaking
from app.models.user import User
from app.models.writing import Writing
from app.schemas.listening import ListeningResponse
from app.schemas.speaking import SpeakingAdminResponse
from app.schemas.writing import WritingAdminResponse
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import skill_tests as tests
from app.services.lesson_skills.ai_evaluation import run_speaking_evaluation, run_writing_evaluation

router = APIRouter(prefix="/admin/lesson-skills", tags=["Admin - Lesson skills"])


class OptionIn(BaseModel):
    id: UUID | None = None
    text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class QuestionIn(BaseModel):
    id: UUID | None = None
    question: str = Field(min_length=1, max_length=2000)
    question_type: str = "MULTIPLE_CHOICE"
    points: int = Field(default=1, ge=1, le=100)
    explanation: str | None = Field(default=None, max_length=2000)
    options: list[OptionIn] = Field(min_length=2, max_length=6)


class QuestionsIn(BaseModel):
    questions: list[QuestionIn] = Field(max_length=100)


class OverrideIn(BaseModel):
    score: int = Field(ge=0, le=100)
    feedback: str | None = Field(default=None, max_length=5000)
    reason: str | None = Field(default=None, max_length=1000)


def _lesson_or_404(db: Session, lesson_id: UUID) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found.")
    return lesson


def _payload(data: QuestionsIn) -> list[dict]:
    return [
        {**q.model_dump(exclude={"options"}), "options": [o.model_dump() for o in q.options]} for q in data.questions
    ]


# ============================================================
# Overview
# ============================================================


@router.get("/lessons/{lesson_id}")
def lesson_overview(lesson_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Lesen texts and Hören tasks with their questions INCLUDING the answer
    key (admin only), plus the Schreiben / Sprechen tasks with AI settings."""
    lesson = _lesson_or_404(db, lesson_id)
    readings = sorted(db.query(Reading).filter(Reading.lesson_id == lesson_id).all(), key=lambda r: (r.order_index, r.created_at))
    listenings = sorted(db.query(Listening).filter(Listening.lesson_id == lesson_id).all(), key=lambda r: (r.order_index, r.created_at))
    return {
        "lesson": {"id": lesson.id, "title": lesson.title, "number": lesson.number},
        "lesen": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "order_index": r.order_index,
                "is_published": r.is_published,
                "questions": [skill_admin.admin_question(q) for q in sorted(r.questions, key=lambda q: (q.order_index, q.created_at))],
            }
            for r in readings
        ],
        "hoeren": [
            {
                **ListeningResponse.model_validate(lst).model_dump(),
                "questions": [skill_admin.admin_question(q) for q in sorted(lst.questions, key=lambda q: (q.order_index, q.created_at))],
                "max_points": sum(q.points for q in lst.questions),
            }
            for lst in listenings
        ],
        "schreiben": [WritingAdminResponse.model_validate(w).model_dump() for w in db.query(Writing).filter(Writing.lesson_id == lesson_id).order_by(Writing.order_index)],
        "sprechen": [SpeakingAdminResponse.model_validate(s).model_dump() for s in db.query(Speaking).filter(Speaking.lesson_id == lesson_id).order_by(Speaking.order_index)],
    }


# ============================================================
# Questions + audio
# ============================================================


@router.put("/readings/{reading_id}/questions")
def put_reading_questions(reading_id: UUID, data: QuestionsIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    reading = skill_admin.replace_reading_questions(db, reading_id, _payload(data))
    return {"id": reading.id, "questions": [skill_admin.admin_question(q) for q in sorted(reading.questions, key=lambda q: q.order_index)]}


@router.put("/listenings/{listening_id}/questions")
def put_listening_questions(listening_id: UUID, data: QuestionsIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    listening = skill_admin.replace_listening_questions(db, listening_id, _payload(data))
    return {"id": listening.id, "questions": [skill_admin.admin_question(q) for q in sorted(listening.questions, key=lambda q: q.order_index)]}


@router.post("/listenings/{listening_id}/audio", response_model=ListeningResponse)
async def upload_listening_audio(
    listening_id: UUID,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    """MP3 / WAV / M4A, max 25 MB; type checked by content, stored privately."""
    return await skill_admin.upload_listening_audio(db, listening_id, file, duration_seconds)


@router.get("/listenings/{listening_id}/audio")
def preview_listening_audio(listening_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    listening = db.get(Listening, listening_id)
    path = skill_admin.listening_audio_path(listening) if listening else None
    if path is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path, media_type=listening.audio_content_type or "audio/mpeg", headers={"Cache-Control": "private, no-store"})


# ============================================================
# Duplicate (copies are unpublished)
# ============================================================


@router.post("/readings/{reading_id}/duplicate")
def duplicate_reading(reading_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return {"id": skill_admin.duplicate_reading(db, reading_id).id}


@router.post("/listenings/{listening_id}/duplicate")
def duplicate_listening(listening_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return {"id": skill_admin.duplicate_listening(db, listening_id).id}


@router.post("/writings/{writing_id}/duplicate", response_model=WritingAdminResponse)
def duplicate_writing(writing_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return skill_admin.duplicate_task(db, Writing, writing_id)


@router.post("/speakings/{speaking_id}/duplicate", response_model=SpeakingAdminResponse)
def duplicate_speaking(speaking_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return skill_admin.duplicate_task(db, Speaking, speaking_id)


# ============================================================
# Results + AI review
# ============================================================


@router.get("/lessons/{lesson_id}/results")
def lesson_results(lesson_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    _lesson_or_404(db, lesson_id)
    return {"students": skill_admin.lesson_students(db, lesson_id), "submissions": skill_admin.lesson_submissions(db, lesson_id)}


def _kind(kind: str) -> str:
    mapping = {"writing": EVAL_KIND_WRITING, "speaking": EVAL_KIND_SPEAKING}
    if kind not in mapping:
        raise HTTPException(status_code=404, detail="Unknown submission kind.")
    return mapping[kind]


@router.put("/submissions/{kind}/{submission_id}/score")
def override_score(kind: str, submission_id: UUID, data: OverrideIn, db: Session = Depends(get_db), actor: User = Depends(require_admin_panel_access)):
    """Corrects a score. The original AI result stays in the audit history."""
    return skill_admin.override_score(db, _kind(kind), submission_id, actor, data.score, data.feedback, data.reason)


@router.post("/submissions/{kind}/{submission_id}/evaluate")
def reevaluate(kind: str, submission_id: UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    sub = skill_admin.request_reevaluation(db, _kind(kind), submission_id)
    background_tasks.add_task(run_writing_evaluation if kind == "writing" else run_speaking_evaluation, sub.id)
    return {"id": sub.id, "status": sub.status}


__all__ = ["router", "tests"]
