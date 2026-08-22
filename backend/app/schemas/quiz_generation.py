from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class QuizGenerationTopicQuestionType(BaseSchema):
    template_type: str
    label: str
    difficulty: str


class QuizGenerationTopic(BaseSchema):
    topic: str
    label: str
    question_types: list[QuizGenerationTopicQuestionType]


class QuizGenerationTopicsResponse(BaseSchema):
    level: str
    topics: list[QuizGenerationTopic]


class QuizGenerationRequest(BaseSchema):
    lesson_id: UUID
    quiz_id: UUID
    topic: str
    count: int = Field(gt=0, le=500)
    question_types: list[str] | None = None
    seed: int | None = None


class QuizGenerationResponse(BaseSchema):
    quiz_id: UUID
    created_count: int
    requested_count: int
    shortfall: bool
    message: str | None = None
