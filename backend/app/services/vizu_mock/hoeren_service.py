from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_mock_attempt import VizuMockAttempt
from app.models.vizu_mock_audio import VizuMockAudio
from app.models.vizu_mock_content import SKILL_HOEREN, CEFR_LEVELS, VizuMockAnswer, VizuMockQuestion, VizuMockTask

# Same "kamida 3/4" cascade rule as Lesen (see lesen_service.py's own
# docstring) — duplicated rather than imported so each skill module stays
# independently readable/self-contained, matching this codebase's
# existing per-skill service convention.
PASS_NUMERATOR = 3
PASS_DENOMINATOR = 4


def list_hoeren_tasks(db: Session) -> list[dict]:
    """Like lesen_service.list_lesen_tasks, but each task also carries its
    active Hören audio's URL (never the script/transcript — Hören content
    has no passage_text at all, only spoken audio + questions)."""
    tasks = list(
        db.scalars(
            select(VizuMockTask)
            .where(VizuMockTask.skill == SKILL_HOEREN)
            .options(joinedload(VizuMockTask.questions).joinedload(VizuMockQuestion.options))
            .order_by(VizuMockTask.order_index)
        ).unique()
    )
    task_ids = [t.id for t in tasks]

    audio_by_task: dict[UUID, str] = {}
    if task_ids:
        audio_rows = db.execute(
            select(VizuMockAudio.task_id, VizuMockAudio.audio_url)
            .where(VizuMockAudio.task_id.in_(task_ids), VizuMockAudio.is_active.is_(True))
            .order_by(VizuMockAudio.created_at.desc())
        ).all()
        for task_id, audio_url in audio_rows:
            # Most-recently-created active audio wins if more than one was
            # ever attached to the same task (rows are already newest-first).
            audio_by_task.setdefault(task_id, audio_url)

    return [
        {
            "id": t.id,
            "skill": t.skill,
            "level": t.level,
            "order_index": t.order_index,
            "passage_text": t.passage_text,
            "audio_url": audio_by_task.get(t.id),
            "questions": t.questions,
        }
        for t in tasks
    ]


def _level_breakdown(db: Session, attempt_id: UUID) -> list[dict]:
    rows = db.execute(
        select(VizuMockTask.level, VizuMockQuestion.points, VizuMockAnswer.points_earned)
        .select_from(VizuMockAnswer)
        .join(VizuMockQuestion, VizuMockAnswer.question_id == VizuMockQuestion.id)
        .join(VizuMockTask, VizuMockQuestion.task_id == VizuMockTask.id)
        .where(VizuMockAnswer.attempt_id == attempt_id, VizuMockTask.skill == SKILL_HOEREN)
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
    confirmed = None
    for entry in level_scores:
        if entry["passed"]:
            confirmed = entry["level"]
        else:
            break
    return confirmed


def get_hoeren_result(db: Session, attempt: VizuMockAttempt) -> dict:
    level_scores = _level_breakdown(db, attempt.id)
    return {
        "attempt_id": attempt.id,
        "total_points": sum(entry["points"] for entry in level_scores),
        "max_points": sum(entry["max_points"] for entry in level_scores),
        "level_scores": level_scores,
        "hoeren_level": attempt.hoeren_level,
    }


def submit_hoeren(db: Session, attempt: VizuMockAttempt, answers: list) -> dict:
    """Grades every Hören question server-side and writes hoeren_score/
    hoeren_level onto the attempt exactly once — idempotent resubmit,
    same construction as lesen_service.submit_lesen."""
    already_graded = (
        db.execute(
            select(VizuMockAnswer.id)
            .join(VizuMockQuestion, VizuMockAnswer.question_id == VizuMockQuestion.id)
            .join(VizuMockTask, VizuMockQuestion.task_id == VizuMockTask.id)
            .where(VizuMockAnswer.attempt_id == attempt.id, VizuMockTask.skill == SKILL_HOEREN)
            .limit(1)
        ).first()
        is not None
    )
    if already_graded:
        return get_hoeren_result(db, attempt)

    questions = list(
        db.scalars(
            select(VizuMockQuestion)
            .join(VizuMockTask, VizuMockQuestion.task_id == VizuMockTask.id)
            .where(VizuMockTask.skill == SKILL_HOEREN)
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
    attempt.hoeren_score = sum(entry["points"] for entry in level_scores)
    attempt.hoeren_level = _confirmed_level(level_scores)
    db.commit()
    db.refresh(attempt)

    return get_hoeren_result(db, attempt)
