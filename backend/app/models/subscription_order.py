from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SubscriptionOrder(BaseModel):
    __tablename__ = "subscription_orders"
    __table_args__ = (
        Index("ix_subscription_orders_created_at", "created_at"),
        Index("ix_subscription_orders_access_window", "user_id", "access_start_date", "access_end_date"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    base_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    discount_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    final_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # part of discount_amount that came from a medal reward (user_achievements.reward_order_id points here)
    reward_discount_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="UZS",
        server_default="UZS",
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
        index=True,
    )

    proof_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    proof_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    promo_code_id: Mapped[str | None] = mapped_column(
        ForeignKey("promo_codes.id", ondelete="SET NULL"),
        nullable=True,
    )

    promo_code_snapshot: Mapped[str | None] = mapped_column(String(40), nullable=True)

    promo_discount_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    gateway: Mapped[str] = mapped_column(
        String(20),
        default="manual",
        server_default="manual",
        nullable=False,
    )

    gateway_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reviewed_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    purchase_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    access_start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    access_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    user = relationship("User", foreign_keys=[user_id])

    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    promo_code = relationship("PromoCode")
