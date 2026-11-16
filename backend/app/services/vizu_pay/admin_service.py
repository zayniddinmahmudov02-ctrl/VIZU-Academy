from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import extract, func, literal_column, or_
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.exceptions import NotFoundError
from app.core.pagination import clamp_page_params, paginated_response
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.promo_code import (APPROVAL_ACTIVE, APPROVAL_APPROVED, APPROVAL_DISABLED, APPROVAL_PENDING, APPROVAL_REJECTED, CATEGORIES,
                                   CATEGORY_COURSES, CATEGORY_MULTILEVEL, CATEGORY_PACKAGES, PromoCode)
from app.models.promo_code_request import (KIND_CODE_APPROVAL, KIND_COURSE_REQUEST, REQUEST_APPROVED, REQUEST_PENDING, REQUEST_REJECTED,
                                           REQUEST_USED, PromoCodeRequest)
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User
from app.services import achievements
from sqlalchemy.exc import IntegrityError

from . import offers as offer_config
from . import plans as plan_config
from . import purchases
from .service import VizuPayError, VizuPayService

PAYMENT_LOG_ACTIONS = [
    "order_created",
    "order_approved",
    "order_rejected",
    "order_refunded",
    "order_note_updated",
    "promo_redeemed",
    "promo_free_access_redeemed",
    "ml_premium_promo_redeemed",
    "promo_code_created",
    "promo_code_updated",
    "promo_code_reviewed",
    "promo_course_requested",
    "promo_course_request_reviewed",
    "ml_premium_settings_updated",
    "trial_started",  # historical only — the trial feature itself is removed
]

