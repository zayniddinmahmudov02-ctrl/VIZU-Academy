"""VIZU-Multilevel Hören — task list, autosave, server-side grading.

5 Aufgaben x 1 audio x 4 multiple-choice questions, 1 point each = 20.
Correctness lives only in the database: students receive questions and
options, never `is_correct`, never the audio script (transcript) and never
a storage path — the audio itself is streamed through an authenticated
endpoint (see hoeren_audio_service). The level used for the overall result
is derived from the total score with the same percentage thresholds as
Lesen and is never shown to the student."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_attempt import VizuMultilevelAttempt
from app.models.vizu_multilevel_content import (
    SKILL_HOEREN,
    VizuMultilevelAnswer,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)
from app.services.vizu_multilevel import hoeren_audio_service, service
from app.services.vizu_multilevel.lesen_service import level_for_score



def list_hoeren_tasks(db: Session) -> list[dict]:
    tasks = list(
        db.scalars(
            select(VizuMultilevelTask)
            .where(VizuMultilevelTask.skill == SKILL_HOEREN, VizuMultilevelTask.is_published.is_(True))
            .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
            .order_by(VizuMultilevelTask.order_index)
        ).unique()
    )
    with_audio = hoeren_audio_service.numbers_with_audio(db)
    return [
        {
            "id": t.id,
            "skill": t.skill,
            "order_index": t.order_index,
            # Hören has no reading text; the transcript is admin-only.
            "passage_text": None,
            "has_audio": t.order_index in with_audio,
            "questions": t.questions,
        }
        for t in tasks
    ]


def _questions(db: Session) -> list[VizuMultilevelQuestion]:
    return list(
        db.scalars(
            select(VizuMultilevelQuestion)
            .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
            .where(VizuMultilevelTask.skill == SKILL_HOEREN, VizuMultilevelTask.is_published.is_(True))
            .options(joinedload(VizuMultilevelQuestion.options))
            .order_by(VizuMultilevelQuestion.order_index)
        ).unique()
    )


def _valid_choice(question: VizuMultilevelQuestion, option_id: str | None) -> bool:
    return bool(option_id) and any(str(o.id) == option_id for o in question.options)


# ============================================================
# Autosave
# ============================================================


def get_draft(attempt: VizuMultilevelAttempt) -> dict[str, str]:
    return dict(attempt.hoeren_draft or {})


def save_draft(db: Session, attempt: VizuMultilevelAttempt, answers: list) -> dict[str, str]:
    """Merges the given answers into the attempt's draft. Only possible
    while the competency is open (not submitted, inside the 20 minutes);
    selections that do not belong to a real Hören question are ignored."""
    service.ensure_section_open_strict(db, attempt, "hoeren")
    by_id = {str(q.id): q for q in _questions(db)}
    draft = get_draft(attempt)
    for answer in answers:
        question = by_id.get(str(answer.question_id))
        if question is None:
            continue
        option_id = str(answer.option_id) if answer.option_id else None
        if option_id is None:
            draft.pop(str(question.id), None)
        elif _valid_choice(question, option_id):
            draft[str(question.id)] = option_id
    attempt.hoeren_draft = draft
    db.commit()
    return draft


# ============================================================
# Result / submit
# ============================================================


def get_hoeren_result(db: Session, attempt: VizuMultilevelAttempt) -> dict:
    rows = db.execute(
        select(VizuMultilevelQuestion.points)
        .select_from(VizuMultilevelAnswer)
        .join(VizuMultilevelQuestion, VizuMultilevelAnswer.question_id == VizuMultilevelQuestion.id)
        .join(VizuMultilevelTask, VizuMultilevelQuestion.task_id == VizuMultilevelTask.id)
        .where(VizuMultilevelAnswer.attempt_id == attempt.id, VizuMultilevelTask.skill == SKILL_HOEREN)
    ).all()
    return {
        "attempt_id": attempt.id,
        "total_points": float(attempt.hoeren_score or 0),
        "max_points": float(sum(r[0] for r in rows)),
        "correct": attempt.hoeren_correct or 0,
        "wrong": attempt.hoeren_wrong or 0,
        "unanswered": attempt.hoeren_unanswered or 0,
    }


def submit_hoeren(db: Session, attempt: VizuMultilevelAttempt, answers: list) -> dict:
    """Final "Hören abschließen". Grades every published Hören question on
    the server (1 point each, no negatives) and stores score + counts +
    level on the attempt exactly once — afterwards answers can no longer
    change. Answers = the autosaved draft, overridden by the ones sent now
    (ignored if the window already closed). Unless the time is up, at least
    MIN_ANSWERS questions must be answered."""
    service.ensure_attempt_active(attempt)
    if service.is_submitted(attempt, "hoeren"):
        return get_hoeren_result(db, attempt)

    in_time = service.begin_submission(db, attempt, "hoeren")
    questions = _questions(db)

    chosen = get_draft(attempt)
    if in_time:
        for answer in answers:
            if answer.option_id:
                chosen[str(answer.question_id)] = str(answer.option_id)

    answered = sum(1 for q in questions if _valid_choice(q, chosen.get(str(q.id))))
    # At least 5 answered (or all, if fewer exist) — unless the time is up.
    service.check_min_answers(attempt, "hoeren", answered, len(questions))

    total = maximum = 0.0
    correct = wrong = unanswered = 0
    for question in questions:
        selected_id = chosen.get(str(question.id))
        selected = next((o for o in question.options if str(o.id) == selected_id), None) if selected_id else None
        is_correct = bool(selected and selected.is_correct)
        earned = question.points if is_correct else 0
        total += earned
        maximum += question.points
        if selected is None:
            unanswered += 1
        elif is_correct:
            correct += 1
        else:
            wrong += 1
        db.add(
            VizuMultilevelAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected.id if selected else None,
                is_correct=is_correct,
                points_earned=earned,
            )
        )

    attempt.hoeren_score = total
    attempt.hoeren_correct = correct
    attempt.hoeren_wrong = wrong
    attempt.hoeren_unanswered = unanswered
    attempt.hoeren_level = level_for_score(total, maximum)
    attempt.hoeren_draft = None
    service.mark_submitted(db, attempt, "hoeren")
    return get_hoeren_result(db, attempt)
