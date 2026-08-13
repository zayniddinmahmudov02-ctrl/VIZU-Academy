"""Central plan/pricing configuration for VIZU Pay.

Prices are placeholders in UZS pending real business figures — change here,
nowhere else. Not wired to any external gateway (see gateways.py).
"""

# PLAN_TRIAL is kept only so historical orders/audit log rows referencing
# it (created back when the 7-day trial existed) still resolve a label —
# the trial feature itself is fully removed: no endpoint grants it, and it
# is deliberately absent from PAID_PLANS/ALL_PLANS so nothing new can be
# created with this plan.
PLAN_TRIAL = "TRIAL"
PLAN_PROMO = "PROMO"
PLAN_MONTH_1 = "MONTH_1"
PLAN_MONTH_3 = "MONTH_3"
PLAN_MONTH_6 = "MONTH_6"
PLAN_MONTH_12 = "MONTH_12"

PAID_PLANS = {PLAN_MONTH_1, PLAN_MONTH_3, PLAN_MONTH_6, PLAN_MONTH_12}
ALL_PLANS = PAID_PLANS | {PLAN_TRIAL, PLAN_PROMO}

PLAN_CONFIG = {
    PLAN_TRIAL: {"days": 7, "price": 0, "label": "7-Day Trial (discontinued)"},
    PLAN_PROMO: {"days": 0, "price": 0, "label": "Promo Code"},
    PLAN_MONTH_1: {"days": 30, "price": 49_000, "label": "1 Month"},
    PLAN_MONTH_3: {"days": 90, "price": 129_000, "label": "3 Months"},
    PLAN_MONTH_6: {"days": 180, "price": 229_000, "label": "6 Months"},
    PLAN_MONTH_12: {"days": 365, "price": 399_000, "label": "12 Months"},
}

# Manual bank transfer — authoritative card numbers. Do not change without
# explicit instruction; must stay identical to what the Telegram bot shows.
PAYMENT_CARDS = [
    {"label": "UzCard", "number": "9860350144907192"},
    {"label": "Visa", "number": "4448844427532174"},
]

PAYMENT_METHOD_VISA = "VISA"
PAYMENT_METHOD_MASTERCARD = "MASTERCARD"
PAYMENT_METHOD_UZCARD = "UZCARD"
PAYMENT_METHOD_HUMO = "HUMO"
PAYMENT_METHOD_TELEGRAM = "TELEGRAM"
PAYMENT_METHOD_TRIAL = "TRIAL"
PAYMENT_METHOD_PROMO = "PROMO"

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
