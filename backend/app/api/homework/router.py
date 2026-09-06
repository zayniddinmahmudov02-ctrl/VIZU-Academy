from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db

from app.models.user import User

from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkResponse,
)
from app.schemas.homework_submission import HomeworkSubmissionCreate, HomeworkSubmissionResponse

from app.services.homework import HomeworkService
from app.services.homework_submission import HomeworkSubmissionService

router = APIRouter(
    prefix="/homeworks",
    tags=["Homeworks"],
)


@router.get(
    "",
    response_model=list[HomeworkResponse],
)
def get_all(
    db: Session = Depends(get_db),
):
    return HomeworkService(db).get_all()


@router.get(
    "/lesson/{lesson_id}",
    response_model=list[HomeworkResponse],
)
def get_lesson_homework(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    __: object = Depends(require_lesson_access),
):
    """Student-facing, published-only — the Hausaufgabe section's real
    source of truth (see components/lesson-player/homework/
    homework-section.tsx). Same free-3-lessons/Premium gate every other
    lesson-content endpoint uses."""
    return HomeworkService(db).get_by_lesson(lesson_id, published_only=True)


@router.get(
    "/{item_id}",
    response_model=HomeworkResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
):
    item = HomeworkService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Homework not found",
        )

    return item


@router.post(
    "",
    response_model=HomeworkResponse,
)
def create(
    data: HomeworkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return HomeworkService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=HomeworkResponse,
)
def update(
    item_id: str,
    data: HomeworkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    item = HomeworkService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Homework not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = HomeworkService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Homework not found",
        )

    return {
        "message": "Deleted",
    }


# ==========================
# Student submission (new — see app/models/homework_submission.py)
# ==========================
# The Homework task/CRUD endpoints above are unchanged; this is the
# missing "student answers it" half. Own-submission only — there is no
# admin/teacher path through this router, that's /teacher/homework/*
# (app/api/teacher/router.py), scoped through TeacherAssignment.


@router.post(
    "/{homework_id}/submissions",
    response_model=HomeworkSubmissionResponse,
)
def submit_homework(
    homework_id: UUID,
    data: HomeworkSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HomeworkSubmissionService(db).submit(current_user.id, homework_id, data.text_content)


@router.get(
    "/{homework_id}/submissions/me",
    response_model=HomeworkSubmissionResponse | None,
)
def get_my_submission(
    homework_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HomeworkSubmissionService(db).get_own(current_user.id, homework_id)