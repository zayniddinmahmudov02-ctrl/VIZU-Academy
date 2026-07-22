import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.pagination import clamp_page_params, paginated_response
from app.core.storage.factory import StorageFactory
from app.models.promo_code import PromoCode
from app.models.promo_code_redemption import PromoCodeRedemption
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User

from . import plans as plan_config

ALLOWED_PROOF_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_PROOF_SIZE_BYTES = 10 * 1024 * 1024

# Extension is client-supplied and trivially spoofable (rename a .exe to
# .png) — sniff the real file signature and cross-check it against the
# claimed extension before trusting either.
_EXTENSION_KIND = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
    ".webp": "webp",
    ".pdf": "pdf",
}


def _sniff_file_kind(contents: bytes) -> str | None:
    if contents.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return "webp"
    if contents.startswith(b"%PDF"):
        return "pdf"
    return None


class VizuPayError(DomainError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VizuPayService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = StorageFactory.create(settings.STORAGE_PROVIDER)

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    def list_plans(self) -> list[dict]:
        return [
            {
                "plan": plan,
                "label": cfg["label"],
                "days": cfg["days"],
                "price": cfg["price"],
                "currency": "UZS",
            }
            for plan, cfg in plan_config.PLAN_CONFIG.items()
            if plan in plan_config.PAID_PLANS
        ]

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _sweep_expired(self, user_id: UUID) -> None:
        now = _now()
        expired = (
            self.db.query(SubscriptionOrder)
            .filter(
                SubscriptionOrder.user_id == user_id,
                SubscriptionOrder.status == plan_config.STATUS_PENDING,
                SubscriptionOrder.expires_at.isnot(None),
                SubscriptionOrder.expires_at <= now,
            )
            .all()
        )
        for order in expired:
            order.status = plan_config.STATUS_EXPIRED
        if expired:
            self.db.commit()

    def get_my_status(self, user: User) -> dict:
        self._sweep_expired(user.id)

        now = _now()
        is_premium = bool(user.premium_until and user.premium_until > now)

        has_paid_approval = (
            self.db.query(SubscriptionOrder)
            .filter(
                SubscriptionOrder.user_id == user.id,
                SubscriptionOrder.status == plan_config.STATUS_APPROVED,
                SubscriptionOrder.plan.in_(list(plan_config.PAID_PLANS)),
            )
            .first()
            is not None
        )

        is_trial = is_premium and user.trial_used_at is not None and not has_paid_approval

        trial_days_remaining = None
        if is_trial and user.premium_until:
            trial_days_remaining = max(math.ceil((user.premium_until - now).total_seconds() / 86400), 0)

        has_pending_order = (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.user_id == user.id, SubscriptionOrder.status == plan_config.STATUS_PENDING)
            .first()
            is not None
        )

        return {
            "is_premium": is_premium,
            "premium_until": user.premium_until,
            "is_trial": is_trial,
            "trial_available": user.trial_used_at is None,
            "trial_days_remaining": trial_days_remaining,
            "has_pending_order": has_pending_order,
        }

    # ------------------------------------------------------------------
    # Trial
    # ------------------------------------------------------------------

    def activate_trial(self, user: User, ip: str | None) -> dict:
        if user.trial_used_at is not None:
            raise VizuPayError("Trial already used for this account.")

        now = _now()
        base = user.premium_until if (user.premium_until and user.premium_until > now) else now

        user.trial_used_at = now
        user.premium_until = base + timedelta(days=plan_config.plan_days(plan_config.PLAN_TRIAL))

        order = SubscriptionOrder(
            user_id=user.id,
            plan=plan_config.PLAN_TRIAL,
            duration_days=plan_config.plan_days(plan_config.PLAN_TRIAL),
            base_amount=0,
            discount_amount=0,
            final_amount=0,
            currency="UZS",
            payment_method=plan_config.PAYMENT_METHOD_TRIAL,
            status=plan_config.STATUS_APPROVED,
            reviewed_at=now,
            gateway="manual",
        )
        self.db.add(order)
        self.db.commit()

        write_audit(self.db, actor_id=user.id, action="trial_started", target_user_id=user.id, ip_address=ip)

        return {"premium_until": user.premium_until}

    # ------------------------------------------------------------------
    # Promo validation
    # ------------------------------------------------------------------

    def _find_promo(self, code: str) -> PromoCode | None:
        return (
            self.db.query(PromoCode)
            .filter(PromoCode.code == code.strip().upper())
            .first()
        )

    def _check_promo(self, promo: PromoCode | None, user: User) -> str | None:
        """Returns an error message if the promo can't be applied, else None."""
        if promo is None:
            return "Promo code not found."
        if not promo.is_active:
            return "Promo code is no longer active."
        if promo.expires_at and promo.expires_at <= _now():
            return "Promo code has expired."
        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            return "Promo code usage limit reached."
        already_redeemed = (
            self.db.query(PromoCodeRedemption)
            .filter(PromoCodeRedemption.promo_code_id == promo.id, PromoCodeRedemption.user_id == user.id)
            .first()
        )
        if already_redeemed:
            return "You have already used this promo code."
        return None

    def validate_promo(self, code: str, user: User) -> dict:
        promo = self._find_promo(code)
        error = self._check_promo(promo, user)
        if error:
            return {"valid": False, "discount_type": None, "discount_value": None, "message": error}
        return {"valid": True, "discount_type": promo.discount_type, "discount_value": promo.discount_value, "message": None}

    def _apply_discount(self, base_amount: int, promo: PromoCode) -> int:
        if promo.discount_type == "PERCENT":
            return min(base_amount * promo.discount_value // 100, base_amount)
        return min(promo.discount_value, base_amount)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def _build_proof_path(self, order_id: UUID, file: UploadFile, contents: bytes) -> tuple[str, str]:
        extension = Path(file.filename or "").suffix.lower()
        if extension not in ALLOWED_PROOF_EXTENSIONS:
            raise VizuPayError(f"Unsupported proof file type: {extension or 'unknown'}")

        claimed_kind = _EXTENSION_KIND[extension]
        actual_kind = _sniff_file_kind(contents)

        if actual_kind is None or actual_kind != claimed_kind:
            raise VizuPayError(
                "File content doesn't match its extension — upload a real screenshot or PDF."
            )

        proof_type = "pdf" if extension == ".pdf" else "image"
        filename = f"{order_id}_{uuid4().hex[:8]}{extension}"
        path = f"payment-proofs/{filename}"

        return path, proof_type

    async def create_order(
        self,
        user: User,
        plan: str,
        payment_method: str,
        promo_code: str | None,
        proof_file: UploadFile,
        ip: str | None,
    ) -> dict:
        if plan not in plan_config.PAID_PLANS:
            raise VizuPayError("Invalid plan.")
        if payment_method not in plan_config.PAYMENT_METHODS:
            raise VizuPayError("Invalid payment method.")

        contents = await proof_file.read()
        if len(contents) == 0:
            raise VizuPayError("Payment proof file is empty.")
        if len(contents) > MAX_PROOF_SIZE_BYTES:
            raise VizuPayError("Payment proof file is too large (max 10MB).")
        await proof_file.seek(0)

        base_amount = plan_config.plan_price(plan)
        discount_amount = 0
        promo: PromoCode | None = None

        if promo_code:
            promo = self._find_promo(promo_code)
            error = self._check_promo(promo, user)
            if error:
                raise VizuPayError(error)
            discount_amount = self._apply_discount(base_amount, promo)

        final_amount = max(base_amount - discount_amount, 0)

        order_id = uuid4()
        proof_path, proof_type = self._build_proof_path(order_id, proof_file, contents)

        await self.storage.upload(proof_file, proof_path)
        proof_url = self.storage.url(proof_path)

        order = SubscriptionOrder(
            id=order_id,
            user_id=user.id,
            plan=plan,
            duration_days=plan_config.plan_days(plan),
            base_amount=base_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            currency="UZS",
            payment_method=payment_method,
            status=plan_config.STATUS_PENDING,
            proof_url=proof_url,
            proof_type=proof_type,
            promo_code_id=promo.id if promo else None,
            gateway="manual",
            expires_at=_now() + timedelta(days=plan_config.ORDER_REVIEW_WINDOW_DAYS),
        )
        self.db.add(order)
        self.db.flush()

        if promo:
            promo.used_count += 1
            self.db.add(PromoCodeRedemption(promo_code_id=promo.id, user_id=user.id, order_id=order_id))

        self.db.commit()
        self.db.refresh(order)

        write_audit(
            self.db,
            actor_id=user.id,
            action="order_created",
            target_user_id=user.id,
            details=f"{plan} via {payment_method}, final={final_amount} UZS",
            ip_address=ip,
        )

        return self.serialize_order(order)

    def serialize_order(self, order: SubscriptionOrder) -> dict:
        return {
            "id": str(order.id),
            "plan": order.plan,
            "plan_label": plan_config.plan_label(order.plan),
            "duration_days": order.duration_days,
            "base_amount": order.base_amount,
            "discount_amount": order.discount_amount,
            "final_amount": order.final_amount,
            "currency": order.currency,
            "payment_method": order.payment_method,
            "status": order.status,
            "proof_url": order.proof_url,
            "proof_type": order.proof_type,
            "promo_code": order.promo_code.code if order.promo_code else None,
            "rejection_reason": order.rejection_reason,
            "expires_at": order.expires_at,
            "reviewed_at": order.reviewed_at,
            "created_at": order.created_at,
        }

    def get_my_orders(self, user: User, page: int = 1, page_size: int = 20) -> dict:
        self._sweep_expired(user.id)

        query = (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.user_id == user.id)
            .order_by(SubscriptionOrder.created_at.desc())
        )

        total = query.count()
        page, page_size = clamp_page_params(page, page_size)

        rows = query.offset((page - 1) * page_size).limit(page_size).all()

        return paginated_response([self.serialize_order(o) for o in rows], total, page, page_size)
