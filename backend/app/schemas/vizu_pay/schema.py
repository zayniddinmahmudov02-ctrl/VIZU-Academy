from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class PlanOption(BaseSchema):
    plan: str
    label: str
    days: int
    price: int
    currency: str = "UZS"


class OfferItem(BaseSchema):
    """One Angebote offer (single level or package) — values come from
    app.services.vizu_pay.offers, the single source of truth."""

    code: str
    kind: str
    label: str
    levels: list[str]
    original_price: int | None
    sale_price: int | None
    discount_percent: int | None
    active: bool
    # server decision: active, priced and (single level) the level is released
    purchasable: bool = False
    # levels of the offer students can open today ("Tez orada" levels are not)
    available_levels: list[str] = []
    # levels approved for sale (Admin -> Angebote); the others show "Tez orada"
    sales_levels: list[str] = []
    free_lessons: int
    duration_months: int
    currency: str = "UZS"


class CourseAccessItem(BaseSchema):
    order_id: UUID
    plan: str
    plan_label: str
    levels: list[str]
    purchase_date: datetime | None
    access_start_date: datetime | None
    access_end_date: datetime | None
    status: str
    remaining_seconds: int


class MySubscriptionStatus(BaseSchema):
    is_premium: bool
    premium_until: datetime | None
    owned_levels: list[str] = []
    has_pending_order: bool
    rejection_count: int
    is_blocked: bool
    latest_rejection_reason: str | None
    course_accesses: list[CourseAccessItem] = []


class OrderItem(BaseSchema):
    id: UUID
    plan: str
    plan_label: str
    duration_days: int
    base_amount: int
    discount_amount: int
    # part of discount_amount from a medal reward (Starter: 5 000 on A1)
    reward_discount_amount: int = 0
    final_amount: int
    currency: str
    payment_method: str
    status: str
    has_proof: bool
    proof_download_url: str | None
    promo_code: str | None
    rejection_reason: str | None
    expires_at: datetime | None
    reviewed_at: datetime | None
    purchase_date: datetime | None = None
    access_start_date: datetime | None = None
    access_end_date: datetime | None = None
    created_at: datetime


class OrderListResponse(BaseSchema):
    items: list[OrderItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaymentCardItem(BaseSchema):
    label: str
    number: str


class PromoRedeemRequest(BaseSchema):
    code: str


class PromoRedeemResponse(BaseSchema):
    premium_until: datetime | None = None
    days_granted: int = 0
    granted_offers: list[str] = []


class AdminOrderItem(OrderItem):
    user_id: UUID
    user_email: str
    user_username: str
    user_first_name: str | None
    user_last_name: str | None
    user_phone_number: str | None
    reviewed_by_email: str | None
    # Total REJECTED orders for this user across all time (not just this
    # order) — lets the admin see "this is their 2nd/3rd attempt" at a
    # glance without opening the user's full history.
    rejection_count: int


class AdminOrderListResponse(BaseSchema):
    items: list[AdminOrderItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class BlockedUserItem(BaseSchema):
    user_id: UUID
    user_email: str
    user_username: str
    user_first_name: str | None
    user_last_name: str | None
    user_phone_number: str | None
    rejection_count: int
    last_rejected_at: datetime | None


class RejectOrderRequest(BaseSchema):
    reason: str


class ExtendOrderAccessRequest(BaseSchema):
    months: int = Field(ge=1, le=120)
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_and_validate_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("reason must contain at least 3 non-whitespace characters")
        return value


class RefundOrderRequest(BaseSchema):
    reason: str | None = None


class PromoCodeItem(BaseSchema):
    id: UUID
    code: str
    campaign: str | None
    discount_type: str
    discount_value: int
    starts_at: datetime | None = None
    max_uses: int | None
    used_count: int
    max_uses_per_user: int
    applicable_course_ids: list[str]
    applicable_package_codes: list[str]
    successful_uses: int
    successful_discount_amount: int
    successful_revenue_amount: int = 0
    remaining_uses: int | None
    status: str
    successful_products: list[dict]
    expires_at: datetime | None
    is_active: bool
    created_at: datetime


class PromoCodeListResponse(BaseSchema):
    items: list[PromoCodeItem]


class PromoCodeCreateRequest(BaseSchema):
    code: str = Field(min_length=1, max_length=40)
    campaign: str | None = Field(default=None, max_length=120)
    discount_type: str
    discount_value: int = Field(ge=0, le=100_000_000)
    applicable_course_ids: list[str] = Field(default_factory=list)
    applicable_package_codes: list[str] = Field(default_factory=list)
    starts_at: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1)
    max_uses_per_user: int = Field(default=1, ge=1, le=1000)
    expires_at: datetime | None = None
    is_active: bool = True


class PromoCodeUpdateRequest(BaseSchema):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    campaign: str | None = Field(default=None, max_length=120)
    discount_type: str | None = None
    discount_value: int | None = Field(default=None, ge=0, le=100_000_000)
    applicable_course_ids: list[str] | None = None
    applicable_package_codes: list[str] | None = None
    starts_at: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1)
    max_uses_per_user: int | None = Field(default=None, ge=1, le=1000)
    is_active: bool | None = None
    expires_at: datetime | None = None


class PromoValidateResponse(BaseSchema):
    valid: bool
    discount_type: str | None = None
    discount_value: int | None = None
    message: str | None = None
    discount_amount: int | None = None
    final_amount: int | None = None


class RevenueChartPoint(BaseSchema):
    label: str
    value: int


class PlanBreakdown(BaseSchema):
    plan: str
    label: str
    orders: int
    revenue: int
    buyers: int = 0  # distinct students
    is_course: bool = False  # an Angebote course offer (vs. legacy Premium plan)
    levels: list[str] = []


class MethodBreakdown(BaseSchema):
    method: str
    orders: int
    revenue: int


class StatusBreakdown(BaseSchema):
    status: str
    count: int


class RevenueOverview(BaseSchema):
    total_revenue: int
    revenue_this_month: int
    revenue_today: int
    total_orders: int
    pending_orders: int
    course_purchases: int = 0  # APPROVED course orders
    course_buyers: int = 0  # distinct students with an APPROVED course order
    premium_active: int = 0  # legacy time-based Premium still running
    paying_users: int = 0  # premium_active OR course buyer, each student once
    monthly_revenue_chart: list[RevenueChartPoint]
    plan_breakdown: list[PlanBreakdown]
    method_breakdown: list[MethodBreakdown]
    status_breakdown: list[StatusBreakdown]
