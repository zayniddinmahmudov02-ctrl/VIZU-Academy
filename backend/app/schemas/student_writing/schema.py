from pydantic import ConfigDict

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