"""Lesen / Hören tests of a lesson — server-side grading.

Lesen = every published text (Reading) of the lesson with its questions, as
one test. Hören = one test per published Listening task. Students receive the
questions and options WITHOUT the answer key; `grade()` compares the submitted
option ids with `is_correct` on the server, and the key (correct option per
question) is only returned for an attempt that has been submitted.

Every question is worth its `points` (Lesen: 1 each — 15 questions = 15
points); the score is points / max points scaled to 0-100."""

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.lesson_skill import (
    ATTEMPT_IN_PROGRESS,
    ATTEMPT_SUBMITTED,
    CONFIG_TYPES,
    SKILL_HOEREN,
    SKILL_LESEN,
    LessonSkillAttempt,
)
from app.models.listening import Listening
from app.models.reading import Reading
from app.models.reading_question import ReadingQuestion
from app.services.lesson_skills import question_types as qt


def _now() -> datetime:
    return datetime.now(timezone.utc)


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


# ============================================================
# Content
# ============================================================


def lesen_readings(db: Session, lesson_id: UUID) -> list[Reading]:
    return list(
        db.scalars(
            select(Reading)
            .where(Reading.lesson_id == lesson_id, Reading.is_published.is_(True))
            .order_by(Reading.order_index, Reading.created_at)
        )
    )


def reading_questions(reading: Reading) -> list[ReadingQuestion]:
    return sorted((q for q in reading.questions if q.is_published), key=lambda q: (q.order_index, q.created_at))


def lesen_questions(db: Session, lesson_id: UUID) -> list:
    return [q for r in lesen_readings(db, lesson_id) for q in reading_questions(r)]


def published_listening(db: Session, lesson_id: UUID, listening_id: UUID) -> Listening:
    listening = db.get(Listening, listening_id)
    if listening is None or str(listening.lesson_id) != str(lesson_id) or not listening.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hören task not found.")
    return listening


def lesson_listenings(db: Session, lesson_id: UUID) -> list[Listening]:
    return list(
        db.scalars(
            select(Listening)
            .where(Listening.lesson_id == lesson_id, Listening.is_published.is_(True))
            .order_by(Listening.order_index, Listening.created_at)
        )
    )


def has_audio(listening: Listening) -> bool:
    return bool(listening.audio_storage_path or listening.audio_url)


def public_question(question) -> dict:
    """Student-facing shape — no is_correct, no accepted answers, no pairs,
    no explanation."""
    is_config = question.question_type in CONFIG_TYPES
    options = [] if is_config else sorted(question.options, key=lambda o: (o.order_index, o.created_at))
    return {
        "id": question.id,
        "question": question.question,
        "question_type": question.question_type,
        "points": question.points,
        "options": [{"id": o.id, "text": o.option_text} for o in options],
        "config": qt.public_config(question) if is_config else None,
    }


# ============================================================
# Grading (pure)
# ============================================================


def clean_answers(questions: list, answers: dict) -> dict:
    """Keeps only well-formed answers to the given questions."""
    by_id = {str(q.id): q for q in questions}
    out = {}
    for key, value in (answers or {}).items():
        q = by_id.get(str(key))
        if q is None:
            continue
        if getattr(q, "question_type", None) in CONFIG_TYPES:
            value = qt.clean_answer(q.question_type, value)
        else:
            value = str(value) if isinstance(value, (str, int)) and str(value) else None
        if value is not None:
            out[str(key)] = value
    return out


def grade(questions: list, answers: dict) -> dict:
    """answers: {question_id: option_id | text | {item/gap id: value}}.
    Unknown questions are ignored, an option of another question counts as
    unanswered. Zuordnung / Lückentext earn partial credit per item / gap;
    a question counts as "correct" only when fully right."""
    results = []
    points = max_points = 0.0
    correct = 0
    for q in questions:
        weight = float(q.points or 1)
        max_points += weight
        if getattr(q, "question_type", None) in CONFIG_TYPES:
            g = qt.grade_config_question(q, answers.get(str(q.id)))
            earned = round(weight * g["fraction"], 2)
            points += earned
            full = g["fraction"] >= 0.999
            correct += 1 if full else 0
            results.append(
                {
                    "question_id": q.id,
                    "selected_option_id": None,
                    "correct_option_id": None,
                    "answer": g["selected"],
                    "correct_answer": g["correct_answer"],
                    "details": g["details"],
                    "is_correct": full,
                    "points": earned,
                    "max_points": weight,
                    "explanation": q.explanation,
                }
            )
            continue
        options = {str(o.id): o for o in q.options}
        correct_ids = [oid for oid, o in options.items() if o.is_correct]
        selected = answers.get(str(q.id))
        selected = selected if isinstance(selected, str) and selected in options else None
        is_correct = selected is not None and selected in correct_ids
        if is_correct:
            points += weight
            correct += 1
        results.append(
            {
                "question_id": q.id,
                "selected_option_id": selected,
                "correct_option_id": correct_ids[0] if correct_ids else None,
                "is_correct": is_correct,
                "points": weight if is_correct else 0.0,
                "max_points": weight,
                "explanation": q.explanation,
            }
        )
    score = round_half_up(points / max_points * 100) if max_points else 0
    return {
        "results": results,
        "correct_count": correct,
        "question_count": len(questions),
        "points": points,
        "max_points": max_points,
        "score": max(0, min(100, score)),
    }


# ============================================================
# Attempts
# ============================================================


