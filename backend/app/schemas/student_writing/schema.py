from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema


class StudentWritingBase(BaseSchema):
    user_id: str
    writing_id: str

    answer_text: str

    grammar_score: int = 0
    vocabulary_score: int = 0
    coherence_score: int = 0
    task_score: int = 0
    overall_score: int = 0

    ai_feedback: str | None = None

    status: str = "pending"


class StudentWritingCreate(StudentWritingBase):
    pass


class StudentWritingUpdate(BaseSchema):
    answer_text: str | None = None

    grammar_score: int | None = None
    vocabulary_score: int | None = None
    coherence_score: int | None = None
    task_score: int | None = None
    overall_score: int | None = None

    ai_feedback: str | None = None

    status: str | None = None


class StudentWritingResponse(StudentWritingBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


# ==========================
# Real submission workflow (see app/models/student_writing.py)
# ==========================


class WritingSubmitRequest(BaseSchema):
    answer_text: str = Field(min_length=1, max_length=50000)
    # False = "Entwurf speichern" (no min-word check, status -> DRAFT);
    # True = "Aufgabe abgeben" (min/max words enforced server-side against
    # the task's own config, status -> SUBMITTED).
    submit: bool = False


class StudentWritingOwnResponse(BaseSchema):
    id: UUID
    writing_id: UUID
    answer_text: str
    status: str
    submitted_at: datetime | None
    score: int | None
    feedback: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WritingGradeRequest(BaseSchema):
    score: int = Field(ge=0, le=100)
    feedback: str = Field(min_length=1, max_length=5000)
    status: str = Field(pattern="^(GRADED|NEEDS_REVISION)$")


class TeacherWritingItem(BaseSchema):
    """Denormalized row for Teacher Panel -> Schreiben (legacy) — see
    app/services/student_writing/service.py."""

    id: UUID
    student_id: UUID
    student_name: str
    student_email: str
    course_title: str
    course_level: str
    lesson_title: str
    lesson_number: int
    writing_title: str
    min_words: int
    max_words: int
    answer_text: str
    status: str
    submitted_at: datetime | None
    score: int | None
    feedback: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)