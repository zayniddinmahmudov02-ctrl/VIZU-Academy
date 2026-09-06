from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class TeacherStudent(BaseSchema):
    """One of the current teacher's students — every student enrolled in a
    course the teacher has a TeacherAssignment row for (see
    app/services/teacher/service.py). `progress` mirrors the same 0-100
    per-course completion the Student Dashboard already computes
    (StudentProgress-derived), not a new metric."""

    id: UUID
    name: str
    email: str
    course_title: str
    course_level: str
    progress: int

    model_config = ConfigDict(from_attributes=True)


class TeacherOverview(BaseSchema):
    assigned_course_count: int
    student_count: int