def _scope(query, user_id: UUID, lesson_id: UUID, skill: str, listening_id: UUID | None, exercise_id: UUID | None = None):
    query = query.where(
        LessonSkillAttempt.user_id == user_id, LessonSkillAttempt.lesson_id == lesson_id, LessonSkillAttempt.skill == skill
    )
    if listening_id is not None:
        query = query.where(LessonSkillAttempt.listening_id == listening_id)
    if exercise_id is not None:
        query = query.where(LessonSkillAttempt.exercise_id == exercise_id)
    return query


def attempts(
    db: Session, user_id: UUID, lesson_id: UUID, skill: str, listening_id: UUID | None = None, exercise_id: UUID | None = None
) -> list[LessonSkillAttempt]:
    query = _scope(select(LessonSkillAttempt), user_id, lesson_id, skill, listening_id, exercise_id)
    return list(db.scalars(query.order_by(LessonSkillAttempt.attempt_number)))


def start_attempt(
    db: Session, user_id: UUID, lesson_id: UUID, skill: str, listening_id: UUID | None = None, exercise_id: UUID | None = None
) -> LessonSkillAttempt:
    """Idempotent: an open attempt is returned as is (a reload keeps its start time)."""
    key = f"lesson-skill:{user_id}:{lesson_id}:{skill}:{listening_id or ''}:{exercise_id or ''}"
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key})
    existing = attempts(db, user_id, lesson_id, skill, listening_id, exercise_id)
    open_attempt = next((a for a in existing if a.status == ATTEMPT_IN_PROGRESS), None)
    if open_attempt is not None:
        db.commit()
        return open_attempt
    attempt = LessonSkillAttempt(
        user_id=user_id,
        lesson_id=lesson_id,
        skill=skill,
        listening_id=listening_id,
        exercise_id=exercise_id,
        attempt_number=len(existing) + 1,
        status=ATTEMPT_IN_PROGRESS,
        started_at=_now(),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def submit_attempt(
    db: Session,
    user_id: UUID,
    lesson_id: UUID,
    skill: str,
    attempt_id: UUID,
    answers: dict,
    questions: list,
    listening_id: UUID | None = None,
    exercise_id: UUID | None = None,
) -> tuple[LessonSkillAttempt, dict]:
    if not questions:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NO_QUESTIONS")
    # row lock: two parallel submits of the same attempt cannot both grade it
    attempt = db.scalar(
        _scope(select(LessonSkillAttempt), user_id, lesson_id, skill, listening_id, exercise_id)
        .where(LessonSkillAttempt.id == attempt_id)
        .with_for_update()
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")
    if attempt.status != ATTEMPT_IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ATTEMPT_ALREADY_SUBMITTED")
    clean = clean_answers(questions, answers)
    result = grade(questions, clean)
    now = _now()
    attempt.answers = clean
    attempt.correct_count = result["correct_count"]
    attempt.question_count = result["question_count"]
    attempt.points = result["points"]
    attempt.max_points = result["max_points"]
    attempt.score = result["score"]
    attempt.status = ATTEMPT_SUBMITTED
    attempt.submitted_at = now
    started = attempt.started_at if attempt.started_at.tzinfo else attempt.started_at.replace(tzinfo=timezone.utc)
    attempt.duration_seconds = max(0, int((now - started).total_seconds()))
    # Lernserie: server start -> submit time of this attempt, capped, credited once
    from app.services.learning_activity import credit_attempt

    credit_attempt(db, user_id, attempt.id, lesson_id, attempt.duration_seconds, now)
    db.commit()
    db.refresh(attempt)
    return attempt, result


def review(attempt: LessonSkillAttempt, questions: list) -> dict:
    """Result of a SUBMITTED attempt, graded against the current key."""
    if attempt.status != ATTEMPT_SUBMITTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ATTEMPT_NOT_SUBMITTED")
    return grade(questions, attempt.answers or {})


def summary(rows: list[LessonSkillAttempt]) -> dict:
    submitted = [a for a in rows if a.status == ATTEMPT_SUBMITTED and a.score is not None]
    best = max(submitted, key=lambda a: (a.score, a.submitted_at), default=None)
    last = submitted[-1] if submitted else None
    return {
        "attempts_count": len(submitted),
        "best_score": best.score if best else None,
        "last_score": last.score if last else None,
        "last_submitted_at": last.submitted_at if last else None,
        "in_progress_attempt_id": next((a.id for a in rows if a.status == ATTEMPT_IN_PROGRESS), None),
    }


def attempt_item(a: LessonSkillAttempt) -> dict:
    return {
        "id": a.id,
        "attempt_number": a.attempt_number,
        "status": a.status,
        "score": a.score,
        "correct_count": a.correct_count,
        "question_count": a.question_count,
        "started_at": a.started_at,
        "submitted_at": a.submitted_at,
        "duration_seconds": a.duration_seconds,
    }


def count_attempts(db: Session, user_id: UUID, lesson_id: UUID, skill: str) -> int:
    return int(
        db.scalar(
            select(func.count(LessonSkillAttempt.id)).where(
                LessonSkillAttempt.user_id == user_id,
                LessonSkillAttempt.lesson_id == lesson_id,
                LessonSkillAttempt.skill == skill,
                LessonSkillAttempt.status == ATTEMPT_SUBMITTED,
            )
        )
        or 0
    )


__all__ = ["SKILL_LESEN", "SKILL_HOEREN"]
