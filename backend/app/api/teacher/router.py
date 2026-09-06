from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_teacher_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.teacher import TeacherOverview, TeacherStudent
from app.services.teacher import TeacherService

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher Panel"],
)


@router.get("/overview", response_model=TeacherOverview)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return TeacherService(db).overview(current_user.id)


@router.get("/students", response_model=list[TeacherStudent])
def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_panel_access),
):
    return TeacherService(db).list_students(current_user.id)
