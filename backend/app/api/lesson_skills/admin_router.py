"""Admin endpoints of the lesson skills — Lesen / Hören questions and answer
keys, Hören audio, duplication, per-student results, AI review, manual score
override and re-evaluation. Admin-panel roles only (backend-enforced)."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_content_editor
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.grammar import Grammar
from app.models.lesson_skill import EVAL_KIND_SPEAKING, EVAL_KIND_WRITING, TASK_KIND_FRAGE, TASK_KIND_SPRECHEN
from app.models.vocabulary import Vocabulary
from app.models.listening import Listening
from app.models.reading import Reading
from app.models.speaking import Speaking
from app.models.user import User
from app.models.writing import Writing
from app.schemas.listening import ListeningResponse
from app.schemas.speaking import SpeakingAdminResponse
from app.schemas.writing import WritingAdminResponse
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import exercises as ex_service
from app.services.lesson_skills import skill_tests as tests
from app.services.lesson_skills import levels
from app.services.lesson_skills import results as skill_results
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
    # option-based types: 2-6 options; MATCHING / GAP_FILL / SHORT_ANSWER: config
    options: list[OptionIn] = Field(default_factory=list, max_length=6)
    config: dict | None = None


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
    level = levels.lesson_level(db, lesson_id)
    return {
        "lesson": {"id": lesson.id, "title": lesson.title, "number": lesson.number, "level": level},
        "default_rubrics": {"writing": levels.writing_rubric(level), "speaking": levels.speaking_rubric(level)},
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
                # questions without a complete key (e.g. imported before the
                # audio was checked) block publishing
                "key_missing": sum(1 for q in lst.questions if not ex_service.has_key(q)),
            }
            for lst in listenings
        ],
        "schreiben": [WritingAdminResponse.model_validate(w).model_dump() for w in db.query(Writing).filter(Writing.lesson_id == lesson_id).order_by(Writing.order_index)],
        "sprechen": [
            SpeakingAdminResponse.model_validate(s).model_dump()
            for s in db.query(Speaking).filter(Speaking.lesson_id == lesson_id, Speaking.task_kind == TASK_KIND_SPRECHEN).order_by(Speaking.order_index)
        ],
        "frage": [
            SpeakingAdminResponse.model_validate(s).model_dump()
            for s in db.query(Speaking).filter(Speaking.lesson_id == lesson_id, Speaking.task_kind == TASK_KIND_FRAGE).order_by(Speaking.order_index)
        ],
        "grammatik": [ex_service.admin_grammar(g) for g in db.query(Grammar).filter(Grammar.lesson_id == lesson_id).order_by(Grammar.order_index)],
        "wortschatz": [ex_service.admin_word(v) for v in db.query(Vocabulary).filter(Vocabulary.lesson_id == lesson_id).order_by(Vocabulary.order_index)],
        "exercises": [ex_service.admin_exercise(e) for e in ex_service.lesson_exercises(db, lesson_id)],
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
    user: User = Depends(require_admin_panel_access),
):
    """MP3 / WAV / M4A, max 100 MB; type checked by content, stored privately."""
    listening = await skill_admin.upload_listening_audio(
        db,
        listening_id,
        file,
        duration_seconds,
        replaced_by_id=user.id,
    )
    if listening.a2_material_key:
        write_audit(
            db,
            actor_id=str(user.id),
            action="a2_audio_replaced",
            details=f"key={listening.a2_material_key}; task={listening_id}; original_name={(file.filename or '')[:255]}",
        )
    return listening


@router.delete("/listenings/{listening_id}/audio", response_model=ListeningResponse)
async def delete_listening_audio(listening_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Removes the uploaded audio; the task is hidden until a new one is uploaded."""
    listening = await skill_admin.delete_listening_audio(db, listening_id)
    write_audit(db, actor_id=user.id, action="listening_audio_deleted", details=f"listening={listening_id}")
    return listening


