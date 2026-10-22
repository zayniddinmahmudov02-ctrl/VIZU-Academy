from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ManagedPage(BaseModel):
    __tablename__ = "managed_pages"

    route: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    navigation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    updated_by = relationship("User", foreign_keys=[updated_by_id])


class ManagedPageAudit(BaseModel):
    __tablename__ = "managed_page_audits"

    route: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    actor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    previous_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    new_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    actor = relationship("User", foreign_keys=[actor_id])
