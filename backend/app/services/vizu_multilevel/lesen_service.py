from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.services.vizu_multilevel import service
from app.models.vizu_multilevel_content import SKILL_LESEN, CEFR_LEVELS, VizuMultilevelAnswer, VizuMultilevelQuestion, VizuMultilevelTask

# "kamida 3/4" — a level counts as confirmed once its 4 questions earn at
# least 3 of their 4 points. Computed as a fraction of each level's real
# max (not hardcoded to 4) so this still works if content is added later
# with a different question count per level.
PASS_NUMERATOR = 3
PASS_DENOMINATOR = 4


def list_lesen_tasks(db: Session, include_unpublished: bool = False) -> list[VizuMultilevelTask]:
    query = select(VizuMultilevelTask).where(VizuMultilevelTask.skill == SKILL_LESEN)
    if not include_unpublished:
        query = query.where(VizuMultilevelTask.is_published.is_(True))
    return list(
        db.scalars(
            query
            .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
            .order_by(VizuMultilevelTask.order_index)
        )
        .unique()
    )


def _level_breakdown(db: Session, attempt_id: UUID) -> list[dict]:
    """Aggregates this attempt's stored VizuMultilevelAnswer rows into a
    per-level points/max_points/passed breakdown — the single function
    both a fresh grading and a later idempotent re-fetch build their
    response from, so they can never disagree with each other."""
    rows = db.execute(
        select(VizuMultilevelTask.level, VizuMultilevelQuestion.points, VizuMultilevelAnswer.points_earned)
        .select_from(VizuMultilevelAnswer)
        .join(VizuMultilevelQuestion, VizuMultilevelAnswer.question_id == VizuMultilevelQuestion.id)
        .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
        .where(VizuMultilevelAnswer.attempt_id == attempt_id, VizuMultilevelTask.skill == SKILL_LESEN)
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


def get_lesen_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    level_scores = _level_breakdown(db, attempt.id)
    return {
        "attempt_id": attempt.id,
        "total_points": sum(entry["points"] for entry in level_scores),
        "max_points": sum(entry["max_points"] for entry in level_scores),
        "level_scores": level_scores,
        "lesen_level": attempt.lesen_level,
    }


def submit_lesen(db: Session, attempt: VizuMultilevelAttempt, answers: list) -> dict:
    """Grades every Lesen question server-side (never trusting anything the
    client claims about correctness) and writes lesen_score/lesen_level
    onto the attempt exactly once. Unanswered questions earn 0 points, so
    the student may finish at any time without answering everything.
    If the 20-minute window has already closed (server clock, deadline +
    grace) the submitted answers are ignored and the section is graded as
    unanswered. A resubmit is a no-op that returns the stored result."""
    if service.is_submitted(attempt, "lesen"):
        return get_lesen_result(db, attempt)

    in_time = service.begin_submission(db, attempt, "lesen")
    if not in_time:
        answers = []

    questions = list(
        db.scalars(
            select(VizuMultilevelQuestion)
            .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
            .where(VizuMultilevelTask.skill == SKILL_LESEN, VizuMultilevelTask.is_published.is_(True))
            .options(joinedload(VizuMultilevelQuestion.options))
        ).unique()
    )
    answer_by_question = {a.question_id: a.option_id for a in answers}

    for question in questions:
        selected_id = answer_by_question.get(question.id)
        selected_option = next((o for o in question.options if o.id == selected_id), None) if selected_id else None
        is_correct = bool(selected_option and selected_option.is_correct)
        db.add(
            VizuMultilevelAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                # Only keep a selection that really belongs to this question.
                selected_option_id=selected_option.id if selected_option else None,
                is_correct=is_correct,
                points_earned=question.points if is_correct else 0,
            )
        )

    db.flush()
    level_scores = _level_breakdown(db, attempt.id)
    attempt.lesen_score = sum(entry["points"] for entry in level_scores)
    attempt.lesen_level = _confirmed_level(level_scores)
    service.mark_submitted(db, attempt, "lesen")

    return get_lesen_result(db, attempt)
