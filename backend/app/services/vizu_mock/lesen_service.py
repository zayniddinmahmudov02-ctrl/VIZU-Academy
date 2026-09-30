from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_mock_attempt import VizuMockAttempt
from app.models.vizu_mock_content import SKILL_LESEN, CEFR_LEVELS, VizuMockAnswer, VizuMockQuestion, VizuMockTask

# "kamida 3/4" — a level counts as confirmed once its 4 questions earn at
# least 3 of their 4 points. Computed as a fraction of each level's real
# max (not hardcoded to 4) so this still works if content is added later
# with a different question count per level.
PASS_NUMERATOR = 3
PASS_DENOMINATOR = 4


def list_lesen_tasks(db: Session) -> list[VizuMockTask]:
    return list(
        db.scalars(
            select(VizuMockTask)
            .where(VizuMockTask.skill == SKILL_LESEN)
            .options(joinedload(VizuMockTask.questions).joinedload(VizuMockQuestion.options))
            .order_by(VizuMockTask.order_index)
        )
        .unique()
    )


def _level_breakdown(db: Session, attempt_id: UUID) -> list[dict]:
    """Aggregates this attempt's stored VizuMockAnswer rows into a
    per-level points/max_points/passed breakdown — the single function
    both a fresh grading and a later idempotent re-fetch build their
    response from, so they can never disagree with each other."""
    rows = db.execute(
        select(VizuMockTask.level, VizuMockQuestion.points, VizuMockAnswer.points_earned)
        .select_from(VizuMockAnswer)
        .join(VizuMockQuestion, VizuMockAnswer.question_id == VizuMockQuestion.id)
        .join(VizuMockTask, VizuMockQuestion.task_id == VizuMockTask.id)
        .where(VizuMockAnswer.attempt_id == attempt_id, VizuMockTask.skill == SKILL_LESEN)
    ).all()

    points_by_level = {level: 0 for level in CEFR_LEVELS}
    max_by_level = {level: 0 for level in CEFR_LEVELS}
    for level, max_points, earned in rows:
        max_by_level[level] += max_points
        points_by_level[level] += earned

    return [
        {
            "level": level,
            "points": points_by_level[level],
            "max_points": max_by_level[level],
            "passed": max_by_level[level] > 0
            and points_by_level[level] * PASS_DENOMINATOR >= PASS_NUMERATOR * max_by_level[level],
        }
        for level in CEFR_LEVELS
    ]


def _confirmed_level(level_scores: list[dict]) -> str | None:
    """The result is the highest level in an unbroken chain of passes
    starting from A1 — never just "whichever levels passed", so a
    student who fails B1 but somehow passes B2 still gets A2, matching
    the spec's example exactly."""
    confirmed = None
    for entry in level_scores:
        if entry["passed"]:
            confirmed = entry["level"]
        else:
            break
    return confirmed


def get_lesen_result(db: Session, attempt: VizuMockAttempt) -> dict:
    level_scores = _level_breakdown(db, attempt.id)
    return {
        "attempt_id": attempt.id,
        "total_points": sum(entry["points"] for entry in level_scores),
        "max_points": sum(entry["max_points"] for entry in level_scores),
        "level_scores": level_scores,
        "lesen_level": attempt.lesen_level,
    }


def submit_lesen(db: Session, attempt: VizuMockAttempt, answers: list) -> dict:
    """Grades every Lesen question server-side (never trusting anything
    the client claims about correctness) and writes lesen_score/
    lesen_level onto the attempt exactly once. A resubmit for an attempt
    that's already been graded is a no-op that just returns the stored
    result — idempotent by construction, not by accident."""
    already_graded = (
        db.execute(
            select(VizuMockAnswer.id)
            .join(VizuMockQuestion, VizuMockAnswer.question_id == VizuMockQuestion.id)
            .join(VizuMockTask, VizuMockQuestion.task_id == VizuMockTask.id)
            .where(VizuMockAnswer.attempt_id == attempt.id, VizuMockTask.skill == SKILL_LESEN)
            .limit(1)
        ).first()
        is not None
    )
    if already_graded:
        return get_lesen_result(db, attempt)

    questions = list(
        db.scalars(
            select(VizuMockQuestion)
            .join(VizuMockTask, VizuMockQuestion.task_id == VizuMockTask.id)
            .where(VizuMockTask.skill == SKILL_LESEN)
            .options(joinedload(VizuMockQuestion.options))
        ).unique()
    )
    answer_by_question = {a.question_id: a.option_id for a in answers}

    for question in questions:
        selected_id = answer_by_question.get(question.id)
        selected_option = next((o for o in question.options if o.id == selected_id), None) if selected_id else None
        is_correct = bool(selected_option and selected_option.is_correct)
        db.add(
            VizuMockAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected_id,
                is_correct=is_correct,
                points_earned=question.points if is_correct else 0,
            )
        )

    db.flush()
    level_scores = _level_breakdown(db, attempt.id)
    attempt.lesen_score = sum(entry["points"] for entry in level_scores)
    attempt.lesen_level = _confirmed_level(level_scores)
    db.commit()
    db.refresh(attempt)

    return get_lesen_result(db, attempt)
