from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class TeacherAssignmentCreate(BaseSchema):
    teacher_id: UUID
    course_id: UUID


class TeacherAssignmentResponse(BaseSchema):
    id: UUID
    teacher_id: UUID
    course_id: UUID
    # Denormalized display fields — set by the service, not stored columns —
    # so the admin "Teacher Assignments" page never has to make N+1 calls
    # just to show who's assigned to what.
    teacher_name: str
    teacher_email: str
    course_title: str
    course_level: str

    model_config = ConfigDict(from_attributes=True)


class TeacherCandidate(BaseSchema):
    """One TEACHER-role user, for the admin assignment form's picker."""

    id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)
