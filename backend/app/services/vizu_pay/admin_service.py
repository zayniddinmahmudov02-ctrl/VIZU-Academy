from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import extract, func, literal_column, or_
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.exceptions import NotFoundError
from app.core.pagination import clamp_page_params, paginated_response
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.promo_code import PromoCode
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
    "promo_redeemed",
    "trial_started",  # historical only — the trial feature itself is removed
]


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
        # order is no longer APPROVED); only legacy plans touch premium_until.
        if user.premium_until and not offer_config.is_offer(order.plan):
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

    # ------------------------------------------------------------------
    # Promo codes
    # ------------------------------------------------------------------

    def _serialize_promo(self, promo: PromoCode) -> dict:
        applicable_course_ids = promo.applicable_course_ids or []
        applicable_package_codes = promo.applicable_package_codes or []
        if promo.discount_type != "FREE_DAYS" and not applicable_course_ids and not applicable_package_codes:
            applicable_course_ids = [
                str(course_id)
                for (course_id,) in self.db.query(Course.id)
                .filter(
                    Course.is_active.is_(True),
                    Course.level.in_(
                        [code for code, config in offer_config.OFFERS.items() if config["kind"] == offer_config.KIND_LEVEL]
                    ),
                )
                .all()
            ]
            applicable_package_codes = [
                code for code, config in offer_config.OFFERS.items()
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
        if not promo.is_active:
            status = "INACTIVE"
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
            "created_at": promo.created_at,
        }

    def list_promos(self) -> list[dict]:
        rows = self.db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()
        return [self._serialize_promo(p) for p in rows]

    def list_promo_orders(self, promo_id: str, page: int = 1, page_size: int = 20) -> dict:
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
            code for code, cfg in offer_config.OFFERS.items()
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
        return {
            "courses": [
                {"id": str(course.id), "title": course.title, "level": course.level}
                for course in courses
            ],
            "packages": packages,
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
    ) -> tuple[list[str], list[str]]:
        starts_at = _utc_naive(starts_at)
        expires_at = _utc_naive(expires_at)
        if discount_type not in {"PERCENT", "FIXED", "SPECIAL_PRICE", "FREE_DAYS"}:
            raise VizuPayError("Invalid promo pricing type.")
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
            code for code, cfg in offer_config.OFFERS.items()
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
                code for code, config in offer_config.OFFERS.items()
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
        elif not normalized_ids and not package_codes and not allow_unscoped:
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
    ) -> dict:
        code = code.strip().upper()
        if not code or len(code) > 40 or not all(char.isalnum() or char in "-_" for char in code):
            raise VizuPayError("Code must contain only letters, numbers, hyphens, or underscores (max 40).")
        if campaign and len(campaign) > 120:
            raise VizuPayError("Campaign name is too long.")
        course_ids, package_codes = self._validate_promo_fields(
            discount_type, discount_value, applicable_course_ids, applicable_package_codes,
            max_uses, max_uses_per_user, starts_at, expires_at,
        )
        starts_at = _utc_naive(starts_at)
        expires_at = _utc_naive(expires_at)

        existing = self.db.query(PromoCode).filter(PromoCode.code == code).first()
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
            is_active=is_active,
            created_by_id=actor.id,
        )
        self.db.add(promo)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise VizuPayError("A promo code with this code already exists.") from None
        self.db.refresh(promo)

        write_audit(self.db, actor_id=actor.id, action="promo_code_created", details=code)

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
                {"code", "campaign", "starts_at", "expires_at", "max_uses", "max_uses_per_user", "is_active"}
            )
        )
        course_ids, package_codes = self._validate_promo_fields(
            updated_type, updated_value, course_ids, package_codes,
            max_uses, max_uses_per_user, starts_at, expires_at, allow_unscoped=safe_legacy_edit,
        )
        starts_at = _utc_naive(starts_at)
        expires_at = _utc_naive(expires_at)
        if max_uses is not None and max_uses < promo.used_count:
            raise VizuPayError("Maximum uses cannot be lower than existing uses or pending reservations.")

        code = changes.get("code", promo.code)
        code = code.strip().upper()
        if not code or len(code) > 40 or not all(char.isalnum() or char in "-_" for char in code):
            raise VizuPayError("Code must contain only letters, numbers, hyphens, or underscores (max 40).")
        campaign = changes.get("campaign", promo.campaign)
        if campaign and len(campaign) > 120:
            raise VizuPayError("Campaign name is too long.")

        promo.code = code
        promo.campaign = campaign
        promo.discount_type = updated_type
        promo.discount_value = updated_value
        promo.applicable_course_ids = course_ids
        promo.applicable_package_codes = package_codes
        promo.starts_at = starts_at
        promo.expires_at = expires_at
        promo.max_uses = max_uses
        promo.max_uses_per_user = max_uses_per_user
        if "is_active" in changes:
            promo.is_active = changes["is_active"]

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise VizuPayError("A promo code with this code already exists.") from None
        self.db.refresh(promo)

        write_audit(
            self.db, actor_id=actor.id, action="promo_code_updated",
            details=f"{promo.code}; fields={','.join(sorted(changes))}",
        )

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