@router.get("/listenings/{listening_id}/audio")
def preview_listening_audio(listening_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    listening = db.get(Listening, listening_id)
    path = skill_admin.listening_audio_path(listening) if listening else None
    if path is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path, media_type=listening.audio_content_type or "audio/mpeg", headers={"Cache-Control": "private, no-store"})


# ---- several labelled audio files per Hören task (main audio + extra tracks) ----


class AudioLabelIn(BaseModel):
    label: str | None = Field(default=None, max_length=120)


def _listening_or_404(db: Session, listening_id: UUID) -> Listening:
    listening = db.get(Listening, listening_id)
    if listening is None:
        raise HTTPException(status_code=404, detail="Listening not found.")
    return listening


@router.get("/listenings/{listening_id}/audio-slots")
def audio_slots(listening_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Every audio slot of the task: the main audio first, then the extra tracks (also empty / missing ones)."""
    return skill_admin.audio_tracks_admin(_listening_or_404(db, listening_id))


@router.put("/listenings/{listening_id}/audio-label")
def put_audio_label(listening_id: UUID, data: AudioLabelIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    listening = skill_admin.set_audio_label(db, listening_id, data.label)
    write_audit(db, actor_id=user.id, action="listening_audio_label_set", details=f"listening={listening_id} label={listening.audio_label}")
    return skill_admin.audio_tracks_admin(listening)


@router.post("/listenings/{listening_id}/audio-tracks")
async def create_audio_track(
    listening_id: UUID,
    label: str = Form(..., max_length=120),
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_content_editor),
):
    """An additional labelled audio file (MP3 / WAV / M4A, max 100 MB, checked by content, stored privately)."""
    track = await skill_admin.upload_audio_track(db, listening_id, label, file, duration_seconds)
    write_audit(db, actor_id=user.id, action="listening_audio_track_added", details=f"listening={listening_id} track={track.id} label={track.label}")
    return skill_admin.audio_tracks_admin(_listening_or_404(db, listening_id))


@router.put("/listenings/{listening_id}/audio-tracks/{track_id}")
async def update_audio_track(
    listening_id: UUID,
    track_id: UUID,
    label: str | None = Form(None, max_length=120),
    file: UploadFile | None = File(None),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_content_editor),
):
    """Replace the file (and / or rename the track)."""
    if file is not None:
        await skill_admin.upload_audio_track(db, listening_id, label or "", file, duration_seconds, track_id=track_id)
        action = "listening_audio_track_replaced"
    elif label:
        skill_admin.rename_audio_track(db, listening_id, track_id, label)
        action = "listening_audio_track_renamed"
    else:
        raise HTTPException(status_code=422, detail="file or label required")
    write_audit(db, actor_id=user.id, action=action, details=f"listening={listening_id} track={track_id}")
    return skill_admin.audio_tracks_admin(_listening_or_404(db, listening_id))


@router.delete("/listenings/{listening_id}/audio-tracks/{track_id}")
async def delete_audio_track(listening_id: UUID, track_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    await skill_admin.delete_audio_track(db, listening_id, track_id)
    write_audit(db, actor_id=user.id, action="listening_audio_track_deleted", details=f"listening={listening_id} track={track_id}")
    return skill_admin.audio_tracks_admin(_listening_or_404(db, listening_id))


@router.delete("/listenings/{listening_id}/audio-tracks/{track_id}/file")
async def delete_audio_track_file(listening_id: UUID, track_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Removes only the file of a track; the labelled slot stays for a new upload."""
    await skill_admin.clear_audio_track_file(db, listening_id, track_id)
    write_audit(db, actor_id=user.id, action="listening_audio_track_file_removed", details=f"listening={listening_id} track={track_id}")
    return skill_admin.audio_tracks_admin(_listening_or_404(db, listening_id))


@router.get("/listenings/{listening_id}/audio-tracks/{track_id}")
def preview_audio_track(listening_id: UUID, track_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    track = skill_admin._track(db, listening_id, track_id)
    path = skill_admin.track_audio_path(track)
    if path is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path, media_type=track.content_type or "audio/mpeg", headers={"Cache-Control": "private, no-store"})


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


# ============================================================
# Course (level) structure + result configuration — A1-C1
# ============================================================


class ResultConfigIn(BaseModel):
    weights: dict[str, int]
    required: list[str]


def _course_or_404(db: Session, course_id: UUID):
    from app.models.course import Course

    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


def _counts(db: Session, model, lesson_ids: list, *where) -> dict:
    from sqlalchemy import case, func, select

    rows = db.execute(
        select(model.lesson_id, func.count(model.id), func.sum(case((model.is_published.is_(True), 1), else_=0)))
        .where(model.lesson_id.in_(lesson_ids), *where)
        .group_by(model.lesson_id)
    ).all()
    return {str(lid): {"total": int(total), "published": int(published or 0)} for lid, total, published in rows}


STRUCTURE_KEYS = ("frage", "grammatik", "lesen", "hoeren", "schreiben", "sprechen", "wortschatz", "uebungen", "yakuniy")


@router.get("/courses/{course_id}/structure")
def course_structure(course_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Every module of a level with its lessons and per-skill content counts
    (Lesen texts, Hören tasks, Schreiben / Sprechen tasks; total + published)."""
    from sqlalchemy import select

    from app.models.module import Module

    course = _course_or_404(db, course_id)
    modules = list(db.scalars(select(Module).where(Module.course_id == course.id).order_by(Module.order_index, Module.number)))
    lessons = list(db.scalars(select(Lesson).where(Lesson.module_id.in_([m.id for m in modules])).order_by(Lesson.number))) if modules else []
    ids = [lesson.id for lesson in lessons]
    from app.models.lesson_skill import SkillExercise

    counts = {
        "frage": _counts(db, Speaking, ids, Speaking.task_kind == TASK_KIND_FRAGE),
        "grammatik": _counts(db, Grammar, ids),
        "lesen": _counts(db, Reading, ids),
        "hoeren": _counts(db, Listening, ids),
        "schreiben": _counts(db, Writing, ids),
        "sprechen": _counts(db, Speaking, ids, Speaking.task_kind == TASK_KIND_SPRECHEN),
        "wortschatz": _counts(db, Vocabulary, ids),
        "uebungen": _counts(db, SkillExercise, ids, SkillExercise.skill.in_(("GRAMMATIK", "WORTSCHATZ"))),
        "yakuniy": _counts(db, SkillExercise, ids, SkillExercise.skill == "YAKUNIY"),
    } if ids else {}
    empty = {"total": 0, "published": 0}
    return {
        "course": {"id": course.id, "level": course.level, "title": course.title, "is_active": course.is_active},
        "result_config": skill_results.validate_result_config(course.result_config),
        "result_config_is_default": course.result_config is None,
        "modules": [
            {
                "id": m.id,
                "number": m.number,
                "title": m.title,
                "is_active": m.is_active,
                "lessons": [
                    {
                        "id": lesson.id,
                        "number": lesson.number,
                        "title": lesson.title,
                        "skills": {k: counts.get(k, {}).get(str(lesson.id), empty) for k in STRUCTURE_KEYS},
                    }
                    for lesson in lessons
                    if str(lesson.module_id) == str(m.id)
                ],
            }
            for m in modules
        ],
    }


@router.put("/courses/{course_id}/result-config")
def put_result_config(course_id: UUID, data: ResultConfigIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Weights and required skills of the lesson overall result for this level."""
    course = _course_or_404(db, course_id)
    try:
        config = skill_results.validate_result_config(data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    course.result_config = config
    db.commit()
    return {"result_config": config, "result_config_is_default": False}


@router.delete("/courses/{course_id}/result-config")
def reset_result_config(course_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    course = _course_or_404(db, course_id)
    course.result_config = None
    db.commit()
    return {"result_config": skill_results.validate_result_config(None), "result_config_is_default": True}


@router.get("/rubrics")
def default_rubrics(_: User = Depends(require_admin_panel_access)):
    """Default Schreiben / Sprechen rubrics of every level."""
    return levels.all_default_rubrics()


# ============================================================
# Exercise sets (Grammatik / Wortschatz / Yakuniy Test), Grammatik rules,
# Wortschatz words
# ============================================================


class ExerciseIn(BaseModel):
    skill: str | None = Field(default=None, pattern=r"^(GRAMMATIK|WORTSCHATZ|YAKUNIY)$")
    title: str | None = Field(default=None, max_length=255)
    instruction: str | None = Field(default=None, max_length=5000)
    order_index: int | None = Field(default=None, ge=1, le=1000)
    is_published: bool | None = None
    source: str | None = Field(default=None, pattern=r"^(book|vizu)$")


class GrammarIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=100_000)
    order_index: int = Field(default=1, ge=1, le=1000)
    is_published: bool = False


class WordIn(BaseModel):
    german_word: str = Field(min_length=1, max_length=255)
    translation: str = Field(min_length=1, max_length=255)
    article: str | None = Field(default=None, max_length=10)
    plural: str | None = Field(default=None, max_length=255)
    example_sentence: str | None = Field(default=None, max_length=1000)
    example_translation: str | None = Field(default=None, max_length=1000)
    order_index: int | None = Field(default=None, ge=1, le=10000)
    is_published: bool = True


@router.post("/lessons/{lesson_id}/exercises")
def create_exercise(lesson_id: UUID, data: ExerciseIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    _lesson_or_404(db, lesson_id)
    return ex_service.admin_exercise(ex_service.create_exercise(db, lesson_id, data.model_dump()))


@router.put("/exercises/{exercise_id}")
def update_exercise(exercise_id: UUID, data: ExerciseIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ex_service.admin_exercise(ex_service.update_exercise(db, exercise_id, data.model_dump(exclude={"skill"})))


@router.delete("/exercises/{exercise_id}")
def delete_exercise(exercise_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    ex_service.delete_exercise(db, exercise_id)
    return {"deleted": True}


@router.put("/exercises/{exercise_id}/questions")
def put_exercise_questions(exercise_id: UUID, data: QuestionsIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ex_service.admin_exercise(ex_service.replace_exercise_questions(db, exercise_id, _payload(data)))


@router.post("/exercises/{exercise_id}/duplicate")
def duplicate_exercise(exercise_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ex_service.admin_exercise(ex_service.duplicate_exercise(db, exercise_id))


@router.post("/lessons/{lesson_id}/grammars")
def create_grammar(lesson_id: UUID, data: GrammarIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    _lesson_or_404(db, lesson_id)
    return ex_service.admin_grammar(ex_service.save_grammar(db, lesson_id, data.model_dump()))


@router.put("/grammars/{grammar_id}")
def update_grammar(grammar_id: UUID, data: GrammarIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ex_service.admin_grammar(ex_service.save_grammar(db, None, data.model_dump(), grammar_id))


@router.delete("/grammars/{grammar_id}")
def delete_grammar(grammar_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    grammar = db.get(Grammar, grammar_id)
    if grammar is None:
        raise HTTPException(status_code=404, detail="Grammar not found.")
    db.delete(grammar)
    db.commit()
    return {"deleted": True}


@router.post("/lessons/{lesson_id}/words")
def create_word(lesson_id: UUID, data: WordIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    _lesson_or_404(db, lesson_id)
    return ex_service.admin_word(ex_service.save_word(db, lesson_id, data.model_dump()))


@router.put("/words/{word_id}")
def update_word(word_id: UUID, data: WordIn, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ex_service.admin_word(ex_service.save_word(db, None, data.model_dump(), word_id))


@router.delete("/words/{word_id}")
def delete_word(word_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    word = db.get(Vocabulary, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found.")
    db.delete(word)
    db.commit()
    return {"deleted": True}
