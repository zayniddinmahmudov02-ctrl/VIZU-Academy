from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import (
    get_current_user,
    require_super_admin,
)

from app.core.security.roles import UserRole

from app.db.session import get_db

from app.models.user import User

from app.schemas.student_progress import (
    StudentProgressCreate,
    StudentProgressUpdate,
    StudentProgressResponse,
)

from app.services.student_progress import (
    StudentProgressService,
)

router = APIRouter(
    prefix="/student-progress",
    tags=["Student Progress"],
)


@router.get(
    "",
    response_model=list[StudentProgressResponse],
)
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return StudentProgressService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=StudentProgressResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = StudentProgressService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Progress not found",
        )

    if (
        item.user_id != str(current_user.id)
        and current_user.role not in UserRole.ADMIN_PANEL_ROLES
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this progress record",
        )

    return item


@router.post(
    "",
    response_model=StudentProgressResponse,
)
def create(
    data: StudentProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return StudentProgressService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=StudentProgressResponse,
)
def update(
    item_id: str,
    data: StudentProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    item = StudentProgressService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Progress not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    deleted = StudentProgressService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Progress not found",
        )

    return {
        "message": "Deleted"
    }
