from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ModuleBase(BaseSchema):
    course_id: UUID
    number: int
    title: str
    description: str | None = None
    order_index: int = 1
    is_active: bool = True


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseSchema):
    number: int | None = None
    title: str | None = None
    description: str | None = None
    order_index: int | None = None
    is_active: bool | None = None


class ModuleResponse(ModuleBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)