"""Admin CRUD for VIZU-Multilevel Sprechen Aufgaben (content starts empty)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingTask
from app.schemas.vizu_multilevel import VizuMultilevelSpeakingTaskAdminCreate, VizuMultilevelSpeakingTaskAdminUpdate
from app.services.admin.vizu_multilevel_content_admin_service import ContentConflictError


def list_tasks(db: Session) -> list[VizuMultilevelSpeakingTask]:
    return list(db.scalars(select(VizuMultilevelSpeakingTask).order_by(VizuMultilevelSpeakingTask.order_index)))


def _order_taken(db: Session, order_index: int, exclude: UUID | None = None) -> bool:
    query = select(VizuMultilevelSpeakingTask.id).where(VizuMultilevelSpeakingTask.order_index == order_index)
    if exclude is not None:
        query = query.where(VizuMultilevelSpeakingTask.id != exclude)
    return db.scalar(query) is not None


def create_task(db: Session, data: VizuMultilevelSpeakingTaskAdminCreate) -> VizuMultilevelSpeakingTask:
    if _order_taken(db, data.order_index):
        raise ContentConflictError("A Sprechen Aufgabe with this order already exists.")
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
    if "order_index" in updates and _order_taken(db, updates["order_index"], exclude=task.id):
        raise ContentConflictError("A Sprechen Aufgabe with this order already exists.")
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: UUID) -> bool:
    task = db.scalar(select(VizuMultilevelSpeakingTask).where(VizuMultilevelSpeakingTask.id == task_id))
    if task is None:
        return False
    db.delete(task)
    db.commit()
    return True
