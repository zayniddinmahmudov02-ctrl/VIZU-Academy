from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class TeacherStudent(BaseSchema):
    """One of the current teacher's students — every student enrolled in a
    course the teacher has a TeacherAssignment row for (see
    app/services/teacher/service.py). `progress` mirrors the same 0-100
    per-course completion the Student Dashboard already computes
    (StudentProgress-derived), not a new metric. `last_activity` is the
    most recent StudentProgress.updated_at across that course's lessons —
    null if the student has never touched a lesson yet (never fabricated
    as "just now")."""

    id: UUID
    name: str
    email: str
    course_title: str
    course_level: str
    progress: int
    last_activity: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TeacherOverview(BaseSchema):
    assigned_course_count: int
    student_count: int
    new_homework_count: int
    to_grade_count: int
    graded_count: int
    average_progress: int
