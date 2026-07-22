from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LoginHistory(BaseModel):
    __tablename__ = "login_history"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    device: Mapped[str] = mapped_column(
        String(50),
        default="Unknown",
    )

    os: Mapped[str] = mapped_column(
        String(50),
        default="Unknown",
    )

    browser: Mapped[str] = mapped_column(
        String(50),
        default="Unknown",
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    user = relationship("User")
