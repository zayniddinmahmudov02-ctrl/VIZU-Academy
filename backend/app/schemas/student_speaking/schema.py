from pydantic import ConfigDict

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