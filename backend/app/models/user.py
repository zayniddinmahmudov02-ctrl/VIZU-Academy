from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        default="STUDENT",
        server_default="STUDENT",
        nullable=False,
        index=True,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    ban_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    banned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    suspended_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    suspend_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    premium_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    trial_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    profile_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="de",
        server_default="de",
        nullable=False,
    )