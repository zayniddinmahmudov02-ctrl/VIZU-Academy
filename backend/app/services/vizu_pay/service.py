from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.exceptions import DomainError
from app.core.pagination import clamp_page_params, paginated_response
from app.core.security.roles import UserRole
from app.core.storage.protected_local import ProtectedPaymentProofStorage
from app.models.promo_code import PromoCode
from app.models.promo_code_redemption import PromoCodeRedemption
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User

from . import plans as plan_config

DISCOUNT_TYPES_AT_CHECKOUT = {"PERCENT", "FIXED"}
DISCOUNT_TYPE_FREE_DAYS = "FREE_DAYS"
ALL_DISCOUNT_TYPES = DISCOUNT_TYPES_AT_CHECKOUT | {DISCOUNT_TYPE_FREE_DAYS}

_PROOF_CONTENT_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}

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
        # Receipts are never publicly reachable — a dedicated, isolated
        # storage root served only via the authenticated
        # GET /vizu-pay/orders/{id}/proof endpoint, same pattern as
        # protected Hören audio.
        self.proof_storage = ProtectedPaymentProofStorage()

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

    def list_payment_cards(self) -> list[dict]:
        return plan_config.PAYMENT_CARDS

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

    def get_rejection_count(self, user_id) -> int:
        return (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.user_id == user_id, SubscriptionOrder.status == plan_config.STATUS_REJECTED)
            .count()
        )

    def is_user_blocked(self, user_id) -> bool:
        return self.get_rejection_count(user_id) >= plan_config.MAX_REJECTIONS

    def get_my_status(self, user: User) -> dict:
        self._sweep_expired(user.id)

        now = _now()
        is_premium = bool(user.premium_until and user.premium_until > now)

        has_pending_order = (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.user_id == user.id, SubscriptionOrder.status == plan_config.STATUS_PENDING)
            .first()
            is not None
        )

        rejection_count = self.get_rejection_count(user.id)

        latest_rejected = (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.user_id == user.id, SubscriptionOrder.status == plan_config.STATUS_REJECTED)
            .order_by(SubscriptionOrder.reviewed_at.desc())
            .first()
        )

        return {
            "is_premium": is_premium,
            "premium_until": user.premium_until,
            "has_pending_order": has_pending_order,
            "rejection_count": rejection_count,
            "is_blocked": rejection_count >= plan_config.MAX_REJECTIONS,
            "latest_rejection_reason": (
                latest_rejected.rejection_reason if latest_rejected and not has_pending_order else None
            ),
        }

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
        """Returns an error message if the promo can't be applied, else None.
        Shared by checkout-discount validation and direct FREE_DAYS
        redemption — every rule here (active, expiry, usage limit,
        one-per-user) applies identically to both."""
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
        """Checkout-time preview only — for FREE_DAYS codes (which grant
        Premium directly and never apply to a paid order) this always
        reports invalid with a message pointing at the redeem flow."""
        promo = self._find_promo(code)
        error = self._check_promo(promo, user)
        if error:
            return {"valid": False, "discount_type": None, "discount_value": None, "message": error}
        if promo.discount_type == DISCOUNT_TYPE_FREE_DAYS:
            return {
                "valid": False,
                "discount_type": promo.discount_type,
                "discount_value": promo.discount_value,
                "message": "This code grants Premium directly — use 'Enter promo code', not checkout.",
            }
        return {"valid": True, "discount_type": promo.discount_type, "discount_value": promo.discount_value, "message": None}

    def _apply_discount(self, base_amount: int, promo: PromoCode) -> int:
        if promo.discount_type == "PERCENT":
            return min(base_amount * promo.discount_value // 100, base_amount)
        return min(promo.discount_value, base_amount)

    # ------------------------------------------------------------------
    # Promo — direct redemption (grants Premium, no payment)
    # ------------------------------------------------------------------

    def redeem_promo(self, code: str, user: User, ip: str | None) -> dict:
        """FREE_DAYS codes only. Row-locks the PromoCode for the duration
        of the check-then-increment so two simultaneous redemptions of a
        near-exhausted code can't both succeed (the DB-level unique
        constraint on (promo_code_id, user_id) is the backstop for the
        one-user-one-use rule, in case app logic is ever bypassed)."""
        promo = (
            self.db.query(PromoCode)
            .filter(PromoCode.code == code.strip().upper())
            .with_for_update()
            .first()
        )

        error = self._check_promo(promo, user)
        if error:
            raise VizuPayError(error)

        if promo.discount_type != DISCOUNT_TYPE_FREE_DAYS:
            raise VizuPayError("This code is a checkout discount — apply it at checkout instead.")

        days = promo.discount_value
        now = _now()
        base = user.premium_until if (user.premium_until and user.premium_until > now) else now
        user.premium_until = base + timedelta(days=days)

        order_id = uuid4()
        order = SubscriptionOrder(
            id=order_id,
            user_id=user.id,
            plan=plan_config.PLAN_PROMO,
            duration_days=days,
            base_amount=0,
            discount_amount=0,
            final_amount=0,
            currency="UZS",
            payment_method=plan_config.PAYMENT_METHOD_PROMO,
            status=plan_config.STATUS_APPROVED,
            promo_code_id=promo.id,
            gateway="promo",
            reviewed_at=now,
        )
        self.db.add(order)
        self.db.flush()

        promo.used_count += 1
        self.db.add(PromoCodeRedemption(promo_code_id=promo.id, user_id=user.id, order_id=order_id))

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise VizuPayError("You have already used this promo code.")

        write_audit(
            self.db,
            actor_id=user.id,
            action="promo_redeemed",
            target_user_id=user.id,
            details=f"{promo.code} (+{days}d)",
            ip_address=ip,
        )

        return {"premium_until": user.premium_until, "days_granted": days}

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

        # No "payment-proofs/" prefix here — self.proof_storage's ROOT
        # (ProtectedPaymentProofStorage) already isolates this tree, so
        # the stored path is just the filename to avoid a redundant
        # payment-proofs/payment-proofs/ nesting on disk.
        return filename, proof_type

    def _has_open_order(self, user: User) -> bool:
        return (
            self.db.query(SubscriptionOrder)
            .filter(SubscriptionOrder.user_id == user.id, SubscriptionOrder.status == plan_config.STATUS_PENDING)
            .first()
            is not None
        )

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

        self._sweep_expired(user.id)

        if self.is_user_blocked(user.id):
            raise HTTPException(
                status_code=403,
                detail="PAYMENT_REQUEST_BLOCKED",
            )

        if self._has_open_order(user):
            raise HTTPException(
                status_code=409,
                detail="PAYMENT_REQUEST_ALREADY_PENDING",
            )

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
            if promo.discount_type == DISCOUNT_TYPE_FREE_DAYS:
                raise VizuPayError("This code grants Premium directly — use 'Enter promo code', not checkout.")
            discount_amount = self._apply_discount(base_amount, promo)

        final_amount = max(base_amount - discount_amount, 0)

        order_id = uuid4()
        proof_path, proof_type = self._build_proof_path(order_id, proof_file, contents)

        await self.proof_storage.upload(proof_file, proof_path)

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
            proof_url=proof_path,
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
            "has_proof": order.proof_url is not None,
            "proof_download_url": f"/api/v1/vizu-pay/orders/{order.id}/proof" if order.proof_url else None,
            "promo_code": order.promo_code.code if order.promo_code else None,
            "rejection_reason": order.rejection_reason,
            "expires_at": order.expires_at,
            "reviewed_at": order.reviewed_at,
            "created_at": order.created_at,
        }

    def get_order_proof(self, order_id: str, user: User) -> tuple[Path, str, str]:
        """Authorization: the order's own user, or staff. Returns
        (absolute file path, content type, download filename) for
        FileResponse — never a public URL."""
        order = self.db.get(SubscriptionOrder, UUID(order_id))
        if order is None or not order.proof_url:
            raise VizuPayError("No receipt for this order.")

        is_owner = order.user_id == user.id
        is_staff = user.role in UserRole.ADMIN_PANEL_ROLES
        if not is_owner and not is_staff:
            raise HTTPException(status_code=403, detail="Not authorized to view this receipt.")

        path = self.proof_storage.ROOT / order.proof_url
        extension = Path(order.proof_url).suffix.lower()
        content_type = _PROOF_CONTENT_TYPE.get(extension, "application/octet-stream")
        filename = f"receipt-{order.id}{extension}"

        return path, content_type, filename

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
