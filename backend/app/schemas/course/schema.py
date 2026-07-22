from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CourseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    name: str
    code: str
    language: str
    level: str
    modules_count: int
    is_active: bool


class CourseCreate(BaseModel):
    name: str
    code: str
    language: str
    level: str
    modules_count: int