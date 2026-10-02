"""Admin CRUD for VIZU-Multilevel Lesen / Hören content: Aufgabe (reading
text or audio+transcript, level, order, publish state), questions and
their options (exactly one correct). Content starts EMPTY — everything
here is authored by the admin (or imported via CSV). Students only ever
see published Aufgaben, and never the level / correct answers."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_audio import VizuMultilevelAudio
from app.models.vizu_multilevel_content import (
    SKILL_HOEREN,
    SKILL_LESEN,
    VizuMultilevelOption,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)
from app.schemas.vizu_multilevel import (
    VizuMultilevelQuestionInput,
    VizuMultilevelTaskAdminCreate,
    VizuMultilevelTaskAdminUpdate,
)

CONTENT_SKILLS = {"lesen": SKILL_LESEN, "hoeren": SKILL_HOEREN}


class ContentConflictError(Exception):
    """A (skill, order_index) / (task, order_index) uniqueness clash."""


def _load_task(db: Session, task_id: UUID) -> VizuMultilevelTask | None:
    return db.scalar(
        select(VizuMultilevelTask)
        .where(VizuMultilevelTask.id == task_id)
        .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
    )


def _is_content_task(task: VizuMultilevelTask | None) -> bool:
    return task is not None and task.skill in CONTENT_SKILLS.values()


def _audio_by_task(db: Session, task_ids: list[UUID]) -> dict[UUID, str]:
    if not task_ids:
        return {}
    out: dict[UUID, str] = {}
    rows = db.execute(
        select(VizuMultilevelAudio.task_id, VizuMultilevelAudio.audio_url)
        .where(VizuMultilevelAudio.task_id.in_(task_ids), VizuMultilevelAudio.is_active.is_(True))
        .order_by(VizuMultilevelAudio.created_at.desc())
    ).all()
    for task_id, url in rows:
        out.setdefault(task_id, url)
    return out


def _to_admin(task: VizuMultilevelTask, audio_url: str | None) -> dict:
    return {
        "id": task.id,
        "skill": task.skill,
        "level": task.level,
        "order_index": task.order_index,
        "passage_text": task.passage_text,
        "transcript": task.transcript,
        "is_published": task.is_published,
        "audio_url": audio_url,
        "questions": [
            {
                "id": q.id,
                "question_type": q.question_type,
                "passage_text": q.passage_text,
                "prompt": q.prompt,
                "order_index": q.order_index,
                "points": q.points,
                "is_active": q.is_active,
                "options": [
                    {"id": o.id, "option_text": o.option_text, "is_correct": o.is_correct, "order_index": o.order_index}
                    for o in q.options
                ],
            }
            for q in task.questions
        ],
    }


def list_tasks(db: Session, skill: str) -> list[dict]:
    const = CONTENT_SKILLS[skill]
    tasks = list(
        db.scalars(
            select(VizuMultilevelTask)
            .where(VizuMultilevelTask.skill == const)
            .options(joinedload(VizuMultilevelTask.questions).joinedload(VizuMultilevelQuestion.options))
            .order_by(VizuMultilevelTask.order_index)
        ).unique()
    )
    audio = _audio_by_task(db, [t.id for t in tasks]) if const == SKILL_HOEREN else {}
    return [_to_admin(t, audio.get(t.id)) for t in tasks]


def get_task(db: Session, task_id: UUID) -> dict | None:
    task = _load_task(db, task_id)
    if not _is_content_task(task):
        return None
    audio = _audio_by_task(db, [task.id]) if task.skill == SKILL_HOEREN else {}
    return _to_admin(task, audio.get(task.id))


def _order_taken(db: Session, skill_value: str, order_index: int, exclude: UUID | None = None) -> bool:
    query = select(VizuMultilevelTask.id).where(
        VizuMultilevelTask.skill == skill_value, VizuMultilevelTask.order_index == order_index
    )
    if exclude is not None:
        query = query.where(VizuMultilevelTask.id != exclude)
    return db.scalar(query) is not None


def create_task(db: Session, skill: str, data: VizuMultilevelTaskAdminCreate) -> dict:
    const = CONTENT_SKILLS[skill]
    if _order_taken(db, const, data.order_index):
        raise ContentConflictError("An Aufgabe with this order already exists.")
    task = VizuMultilevelTask(
        skill=const,
        level=data.level,
        order_index=data.order_index,
        # Lesen: shared reading text. Hören: no reading text — audio + transcript only.
        passage_text=data.passage_text if const == SKILL_LESEN else None,
        transcript=data.transcript if const == SKILL_HOEREN else None,
        is_published=data.is_published,
    )
    db.add(task)
    db.commit()
    return get_task(db, task.id)


def update_task(db: Session, task_id: UUID, data: VizuMultilevelTaskAdminUpdate) -> dict | None:
    task = _load_task(db, task_id)
    if not _is_content_task(task):
        return None
    updates = data.model_dump(exclude_unset=True)
    if "order_index" in updates and _order_taken(db, task.skill, updates["order_index"], exclude=task.id):
        raise ContentConflictError("An Aufgabe with this order already exists.")
    if task.skill == SKILL_HOEREN:
        updates.pop("passage_text", None)
    else:
        updates.pop("transcript", None)
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    return get_task(db, task_id)


def delete_task(db: Session, task_id: UUID) -> bool:
    task = db.scalar(select(VizuMultilevelTask).where(VizuMultilevelTask.id == task_id))
    if not _is_content_task(task):
        return False
    db.delete(task)
    db.commit()
    return True


# ---- Questions ----


def _replace_options(question: VizuMultilevelQuestion, data: VizuMultilevelQuestionInput) -> None:
    question.options.clear()
    for index, option in enumerate(data.options, start=1):
        question.options.append(
            VizuMultilevelOption(option_text=option.option_text.strip(), is_correct=option.is_correct, order_index=index)
        )


def _question_order_taken(db: Session, task_id: UUID, order_index: int, exclude: UUID | None = None) -> bool:
    query = select(VizuMultilevelQuestion.id).where(
        VizuMultilevelQuestion.task_id == task_id, VizuMultilevelQuestion.order_index == order_index
    )
    if exclude is not None:
        query = query.where(VizuMultilevelQuestion.id != exclude)
    return db.scalar(query) is not None


def create_question(db: Session, task_id: UUID, data: VizuMultilevelQuestionInput) -> dict | None:
    task = _load_task(db, task_id)
    if not _is_content_task(task):
        return None
    if _question_order_taken(db, task_id, data.order_index):
        raise ContentConflictError("A question with this order already exists in this Aufgabe.")
    question = VizuMultilevelQuestion(
        task_id=task_id,
        question_type=data.question_type,
        passage_text=data.passage_text if task.skill == SKILL_LESEN else None,
        prompt=data.prompt,
        order_index=data.order_index,
        points=data.points,
        is_active=data.is_active,
    )
    _replace_options(question, data)
    db.add(question)
    db.commit()
    return get_task(db, task_id)


def update_question(db: Session, question_id: UUID, data: VizuMultilevelQuestionInput) -> dict | None:
    question = db.scalar(
        select(VizuMultilevelQuestion)
        .where(VizuMultilevelQuestion.id == question_id)
        .options(joinedload(VizuMultilevelQuestion.options))
    )
    if question is None:
        return None
    task = _load_task(db, question.task_id)
    if not _is_content_task(task):
        return None
    if _question_order_taken(db, question.task_id, data.order_index, exclude=question.id):
        raise ContentConflictError("A question with this order already exists in this Aufgabe.")
    question.question_type = data.question_type
    question.passage_text = data.passage_text if task.skill == SKILL_LESEN else None
    question.prompt = data.prompt
    question.order_index = data.order_index
    question.points = data.points
    question.is_active = data.is_active
    _replace_options(question, data)
    db.commit()
    return get_task(db, question.task_id)


def delete_question(db: Session, question_id: UUID) -> dict | None:
    question = db.scalar(select(VizuMultilevelQuestion).where(VizuMultilevelQuestion.id == question_id))
    if question is None:
        return None
    task_id = question.task_id
    task = _load_task(db, task_id)
    if not _is_content_task(task):
        return None
    db.delete(question)
    db.commit()
    return get_task(db, task_id)
