from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

REQUEST_PENDING = "PENDING_APPROVAL"
REQUEST_APPROVED = "APPROVED"
REQUEST_REJECTED = "REJECTED"
REQUEST_USED = "USED"  # the approved discount was spent on an order


class PromoCodeRequest(BaseModel):
    """A student's request to use a promo code that `requires_approval` for one package. The discount applies only
    after an admin approved it (VizuPayService.request_promo / AdminVizuPayService.review_promo_request)."""

    __tablename__ = "promo_code_requests"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING_APPROVAL','APPROVED','REJECTED','USED')", name="ck_promo_code_requests_status"),
        Index("uq_promo_code_requests_open", "promo_code_id", "user_id", "plan", unique=True,
              postgresql_where=text("status IN ('PENDING_APPROVAL','APPROVED')")),
    )

    promo_code_id: Mapped[str] = mapped_column(ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=REQUEST_PENDING, index=True)
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True)

    promo_code = relationship("PromoCode")
    user = relationship("User", foreign_keys=[user_id])
