"""VIZU-Multilevel Lesen — task list, server-side grading and the final
level. 20 questions x 5 points = 100 points. The level is derived from the
TOTAL score only (see LEVEL_THRESHOLDS); the CEFR level stored on each
task is internal data and is never sent to the student."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_content import (
    SKILL_LESEN,
    VizuMultilevelAnswer,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)
from app.services.vizu_multilevel import service

POINTS_PER_QUESTION = 5

# (minimum score out of 100, level) — highest first. Below the lowest
# threshold the result is "below A1" (level None).
LEVEL_THRESHOLDS: list[tuple[float, str]] = [
    (90, "C1"),
    (75, "B2"),
    (60, "B1"),
    (40, "A2"),
    (20, "A1"),
]


def level_for_score(total_points: float, max_points: float) -> str | None:
    """Maps the Lesen score to a CEFR level. The thresholds are defined on
    a 0-100 scale, so the score is normalised to a percentage of the max
    (identical to the raw score while the max is 100). No questions at all
    (max 0) never yields a level."""
    if max_points <= 0:
        return None
    percent = total_points / max_points * 100
    for minimum, level in LEVEL_THRESHOLDS:
        if percent >= minimum:
            return level
    return None


def list_lesen_tasks(db: Session) -> list[dict]:
    """Published Aufgaben with their ACTIVE questions, in order. Carries no
    CEFR level and no correct-answer information."""
    tasks = list(
        db.scalars(
            select(VizuMultilevelTask)
            .where(VizuMultilevelTask.skill == SKILL_LESEN, VizuMultilevelTask.is_published.is_(True))
            .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
            .order_by(VizuMultilevelTask.order_index)
        ).unique()
    )
    result = []
    for task in tasks:
        questions = [q for q in task.questions if q.is_active]
        if questions:
            result.append(
                {
                    "id": task.id,
                    "skill": task.skill,
                    "order_index": task.order_index,
                    "passage_text": task.passage_text,
                    "questions": questions,
                }
            )
    return result


def get_lesen_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    max_points = _answered_max(db, attempt)
    return {
        "attempt_id": attempt.id,
        "total_points": float(attempt.lesen_score or 0),
        "max_points": max_points,
        "correct": attempt.lesen_correct or 0,
        "wrong": attempt.lesen_wrong or 0,
        "unanswered": attempt.lesen_unanswered or 0,
        "lesen_level": attempt.lesen_level,
        "below_a1": service.is_submitted(attempt, "lesen") and attempt.lesen_level is None and max_points > 0,
    }


def _answered_max(db: Session, attempt: VizuMultilevelAttempt) -> float:
    rows = db.execute(
        select(VizuMultilevelQuestion.points)
        .select_from(VizuMultilevelAnswer)
        .join(VizuMultilevelQuestion, VizuMultilevelAnswer.question_id == VizuMultilevelQuestion.id)
        .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
        .where(VizuMultilevelAnswer.attempt_id == attempt.id, VizuMultilevelTask.skill == SKILL_LESEN)
    ).all()
    return float(sum(r[0] for r in rows))


def submit_lesen(db: Session, attempt: VizuMultilevelAttempt, answers: list) -> dict:
    """Grades every active Lesen question server-side (the client never
    sends or receives correctness): correct = +5, wrong or unanswered = 0,
    no negative scoring. Writes score, correct/wrong/unanswered counts and
    the level onto the attempt exactly once. Unanswered questions simply
    score 0, so the student may finish at any time. If the 20-minute window
    has already closed (server clock, deadline + grace) the submitted
    answers are ignored. A resubmit returns the stored result."""
    service.ensure_attempt_active(attempt)
    if service.is_submitted(attempt, "lesen"):
        return get_lesen_result(db, attempt)

    in_time = service.begin_submission(db, attempt, "lesen")
    if not in_time:
        answers = []

    questions = list(
        db.scalars(
            select(VizuMultilevelQuestion)
            .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
            .where(
                VizuMultilevelTask.skill == SKILL_LESEN,
                VizuMultilevelTask.is_published.is_(True),
                VizuMultilevelQuestion.is_active.is_(True),
            )
            .options(joinedload(VizuMultilevelQuestion.options))
        ).unique()
    )
    answer_by_question = {a.question_id: a.option_id for a in answers}
    answered = sum(
        1 for q in questions if any(o.id == answer_by_question.get(q.id) for o in q.options)
    )
    service.check_min_answers(attempt, "lesen", answered, len(questions))

    total = 0.0
    maximum = 0.0
    correct = wrong = unanswered = 0
    for question in questions:
        selected_id = answer_by_question.get(question.id)
        selected_option = next((o for o in question.options if o.id == selected_id), None) if selected_id else None
        is_correct = bool(selected_option and selected_option.is_correct)
        earned = question.points if is_correct else 0
        total += earned
        maximum += question.points
        if selected_option is None:
            unanswered += 1
        elif is_correct:
            correct += 1
        else:
            wrong += 1
        db.add(
            VizuMultilevelAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                # Only keep a selection that really belongs to this question.
                selected_option_id=selected_option.id if selected_option else None,
                is_correct=is_correct,
                points_earned=earned,
            )
        )

    attempt.lesen_score = int(total)
    attempt.lesen_correct = correct
    attempt.lesen_wrong = wrong
    attempt.lesen_unanswered = unanswered
    # Below A1 -> None: not stored as a successful level.
    attempt.lesen_level = level_for_score(total, maximum)
    service.mark_submitted(db, attempt, "lesen")

    return get_lesen_result(db, attempt)
