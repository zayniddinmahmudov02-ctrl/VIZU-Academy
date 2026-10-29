from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

REWARD_NONE = "NONE"
REWARD_ORDER_DISCOUNT = "ORDER_DISCOUNT"  # fixed UZS off one order of the listed offers
REWARD_TYPES = (REWARD_NONE, REWARD_ORDER_DISCOUNT)

# UserAchievement.reward_status
REWARD_STATUS_NONE = "NONE"  # the medal carries no reward
REWARD_STATUS_AVAILABLE = "AVAILABLE"
REWARD_STATUS_RESERVED = "RESERVED"  # attached to a pending order
REWARD_STATUS_USED = "USED"  # the order was approved


class AchievementCategory(BaseModel):
    """Medal group shown in the dashboard / admin ("Daraja medallari")."""

    __tablename__ = "achievement_categories"

    key: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    name_de: Mapped[str] = mapped_column(String(120), nullable=False)
    name_uz: Mapped[str] = mapped_column(String(120), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Achievement(BaseModel):
    """A medal. Everything is data (admin-configurable): texts in both
    languages, the icon (a preset of the frontend medal renderer or an
    uploaded image), the condition (a server-checked type from
    app.services.achievements.conditions + params) and the reward."""

    __tablename__ = "achievements"

    key: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    category_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("achievement_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name_de: Mapped[str] = mapped_column(String(120), nullable=False)
    name_uz: Mapped[str] = mapped_column(String(120), nullable=False)
    description_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_preset: Mapped[str] = mapped_column(String(40), nullable=False, default="rocket", server_default="rocket")
    icon_color: Mapped[str] = mapped_column(String(20), nullable=False, default="green", server_default="green")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    condition_type: Mapped[str] = mapped_column(String(40), nullable=False)
    condition_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    reward_type: Mapped[str] = mapped_column(String(30), nullable=False, default=REWARD_NONE, server_default=REWARD_NONE)
    reward_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # offer codes the reward applies to (["A1"]); never applied to anything else
    reward_offers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    # may the reward be combined with a promo code in the same order (the sale price always applies)
    reward_combine_with_promo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    category = relationship("AchievementCategory", lazy="joined")


class UserAchievement(BaseModel):
    """One awarded medal — at most once per student and medal (unique key),
    with the reward snapshot of the moment it was awarded and its use."""

    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(30), nullable=False, default=REWARD_NONE, server_default=REWARD_NONE)
    reward_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    reward_offers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    reward_status: Mapped[str] = mapped_column(String(20), nullable=False, default=REWARD_STATUS_NONE, server_default=REWARD_STATUS_NONE)
    reward_order_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    reward_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    achievement = relationship("Achievement", lazy="joined")
