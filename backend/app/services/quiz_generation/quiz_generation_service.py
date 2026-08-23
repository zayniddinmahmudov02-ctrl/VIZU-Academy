"""Deterministic (no AI/LLM) quiz generation — Lesson -> Topic -> Question
Templates -> Quiz. Pools every candidate every matching template can
produce, deduplicates (against both this batch and any questions already
in the target quiz), shuffles with a seeded RNG, and takes up to the
requested count. Never pads short of an honest count — if only N unique
questions exist for the topic/level, exactly N are created and the
shortfall is reported, never invented filler.

Writes directly into the existing Quiz/QuizQuestion/QuizOption tables
(same models/tables the manual admin UI and the legacy AI-preview flow
already use) — grading, scoring, and the student-facing API are
completely untouched.

Publishing: for GRAMMAR-type quizzes specifically, a successful
generation immediately publishes both the quiz container and every
question it just created (QuizOption has no publish flag of its own —
it's always visible once its parent question is). This was a deliberate
change from the original "always draft" default: a two-gate design
(quiz-level + question-level, both defaulting unpublished) turned out to
be a real, repeated source of "questions exist in the DB but the quiz
doesn't fully show" bugs, since nothing prompted an admin to flip both
switches after generating a batch. Scoped to GRAMMAR only — other quiz
types generated through this same service (should that ever happen; only
GRAMMAR/LESSON quizzes expose "Automatisch erstellen" in the admin UI
today) keep the original draft-first behavior."""

import random
import unicodedata
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

# Importing alphabet_templates registers its templates as a side effect
# (see registry.py) — this is the one place every topic module must be
# imported so `get_templates`/`get_topics_for_level` see it. A future
# topic module just needs its import added here.
from app.services.quiz_generation import alphabet_templates  # noqa: F401
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.quiz import QUIZ_TYPE_GRAMMAR, Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.services.ai_content import generate_grammar_quiz_mc_from_prompt
from app.services.quiz_generation.registry import get_templates, get_topics_for_level

__all__ = [
    "generate_quiz",
    "generate_quiz_from_prompt",
    "list_topics_for_lesson",
    "QuizGenerationError",
    "QuizGenerationResult",
]


class QuizGenerationError(Exception):
    pass


@dataclass
class QuizGenerationResult:
    quiz_id: UUID
    created_count: int
    requested_count: int
    shortfall: bool
    message: str | None


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip().lower()


def _get_lesson_level(db: Session, lesson_id: UUID) -> str:
    row = (
        db.query(Course.level)
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .filter(Lesson.id == lesson_id)
        .first()
    )
    if row is None:
        raise QuizGenerationError("Lektion nicht gefunden.")
    return row[0]


def list_topics_for_lesson(db: Session, lesson_id: UUID) -> dict:
    level = _get_lesson_level(db, lesson_id)
    return {"level": level, "topics": get_topics_for_level(level)}


def generate_quiz(
    db: Session,
    quiz_id: UUID,
    lesson_id: UUID,
    topic: str,
    count: int,
    question_types: list[str] | None = None,
    seed: int | None = None,
) -> QuizGenerationResult:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise QuizGenerationError("Quiz nicht gefunden.")
    if str(quiz.lesson_id) != str(lesson_id):
        raise QuizGenerationError("Quiz gehört nicht zu dieser Lektion.")

    level = _get_lesson_level(db, lesson_id)
    templates = get_templates(topic=topic, level=level, question_types=question_types)
    if not templates:
        raise QuizGenerationError(f"Kein Template für Thema '{topic}' und Niveau '{level}' gefunden.")

    type_by_template = {t.template_type: t.question_type for t in templates}

    rng = random.Random(seed)

    # Dedup seeds with what's already in this quiz, so re-running
    # "Automatisch erstellen" on the same quiz never creates duplicates.
    existing_rows = db.query(QuizQuestion.question).filter(QuizQuestion.quiz_id == quiz.id).all()
    seen_texts = {_normalize_text(row[0]) for row in existing_rows}
    seen_keys: set[tuple[str, str]] = set()

    pool = []
    for template in templates:
        for candidate in template.generate(rng):
            key = (candidate.template_type, candidate.source_value)
            norm_text = _normalize_text(candidate.question_text)
            if key in seen_keys or norm_text in seen_texts:
                continue
            seen_keys.add(key)
            seen_texts.add(norm_text)
            pool.append(candidate)

    rng.shuffle(pool)
    selected = pool[:count]

    order_index = db.query(func.max(QuizQuestion.order_index)).filter(QuizQuestion.quiz_id == quiz.id).scalar() or 0

    # GRAMMAR only (see module docstring) — a generated question is
    # published immediately, not left in a draft an admin has to
    # remember to flip. QuizOption has no publish flag of its own; it's
    # always visible once its parent question is.
    publish_immediately = quiz.quiz_type == QUIZ_TYPE_GRAMMAR

    for candidate in selected:
        order_index += 1
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=candidate.question_text,
            question_type=type_by_template[candidate.template_type],
            points=1,
            order_index=order_index,
            is_published=publish_immediately,
        )
        db.add(question)
        db.flush()

        options = [(candidate.correct_text, True), *((d, False) for d in candidate.distractor_texts)]
        rng.shuffle(options)
        for i, (option_text, is_correct) in enumerate(options, start=1):
            db.add(
                QuizOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=is_correct,
                    order_index=i,
                )
            )

    if publish_immediately and not quiz.is_published:
        quiz.is_published = True

    db.commit()

    created = len(selected)
    shortfall = created < count
    message = (
        f"Nur {created} von {count} angeforderten Fragen konnten eindeutig generiert werden "
        f"(keine weiteren eindeutigen Fragen für Thema '{topic}' / Niveau '{level}' verfügbar)."
        if shortfall
        else None
    )

    return QuizGenerationResult(
        quiz_id=quiz.id,
        created_count=created,
        requested_count=count,
        shortfall=shortfall,
        message=message,
    )


