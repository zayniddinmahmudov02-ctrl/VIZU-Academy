from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class QuizBase(BaseSchema):
    lesson_id: UUID
    quiz_type: str = "GRAMMAR"
    title: str
    description: str | None = None
    passing_score: int = 70
    order_index: int = 1
    is_published: bool = False


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseSchema):
    quiz_type: str | None = None
    title: str | None = None
    description: str | None = None
    passing_score: int | None = None
    order_index: int | None = None
    is_published: bool | None = None


class QuizResponse(QuizBase):
    id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# Server-side grading (see app/services/quiz/grading_service.py) —
# the correct answer never reaches the client until after this
# submission is graded and this response is returned.
# ============================================================


class QuizAnswerSubmit(BaseSchema):
    question_id: UUID
    option_id: UUID | None = None
    text_answer: str | None = None
    ordered_option_ids: list[UUID] | None = None
    matches: dict[str, str] | None = None


class QuizSubmitRequest(BaseSchema):
    answers: list[QuizAnswerSubmit] = []


class QuizAnswerResult(BaseSchema):
    question_id: UUID
    is_correct: bool
    correct_option_id: UUID | None = None
    correct_text_answer: str | None = None
    correct_order_option_ids: list[UUID] | None = None
    correct_matches: dict[str, str] | None = None


class QuizSubmitResponse(BaseSchema):
    score: int
    correct_answers: int
    wrong_answers: int
    skipped_answers: int
    passed: bool
    results: list[QuizAnswerResult]