# discount types per promo category: a Multilevel code is a percentage or 100 % free access (the Premium has one price)
CATEGORY_DISCOUNT_TYPES = {
    CATEGORY_COURSES: {"PERCENT", "FIXED", "SPECIAL_PRICE", "FREE_DAYS", "FREE_ACCESS"},
    CATEGORY_PACKAGES: {"PERCENT", "FIXED", "SPECIAL_PRICE", "FREE_ACCESS"},
    CATEGORY_MULTILEVEL: {"PERCENT", "FREE_ACCESS"},
}
# fields whose change is a new offer: the code goes back to PENDING and needs a new approval
MATERIAL_PROMO_FIELDS = {"discount_type", "discount_value", "applicable_course_ids", "applicable_package_codes", "product_category"}
REVIEW_ACTIONS = ("approve", "approve_activate", "activate", "reject", "disable")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _utc_naive(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


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
                "admin_note": order.admin_note,
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
            query = query.filter(SubscriptionOrder.plan.in_(list(offer_config.offer_codes())))
        elif kind == "multilevel":
            query = query.filter(SubscriptionOrder.plan == offer_config.ML_PREMIUM_PLAN)
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

        if order.plan == offer_config.ML_PREMIUM_PLAN:
            from . import multilevel_premium

            multilevel_premium.grant_for_order(self.db, order, actor)  # all 10 Multilevel Modelltests, unlimited
        elif offer_config.is_offer(order.plan):
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
                f"{order.plan} Multilevel Modelltest 1-10 (unlimited), {order.final_amount} {order.currency}"
                if order.plan == offer_config.ML_PREMIUM_PLAN
                else f"{order.plan} levels={','.join(offer_config.offer_levels(order.plan))}, {order.final_amount} {order.currency}"
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
            self.pay.release_promo_reservation(order)

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
        # order is no longer APPROVED); the Multilevel Premium revokes its
        # entitlement; only legacy plans touch premium_until.
        if order.plan == offer_config.ML_PREMIUM_PLAN:
            from . import multilevel_premium

            multilevel_premium.revoke_for_order(self.db, order, actor, reason)
        elif user.premium_until and not offer_config.is_offer(order.plan):
            user.premium_until = max(_now(), user.premium_until - timedelta(days=order.duration_days))

        order.status = plan_config.STATUS_REFUNDED
        order.rejection_reason = reason
        order.reviewed_by_id = actor.id
        order.reviewed_at = _now()
        achievements.on_order_status(self.db, order)  # refunded purchase: the reward can be used again
        self.pay.release_promo_reservation(order)

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

    def set_order_note(self, order_id: str, note: str | None, actor: User, ip: str | None) -> dict:
        """The Super Admin's own note on a payment request ("Izoh yozish"); never shown to the student."""
        order = self._get_order_for_review(order_id)
        text_ = (note or "").strip()
        if len(text_) > 1000:
            raise VizuPayError("Note is too long (max 1000).")
        order.admin_note = text_ or None
        self.db.commit()
        write_audit(self.db, actor_id=actor.id, action="order_note_updated", target_user_id=order.user_id,
                    details=f"order={order.id}, {len(text_)} chars", ip_address=ip)
        self.db.refresh(order)
        return self._serialize_admin_order(order)

    # ------------------------------------------------------------------
    # Promo codes
    # ------------------------------------------------------------------

    def _serialize_promo(self, promo: PromoCode) -> dict:
        applicable_course_ids = promo.applicable_course_ids or []
        applicable_package_codes = promo.applicable_package_codes or []
        category = promo.product_category or CATEGORY_COURSES
        if (category != CATEGORY_MULTILEVEL and promo.discount_type != "FREE_DAYS"
                and not applicable_course_ids and not applicable_package_codes):
            applicable_course_ids = [
                str(course_id)
                for (course_id,) in self.db.query(Course.id)
                .filter(
                    Course.is_active.is_(True),
                    Course.level.in_(
                        [code for code, config in offer_config.effective()["offers"].items() if config["kind"] == offer_config.KIND_LEVEL]
                    ),
                )
                .all()
            ]
            applicable_package_codes = [
                code for code, config in offer_config.effective()["offers"].items()
                if config["kind"] == offer_config.KIND_PACKAGE
            ]
        approved = (
            self.db.query(
                SubscriptionOrder.plan,
                func.count(SubscriptionOrder.id),
                func.coalesce(func.sum(SubscriptionOrder.promo_discount_amount), 0),
                func.coalesce(func.sum(SubscriptionOrder.final_amount), 0),
            )
            .filter(
                SubscriptionOrder.promo_code_id == promo.id,
                SubscriptionOrder.status == plan_config.STATUS_APPROVED,
            )
            .group_by(SubscriptionOrder.plan)
            .all()
        )
        now = _now()
        approval = promo.approval_status or APPROVAL_PENDING
        if approval != APPROVAL_ACTIVE:
            # PENDING / APPROVED (not switched on yet) / REJECTED / DISABLED — never usable; an expired code shows EXPIRED
            status = "EXPIRED" if approval in (APPROVAL_APPROVED, APPROVAL_DISABLED) and promo.expires_at and promo.expires_at <= now else approval
        elif promo.starts_at and promo.starts_at > now:
            status = "SCHEDULED"
        elif promo.expires_at and promo.expires_at <= now:
            status = "EXPIRED"
        elif promo.max_uses is not None and promo.used_count >= promo.max_uses:
            status = "EXHAUSTED"
        else:
            status = "ACTIVE"
        return {
            "id": str(promo.id),
            "code": promo.code,
            "campaign": promo.campaign,
            "discount_type": promo.discount_type,
            "discount_value": promo.discount_value,
            "starts_at": promo.starts_at,
            "max_uses": promo.max_uses,
            "used_count": promo.used_count,
            "max_uses_per_user": promo.max_uses_per_user,
            "applicable_course_ids": applicable_course_ids,
            "applicable_package_codes": applicable_package_codes,
            "successful_uses": sum(int(row[1]) for row in approved),
            "successful_discount_amount": sum(int(row[2]) for row in approved),
            "successful_revenue_amount": sum(int(row[3]) for row in approved),
            "remaining_uses": max(0, promo.max_uses - promo.used_count) if promo.max_uses is not None else None,
            "status": status,
            "successful_products": [
                {
                    "product_code": plan,
                    "product_name": plan_config.plan_label(plan),
                    "orders": int(count),
                    "discount_amount": int(discount),
                    "revenue_amount": int(revenue),
                }
                for plan, count, discount, revenue in approved
            ],
            "expires_at": promo.expires_at,
            "is_active": promo.is_active,
            "product_category": category,
            "approval_status": approval,
            "approved_at": promo.approved_at,
            "approved_by_email": getattr(getattr(promo, "approved_by", None), "email", None),
            "review_note": promo.review_note,
            "assigned_user_id": str(promo.assigned_user_id) if promo.assigned_user_id else None,
            "assigned_user_email": getattr(getattr(promo, "assigned_user", None), "email", None),
            "requires_approval": bool(getattr(promo, "requires_approval", False)),
            "pending_requests": self.db.query(PromoCodeRequest)
            .filter(PromoCodeRequest.promo_code_id == promo.id, PromoCodeRequest.status == REQUEST_PENDING).count(),
            "created_by_email": getattr(getattr(promo, "created_by", None), "email", None),
            "created_at": promo.created_at,
        }

    def list_promos(self) -> list[dict]:
        rows = self.db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()
        return [self._serialize_promo(p) for p in rows]

    # ------------------------------------------------------------------
    # Promo approval requests (codes with requires_approval)
    # ------------------------------------------------------------------

    def list_promo_requests(self, status: str | None = None, promo_id: str | None = None, search: str | None = None,
                            plan: str | None = None, page: int = 1, page_size: int = 20, kind: str | None = None) -> dict:
        query = self.db.query(PromoCodeRequest).join(User, PromoCodeRequest.user_id == User.id)
        if kind:
            query = query.filter(PromoCodeRequest.kind == kind)
        if status:
            query = query.filter(PromoCodeRequest.status == status)
        if promo_id:
            try:
                query = query.filter(PromoCodeRequest.promo_code_id == UUID(promo_id))
            except ValueError:
                raise NotFoundError("Promo code not found") from None
        if plan:
            query = query.filter(PromoCodeRequest.plan == plan)
        if search:
            like = f"%{search.strip()}%"
            query = query.filter(or_(User.email.ilike(like), User.username.ilike(like)))
        total = query.count()
        page, page_size = clamp_page_params(page, page_size)
        rows = query.order_by(PromoCodeRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return paginated_response([self._request_item(req) for req in rows], total, page, page_size)

    def review_promo_request(self, request_id: str, approve: bool, reason: str | None, actor: User, ip: str | None) -> dict:
        try:
            req_uuid = UUID(request_id)
        except ValueError:
            raise NotFoundError("Promo request not found") from None
        req = self.db.query(PromoCodeRequest).filter(PromoCodeRequest.id == req_uuid).with_for_update().first()
        if req is None:
            raise NotFoundError("Promo request not found")
        if (req.kind or KIND_CODE_APPROVAL) != KIND_CODE_APPROVAL:
            raise VizuPayError("Course promo requests are reviewed with /course-review.")
        if req.status != REQUEST_PENDING:
            raise VizuPayError(f"This request was already reviewed (current status: {req.status}).")
        if approve and req.promo_code is not None and (not req.promo_code.is_active or (req.promo_code.expires_at and req.promo_code.expires_at <= _now())):
            raise VizuPayError("The promo code is disabled or expired — it cannot be approved.")
        req.status = REQUEST_APPROVED if approve else REQUEST_REJECTED
        req.reason = (reason or "").strip() or None
        req.reviewed_by_id = actor.id
        req.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        write_audit(self.db, actor_id=actor.id, action="promo_request_approved" if approve else "promo_request_rejected",
                    target_user_id=req.user_id, details=f"{req.promo_code.code if req.promo_code else ''} -> {req.plan}"
                    + (f"; {req.reason}" if req.reason else ""), ip_address=ip)
        self.db.refresh(req)
        return self.pay._serialize_request(req)

    def review_course_request(self, request_id: str, approve: bool, reason: str | None, actor: User, ip: str | None, *,
                              mode: str = "create", discount_type: str | None = None, discount_value: int | None = None,
                              expires_at: datetime | None = None, promo_code_id: str | None = None) -> dict:
        """"Promo so'rovi" review (Super Admin, row-locked, audited). Reject: REJECTED with an optional reason (the student may ask again).
        Approve, mode "create": a new personal code for this student only (category of the package, scope = this package / its course,
        1 use) — approved and ACTIVE at once, because this approval IS the Super Admin's approval. Mode "attach": an existing code that is
        already approved + ACTIVE, fits the package and is not someone else's personal code. Neither buys or opens anything: the student
        still has to check out (or redeem a 100 % code)."""
        try:
            req_uuid = UUID(request_id)
        except ValueError:
            raise NotFoundError("Promo request not found") from None
        req = self.db.query(PromoCodeRequest).filter(PromoCodeRequest.id == req_uuid).with_for_update().first()
        if req is None or req.kind != KIND_COURSE_REQUEST:
            raise NotFoundError("Promo request not found")
        if req.status != REQUEST_PENDING:
            raise VizuPayError(f"This request was already reviewed (current status: {req.status}).")
        note = (reason or "").strip()[:500] or None
        now = datetime.now(timezone.utc)
        if not approve:
            req.status, req.reason, req.reviewed_by_id, req.reviewed_at = REQUEST_REJECTED, note, actor.id, now
            self.db.commit()
            write_audit(self.db, actor_id=actor.id, action="promo_course_request_reviewed", target_user_id=req.user_id,
                        details=f"{req.plan}: REJECTED" + (f"; {note}" if note else ""), ip_address=ip)
            self.db.refresh(req)
            return self._request_item(req)

        if not offer_config.is_offer(req.plan):
            raise VizuPayError("The requested package does not exist any more.")
        offer = offer_config.offer(req.plan) or {}
        is_package = offer.get("kind") == offer_config.KIND_PACKAGE
        category = CATEGORY_PACKAGES if is_package else CATEGORY_COURSES
        if mode == "attach":
            try:
                promo = self.db.query(PromoCode).filter(PromoCode.id == UUID(str(promo_code_id))).with_for_update().first()
            except ValueError:
                promo = None
            if promo is None:
                raise NotFoundError("Promo code not found")
            if promo.approval_status != APPROVAL_ACTIVE or promo.approved_at is None or not promo.is_active:
                raise VizuPayError("Only an approved, ACTIVE code can be attached.")
            if promo.assigned_user_id is not None and str(promo.assigned_user_id) != str(req.user_id):
                raise VizuPayError("This code belongs to another student.")
            if not self.pay.promo_category_fits(promo, req.plan) or (
                    (promo.applicable_course_ids or promo.applicable_package_codes) and not self.pay._promo_applies_to_plan(promo, req.plan)):
                raise VizuPayError("This code does not apply to the requested package.")
            if promo.expires_at and promo.expires_at <= _now():
                raise VizuPayError("This code has expired.")
        elif mode == "create":
            if discount_type not in ("PERCENT", "FIXED", "FREE_ACCESS"):
                raise VizuPayError("Pricing type: PERCENT, FIXED or FREE_ACCESS.")
            value = 100 if discount_type == "FREE_ACCESS" else int(discount_value or 0)
            if discount_type == "PERCENT" and not 1 <= value <= 100:
                raise VizuPayError("Percent discount must be 1–100.")
            price = offer.get("sale_price") or 0
            if discount_type == "FIXED" and not 1 <= value <= max(price, 1):
                raise VizuPayError("The fixed discount must be positive and not above the price.")
            expires = _utc_naive(expires_at)
            if expires is not None and expires <= _now():
                raise VizuPayError("The end date must be in the future.")
            course_ids = [] if is_package else [str(cid) for (cid,) in self.db.query(Course.id).filter(
                Course.level == (offer.get("levels") or [None])[0], Course.is_active.is_(True)).all()]
            if not is_package and not course_ids:
                raise VizuPayError("No active course for this level.")
            import secrets

            code = None
            for _ in range(5):
                candidate = "REQ-" + "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
                if self.db.query(PromoCode.id).filter(PromoCode.code == candidate).first() is None:
                    code = candidate
                    break
            if code is None:
                raise VizuPayError("Could not generate a unique code — try again.")
            promo = PromoCode(code=code, campaign=f"Promo so'rovi {req.plan}", discount_type=discount_type, discount_value=value,
                              applicable_course_ids=course_ids, applicable_package_codes=[req.plan] if is_package else [], max_uses=1,
                              max_uses_per_user=1, expires_at=expires, product_category=category, assigned_user_id=req.user_id,
                              approval_status=APPROVAL_ACTIVE, is_active=True, approved_by_id=actor.id, approved_at=now,
                              review_note=f"Freigegeben mit der Promo-Anfrage {req.id}", created_by_id=actor.id)
            self.db.add(promo)
            self.db.flush()
        else:
            raise VizuPayError("mode must be create or attach.")
        req.status, req.reason, req.reviewed_by_id, req.reviewed_at, req.promo_code_id = REQUEST_APPROVED, note, actor.id, now, promo.id
        self.db.commit()
        write_audit(self.db, actor_id=actor.id, action="promo_course_request_reviewed", target_user_id=req.user_id,
                    details=f"{req.plan}: APPROVED, {mode} {promo.code} ({promo.discount_type} {promo.discount_value})", ip_address=ip)
        self.db.refresh(req)
        return self._request_item(req)

    def _request_item(self, req: PromoCodeRequest) -> dict:
        item = self.pay._serialize_request(req)
        if req.promo_code is not None:
            item["code"] = req.promo_code.code  # the admin always sees the attached code
        user = req.user
        item.update({"user_id": str(req.user_id), "user_email": user.email if user else "",
                     "user_username": user.username if user else "",
                     "user_name": (" ".join(filter(None, [user.first_name, user.last_name])) or user.username) if user else "",
                     "discount_type": req.promo_code.discount_type if req.promo_code else None,
                     "discount_value": req.promo_code.discount_value if req.promo_code else None,
                     "reviewed_by_email": self.db.get(User, req.reviewed_by_id).email if req.reviewed_by_id and self.db.get(User, req.reviewed_by_id) else None})
        return item

    def discount_statistics(self) -> dict:
        """Discount figures over APPROVED orders (the same purchase rule as revenue)."""
        approved = purchases.revenue_conditions()
        total_discount, promo_discount, reward_discount, orders_with_promo = (
            self.db.query(func.coalesce(func.sum(SubscriptionOrder.discount_amount), 0),
                          func.coalesce(func.sum(SubscriptionOrder.promo_discount_amount), 0),
                          func.coalesce(func.sum(SubscriptionOrder.reward_discount_amount), 0),
                          func.count(SubscriptionOrder.promo_code_id))
            .filter(*approved).one())
        by_code = (self.db.query(SubscriptionOrder.promo_code_snapshot, func.count(SubscriptionOrder.id),
                                 func.coalesce(func.sum(SubscriptionOrder.promo_discount_amount), 0),
                                 func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
                   .filter(*approved, SubscriptionOrder.promo_code_id.isnot(None))
                   .group_by(SubscriptionOrder.promo_code_snapshot).all())
        by_plan = (self.db.query(SubscriptionOrder.plan, func.count(SubscriptionOrder.id),
                                 func.coalesce(func.sum(SubscriptionOrder.discount_amount), 0),
                                 func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))
                   .filter(*approved).group_by(SubscriptionOrder.plan).all())
        requests = dict(self.db.query(PromoCodeRequest.status, func.count(PromoCodeRequest.id)).group_by(PromoCodeRequest.status).all())
        return {
            "total_discount": int(total_discount), "promo_discount": int(promo_discount), "reward_discount": int(reward_discount),
            "orders_with_promo": int(orders_with_promo),
            "requests": {k: int(requests.get(k, 0)) for k in (REQUEST_PENDING, REQUEST_APPROVED, REQUEST_REJECTED, REQUEST_USED)},
            "by_code": sorted(({"code": c or "", "orders": int(n), "discount": int(d), "revenue": int(r)} for c, n, d, r in by_code),
                              key=lambda x: -x["discount"]),
            "by_package": sorted(({"plan": p, "label": plan_config.plan_label(p), "orders": int(n), "discount": int(d), "revenue": int(r)}
                                  for p, n, d, r in by_plan), key=lambda x: -x["revenue"]),
        }

    def list_promo_orders(self, promo_id: str, page: int = 1, page_size: int = 20, search: str | None = None,
                          plan: str | None = None) -> dict:
        try:
            promo_uuid = UUID(promo_id)
        except (ValueError, TypeError, AttributeError):
            raise NotFoundError("Promo code not found") from None
        if self.db.get(PromoCode, promo_uuid) is None:
            raise NotFoundError("Promo code not found")

        query = (
            self.db.query(SubscriptionOrder, User)
            .join(User, SubscriptionOrder.user_id == User.id)
            .filter(SubscriptionOrder.promo_code_id == promo_uuid)
        )
        if plan:
            query = query.filter(SubscriptionOrder.plan == plan)
        if search:
            like = f"%{search.strip()}%"
            query = query.filter(or_(User.email.ilike(like), User.username.ilike(like)))
        total = query.count()
        page, page_size = clamp_page_params(page, page_size)
        rows = (
            query.order_by(SubscriptionOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return paginated_response(
            [
                {
                    "id": str(order.id),
                    "promo_code": order.promo_code_snapshot or "",
                    "product_code": order.plan,
                    "product_name": plan_config.plan_label(order.plan),
                    "base_amount": order.base_amount,
                    "discount_amount": order.promo_discount_amount,
                    "final_amount": order.final_amount,
                    "status": order.status,
                    "user_id": str(order.user_id),
                    "user_email": user.email,
                    "user_name": " ".join(filter(None, [user.first_name, user.last_name])) or user.username,
                    "created_at": order.created_at,
                    "reviewed_at": order.reviewed_at,
                }
                for order, user in rows
            ],
            total,
            page,
            page_size,
        )

    def promo_products(self) -> dict:
        level_codes = [
            code for code, cfg in offer_config.effective()["offers"].items()
            if cfg["kind"] == offer_config.KIND_LEVEL
        ]
        courses = (
            self.db.query(Course)
            .filter(Course.is_active.is_(True), Course.level.in_(level_codes))
            .order_by(Course.level, Course.title)
            .all()
        )
        packages = [
            {"code": offer["code"], "label": offer["label"]}
            for offer in offer_config.list_offers()
            if offer["kind"] == offer_config.KIND_PACKAGE
        ]
        from . import multilevel_premium

        ml = multilevel_premium.product(self.db)
        return {
            "courses": [
                {"id": str(course.id), "title": course.title, "level": course.level}
                for course in courses
            ],
            "packages": packages,
            "multilevel": {"code": ml["code"], "label": ml["label"], "price": ml["price"]},
        }

    def payments_overview(self) -> dict:
        """Admin -> Payments -> Overview: every figure counted from subscription_orders / user_entitlements / promo tables (no cache)."""
        from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, SOURCE_PROMO, UserEntitlement

        by_status = dict(self.db.query(SubscriptionOrder.status, func.count(SubscriptionOrder.id)).group_by(SubscriptionOrder.status).all())
        ml = offer_config.ML_PREMIUM_PLAN
        paid = SubscriptionOrder.gateway != "promo"
        course_purchases, course_buyers = purchases.course_purchase_totals(self.db)
        ml_paid = self.db.query(func.count(SubscriptionOrder.id)).filter(
            SubscriptionOrder.plan == ml, SubscriptionOrder.status == plan_config.STATUS_APPROVED, paid).scalar() or 0
        ml_pending = self.db.query(func.count(SubscriptionOrder.id)).filter(
            SubscriptionOrder.plan == ml, SubscriptionOrder.status == plan_config.STATUS_PENDING).scalar() or 0
        course_pending = self.db.query(func.count(SubscriptionOrder.id)).filter(
            SubscriptionOrder.plan != ml, SubscriptionOrder.status == plan_config.STATUS_PENDING).scalar() or 0
        ml_active = self.db.query(func.count(UserEntitlement.id)).filter(
            UserEntitlement.product == PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement.revoked_at.is_(None)).scalar() or 0
        promo_course = self.db.query(func.count(SubscriptionOrder.id)).filter(
            SubscriptionOrder.plan != ml, SubscriptionOrder.status == plan_config.STATUS_APPROVED, SubscriptionOrder.gateway == "promo").scalar() or 0
        promo_ml = self.db.query(func.count(UserEntitlement.id)).filter(
            UserEntitlement.product == PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement.source == SOURCE_PROMO).scalar() or 0
        revenue = lambda *flt: int(self.db.query(func.coalesce(func.sum(SubscriptionOrder.final_amount), 0))  # noqa: E731
                                   .filter(*purchases.revenue_conditions(), *flt).scalar() or 0)
        promo_status = dict(self.db.query(PromoCode.approval_status, func.count(PromoCode.id)).group_by(PromoCode.approval_status).all())
        open_requests = dict(self.db.query(PromoCodeRequest.kind, func.count(PromoCodeRequest.id))
                             .filter(PromoCodeRequest.status == REQUEST_PENDING).group_by(PromoCodeRequest.kind).all())
        return {
            "payments": {"total": int(sum(by_status.values())), **{s.lower(): int(by_status.get(s, 0)) for s in (
                plan_config.STATUS_APPROVED, plan_config.STATUS_PENDING, plan_config.STATUS_REJECTED, plan_config.STATUS_EXPIRED,
                plan_config.STATUS_REFUNDED)}},
            "pending": {"course": int(course_pending), "multilevel": int(ml_pending)},
            "course_purchases": course_purchases,
            "course_buyers": course_buyers,
            "multilevel_purchases": int(ml_paid),
            "multilevel_active": int(ml_active),
            "promo_accesses": {"course": int(promo_course), "multilevel": int(promo_ml), "total": int(promo_course + promo_ml)},
            "revenue": {"total": revenue(), "multilevel": revenue(SubscriptionOrder.plan == ml),
                        "course": revenue(SubscriptionOrder.plan.in_(list(offer_config.offer_codes())))},
            "promo_codes": {s: int(promo_status.get(s, 0)) for s in (APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_ACTIVE, APPROVAL_REJECTED,
                                                                     APPROVAL_DISABLED)},
            "promo_requests_open": {"code_approval": int(open_requests.get(KIND_CODE_APPROVAL, 0)),
                                    "course_request": int(open_requests.get(KIND_COURSE_REQUEST, 0))},
        }

    def _validate_promo_fields(
        self,
        discount_type: str,
        discount_value: int,
        course_ids: list[str],
        package_codes: list[str],
        max_uses: int | None,
        max_uses_per_user: int,
        starts_at: datetime | None,
        expires_at: datetime | None,
        allow_unscoped: bool = False,
        category: str = CATEGORY_COURSES,
    ) -> tuple[list[str], list[str]]:
        starts_at = _utc_naive(starts_at)
        expires_at = _utc_naive(expires_at)
        if category not in CATEGORIES:
            raise VizuPayError("Invalid product category (COURSES, PACKAGES or MULTILEVEL).")
        if discount_type not in {"PERCENT", "FIXED", "SPECIAL_PRICE", "FREE_DAYS", "FREE_ACCESS"}:
            raise VizuPayError("Invalid promo pricing type.")
        if discount_type not in CATEGORY_DISCOUNT_TYPES[category]:
            raise VizuPayError("This pricing type is not available for the selected product category.")
        if category == CATEGORY_MULTILEVEL:
            # the Multilevel Premium is one product: no course / package scope
            if course_ids or package_codes:
                raise VizuPayError("A Multilevel Modelltest code cannot name courses or packages.")
            if discount_value < 0 or (discount_type == "PERCENT" and not 1 <= discount_value <= 100):
                raise VizuPayError("Percent discount must be 1–100.")
            if max_uses is not None and max_uses < 1:
                raise VizuPayError("Maximum uses must be positive.")
            if max_uses_per_user < 1:
                raise VizuPayError("Per-user maximum uses must be positive.")
            if starts_at and expires_at and starts_at >= expires_at:
                raise VizuPayError("Promo start date must be before its expiry date.")
            return [], []
        if category == CATEGORY_COURSES and package_codes:
            raise VizuPayError("A course code cannot name packages — use the category PACKAGES.")
        if category == CATEGORY_PACKAGES and course_ids:
            raise VizuPayError("A package code cannot name single courses — use the category COURSES.")
        if discount_value < 0 or (discount_type != "SPECIAL_PRICE" and discount_value == 0):
            raise VizuPayError("Promo value must be positive (special price may be zero).")
        if discount_type == "PERCENT" and discount_value > 100:
            raise VizuPayError("Percent discount cannot exceed 100.")
        if discount_type == "FREE_DAYS" and discount_value > 365:
            raise VizuPayError("A promo code can't grant more than 365 days at once.")
        if max_uses is not None and max_uses < 1:
            raise VizuPayError("Maximum uses must be positive.")
        if max_uses_per_user < 1:
            raise VizuPayError("Per-user maximum uses must be positive.")
        if starts_at and expires_at and starts_at >= expires_at:
            raise VizuPayError("Promo start date must be before its expiry date.")

        valid_packages = {
            code for code, cfg in offer_config.effective()["offers"].items()
            if cfg["kind"] == offer_config.KIND_PACKAGE
        }
        if len(set(package_codes)) != len(package_codes) or any(code not in valid_packages for code in package_codes):
            raise VizuPayError("One or more package identifiers are invalid.")

        try:
            normalized_ids = [str(UUID(course_id)) for course_id in course_ids]
        except (ValueError, TypeError, AttributeError):
            raise VizuPayError("One or more course identifiers are invalid.") from None
        if len(set(normalized_ids)) != len(normalized_ids):
            raise VizuPayError("Course identifiers must be unique.")
        selected_levels = set()
        if normalized_ids:
            allowed_levels = {
                code for code, config in offer_config.effective()["offers"].items()
                if config["kind"] == offer_config.KIND_LEVEL
            }
            selected_courses = (
                self.db.query(Course.id, Course.level)
                .filter(
                    Course.id.in_(normalized_ids),
                    Course.is_active.is_(True),
                    Course.level.in_(allowed_levels),
                )
                .all()
            )
            found = {str(course_id) for course_id, _ in selected_courses}
            if found != set(normalized_ids):
                raise VizuPayError("Select active courses from the current catalog.")
            selected_levels = {level for _, level in selected_courses}
        if discount_type == "FREE_DAYS":
            if normalized_ids or package_codes:
                raise VizuPayError("Premium-day codes cannot have course or package targets.")
        elif not normalized_ids and not package_codes and (not allow_unscoped or discount_type == "FREE_ACCESS"):
            raise VizuPayError("Select at least one course or package.")
        if discount_type == "SPECIAL_PRICE":
            for product_code in selected_levels | set(package_codes):
                product = offer_config.offer(product_code)
                reference_price = product["sale_price"] or product["original_price"]
                if reference_price is not None and discount_value > reference_price:
                    raise VizuPayError(f"Special price cannot exceed {product_code}'s current configured price.")
        return normalized_ids, package_codes

    def create_promo(
        self,
        code: str,
        campaign: str | None,
        discount_type: str,
        discount_value: int,
        applicable_course_ids: list[str],
        applicable_package_codes: list[str],
        starts_at: datetime | None,
        max_uses: int | None,
        max_uses_per_user: int,
        expires_at: datetime | None,
        actor: User,
        is_active: bool = True,
        requires_approval: bool = False,
        product_category: str = CATEGORY_COURSES,
        assigned_user_id=None,
        ip: str | None = None,
    ) -> dict:
        """A new code always starts PENDING (not usable) — `is_active` is ignored: only review_promo (approve, then activate) makes a code
        work. Kept in the signature for older clients."""
        code = code.strip().upper()
        if requires_approval and (discount_type not in {"PERCENT", "FIXED", "SPECIAL_PRICE"} or product_category == CATEGORY_MULTILEVEL):
            raise VizuPayError("Approval can only be required for course checkout discounts (percent, fixed, special price).")
        if not code or len(code) > 40 or not all(char.isalnum() or char in "-_" for char in code):
            raise VizuPayError("Code must contain only letters, numbers, hyphens, or underscores (max 40).")
        if campaign and len(campaign) > 120:
            raise VizuPayError("Campaign name is too long.")
        course_ids, package_codes = self._validate_promo_fields(
            discount_type, discount_value, applicable_course_ids, applicable_package_codes,
            max_uses, max_uses_per_user, starts_at, expires_at, category=product_category,
        )
        starts_at = _utc_naive(starts_at)
        expires_at = _utc_naive(expires_at)
        if discount_type == "FREE_ACCESS":
            discount_value = 100  # full waiver; the stored value is not client-controlled

        existing =self.db.query(PromoCode).filter(PromoCode.code == code).first()
        if existing:
            raise VizuPayError("A promo code with this code already exists.")

        promo = PromoCode(
            code=code,
            campaign=campaign,
            discount_type=discount_type,
            discount_value=discount_value,
            applicable_course_ids=course_ids,
            applicable_package_codes=package_codes,
            starts_at=starts_at,
            max_uses=max_uses,
            max_uses_per_user=max_uses_per_user,
            expires_at=expires_at,
            is_active=False,
            approval_status=APPROVAL_PENDING,
            product_category=product_category,
            assigned_user_id=assigned_user_id,
            requires_approval=requires_approval,
            created_by_id=actor.id,
        )
        self.db.add(promo)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise VizuPayError("A promo code with this code already exists.") from None
        self.db.refresh(promo)

        write_audit(self.db, actor_id=actor.id, action="promo_code_created", details=f"{code} [{product_category}] -> PENDING", ip_address=ip)

        return self._serialize_promo(promo)

    def review_promo(self, promo_id: str, action: str, note: str | None, actor: User, ip: str | None) -> dict:
        """The approval of a promo code (Super Admin, row-locked, audited):
        approve PENDING -> APPROVED; approve_activate PENDING -> ACTIVE; activate APPROVED / DISABLED (approved before) -> ACTIVE;
        reject PENDING / APPROVED -> REJECTED; disable ACTIVE / APPROVED -> DISABLED. Only ACTIVE codes work."""
        if action not in REVIEW_ACTIONS:
            raise VizuPayError("Unknown review action.")
        try:
            promo_uuid = UUID(promo_id)
        except ValueError:
            raise NotFoundError("Promo code not found") from None
        promo = self.db.query(PromoCode).filter(PromoCode.id == promo_uuid).with_for_update().first()
        if promo is None:
            raise NotFoundError("Promo code not found")
        current = promo.approval_status or APPROVAL_PENDING
        allowed = {
            "approve": {APPROVAL_PENDING},
            "approve_activate": {APPROVAL_PENDING},
            "activate": {APPROVAL_APPROVED, APPROVAL_DISABLED},
            "reject": {APPROVAL_PENDING, APPROVAL_APPROVED},
            "disable": {APPROVAL_ACTIVE, APPROVAL_APPROVED},
        }[action]
        if current not in allowed:
            raise VizuPayError(f"Not possible for a code in status {current}.")
        if action == "activate" and promo.approved_at is None:
            raise VizuPayError("The code was never approved — approve it first.")
        if action in ("approve_activate", "activate") and promo.expires_at and promo.expires_at <= _now():
            raise VizuPayError("The code has expired — change the end date first.")
        now = datetime.now(timezone.utc)
        if action in ("approve", "approve_activate"):
            promo.approved_by_id, promo.approved_at = actor.id, now
        promo.approval_status = {"approve": APPROVAL_APPROVED, "approve_activate": APPROVAL_ACTIVE, "activate": APPROVAL_ACTIVE,
                                 "reject": APPROVAL_REJECTED, "disable": APPROVAL_DISABLED}[action]
        promo.is_active = promo.approval_status == APPROVAL_ACTIVE
        text_ = (note or "").strip()
        if text_:
            promo.review_note = text_[:500]
        self.db.commit()
        write_audit(self.db, actor_id=actor.id, action="promo_code_reviewed",
                    details=f"{promo.code}: {current} -> {promo.approval_status}" + (f"; {text_[:200]}" if text_ else ""), ip_address=ip)
        self.db.refresh(promo)
        return self._serialize_promo(promo)

    def update_promo(
        self,
        promo_id: str,
        changes: dict,
        actor: User,
    ) -> dict:
        try:
            promo_uuid = UUID(promo_id)
        except ValueError:
            raise NotFoundError("Promo code not found") from None
        promo = self.db.query(PromoCode).filter(PromoCode.id == promo_uuid).with_for_update().first()
        if promo is None:
            raise NotFoundError("Promo code not found")
        for required_field in (
            "code",
            "discount_type",
            "discount_value",
            "applicable_course_ids",
            "applicable_package_codes",
            "max_uses_per_user",
        ):
            if required_field in changes and changes[required_field] is None:
                raise VizuPayError(f"{required_field} cannot be null.")

        updated_type = changes.get("discount_type", promo.discount_type)
        updated_value = changes.get("discount_value", promo.discount_value)
        category = changes.get("product_category") or promo.product_category or CATEGORY_COURSES
        course_ids = changes.get("applicable_course_ids", promo.applicable_course_ids or [])
        package_codes = changes.get("applicable_package_codes", promo.applicable_package_codes or [])
        starts_at = changes.get("starts_at", promo.starts_at)
        expires_at = changes.get("expires_at", promo.expires_at)
        max_uses = changes.get("max_uses", promo.max_uses)
        max_uses_per_user = changes.get("max_uses_per_user", promo.max_uses_per_user)
        safe_legacy_edit = (
            not course_ids
            and not package_codes
            and "applicable_course_ids" not in changes
            and "applicable_package_codes" not in changes
            and set(changes).issubset(
                {"code", "campaign", "starts_at", "expires_at", "max_uses", "max_uses_per_user", "is_active", "requires_approval"}
            )
        )
        course_ids, package_codes = self._validate_promo_fields(
            updated_type, updated_value, course_ids, package_codes,
            max_uses, max_uses_per_user, starts_at, expires_at, allow_unscoped=safe_legacy_edit, category=category,
        )
        # a changed offer (type, value, category, scope) is a new code from the approval's point of view
        material = any(field in changes and changes[field] != getattr(promo, field) for field in MATERIAL_PROMO_FIELDS)
        starts_at = _utc_naive(starts_at)
        expires_at = _utc_naive(expires_at)
        if updated_type == "FREE_ACCESS":
            updated_value = 100
        if max_uses is not None and max_uses < promo.used_count:
            raise VizuPayError("Maximum uses cannot be lower than existing uses or pending reservations.")

        code = changes.get("code", promo.code)
        code = code.strip().upper()
        if not code or len(code) > 40 or not all(char.isalnum() or char in "-_" for char in code):
            raise VizuPayError("Code must contain only letters, numbers, hyphens, or underscores (max 40).")
        campaign = changes.get("campaign", promo.campaign)
        if campaign and len(campaign) > 120:
            raise VizuPayError("Campaign name is too long.")

        before_status = promo.approval_status or APPROVAL_PENDING
        if changes.get("is_active") is True and not material and (
                before_status not in (APPROVAL_ACTIVE, APPROVAL_APPROVED, APPROVAL_DISABLED) or promo.approved_at is None):
            raise VizuPayError("PROMO_NOT_APPROVED: Der Code muss zuerst freigegeben werden.")

        promo.code = code
        promo.campaign = campaign
        promo.discount_type = updated_type
        promo.discount_value = updated_value
        promo.product_category = category
        promo.applicable_course_ids = course_ids
        promo.applicable_package_codes = package_codes
        promo.starts_at = starts_at
        promo.expires_at = expires_at
        promo.max_uses = max_uses
        promo.max_uses_per_user = max_uses_per_user
        if material:
            promo.approval_status, promo.approved_at, promo.approved_by_id = APPROVAL_PENDING, None, None
            promo.is_active = False
        elif changes.get("is_active") is True:
            promo.approval_status, promo.is_active = APPROVAL_ACTIVE, True
        elif changes.get("is_active") is False and before_status in (APPROVAL_ACTIVE, APPROVAL_APPROVED):
            promo.approval_status, promo.is_active = APPROVAL_DISABLED, False
        if changes.get("requires_approval") is not None:
            if changes["requires_approval"] and (updated_type not in {"PERCENT", "FIXED", "SPECIAL_PRICE"} or category == CATEGORY_MULTILEVEL):
                raise VizuPayError("Approval can only be required for course checkout discounts (percent, fixed, special price).")
            promo.requires_approval = changes["requires_approval"]

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise VizuPayError("A promo code with this code already exists.") from None
        self.db.refresh(promo)

        write_audit(
            self.db, actor_id=actor.id, action="promo_code_updated",
            details=f"{promo.code}; fields={','.join(sorted(changes))}; {before_status} -> {promo.approval_status}",
        )

        return self._serialize_promo(promo)

    def delete_promo(self, promo_id: str, actor: User) -> None:
        promo = self.db.get(PromoCode, UUID(promo_id))
        if promo is None:
            raise NotFoundError("Promo code not found")
        if promo.used_count > 0 or self.db.query(SubscriptionOrder).filter(SubscriptionOrder.promo_code_id == promo.id).count():
            raise VizuPayError("Cannot delete a promo code that has been used. Deactivate it instead.")
        if self.db.query(PromoCodeRequest).filter(PromoCodeRequest.promo_code_id == promo.id).count():
            raise VizuPayError("Cannot delete a promo code with approval requests. Deactivate it instead.")

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
