from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.teacher_assignment import TeacherAssignmentCreate, TeacherAssignmentResponse, TeacherCandidate
from app.services.teacher_assignment import TeacherAssignmentService

router = APIRouter(
    prefix="/admin/teacher-assignments",
    tags=["Admin - Teacher Assignments"],
)


@router.get("", response_model=list[TeacherAssignmentResponse])
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return TeacherAssignmentService(db).list_all()


@router.get("/candidates", response_model=list[TeacherCandidate])
def list_teacher_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Every TEACHER-role user, for the assignment form's picker — a
    teacher first gets that role via the existing Admin Users page
    (Rolle ändern -> TEACHER), then gets assigned a course here."""
    return TeacherAssignmentService(db).list_teacher_candidates()


@router.post("", response_model=TeacherAssignmentResponse)
def create_assignment(
    data: TeacherAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return TeacherAssignmentService(db).create(data.teacher_id, data.course_id)


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    deleted = TeacherAssignmentService(db).delete(assignment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return {"message": "Deleted"}
