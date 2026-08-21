from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class QuizQuestionBase(BaseSchema):
    quiz_id: UUID
    question: str
    question_type: str = "MULTIPLE_CHOICE"
    correct_text_answer: str | None = None
    explanation: str | None = None
    points: int = 1
    order_index: int = 1
    is_published: bool = False


class QuizQuestionCreate(QuizQuestionBase):
    pass


class QuizQuestionUpdate(BaseSchema):
    question: str | None = None
    question_type: str | None = None
    correct_text_answer: str | None = None
    explanation: str | None = None
    points: int | None = None
    order_index: int | None = None
    is_published: bool | None = None


class QuizQuestionResponse(QuizQuestionBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


class QuizQuestionPublicResponse(BaseSchema):
    """Student/anonymous-facing shape — omits correct_text_answer
    entirely (used by CLOZE_TEXT/SENTENCE_COMPLETION), same rationale
    as QuizOptionPublicResponse.

    match_value_pool is the MATCHING-question analogue: since each
    option's own match_value is hidden (it directly pairs with
    option_text — the answer key itself), a MATCHING question would
    otherwise have no way to render its right-hand column of choices
    at all. This is a fresh, server-shuffled list of just the values
    (no option_id attached), rebuilt on every fetch — populated only
    for question_type == MATCHING, null otherwise."""

    id: UUID
    quiz_id: UUID
    question: str
    question_type: str
    explanation: str | None = None
    points: int
    order_index: int
    is_published: bool
    match_value_pool: list[str] | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
