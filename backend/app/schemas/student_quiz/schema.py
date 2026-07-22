from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class StudentQuizBase(BaseSchema):
    user_id: str
    quiz_id: str

    correct_answers: int = 0
    wrong_answers: int = 0
    skipped_answers: int = 0

    score: int = 0

    passed: bool = False


class StudentQuizCreate(StudentQuizBase):
    pass


class StudentQuizUpdate(BaseSchema):
    correct_answers: int | None = None
    wrong_answers: int | None = None
    skipped_answers: int | None = None
    score: int | None = None
    passed: bool | None = None


class StudentQuizResponse(StudentQuizBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )