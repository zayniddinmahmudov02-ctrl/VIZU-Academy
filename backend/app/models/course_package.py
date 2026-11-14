from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

PACKAGE_ACTIVE = "ACTIVE"
PACKAGE_COMING_SOON = "COMING_SOON"
PACKAGE_DISABLED = "DISABLED"
PACKAGE_STATUSES = (PACKAGE_ACTIVE, PACKAGE_COMING_SOON, PACKAGE_DISABLED)


class CoursePackage(BaseModel):
    """A course offer students can buy (single level "A1" or bundle "A1_B1"): price, access duration, status and the
    levels it opens. `code` is what SubscriptionOrder.plan stores. Rules: app/services/vizu_pay/offers.py; managed in
    Admin -> Angebote (Pakete)."""

    __tablename__ = "course_packages"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','COMING_SOON','DISABLED')", name="ck_course_packages_status"),
        CheckConstraint("package_type IN ('LEVEL','PACKAGE')", name="ck_course_packages_type"),
        CheckConstraint("duration_days > 0 AND duration_days <= 3650", name="ck_course_packages_duration"),
        CheckConstraint("price IS NULL OR (price > 0 AND price <= 100000000)", name="ck_course_packages_price"),
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    package_type: Mapped[str] = mapped_column(String(20), nullable=False)
    included_levels: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PACKAGE_COMING_SOON)
    # {"uz": "...", "de": "...", "en": "...", "ru": "..."}
    description: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
