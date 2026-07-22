from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ExamProviderBase(BaseSchema):
    name: str
    code: str


class ExamProviderCreate(ExamProviderBase):
    pass


class ExamProviderResponse(ExamProviderBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ExamBase(BaseSchema):
    provider_id: str
    level: str
    title: str
    duration: int = 180
    is_active: bool = True


class ExamCreate(ExamBase):
    pass


class ExamUpdate(BaseSchema):
    title: str | None = None
    duration: int | None = None
    is_active: bool | None = None


class ExamResponse(ExamBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ExamPartBase(BaseSchema):
    exam_id: str
    name: str
    duration: int = 0
    max_score: int = 100


class ExamPartCreate(ExamPartBase):
    pass


class ExamPartUpdate(BaseSchema):
    duration: int | None = None
    max_score: int | None = None


class ExamPartResponse(ExamPartBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ExamSessionBase(BaseSchema):
    user_id: str
    exam_id: str
    status: str = "started"
    score: int = 0


class ExamSessionCreate(ExamSessionBase):
    pass


class ExamSessionUpdate(BaseSchema):
    status: str | None = None
    score: int | None = None


class ExamSessionResponse(ExamSessionBase):
    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )