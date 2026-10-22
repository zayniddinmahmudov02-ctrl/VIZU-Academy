"""One rule for "a successful purchase" — shared by Admin Analytics, Premium
Users, Users and the Dashboard so the four never disagree.

* An order is a successful purchase / revenue only when it is APPROVED.
  PENDING, REJECTED, EXPIRED and REFUNDED orders never count (a refund flips
  the order away from APPROVED, so it drops out on its own).
* Revenue = APPROVED orders of a real-money plan (plans.REVENUE_PLANS: the
  Angebote course offers + the legacy time-based Premium plans).
* A course purchase = APPROVED order of an Angebote offer (offers.OFFER_CODES)
  — the same orders access.owned_levels() unlocks lessons with.
* The purchase date is `reviewed_at` (the moment the Super Admin approved it).
* Every figure is aggregated over subscription_orders rows directly, never
  through a join that could repeat an order, so an order counts exactly once.
"""

from calendar import monthrange
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.subscription_order import SubscriptionOrder
from app.models.user import User

from . import offers as offer_config
from . import plans as plan_config


def add_calendar_months(value: datetime, months: int) -> datetime:
    """Add calendar months, clamping month-end dates (Jan 31 -> Feb 28/29)."""
    if months < 1:
        raise ValueError("months must be positive")
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def activate_course_access(order, activated_at: datetime) -> None:
    """Start this order's independent access window after payment approval."""
    if activated_at.tzinfo is None:
        activated_at = activated_at.replace(tzinfo=timezone.utc)
    activated_at = activated_at.astimezone(timezone.utc)
    months = offer_config.access_duration_months(order.plan)
    order.purchase_date = activated_at
    order.access_start_date = activated_at
    order.access_end_date = add_calendar_months(activated_at, months)


def course_access_is_active(order, now: datetime) -> bool:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return bool(
        order.status == plan_config.STATUS_APPROVED
        and order.access_start_date is not None
        and order.access_end_date is not None
        and order.access_start_date <= now
        and now < order.access_end_date
    )


def extend_course_access(order, months: int, now: datetime) -> None:
    if order.status != plan_config.STATUS_APPROVED:
        raise ValueError("Only approved orders can be extended")
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    if order.access_start_date is None:
        order.access_start_date = now
    if order.purchase_date is None:
        order.purchase_date = order.access_start_date
    current_end = order.access_end_date
    order.access_end_date = add_calendar_months(max(current_end, now) if current_end else now, months)


def _naive_utc(dt: datetime | None) -> datetime | None:
    """reviewed_at is a naive-but-UTC column (see admin_service._now) —
    compare it with naive UTC, never with an aware value the database would
    shift by its session time zone."""
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def revenue_conditions() -> tuple:
    return (
        SubscriptionOrder.status == plan_config.STATUS_APPROVED,
        SubscriptionOrder.plan.in_(list(plan_config.REVENUE_PLANS)),
    )


def course_purchase_conditions() -> tuple:
    return (
        SubscriptionOrder.status == plan_config.STATUS_APPROVED,
        SubscriptionOrder.plan.in_(list(offer_config.OFFER_CODES)),
    )


def approved_revenue(db: Session, since: datetime | None = None) -> int:
    query = db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0)).filter(*revenue_conditions())
    if since is not None:
        query = query.filter(SubscriptionOrder.reviewed_at >= _naive_utc(since))
    return int(query.scalar() or 0)


def approved_revenue_orders(db: Session) -> int:
    return db.query(func.count(SubscriptionOrder.id)).filter(*revenue_conditions()).scalar() or 0


def course_purchase_totals(db: Session) -> tuple[int, int]:
    """(approved course orders, distinct students who bought a course)."""
    orders, buyers = db.query(
        func.count(SubscriptionOrder.id), func.count(func.distinct(SubscriptionOrder.user_id))
    ).filter(*course_purchase_conditions()).one()
    return int(orders or 0), int(buyers or 0)


def has_course_purchase_clause():
    """EXISTS filter for a users query: the user bought at least one course."""
    return exists().where(SubscriptionOrder.user_id == User.id, *course_purchase_conditions())


def is_paying_clause(now: datetime):
    """Active legacy Premium OR at least one approved course purchase."""
    return or_(User.premium_until > now, has_course_purchase_clause())


def last_purchase_at_subquery():
    """Correlated scalar: the user's latest approved real-money purchase."""
    return (
        select(func.max(SubscriptionOrder.reviewed_at))
        .where(SubscriptionOrder.user_id == User.id, *revenue_conditions())
        .correlate(User)
        .scalar_subquery()
    )


def course_purchases_by_user(db: Session, user_ids: list[UUID]) -> dict[UUID, list[dict]]:
    """Approved course purchases of the given users (one query for a page),
    newest first. Levels resolve through offers.offer_levels — the mapping
    lesson access uses too."""
    if not user_ids:
        return {}
    rows = (
        db.query(
            SubscriptionOrder.id,
            SubscriptionOrder.user_id,
            SubscriptionOrder.plan,
            SubscriptionOrder.final_amount,
            SubscriptionOrder.currency,
            SubscriptionOrder.reviewed_at,
        )
        .filter(SubscriptionOrder.user_id.in_(user_ids), *course_purchase_conditions())
        .order_by(SubscriptionOrder.reviewed_at.desc().nullslast())
        .all()
    )
    grouped: dict[UUID, list[dict]] = {}
    for order_id, user_id, plan, amount, currency, reviewed_at in rows:
        grouped.setdefault(user_id, []).append(
            {
                "order_id": str(order_id),
                "plan": plan,
                "label": plan_config.plan_label(plan),
                "levels": offer_config.offer_levels(plan),
                "amount": int(amount or 0),
                "currency": currency,
                "purchased_at": reviewed_at,
                "status": plan_config.STATUS_APPROVED,
            }
        )
    return grouped


def pending_orders_by_user(db: Session, user_ids: list[UUID]) -> dict[UUID, int]:
    """Orders still waiting for the Super Admin — shown apart, never as a purchase."""
    if not user_ids:
        return {}
    rows = (
        db.query(SubscriptionOrder.user_id, func.count(SubscriptionOrder.id))
        .filter(SubscriptionOrder.user_id.in_(user_ids), SubscriptionOrder.status == plan_config.STATUS_PENDING)
        .group_by(SubscriptionOrder.user_id)
        .all()
    )
    return {user_id: int(count) for user_id, count in rows}


def revenue_of_user(db: Session, user_id: UUID) -> tuple[int, int]:
    """(approved revenue, approved orders) of one user."""
    total, count = (
        db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0), func.count(SubscriptionOrder.id))
        .filter(SubscriptionOrder.user_id == user_id, *revenue_conditions())
        .one()
    )
    return int(total or 0), int(count or 0)
