"""One committed Claude/JSON content import (LMS A1-C1).

The flow is JSON -> validation -> preview -> admin commit (creates the content
UNPUBLISHED) -> admin publish. Validation/preview are stateless; a row here is
written only on commit and keeps, per item, what was created or why it was
rejected, so the admin can publish exactly that batch later."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ContentImport(BaseModel):
    __tablename__ = "content_imports"

    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    levels: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["A1", ...] touched by the batch
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # [{index, content_id, skill, title, status: created|error, errors: [...], target: {...}, created: {kind, id}}]
    items: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
