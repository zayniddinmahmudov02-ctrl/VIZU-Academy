from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.exceptions import NotFoundError
from app.core.pagination import clamp_page_params, paginated_response
from app.models.audit_log import AuditLog
from app.models.promo_code import PromoCode
from app.models.promo_code_redemption import PromoCodeRedemption
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User

from . import plans as plan_config
from .service import VizuPayError, VizuPayService

PAYMENT_LOG_ACTIONS = [
    "order_created",
    "order_approved",
    "order_rejected",
    "order_refunded",
    "trial_started",
]


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AdminVizuPayService:
    def __init__(self, db: Session):
        self.db = db
        self.pay = VizuPayService(db)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def _serialize_admin_order(self, order: SubscriptionOrder) -> dict:
        base = self.pay.serialize_order(order)
        base.update(
            {
                "user_id": str(order.user_id),
                "user_email": order.user.email if order.user else "",
                "user_username": order.user.username if order.user else "",
                "reviewed_by_email": order.reviewed_by.email if order.reviewed_by else None,
            }
        )
        return base

    def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        plan: str | None = None,
        search: str | None = None,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
    ) -> dict:
        query = self.db.query(SubscriptionOrder).join(User, SubscriptionOrder.user_id == User.id)

        if status:
            query = query.filter(SubscriptionOrder.status == status)
        if plan:
            query = query.filter(SubscriptionOrder.plan == plan)
        if search:
            like = f"%{search.strip()}%"
            query = query.filter(or_(User.email.ilike(like), User.username.ilike(like)))
        if year is not None:
            query = query.filter(extract("year", SubscriptionOrder.created_at) == year)
        if month is not None:
            query = query.filter(extract("month", SubscriptionOrder.created_at) == month)
        if day is not None:
            query = query.filter(extract("day", SubscriptionOrder.created_at) == day)

        total = query.count()
        page, page_size = clamp_page_params(page, page_size)

        rows = (
            query.order_by(SubscriptionOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return paginated_response([self._serialize_admin_order(o) for o in rows], total, page, page_size)

    def _get_order(self, order_id: str) -> SubscriptionOrder:
        order = self.db.get(SubscriptionOrder, UUID(order_id))
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def approve_order(self, order_id: str, actor: User, ip: str | None) -> dict:
        order = self._get_order(order_id)
        if order.status != plan_config.STATUS_PENDING:
            raise VizuPayError(f"Order is not pending (current status: {order.status}).")

        now = _now()
        user = order.user

        base = user.premium_until if (user.premium_until and user.premium_until > now) else now
        user.premium_until = base + timedelta(days=order.duration_days)

        order.status = plan_config.STATUS_APPROVED
        order.reviewed_by_id = actor.id
        order.reviewed_at = now

        self.db.commit()

        write_audit(
            self.db,
            actor_id=actor.id,
            action="order_approved",
            target_user_id=order.user_id,
            details=f"{order.plan} +{order.duration_days}d, {order.final_amount} {order.currency}",
            ip_address=ip,
        )

        self.db.refresh(order)
        return self._serialize_admin_order(order)

    def reject_order(self, order_id: str, reason: str, actor: User, ip: str | None) -> dict:
        order = self._get_order(order_id)
        if order.status != plan_config.STATUS_PENDING:
            raise VizuPayError(f"Order is not pending (current status: {order.status}).")

        order.status = plan_config.STATUS_REJECTED
        order.rejection_reason = reason
        order.reviewed_by_id = actor.id
        order.reviewed_at = _now()

        if order.promo_code_id:
            redemption = (
                self.db.query(PromoCodeRedemption)
                .filter(PromoCodeRedemption.order_id == order.id)
                .first()
            )
            if redemption:
                self.db.delete(redemption)
            promo = self.db.get(PromoCode, order.promo_code_id)
            if promo and promo.used_count > 0:
                promo.used_count -= 1

        self.db.commit()

        write_audit(
            self.db,
            actor_id=actor.id,
            action="order_rejected",
            target_user_id=order.user_id,
            details=reason,
            ip_address=ip,
        )

        self.db.refresh(order)
        return self._serialize_admin_order(order)

    def refund_order(self, order_id: str, reason: str | None, actor: User, ip: str | None) -> dict:
        order = self._get_order(order_id)
        if order.status != plan_config.STATUS_APPROVED:
            raise VizuPayError(f"Only approved orders can be refunded (current status: {order.status}).")

        user = order.user
        if user.premium_until:
            user.premium_until = max(_now(), user.premium_until - timedelta(days=order.duration_days))

        order.status = plan_config.STATUS_REFUNDED
        order.rejection_reason = reason
        order.reviewed_by_id = actor.id
        order.reviewed_at = _now()

        self.db.commit()

        write_audit(
            self.db,
            actor_id=actor.id,
            action="order_refunded",
            target_user_id=order.user_id,
            details=reason,
            ip_address=ip,
        )

        self.db.refresh(order)
        return self._serialize_admin_order(order)

    # ------------------------------------------------------------------
    # Promo codes
    # ------------------------------------------------------------------

    def _serialize_promo(self, promo: PromoCode) -> dict:
        return {
            "id": str(promo.id),
            "code": promo.code,
            "campaign": promo.campaign,
            "discount_type": promo.discount_type,
            "discount_value": promo.discount_value,
            "max_uses": promo.max_uses,
            "used_count": promo.used_count,
            "expires_at": promo.expires_at,
            "is_active": promo.is_active,
            "created_at": promo.created_at,
        }

    def list_promos(self) -> list[dict]:
        rows = self.db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()
        return [self._serialize_promo(p) for p in rows]

    def create_promo(
        self,
        code: str,
        campaign: str | None,
        discount_type: str,
        discount_value: int,
        max_uses: int | None,
        expires_at: datetime | None,
        actor: User,
    ) -> dict:
        code = code.strip().upper()
        if not code:
            raise VizuPayError("Code cannot be empty.")
        if discount_type not in {"PERCENT", "FIXED"}:
            raise VizuPayError("discount_type must be PERCENT or FIXED.")
        if discount_value <= 0:
            raise VizuPayError("discount_value must be positive.")
        if discount_type == "PERCENT" and discount_value > 100:
            raise VizuPayError("Percent discount cannot exceed 100.")

        existing = self.db.query(PromoCode).filter(PromoCode.code == code).first()
        if existing:
            raise VizuPayError("A promo code with this code already exists.")

        promo = PromoCode(
            code=code,
            campaign=campaign,
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            expires_at=expires_at,
            created_by_id=actor.id,
        )
        self.db.add(promo)
        self.db.commit()
        self.db.refresh(promo)

        write_audit(self.db, actor_id=actor.id, action="promo_code_created", details=code)

        return self._serialize_promo(promo)

    def update_promo(
        self,
        promo_id: str,
        campaign: str | None,
        is_active: bool | None,
        expires_at: datetime | None,
        actor: User,
    ) -> dict:
        promo = self.db.get(PromoCode, UUID(promo_id))
        if promo is None:
            raise NotFoundError("Promo code not found")

        if campaign is not None:
            promo.campaign = campaign
        if is_active is not None:
            promo.is_active = is_active
        if expires_at is not None:
            promo.expires_at = expires_at

        self.db.commit()
        self.db.refresh(promo)

        write_audit(self.db, actor_id=actor.id, action="promo_code_updated", details=promo.code)

        return self._serialize_promo(promo)

    def delete_promo(self, promo_id: str, actor: User) -> None:
        promo = self.db.get(PromoCode, UUID(promo_id))
        if promo is None:
            raise NotFoundError("Promo code not found")
        if promo.used_count > 0:
            raise VizuPayError("Cannot delete a promo code that has been used. Deactivate it instead.")

        code = promo.code
        self.db.delete(promo)
        self.db.commit()

        write_audit(self.db, actor_id=actor.id, action="promo_code_deleted", details=code)

    # ------------------------------------------------------------------
    # Revenue
    # ------------------------------------------------------------------

    def revenue_overview(self) -> dict:
        now = _now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)

        total_revenue = int(
            self.db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(SubscriptionOrder.status == plan_config.STATUS_APPROVED, SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)))
            .scalar()
            or 0
        )

        revenue_this_month = int(
            self.db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(
                SubscriptionOrder.status == plan_config.STATUS_APPROVED,
                SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)),
                SubscriptionOrder.reviewed_at >= month_start,
            )
            .scalar()
            or 0
        )

        revenue_today = int(
            self.db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(
                SubscriptionOrder.status == plan_config.STATUS_APPROVED,
                SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)),
                SubscriptionOrder.reviewed_at >= today_start,
            )
            .scalar()
            or 0
        )

        total_orders = self.db.query(SubscriptionOrder).count()
        pending_orders = self.db.query(SubscriptionOrder).filter(SubscriptionOrder.status == plan_config.STATUS_PENDING).count()

        trials_started = self.db.query(User).filter(User.trial_used_at.isnot(None)).count()

        converted_user_ids = (
            self.db.query(SubscriptionOrder.user_id)
            .filter(SubscriptionOrder.status == plan_config.STATUS_APPROVED, SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)))
            .join(User, User.id == SubscriptionOrder.user_id)
            .filter(User.trial_used_at.isnot(None))
            .distinct()
        )
        trials_converted = converted_user_ids.count()

        trial_conversion_rate = round((trials_converted / trials_started * 100), 1) if trials_started > 0 else 0.0

        bucket = func.to_char(SubscriptionOrder.reviewed_at, "YYYY-MM")
        monthly_rows = (
            self.db.query(bucket.label("label"), func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(SubscriptionOrder.status == plan_config.STATUS_APPROVED, SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)))
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )
        monthly_revenue_chart = [{"label": label, "value": int(value)} for label, value in monthly_rows][-12:]

        plan_rows = (
            self.db.query(SubscriptionOrder.plan, func.count(SubscriptionOrder.id), func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(SubscriptionOrder.status == plan_config.STATUS_APPROVED, SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)))
            .group_by(SubscriptionOrder.plan)
            .all()
        )
        plan_breakdown = [
            {"plan": plan, "label": plan_config.plan_label(plan), "orders": int(count), "revenue": int(revenue)}
            for plan, count, revenue in plan_rows
        ]

        method_rows = (
            self.db.query(SubscriptionOrder.payment_method, func.count(SubscriptionOrder.id), func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(SubscriptionOrder.status == plan_config.STATUS_APPROVED, SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)))
            .group_by(SubscriptionOrder.payment_method)
            .all()
        )
        method_breakdown = [
            {"method": method, "orders": int(count), "revenue": int(revenue)} for method, count, revenue in method_rows
        ]

        status_rows = (
            self.db.query(SubscriptionOrder.status, func.count(SubscriptionOrder.id))
            .group_by(SubscriptionOrder.status)
            .all()
        )
        status_breakdown = [{"status": status, "count": int(count)} for status, count in status_rows]

        return {
            "total_revenue": total_revenue,
            "revenue_this_month": revenue_this_month,
            "revenue_today": revenue_today,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "trials_started": trials_started,
            "trials_converted": trials_converted,
            "trial_conversion_rate": trial_conversion_rate,
            "monthly_revenue_chart": monthly_revenue_chart,
            "plan_breakdown": plan_breakdown,
            "method_breakdown": method_breakdown,
            "status_breakdown": status_breakdown,
        }

    # ------------------------------------------------------------------
    # Payment logs
    # ------------------------------------------------------------------

    def get_payment_logs(self, page: int = 1, page_size: int = 20) -> dict:
        query = (
            self.db.query(AuditLog)
            .filter(AuditLog.action.in_(PAYMENT_LOG_ACTIONS))
            .order_by(AuditLog.created_at.desc())
        )

        total = query.count()
        page, page_size = clamp_page_params(page, page_size)

        rows = query.offset((page - 1) * page_size).limit(page_size).all()

        items = [
            {
                "id": str(row.id),
                "actor_email": row.actor.email if row.actor else None,
                "action": row.action,
                "details": row.details,
                "ip_address": row.ip_address,
                "created_at": row.created_at,
            }
            for row in rows
        ]

        return paginated_response(items, total, page, page_size)
