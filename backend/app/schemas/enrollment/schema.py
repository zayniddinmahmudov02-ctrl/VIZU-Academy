from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class EnrollmentBase(BaseSchema):

    user_id: str

    course_id: str

    is_active: bool = True

    completed: bool = False


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseSchema):

    is_active: bool | None = None

    completed: bool | None = None


class EnrollmentResponse(EnrollmentBase):

    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )