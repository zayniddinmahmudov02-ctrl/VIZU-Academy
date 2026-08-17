from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema


class NotificationCreate(BaseSchema):
    """Mirrors the frontend's NotificationInput exactly — always scoped
    to the requesting user, no user_id in the body."""

    title: str
    message: str
    type: str = "information"


class NotificationResponse(BaseSchema):
    """The frontend's notification contract is camelCase
    (createdAt/isRead) while the rest of this backend is snake_case —
    aliased here rather than bending the whole codebase's convention."""

    id: UUID
    title: str
    message: str
    type: str
    is_read: bool = Field(serialization_alias="isRead")
    audio_url: str | None = Field(default=None, serialization_alias="audioUrl")
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
