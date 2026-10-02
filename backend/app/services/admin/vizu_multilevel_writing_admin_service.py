"""Admin CRUD for VIZU-Multilevel's Schreiben Aufgabe (topic + rubric) — unlike
Lesen/Hören (read-only content preview, content seeded once and never
admin-edited by explicit earlier-phase instruction), this module was
explicitly asked for a real admin editor: title/level/instruction/word
limits/image/points/order/status, plus the per-Aufgabe scoring rubric."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_writing import VizuMultilevelWritingRubricCriterion, VizuMultilevelWritingTask
from app.schemas.vizu_multilevel import (
    VizuMultilevelWritingRubricCriterionInput,
    VizuMultilevelWritingTaskAdminCreate,
    VizuMultilevelWritingTaskAdminUpdate,
)


def _load(db: Session, task_id: UUID) -> VizuMultilevelWritingTask | None:
    return db.scalar(
        select(VizuMultilevelWritingTask)
        .where(VizuMultilevelWritingTask.id == task_id)
        .options(joinedload(VizuMultilevelWritingTask.rubric_criteria))
    )


def list_tasks(db: Session) -> list[VizuMultilevelWritingTask]:
    return list(
        db.scalars(
            select(VizuMultilevelWritingTask)
            .options(joinedload(VizuMultilevelWritingTask.rubric_criteria))
            .order_by(VizuMultilevelWritingTask.order_index)
        ).unique()
    )


def get_task(db: Session, task_id: UUID) -> VizuMultilevelWritingTask | None:
    return _load(db, task_id)


def _apply_rubric(
    db: Session, task: VizuMultilevelWritingTask, criteria: list[VizuMultilevelWritingRubricCriterionInput]
) -> None:
    """Reconciles the task's rubric to exactly the given list: existing
    rows with a matching `id` are updated in place, rows not present in
    the new list are deleted, entries with `id=None` are created."""
    existing_by_id = {c.id: c for c in task.rubric_criteria}
    new_ids = {entry.id for entry in criteria if entry.id is not None}

    # Delete anything that existed before and isn't referenced by id in
    # the new list.
    for criterion in list(task.rubric_criteria):
        if criterion.id not in new_ids:
            db.delete(criterion)

    for entry in criteria:
        if entry.id is not None and entry.id in existing_by_id:
            criterion = existing_by_id[entry.id]
        else:
            criterion = VizuMultilevelWritingRubricCriterion(task_id=task.id)
            db.add(criterion)
        criterion.name = entry.name
        criterion.max_score = entry.max_score
        criterion.order_index = entry.order_index


def create_task(db: Session, data: VizuMultilevelWritingTaskAdminCreate) -> VizuMultilevelWritingTask:
    task = VizuMultilevelWritingTask(
        level=data.level,
        order_index=data.order_index,
        title=data.title,
        instruction=data.instruction,
        min_words=data.min_words,
        max_words=data.max_words,
        image_url=data.image_url,
        points=data.points,
        is_active=data.is_active,
    )
    db.add(task)
    db.flush()

    for entry in data.rubric_criteria:
        db.add(
            VizuMultilevelWritingRubricCriterion(
                task_id=task.id, name=entry.name, max_score=entry.max_score, order_index=entry.order_index
            )
        )

    db.commit()
    return _load(db, task.id)


def update_task(db: Session, task_id: UUID, data: VizuMultilevelWritingTaskAdminUpdate) -> VizuMultilevelWritingTask | None:
    task = _load(db, task_id)
    if task is None:
        return None

    updates = data.model_dump(exclude_unset=True, exclude={"rubric_criteria"})
    for field, value in updates.items():
        setattr(task, field, value)

    if data.rubric_criteria is not None:
        _apply_rubric(db, task, data.rubric_criteria)

    db.commit()
    return _load(db, task_id)


def delete_task(db: Session, task_id: UUID) -> bool:
    task = db.scalar(select(VizuMultilevelWritingTask).where(VizuMultilevelWritingTask.id == task_id))
    if task is None:
        return False
    db.delete(task)
    db.commit()
    return True
