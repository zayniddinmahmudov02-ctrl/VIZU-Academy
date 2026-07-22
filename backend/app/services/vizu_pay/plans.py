"""Central plan/pricing configuration for VIZU Pay.

Prices are placeholders in UZS pending real business figures — change here,
nowhere else. Not wired to any external gateway (see gateways.py).
"""

PLAN_TRIAL = "TRIAL"
PLAN_MONTH_1 = "MONTH_1"
PLAN_MONTH_3 = "MONTH_3"
PLAN_MONTH_6 = "MONTH_6"
PLAN_MONTH_12 = "MONTH_12"

PAID_PLANS = {PLAN_MONTH_1, PLAN_MONTH_3, PLAN_MONTH_6, PLAN_MONTH_12}
ALL_PLANS = PAID_PLANS | {PLAN_TRIAL}

PLAN_CONFIG = {
    PLAN_TRIAL: {"days": 7, "price": 0, "label": "7-Day Trial"},
    PLAN_MONTH_1: {"days": 30, "price": 49_000, "label": "1 Month"},
    PLAN_MONTH_3: {"days": 90, "price": 129_000, "label": "3 Months"},
    PLAN_MONTH_6: {"days": 180, "price": 229_000, "label": "6 Months"},
    PLAN_MONTH_12: {"days": 365, "price": 399_000, "label": "12 Months"},
}

PAYMENT_METHOD_VISA = "VISA"
PAYMENT_METHOD_MASTERCARD = "MASTERCARD"
PAYMENT_METHOD_UZCARD = "UZCARD"
PAYMENT_METHOD_HUMO = "HUMO"
PAYMENT_METHOD_TELEGRAM = "TELEGRAM"
PAYMENT_METHOD_TRIAL = "TRIAL"

PAYMENT_METHODS = {
    PAYMENT_METHOD_VISA,
    PAYMENT_METHOD_MASTERCARD,
    PAYMENT_METHOD_UZCARD,
    PAYMENT_METHOD_HUMO,
    PAYMENT_METHOD_TELEGRAM,
}

STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_EXPIRED = "EXPIRED"
STATUS_REFUNDED = "REFUNDED"

ORDER_REVIEW_WINDOW_DAYS = 3


def plan_label(plan: str) -> str:
    return PLAN_CONFIG.get(plan, {}).get("label", plan)


def plan_days(plan: str) -> int:
    return PLAN_CONFIG.get(plan, {}).get("days", 0)


def plan_price(plan: str) -> int:
    return PLAN_CONFIG.get(plan, {}).get("price", 0)
