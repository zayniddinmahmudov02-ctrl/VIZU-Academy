"""Deterministic (no AI/LLM) quiz generation — Lesson -> Topic -> Question
Templates -> Quiz. Pools every candidate every matching template can
produce, deduplicates (against both this batch and any questions already
in the target quiz), shuffles with a seeded RNG, and takes up to the
requested count. Never pads short of an honest count — if only N unique
questions exist for the topic/level, exactly N are created and the
shortfall is reported, never invented filler.

Writes directly into the existing Quiz/QuizQuestion/QuizOption tables
(same models/tables the manual admin UI and the legacy AI-preview flow
already use) — grading, scoring, publishing and the student-facing API
are completely untouched; a generated question is just a QuizQuestion
row like any other, created as a draft (is_published=False) exactly like
the AI-generated flow's rows, until an admin reviews and publishes it."""

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
from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.services.quiz_generation.registry import get_templates, get_topics_for_level

__all__ = ["generate_quiz", "list_topics_for_lesson", "QuizGenerationError", "QuizGenerationResult"]


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

    for candidate in selected:
        order_index += 1
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=candidate.question_text,
            question_type=type_by_template[candidate.template_type],
            points=1,
            order_index=order_index,
            is_published=False,
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
