from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CourseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    language_id: UUID
    level: str
    title: str
    description: str | None = None
    order_index: int
    is_active: bool


class CourseCreate(BaseModel):
    language_id: UUID
    level: str
    title: str
    description: str | None = None
    order_index: int = 1
    is_active: bool = True


class CourseUpdate(BaseModel):
    language_id: UUID | None = None
    level: str | None = None
    title: str | None = None
    description: str | None = None
    order_index: int | None = None
    is_active: bool | None = None
