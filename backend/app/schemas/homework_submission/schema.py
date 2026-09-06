from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema


class HomeworkSubmissionCreate(BaseSchema):
    text_content: str = Field(min_length=1, max_length=20000)


class HomeworkSubmissionResponse(BaseSchema):
    """The student's own view of their submission — GET
    /homeworks/{id}/submissions/me."""

    id: UUID
    homework_id: UUID
    text_content: str
    status: str
    submitted_at: datetime
    score: int | None
    feedback: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class HomeworkGradeRequest(BaseSchema):
    score: int = Field(ge=0, le=100)
    feedback: str = Field(min_length=1, max_length=5000)
    status: str = Field(pattern="^(GRADED|NEEDS_REVISION)$")


class TeacherHomeworkSubmission(BaseSchema):
    """Denormalized row for the Teacher Panel's Hausaufgaben list/detail —
    everything a teacher needs without a second round-trip. Set by
    HomeworkSubmissionService, not stored columns."""

    id: UUID
    student_id: UUID
    student_name: str
    student_email: str
    course_title: str
    course_level: str
    lesson_title: str
    lesson_number: int
    homework_title: str
    text_content: str
    status: str
    submitted_at: datetime
    score: int | None
    feedback: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
