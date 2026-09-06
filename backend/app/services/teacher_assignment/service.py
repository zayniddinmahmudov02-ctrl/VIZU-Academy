from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.course import Course
from app.models.user import User
from app.repositories.teacher_assignment import TeacherAssignmentRepository
from app.schemas.teacher_assignment import TeacherAssignmentResponse, TeacherCandidate


def _display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


class TeacherAssignmentService:
    """Admin-only management of which courses a TEACHER-role user may see
    students for (see app/models/teacher_assignment.py). Used exclusively
    by /admin/teacher-assignments — a TEACHER never calls this."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = TeacherAssignmentRepository(db)

    def _to_response(self, item) -> TeacherAssignmentResponse:
        return TeacherAssignmentResponse(
            id=item.id,
            teacher_id=item.teacher_id,
            course_id=item.course_id,
            teacher_name=_display_name(item.teacher),
            teacher_email=item.teacher.email,
            course_title=item.course.title,
            course_level=item.course.level,
        )

    def list_all(self) -> list[TeacherAssignmentResponse]:
        return [self._to_response(item) for item in self.repository.get_all()]

    def list_teacher_candidates(self) -> list[TeacherCandidate]:
        teachers = (
            self.db.query(User)
            .filter(User.role == UserRole.TEACHER)
            .order_by(User.email)
            .all()
        )
        return [TeacherCandidate(id=t.id, name=_display_name(t), email=t.email) for t in teachers]

    def create(self, teacher_id: UUID, course_id: UUID) -> TeacherAssignmentResponse:
        teacher = self.db.query(User).filter(User.id == teacher_id).first()
        if teacher is None or teacher.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="teacher_id must reference a user with role TEACHER",
            )

        course = self.db.query(Course).filter(Course.id == course_id).first()
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        existing = self.repository.get_by_pair(teacher_id, course_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This teacher is already assigned to this course",
            )

        item = self.repository.create(teacher_id, course_id)
        return self._to_response(item)

    def delete(self, assignment_id: UUID) -> bool:
        item = self.repository.get(assignment_id)
        if item is None:
            return False
        self.repository.delete(item)
        return True
