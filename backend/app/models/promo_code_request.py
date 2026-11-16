from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

REQUEST_PENDING = "PENDING_APPROVAL"
REQUEST_APPROVED = "APPROVED"
REQUEST_REJECTED = "REJECTED"
REQUEST_USED = "USED"  # the approved discount was spent on an order

KIND_CODE_APPROVAL = "CODE_APPROVAL"  # the student entered a code that `requires_approval` for one package
KIND_COURSE_REQUEST = "COURSE_REQUEST"  # the student asks for a promo for a course / package; an admin attaches a code on approval


class PromoCodeRequest(BaseModel):
    """Two kinds of student requests, reviewed by a Super Admin (Admin -> Payments -> Promo Requests):
    * CODE_APPROVAL: a student's request to use a promo code that `requires_approval` for one package. The discount applies only
      after an admin approved it (VizuPayService.request_promo / AdminVizuPayService.review_promo_request).
    * COURSE_REQUEST: "Promo so'rovi" — the student picks a course or package and writes why. Approving creates a personal code for
      that student (or attaches an existing approved one); it never buys or opens anything by itself (review_course_request)."""

    __tablename__ = "promo_code_requests"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING_APPROVAL','APPROVED','REJECTED','USED')", name="ck_promo_code_requests_status"),
        CheckConstraint("kind IN ('CODE_APPROVAL','COURSE_REQUEST')", name="ck_promo_code_requests_kind"),
        CheckConstraint("kind = 'COURSE_REQUEST' OR promo_code_id IS NOT NULL", name="ck_promo_code_requests_code_needed"),
        Index("uq_promo_code_requests_open", "promo_code_id", "user_id", "plan", unique=True,
              postgresql_where=text("status IN ('PENDING_APPROVAL','APPROVED')")),
        Index("uq_promo_code_requests_course_open", "user_id", "plan", unique=True,
              postgresql_where=text("kind = 'COURSE_REQUEST' AND status = 'PENDING_APPROVAL'")),
    )

    promo_code_id: Mapped[str | None] = mapped_column(ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=REQUEST_PENDING, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default=KIND_CODE_APPROVAL, server_default=KIND_CODE_APPROVAL)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True)

    promo_code = relationship("PromoCode")
    user = relationship("User", foreign_keys=[user_id])