async def generate_quiz_from_prompt(
    db: Session,
    quiz_id: UUID,
    lesson_id: UUID,
    prompt: str,
    count: int,
) -> QuizGenerationResult:
    """The Gemini-backed sibling of generate_quiz above, used instead of
    it whenever the admin's "Automatisch erstellen" dialog has a
    non-empty prompt (see quiz_generation_router.generate) — the
    deterministic, template-based generate_quiz itself is completely
    unchanged and still runs whenever the prompt field is left empty.

    GRAMMAR only: an LLM prompt has no natural "which quiz type" signal
    the way the deterministic templates' topic registry does, so this
    is guarded explicitly rather than left implicit.

    Unlike generate_quiz's GRAMMAR auto-publish, questions created here
    always start as drafts (is_published=False) — the deterministic
    generator can safely auto-publish because it's "correctness-
    guaranteed by construction" (its own docstring), which does not
    hold for LLM output; every other AI-generation flow in this
    codebase already requires an explicit admin review + publish step
    before content reaches students (see ai_content_router.py's
    docstring), and this follows the same rule instead of carving out
    an exception."""
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise QuizGenerationError("Quiz nicht gefunden.")
    if str(quiz.lesson_id) != str(lesson_id):
        raise QuizGenerationError("Quiz gehört nicht zu dieser Lektion.")
    if quiz.quiz_type != QUIZ_TYPE_GRAMMAR:
        raise QuizGenerationError("KI-Generierung per Prompt ist nur für Grammatik Quiz verfügbar.")

    level = _get_lesson_level(db, lesson_id)

    ai_questions = await generate_grammar_quiz_mc_from_prompt(prompt, level, count)

    # Same dedup-against-existing-questions rule as generate_quiz, so
    # re-running this on the same quiz never creates duplicates.
    existing_rows = db.query(QuizQuestion.question).filter(QuizQuestion.quiz_id == quiz.id).all()
    seen_texts = {_normalize_text(row[0]) for row in existing_rows}

    order_index = db.query(func.max(QuizQuestion.order_index)).filter(QuizQuestion.quiz_id == quiz.id).scalar() or 0

    created = 0
    for q in ai_questions:
        norm_text = _normalize_text(q.question)
        if norm_text in seen_texts:
            continue
        seen_texts.add(norm_text)

        order_index += 1
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=q.question,
            question_type="MULTIPLE_CHOICE",
            points=1,
            order_index=order_index,
            is_published=False,
        )
        db.add(question)
        db.flush()

        for i, option in enumerate(q.options, start=1):
            db.add(
                QuizOption(
                    question_id=question.id,
                    option_text=option.option_text,
                    is_correct=option.is_correct,
                    order_index=i,
                )
            )
        created += 1

    db.commit()

    shortfall = created < count
    message = (
        f"Nur {created} von {count} angeforderten Fragen konnten von der KI erstellt werden "
        "(Duplikate oder Fragen in ungültigem Format wurden übersprungen). "
        if shortfall
        else f"{created} Fragen von der KI erstellt. "
    ) + "Als Entwurf gespeichert — bitte prüfen und veröffentlichen."

    return QuizGenerationResult(
        quiz_id=quiz.id,
        created_count=created,
        requested_count=count,
        shortfall=shortfall,
        message=message,
    )
