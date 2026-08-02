from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class PlanOption(BaseSchema):
    plan: str
    label: str
    days: int
    price: int
    currency: str = "UZS"


class MySubscriptionStatus(BaseSchema):
    is_premium: bool
    premium_until: datetime | None
    is_trial: bool
    trial_available: bool
    trial_days_remaining: int | None
    has_pending_order: bool


class OrderItem(BaseSchema):
    id: UUID
    plan: str
    plan_label: str
    duration_days: int
    base_amount: int
    discount_amount: int
    final_amount: int
    currency: str
    payment_method: str
    status: str
    proof_url: str | None
    proof_type: str | None
    promo_code: str | None
    rejection_reason: str | None
    expires_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime


class OrderListResponse(BaseSchema):
    items: list[OrderItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class TrialActivateResponse(BaseSchema):
    premium_until: datetime


class AdminOrderItem(OrderItem):
    user_id: UUID
    user_email: str
    user_username: str
    reviewed_by_email: str | None


class AdminOrderListResponse(BaseSchema):
    items: list[AdminOrderItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class RejectOrderRequest(BaseSchema):
    reason: str


class RefundOrderRequest(BaseSchema):
    reason: str | None = None


class PromoCodeItem(BaseSchema):
    id: UUID
    code: str
    campaign: str | None
    discount_type: str
    discount_value: int
    max_uses: int | None
    used_count: int
    expires_at: datetime | None
    is_active: bool
    created_at: datetime


class PromoCodeListResponse(BaseSchema):
    items: list[PromoCodeItem]


class PromoCodeCreateRequest(BaseSchema):
    code: str
    campaign: str | None = None
    discount_type: str
    discount_value: int
    max_uses: int | None = None
    expires_at: datetime | None = None


class PromoCodeUpdateRequest(BaseSchema):
    campaign: str | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None


class PromoValidateResponse(BaseSchema):
    valid: bool
    discount_type: str | None = None
    discount_value: int | None = None
    message: str | None = None


class RevenueChartPoint(BaseSchema):
    label: str
    value: int


class PlanBreakdown(BaseSchema):
    plan: str
    label: str
    orders: int
    revenue: int


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
    trials_started: int
    trials_converted: int
    trial_conversion_rate: float
    monthly_revenue_chart: list[RevenueChartPoint]
    plan_breakdown: list[PlanBreakdown]
    method_breakdown: list[MethodBreakdown]
    status_breakdown: list[StatusBreakdown]
