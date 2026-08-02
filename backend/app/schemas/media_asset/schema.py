from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    filename: str
    url: str
    folder: str
    media_type: str
    content_type: str | None = None
    size_bytes: int | None = None
    uploaded_by: UUID | None = None
