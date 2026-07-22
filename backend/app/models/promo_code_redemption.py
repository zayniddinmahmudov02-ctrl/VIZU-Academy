from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PromoCodeRedemption(BaseModel):
    __tablename__ = "promo_code_redemptions"
    __table_args__ = (
        UniqueConstraint("promo_code_id", "user_id", name="uq_promo_redemption_user"),
    )

    promo_code_id: Mapped[str] = mapped_column(
        ForeignKey("promo_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_id: Mapped[str] = mapped_column(
        ForeignKey("subscription_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    promo_code = relationship("PromoCode")

    user = relationship("User")
