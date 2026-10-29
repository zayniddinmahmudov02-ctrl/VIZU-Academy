from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access

from app.core.security.roles import UserRole

from app.db.session import get_db

from app.models.user import User

from app.schemas.student_quiz import (
    StudentQuizCreate,
    StudentQuizUpdate,
    StudentQuizResponse,
)

from app.services.student_quiz import (
    StudentQuizService,
)

router = APIRouter(
    prefix="/student-quizzes",
    tags=["Student Quizzes"],
)


def _ensure_owner_or_admin(
    item_user_id: str,
    current_user: User,
):
    # the column holds a UUID; compare as text on both sides
    if (
        str(item_user_id) != str(current_user.id)
        and current_user.role not in UserRole.ADMIN_PANEL_ROLES
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this student quiz",
        )


@router.get(
    "",
    response_model=list[StudentQuizResponse],
)
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = StudentQuizService(db).get_all()

    if current_user.role in UserRole.ADMIN_PANEL_ROLES:
        return items

    return [
        item
        for item in items
        if str(item.user_id) == str(current_user.id)
    ]


@router.get(
    "/{item_id}",
    response_model=StudentQuizResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = StudentQuizService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    _ensure_owner_or_admin(item.user_id, current_user)

    return item


@router.post(
    "",
    response_model=StudentQuizResponse,
)
def create(
    data: StudentQuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Staff corrections only. Students get StudentQuiz rows exclusively from the
    # server-graded quiz submit (app.services.quiz.grading_service): the rows feed
    # section gating and the lesson score, so a student must not write a score.
    return StudentQuizService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentQuizResponse,
)
def update(
    item_id: str,
    data: StudentQuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    existing = StudentQuizService(db).get(item_id)

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    _ensure_owner_or_admin(existing.user_id, current_user)

    item = StudentQuizService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    existing = StudentQuizService(db).get(item_id)

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    _ensure_owner_or_admin(existing.user_id, current_user)

    deleted = StudentQuizService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student Quiz not found",
        )

    return {
        "message": "Deleted",
    }
