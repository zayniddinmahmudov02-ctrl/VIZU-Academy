from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema


class StudentSpeakingBase(BaseSchema):
    user_id: str
    speaking_id: str
    audio_url: str
    transcript: str | None = None

    grammar_score: int = 0
    vocabulary_score: int = 0
    pronunciation_score: int = 0
    fluency_score: int = 0
    task_score: int = 0
    overall_score: int = 0

    ai_feedback: str | None = None

    status: str = "pending"


class StudentSpeakingCreate(StudentSpeakingBase):
    pass


class StudentSpeakingUpdate(BaseSchema):
    transcript: str | None = None

    grammar_score: int | None = None
    vocabulary_score: int | None = None
    pronunciation_score: int | None = None
    fluency_score: int | None = None
    task_score: int | None = None
    overall_score: int | None = None

    ai_feedback: str | None = None

    status: str | None = None


class StudentSpeakingResponse(StudentSpeakingBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


# ==========================
# Real submission workflow (see app/models/student_speaking.py)
# ==========================


class StudentSpeakingOwnResponse(BaseSchema):
    id: UUID
    speaking_id: UUID
    filename: str | None
    content_type: str | None
    duration_seconds: int | None
    status: str
    submitted_at: datetime | None
    score: int | None
    feedback: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SpeakingGradeRequest(BaseSchema):
    score: int = Field(ge=0, le=100)
    feedback: str = Field(min_length=1, max_length=5000)
    status: str = Field(pattern="^(GRADED|NEEDS_REVISION)$")


class TeacherSpeakingItem(BaseSchema):
    """Denormalized row for Teacher Panel -> Sprechen (legacy) — see
    app/services/student_speaking/service.py."""

    id: UUID
    student_id: UUID
    student_name: str
    student_email: str
    course_title: str
    course_level: str
    lesson_title: str
    lesson_number: int
    speaking_title: str
    duration_seconds: int | None
    status: str
    submitted_at: datetime | None
    score: int | None
    feedback: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)