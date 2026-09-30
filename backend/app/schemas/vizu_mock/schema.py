from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class VizuMockAttemptResponse(BaseSchema):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    lesen_level: str | None
    hoeren_level: str | None
    schreiben_level: str | None
    sprechen_level: str | None
    overall_level: str | None
    model_config = ConfigDict(from_attributes=True)
