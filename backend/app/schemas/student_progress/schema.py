from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class StudentProgressBase(BaseSchema):
    user_id: str
    lesson_id: str

    video_completed: bool = False
    grammar_completed: bool = False
    reading_completed: bool = False
    listening_completed: bool = False
    writing_completed: bool = False
    speaking_completed: bool = False
    quiz_completed: bool = False

    total_score: int = 0

    lesson_completed: bool = False


class StudentProgressCreate(StudentProgressBase):
    pass


class StudentProgressUpdate(BaseSchema):
    video_completed: bool | None = None
    grammar_completed: bool | None = None
    reading_completed: bool | None = None
    listening_completed: bool | None = None
    writing_completed: bool | None = None
    speaking_completed: bool | None = None
    quiz_completed: bool | None = None
    total_score: int | None = None
    lesson_completed: bool | None = None


class StudentProgressResponse(StudentProgressBase):
    id: str

    model_config = ConfigDict(from_attributes=True)