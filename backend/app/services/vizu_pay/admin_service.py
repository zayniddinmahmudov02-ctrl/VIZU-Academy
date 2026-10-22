from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import extract, func, literal_column, or_
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.exceptions import NotFoundError
from app.core.pagination import clamp_page_params, paginated_response
from app.models.audit_log import AuditLog
from app.models.promo_code import PromoCode
from app.models.promo_code_redemption import PromoCodeRedemption
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User
from app.services import achievements

from . import offers as offer_config
from . import plans as plan_config
from . import purchases
from .service import VizuPayError, VizuPayService

PAYMENT_LOG_ACTIONS = [
    "order_created",
    "order_approved",
    "order_rejected",
    "order_refunded",
    "promo_redeemed",
    "trial_started",  # historical only — the trial feature itself is removed
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
                "user_first_name": order.user.first_name if order.user else None,
                "user_last_name": order.user.last_name if order.user else None,
                "user_phone_number": order.user.phone_number if order.user else None,
                "reviewed_by_email": order.reviewed_by.email if order.reviewed_by else None,
                "rejection_count": self.pay.get_rejection_count(order.user_id),
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
        user_id: str | None = None,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        kind: str | None = None,
    ) -> dict:
        query = self.db.query(SubscriptionOrder).join(User, SubscriptionOrder.user_id == User.id)

        if status:
            query = query.filter(SubscriptionOrder.status == status)
        if plan:
            query = query.filter(SubscriptionOrder.plan == plan)
        if kind == "course":
            # Angebote course orders only (Analytics -> course purchases)
            query = query.filter(SubscriptionOrder.plan.in_(list(offer_config.OFFER_CODES)))
        if user_id:
            query = query.filter(SubscriptionOrder.user_id == UUID(user_id))
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

    def list_blocked_users(self) -> list[dict]:
        """Users with >= MAX_REJECTIONS rejected orders — blocked from
        submitting new payment requests (see VizuPayService.create_order).
        Grouped by user, not a per-order listing like the other tabs."""
        rows = (
            self.db.query(
                SubscriptionOrder.user_id,
                func.count(SubscriptionOrder.id),
                func.max(SubscriptionOrder.reviewed_at),
            )
            .filter(SubscriptionOrder.status == plan_config.STATUS_REJECTED)
            .group_by(SubscriptionOrder.user_id)
            .having(func.count(SubscriptionOrder.id) >= plan_config.MAX_REJECTIONS)
            .all()
        )

        items = []
        for user_id, count, last_rejected_at in rows:
            user = self.db.get(User, user_id)
            items.append(
                {
                    "user_id": str(user_id),
                    "user_email": user.email if user else "",
                    "user_username": user.username if user else "",
                    "user_first_name": user.first_name if user else None,
                    "user_last_name": user.last_name if user else None,
                    "user_phone_number": user.phone_number if user else None,
                    "rejection_count": int(count),
                    "last_rejected_at": last_rejected_at,
                }
            )
        items.sort(key=lambda i: i["last_rejected_at"] or "", reverse=True)
        return items

    def _get_order_for_review(self, order_id: str) -> SubscriptionOrder:
        """Row-locked fetch — the single point every review action (approve/
        reject) goes through, so two admins acting on the same order at the
        same instant can't both succeed (see approve_order/reject_order:
        the second request's status check runs only after the first's
        transaction has committed and released the lock, so it always sees
        the already-finalized status and is rejected with a 400)."""
        order = (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.id == UUID(order_id))
            .with_for_update()
            .first()
        )
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def _get_order(self, order_id: str) -> SubscriptionOrder:
        order = self.db.get(SubscriptionOrder, UUID(order_id))
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def approve_order(self, order_id: str, actor: User, ip: str | None) -> dict:
        order = self._get_order_for_review(order_id)
        if order.status != plan_config.STATUS_PENDING:
            raise VizuPayError(f"This request was already reviewed (current status: {order.status}).")

        now = _now()
        user = order.user

        if offer_config.is_offer(order.plan):
            purchases.activate_course_access(order, now.replace(tzinfo=timezone.utc))
        else:
            base = user.premium_until if (user.premium_until and user.premium_until > now) else now
            user.premium_until = base + timedelta(days=order.duration_days)

        order.status = plan_config.STATUS_APPROVED
        order.reviewed_by_id = actor.id
        order.reviewed_at = now
        achievements.on_order_status(self.db, order)  # a reserved medal reward is now used

        self.db.commit()

        write_audit(
            self.db,
            actor_id=actor.id,
            action="order_approved",
            target_user_id=order.user_id,
            details=(
                f"{order.plan} levels={','.join(offer_config.offer_levels(order.plan))}, {order.final_amount} {order.currency}"
                if offer_config.is_offer(order.plan)
                else f"{order.plan} +{order.duration_days}d, {order.final_amount} {order.currency}"
            ),
            ip_address=ip,
        )

        self.db.refresh(order)
        return self._serialize_admin_order(order)

    def extend_order_access(self, order_id: str, months: int, reason: str, actor: User, ip: str | None) -> dict:
        order = self._get_order_for_review(order_id)
        if order.status != plan_config.STATUS_APPROVED or not offer_config.is_offer(order.plan):
            raise VizuPayError("Only approved course or package orders can be extended.")

        now = datetime.now(timezone.utc)
        current_end = order.access_end_date
        purchases.extend_course_access(order, months, now)
        self.db.add(
            AuditLog(
                actor_id=str(actor.id),
                action="course_access_extended",
                target_user_id=str(order.user_id),
                details=(
                    f"order={order.id}, plan={order.plan}, months=+{months}, "
                    f"old_end={current_end.isoformat() if current_end else None}, "
                    f"new_end={order.access_end_date.isoformat()}, reason={reason.strip()}"
                ),
                ip_address=ip,
            )
        )
        self.db.commit()
        self.db.refresh(order)
        return self._serialize_admin_order(order)

    def reject_order(self, order_id: str, reason: str, actor: User, ip: str | None) -> dict:
        order = self._get_order_for_review(order_id)
        if order.status != plan_config.STATUS_PENDING:
            raise VizuPayError(f"This request was already reviewed (current status: {order.status}).")

        order.status = plan_config.STATUS_REJECTED
        order.rejection_reason = reason
        order.reviewed_by_id = actor.id
        order.reviewed_at = _now()
        achievements.on_order_status(self.db, order)  # the medal reward becomes usable again

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
        # row-locked like approve/reject: a double click must not refund twice
        order = self._get_order_for_review(order_id)
        if order.status != plan_config.STATUS_APPROVED:
            raise VizuPayError(f"Only approved orders can be refunded (current status: {order.status}).")

        user = order.user
        # Refunding an Angebote order revokes its levels automatically (the
        # order is no longer APPROVED); only legacy plans touch premium_until.
        if user.premium_until and not offer_config.is_offer(order.plan):
            user.premium_until = max(_now(), user.premium_until - timedelta(days=order.duration_days))

        order.status = plan_config.STATUS_REFUNDED
        order.rejection_reason = reason
        order.reviewed_by_id = actor.id
        order.reviewed_at = _now()
        achievements.on_order_status(self.db, order)  # refunded purchase: the reward can be used again

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
        if discount_type not in {"PERCENT", "FIXED", "FREE_DAYS"}:
            raise VizuPayError("discount_type must be PERCENT, FIXED, or FREE_DAYS.")
        if discount_value <= 0:
            raise VizuPayError("discount_value must be positive.")
        if discount_type == "PERCENT" and discount_value > 100:
            raise VizuPayError("Percent discount cannot exceed 100.")
        if discount_type == "FREE_DAYS" and discount_value > 365:
            raise VizuPayError("A promo code can't grant more than 365 days at once.")

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
        """Every money figure under the shared purchase rule (purchases.py):
        APPROVED orders of a real-money plan, dated by approval."""
        now = _now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)
        approved = purchases.revenue_conditions()

        total_revenue = purchases.approved_revenue(self.db)
        revenue_this_month = purchases.approved_revenue(self.db, month_start)
        revenue_today = purchases.approved_revenue(self.db, today_start)

        total_orders = self.db.query(SubscriptionOrder).count()
        pending_orders = self.db.query(SubscriptionOrder).filter(SubscriptionOrder.status == plan_config.STATUS_PENDING).count()
        course_purchases, course_buyers = purchases.course_purchase_totals(self.db)
        premium_active = self.db.query(User).filter(User.premium_until.isnot(None), User.premium_until > now).count()
        paying_users = self.db.query(User).filter(purchases.is_paying_clause(now)).count()

        bucket = func.to_char(SubscriptionOrder.reviewed_at, literal_column("'YYYY-MM'"))
        monthly_rows = (
            self.db.query(bucket.label("label"), func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(*approved)
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )
        monthly_revenue_chart = [{"label": label, "value": int(value)} for label, value in monthly_rows][-12:]

        plan_rows = (
            self.db.query(
                SubscriptionOrder.plan,
                func.count(SubscriptionOrder.id),
                func.coalesce(func.sum(SubscriptionOrder.final_amount), 0),
                func.count(func.distinct(SubscriptionOrder.user_id)),
            )
            .filter(*approved)
            .group_by(SubscriptionOrder.plan)
            .all()
        )
        plan_breakdown = [
            {
                "plan": plan,
                "label": plan_config.plan_label(plan),
                "orders": int(count),
                "revenue": int(revenue),
                "buyers": int(buyers),
                "is_course": offer_config.is_offer(plan),
                "levels": offer_config.offer_levels(plan),
            }
            for plan, count, revenue, buyers in plan_rows
        ]
        plan_breakdown.sort(key=lambda p: (-p["revenue"], p["label"]))

        method_rows = (
            self.db.query(SubscriptionOrder.payment_method, func.count(SubscriptionOrder.id), func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
            .filter(*approved)
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
            "course_purchases": course_purchases,
            "course_buyers": course_buyers,
            "premium_active": premium_active,
            "paying_users": paying_users,
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
