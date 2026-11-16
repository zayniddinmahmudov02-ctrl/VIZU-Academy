from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# What a code can be used for (Admin -> Payments -> Promo Codes). A course code never works for the Multilevel Premium and vice versa.
CATEGORY_COURSES = "COURSES"  # single course levels (A1, A2, ...)
CATEGORY_PACKAGES = "PACKAGES"  # course packages (A1 -> B1, ...)
CATEGORY_MULTILEVEL = "MULTILEVEL"  # Multilevel Modelltest Premium (all 10 Modelltests)
CATEGORIES = (CATEGORY_COURSES, CATEGORY_PACKAGES, CATEGORY_MULTILEVEL)

# A code works only when ACTIVE and approved by a Super Admin (approved_at set). Creating it never activates it. EXPIRED is not stored: it is
# shown when expires_at has passed.
APPROVAL_PENDING = "PENDING"
APPROVAL_APPROVED = "APPROVED"
APPROVAL_ACTIVE = "ACTIVE"
APPROVAL_REJECTED = "REJECTED"
APPROVAL_DISABLED = "DISABLED"
APPROVAL_STATUSES = (APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_ACTIVE, APPROVAL_REJECTED, APPROVAL_DISABLED)


class PromoCode(BaseModel):
    __tablename__ = "promo_codes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_promo_codes_code"),
        CheckConstraint("product_category IN ('COURSES','PACKAGES','MULTILEVEL')", name="ck_promo_codes_product_category"),
        CheckConstraint("approval_status IN ('PENDING','APPROVED','ACTIVE','REJECTED','DISABLED')", name="ck_promo_codes_approval_status"),
    )

    code: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
        index=True,
    )

    campaign: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    discount_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    discount_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    max_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    used_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    max_uses_per_user: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
    )

    applicable_course_ids: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)

    applicable_package_codes: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)

    # an admin must approve each student's use (promo_code_requests) before the discount applies
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    created_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    product_category: Mapped[str] = mapped_column(String(20), default=CATEGORY_COURSES, server_default=CATEGORY_COURSES, nullable=False)
    # kept in step with is_active (is_active == (approval_status == ACTIVE)); see AdminVizuPayService.review_promo
    approval_status: Mapped[str] = mapped_column(String(20), default=APPROVAL_PENDING, server_default=APPROVAL_PENDING, nullable=False)
    approved_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL", name="fk_promo_codes_approved_by_id"),
                                                       nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # a personal code (made for one student's course promo request): nobody else can use it
    assigned_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", name="fk_promo_codes_assigned_user_id"),
                                                         nullable=True, index=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
