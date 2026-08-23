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
    # topic drives the deterministic template generator and is required
    # only when prompt is empty; prompt drives the Gemini AI generator
    # instead and makes topic irrelevant (see quiz_generation_router.
    # generate, which validates the actual either/or requirement — a
    # request with neither, or the AI path used for a non-GRAMMAR quiz,
    # is rejected there, not by this schema).
    topic: str | None = None
    prompt: str | None = None
    count: int = Field(gt=0, le=500)
    question_types: list[str] | None = None
    seed: int | None = None


class QuizGenerationResponse(BaseSchema):
    quiz_id: UUID
    created_count: int
    requested_count: int
    shortfall: bool
    message: str | None = None
