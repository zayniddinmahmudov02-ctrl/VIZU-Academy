"""Admin CRUD for the VIZU-Multilevel Sprechen bank: Aufgabe 1-5
(order_index) x internal CEFR level; (order_index, level) is unique.
Deleting an Aufgabe that students already answered is refused — deactivate
it instead (answers and their audio are never deleted)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingSubmission, VizuMultilevelSpeakingTask
from app.schemas.vizu_multilevel import VizuMultilevelSpeakingTaskAdminCreate, VizuMultilevelSpeakingTaskAdminUpdate
from app.services.admin.vizu_multilevel_content_admin_service import ContentConflictError


LEVEL_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5}


def list_tasks(db: Session) -> list[VizuMultilevelSpeakingTask]:
    tasks = list(db.scalars(select(VizuMultilevelSpeakingTask)))
    return sorted(tasks, key=lambda t: (t.order_index, LEVEL_ORDER.get(t.level, 9)))


def _order_taken(db: Session, order_index: int, level: str, exclude: UUID | None = None) -> bool:
    query = select(VizuMultilevelSpeakingTask.id).where(
        VizuMultilevelSpeakingTask.order_index == order_index, VizuMultilevelSpeakingTask.level == level
    )
    if exclude is not None:
        query = query.where(VizuMultilevelSpeakingTask.id != exclude)
    return db.scalar(query) is not None


def create_task(db: Session, data: VizuMultilevelSpeakingTaskAdminCreate) -> VizuMultilevelSpeakingTask:
    if _order_taken(db, data.order_index, data.level):
        raise ContentConflictError("Für diese Aufgabe gibt es auf diesem Niveau bereits eine Variante.")
    task = VizuMultilevelSpeakingTask(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session, task_id: UUID, data: VizuMultilevelSpeakingTaskAdminUpdate
) -> VizuMultilevelSpeakingTask | None:
    task = db.scalar(select(VizuMultilevelSpeakingTask).where(VizuMultilevelSpeakingTask.id == task_id))
    if task is None:
        return None
    updates = data.model_dump(exclude_unset=True)
    order_index = updates.get("order_index", task.order_index)
    level = updates.get("level", task.level)
    if ("order_index" in updates or "level" in updates) and _order_taken(db, order_index, level, exclude=task.id):
        raise ContentConflictError("Für diese Aufgabe gibt es auf diesem Niveau bereits eine Variante.")
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: UUID) -> bool:
    task = db.scalar(select(VizuMultilevelSpeakingTask).where(VizuMultilevelSpeakingTask.id == task_id))
    if task is None:
        return False
    answered = db.scalar(
        select(VizuMultilevelSpeakingSubmission.id).where(VizuMultilevelSpeakingSubmission.task_id == task_id).limit(1)
    )
    if answered is not None:
        raise ContentConflictError("Diese Aufgabe wurde bereits beantwortet — bitte deaktivieren statt löschen.")
    db.delete(task)
    db.commit()
    return True
