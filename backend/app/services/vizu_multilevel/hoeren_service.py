from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.services.vizu_multilevel import service
from app.models.vizu_multilevel_audio import VizuMultilevelAudio
from app.models.vizu_multilevel_content import SKILL_HOEREN, CEFR_LEVELS, VizuMultilevelAnswer, VizuMultilevelQuestion, VizuMultilevelTask

# Same "kamida 3/4" cascade rule as Lesen (see lesen_service.py's own
# docstring) — duplicated rather than imported so each skill module stays
# independently readable/self-contained, matching this codebase's
# existing per-skill service convention.
PASS_NUMERATOR = 3
PASS_DENOMINATOR = 4


def list_hoeren_tasks(db: Session, include_unpublished: bool = False) -> list[dict]:
    """Like lesen_service.list_lesen_tasks, but each task also carries its
    active Hören audio's URL (never the script/transcript — Hören content
    has no passage_text at all, only spoken audio + questions)."""
    query = select(VizuMultilevelTask).where(VizuMultilevelTask.skill == SKILL_HOEREN)
    if not include_unpublished:
        query = query.where(VizuMultilevelTask.is_published.is_(True))
    tasks = list(
        db.scalars(
            query
            .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
            .order_by(VizuMultilevelTask.order_index)
        ).unique()
    )
    task_ids = [t.id for t in tasks]

    audio_by_task: dict[UUID, str] = {}
    if task_ids:
        audio_rows = db.execute(
            select(VizuMultilevelAudio.task_id, VizuMultilevelAudio.audio_url)
            .where(VizuMultilevelAudio.task_id.in_(task_ids), VizuMultilevelAudio.is_active.is_(True))
            .order_by(VizuMultilevelAudio.created_at.desc())
        ).all()
        for task_id, audio_url in audio_rows:
            # Most-recently-created active audio wins if more than one was
            # ever attached to the same task (rows are already newest-first).
            audio_by_task.setdefault(task_id, audio_url)

    return [
        {
            "id": t.id,
            "skill": t.skill,
            "order_index": t.order_index,
            # Hören has no reading text; the transcript is admin-only.
            "passage_text": None,
            "audio_url": audio_by_task.get(t.id),
            "questions": t.questions,
        }
        for t in tasks
    ]


def _level_breakdown(db: Session, attempt_id: UUID) -> list[dict]:
    """Each level's points/max_points are sums of VizuMultilevelQuestion.points
    (a float — Hören weights points by CEFR level, A1=0.5 ... C1=2.5, see
    services/vizu_multilevel/hoeren_csv_import_service.py), not a flat integer
    per question like Lesen. The 3/4 pass check below is a ratio, so it
    stays correct regardless of the per-level point scale."""
    rows = db.execute(
        select(VizuMultilevelTask.level, VizuMultilevelQuestion.points, VizuMultilevelAnswer.points_earned)
        .select_from(VizuMultilevelAnswer)
        .join(VizuMultilevelQuestion, VizuMultilevelAnswer.question_id == VizuMultilevelQuestion.id)
        .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
        .where(VizuMultilevelAnswer.attempt_id == attempt_id, VizuMultilevelTask.skill == SKILL_HOEREN)
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


def get_hoeren_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    level_scores = _level_breakdown(db, attempt.id)
    return {
        "attempt_id": attempt.id,
        "total_points": sum(entry["points"] for entry in level_scores),
        "max_points": sum(entry["max_points"] for entry in level_scores),
        "level_scores": level_scores,
        "hoeren_level": attempt.hoeren_level,
    }


def submit_hoeren(db: Session, attempt: VizuMultilevelAttempt, answers: list) -> dict:
    """Grades every Hören question server-side (never trusting anything the
    client claims about correctness) and writes hoeren_score/hoeren_level
    onto the attempt exactly once. Unanswered questions earn 0 points, so
    the student may finish at any time without answering everything.
    If the 20-minute window has already closed (server clock, deadline +
    grace) the submitted answers are ignored and the section is graded as
    unanswered. A resubmit is a no-op that returns the stored result."""
    if service.is_submitted(attempt, "hoeren"):
        return get_hoeren_result(db, attempt)

    in_time = service.begin_submission(db, attempt, "hoeren")
    if not in_time:
        answers = []

    questions = list(
        db.scalars(
            select(VizuMultilevelQuestion)
            .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
            .where(VizuMultilevelTask.skill == SKILL_HOEREN, VizuMultilevelTask.is_published.is_(True))
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
    attempt.hoeren_score = sum(entry["points"] for entry in level_scores)
    attempt.hoeren_level = _confirmed_level(level_scores)
    service.mark_submitted(db, attempt, "hoeren")

    return get_hoeren_result(db, attempt)
