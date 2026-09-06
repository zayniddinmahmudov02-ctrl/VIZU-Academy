from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class TeacherAssignment(BaseModel):
    """Scopes a TEACHER-role user to one course. The Teacher Panel's "Meine
    Schüler" list (GET /teacher/students) is every student with an active
    Enrollment in any course a teacher has a row here for — a teacher with
    zero rows sees an empty list, never every student in the system.

    Managed exclusively by a SUPER_ADMIN (see
    app/api/admin/teacher_assignments_router.py) — there is no self-service
    way for a teacher to assign themselves to a course."""

    __tablename__ = "teacher_assignments"
    __table_args__ = (UniqueConstraint("teacher_id", "course_id", name="uq_teacher_assignment_teacher_course"),)

    teacher_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    teacher = relationship("User")
    course = relationship("Course")
