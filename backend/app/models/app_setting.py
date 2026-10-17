from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AppSetting(BaseModel):
    """Admin-editable platform configuration, one JSON document per key.

    Used for "angebote" (course prices, sale on/off, package contents, free
    lessons per course, level availability — see
    app/services/vizu_pay/offers.py). The code holds the defaults; a row only
    stores what the admin changed."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
