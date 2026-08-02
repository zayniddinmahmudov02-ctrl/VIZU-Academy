from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LanguageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
    flag: str | None = None
    is_active: bool


class LanguageCreate(BaseModel):
    code: str
    name: str
    flag: str | None = None
    is_active: bool = True


class LanguageUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    flag: str | None = None
    is_active: bool | None = None
