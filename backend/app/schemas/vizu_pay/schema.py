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
    # ACTIVE / COMING_SOON (DISABLED packages are not listed); price and duration are null unless ACTIVE
    status: str = "ACTIVE"
    duration_days: int | None = None
    description: dict[str, str] = {}
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
    # COURSES / PACKAGES / MULTILEVEL / LEGACY (service.order_category)
    product_category: str = "COURSES"
    paid_at: datetime | None = None
    no_receipt: bool = False
    student_note: str | None = None
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
    admin_note: str | None = None


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
    product_category: str = "COURSES"
    approval_status: str = "PENDING"
    approved_at: datetime | None = None
    approved_by_email: str | None = None
    review_note: str | None = None
    assigned_user_id: str | None = None
    assigned_user_email: str | None = None
    requires_approval: bool = False
    pending_requests: int = 0
    created_by_email: str | None = None
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
    # ignored: a new code is always PENDING until a Super Admin approves it (POST /promo-codes/{id}/review)
    is_active: bool = True
    requires_approval: bool = False
    product_category: str = Field(default="COURSES", pattern="^(COURSES|PACKAGES|MULTILEVEL)$")


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
    requires_approval: bool | None = None
    product_category: str | None = Field(default=None, pattern="^(COURSES|PACKAGES|MULTILEVEL)$")


class PromoCodeReviewRequest(BaseSchema):
    """approve (-> APPROVED), approve_activate (-> ACTIVE), activate, reject, disable — see AdminVizuPayService.review_promo."""

    action: str = Field(pattern="^(approve|approve_activate|activate|reject|disable)$")
    note: str | None = Field(default=None, max_length=500)


class OrderNoteRequest(BaseSchema):
    note: str | None = Field(default=None, max_length=1000)


class CourseRequestCreate(BaseSchema):
    plan: str = Field(min_length=1, max_length=20)
    message: str | None = Field(default=None, max_length=1000)


class CourseRequestReview(BaseSchema):
    approve: bool
    reason: str | None = Field(default=None, max_length=500)
    # approve: "create" a personal code for the student, or "attach" an existing approved ACTIVE code
    mode: str = Field(default="create", pattern="^(create|attach)$")
    discount_type: str | None = Field(default=None, pattern="^(PERCENT|FIXED|FREE_ACCESS)$")
    discount_value: int | None = Field(default=None, ge=0, le=100_000_000)
    expires_at: datetime | None = None
    promo_code_id: str | None = Field(default=None, max_length=40)


class MultilevelRedeemRequest(BaseSchema):
    code: str = Field(min_length=1, max_length=40)


class PaymentSettingsUpdate(BaseSchema):
    """Multilevel Modelltest Premium price (UZS) and sale status. Card numbers are not editable here (plans.PAYMENT_CARDS)."""

    multilevel_price: int | None = Field(default=None, ge=1_000, le=10_000_000)
    multilevel_status: str | None = Field(default=None, pattern="^(ACTIVE|DISABLED)$")


class PromoValidateResponse(BaseSchema):
    valid: bool
    discount_type: str | None = None
    discount_value: int | None = None
    message: str | None = None
    discount_amount: int | None = None
    final_amount: int | None = None
    requires_approval: bool = False
    # APPROVED / PROMO_APPROVAL_REQUIRED / PROMO_APPROVAL_PENDING / PROMO_REJECTED (codes that need an admin)
    approval_status: str | None = None


class PromoRequestCreate(BaseSchema):
    code: str = Field(min_length=1, max_length=40)
    plan: str = Field(min_length=1, max_length=20)


class PromoReviewRequest(BaseSchema):
    approve: bool
    reason: str | None = Field(default=None, max_length=500)


class PackageWrite(BaseSchema):
    """Admin create / update of a course package (packages.py validates the business rules)."""

    code: str | None = Field(default=None, max_length=20)
    name: str | None = Field(default=None, max_length=120)
    package_type: str | None = None
    included_levels: list[str] | None = None
    price: int | None = None
    original_price: int | None = None
    discount_percent: int | None = None
    duration_days: int | None = None
    status: str | None = None
    description: dict[str, str] | None = None
    sort_order: int | None = None


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
