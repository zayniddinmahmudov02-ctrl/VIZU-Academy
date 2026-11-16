from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

PRODUCT_MULTILEVEL_PREMIUM = "MULTILEVEL_MODELLTEST_PREMIUM"
SOURCE_PAYMENT = "PAYMENT"  # an APPROVED order (the Super Admin checked the receipt)
SOURCE_PROMO = "PROMO"  # a 100 % promo code that an admin had approved


class UserEntitlement(BaseModel):
    """A product access of one student that is not a course level (services/vizu_pay/multilevel_premium.py). At most one active row
    (revoked_at IS NULL) per user and product, so a payment and a promo code can never grant the same access twice. Unlimited when
    expires_at is NULL. A refund revokes it (revoked_at / revoked_by_id / revoke_reason) — the row stays as history."""

    __tablename__ = "user_entitlements"
    __table_args__ = (
        CheckConstraint("source IN ('PAYMENT','PROMO')", name="ck_user_entitlements_source"),
        Index("uq_user_entitlements_active", "user_id", "product", unique=True, postgresql_where=text("revoked_at IS NULL")),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    promo_code_id: Mapped[str | None] = mapped_column(ForeignKey("promo_codes.id", ondelete="SET NULL"), nullable=True)
    granted_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    order = relationship("SubscriptionOrder", foreign_keys=[order_id])
    promo_code = relationship("PromoCode", foreign_keys=[promo_code_id])
