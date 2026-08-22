"""Auto-generates/syncs the A1-only Wortschatz Quiz whenever a lesson's
vocabulary changes — no admin authoring step. Question count is always
exactly the lesson's published-vocabulary count (one question per word,
no artificial cap — 5 words makes 5 questions, 52 makes 52, 100 makes
100). Reuses the legacy Quiz/QuizQuestion/QuizOption tables
(quiz_type=VOCABULARY) purely for content storage; scoring never reads
back through this machinery (see QUIZ_TYPE_VOCABULARY's docstring in
app/models/quiz.py) — it flows through StudentProgress.vocabulary_score
exactly like the client-side exercise generator it replaces for A1.

Deliberately duplicates the tiny lesson->level lookup already in
VocabularyBulkService.get_lesson_level rather than sharing it, so the
working bulk-import feature is never touched by this module.
"""

import random
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.quiz import QUIZ_TYPE_VOCABULARY, Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.models.vocabulary import Vocabulary


def _get_lesson_level(db: Session, lesson_id: UUID) -> str:
    row = (
        db.query(Course.level)
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .filter(Lesson.id == lesson_id)
        .first()
    )
    return row[0] if row else "A1"


def _get_level_translation_pool(db: Session, level: str) -> list[str]:
    rows = (
        db.query(Vocabulary.translation)
        .join(Lesson, Lesson.id == Vocabulary.lesson_id)
        .join(Module, Module.id == Lesson.module_id)
        .join(Course, Course.id == Module.course_id)
        .filter(Course.level == level, Vocabulary.is_published.is_(True))
        .all()
    )
    return [row[0] for row in rows]


def _get_or_create_quiz(db: Session, lesson_id: UUID) -> Quiz:
    quiz = (
        db.query(Quiz)
        .filter(Quiz.lesson_id == str(lesson_id), Quiz.quiz_type == QUIZ_TYPE_VOCABULARY)
        .first()
    )
    if quiz is not None:
        return quiz

    quiz = Quiz(
        lesson_id=str(lesson_id),
        quiz_type=QUIZ_TYPE_VOCABULARY,
        title="Wortschatz Test",
        is_published=True,
    )
    db.add(quiz)
    db.flush()
    return quiz


def sync_vocabulary_test(db: Session, lesson_id: UUID) -> None:
    """Full regenerate, not incremental diffing — avoids needing a
    word<->question identity column, and a lesson's vocabulary count is
    small enough that this stays cheap regardless of size. Safe to call
    after every vocabulary create/update/delete/publish/unpublish/bulk-op;
    a no-op for every level except A1. Every published word becomes
    exactly one question — no count cap, so growing or shrinking the
    published set (e.g. 20 -> 52 words, or 52 -> 0) is reflected exactly
    on the next sync."""

    if _get_lesson_level(db, lesson_id) != "A1":
        return

    words = (
        db.query(Vocabulary)
        .filter(Vocabulary.lesson_id == str(lesson_id), Vocabulary.is_published.is_(True))
        .order_by(Vocabulary.order_index.asc(), Vocabulary.created_at.asc())
        .all()
    )

    quiz = _get_or_create_quiz(db, lesson_id)

    # Cascades to QuizOption via QuizQuestion.options' cascade="all, delete-orphan".
    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).delete()
    db.flush()

    # Lazily computed, once: every other published A1 word's translation
    # (across all A1 lessons), used only as a fallback distractor source
    # for a word whose own lesson has no other distinct-translation word
    # (e.g. a single-word lesson) — so a word is never skipped just
    # because its own lesson can't supply a second option.
    level_pool: list[str] | None = None

    order_index = 0
    for word in words:
        distractor_pool = [
            w.translation
            for w in words
            if w.id != word.id and w.translation.strip().lower() != word.translation.strip().lower()
        ]
        if not distractor_pool:
            if level_pool is None:
                level_pool = _get_level_translation_pool(db, "A1")
            distractor_pool = [
                t for t in level_pool if t.strip().lower() != word.translation.strip().lower()
            ]
        if not distractor_pool:
            # Only possible if no other distinct-translation A1 word
            # exists anywhere — a valid 2-option question is impossible.
            continue

        distractor = random.choice(distractor_pool)
        question_text = f"{word.article} {word.german_word}" if word.article else word.german_word

        order_index += 1
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=question_text,
            question_type="MULTIPLE_CHOICE",
            points=1,
            order_index=order_index,
            is_published=True,
        )
        db.add(question)
        db.flush()

        options = [(word.translation, True), (distractor, False)]
        random.shuffle(options)
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
