"""Multilevel Modelltest Premium — ONE purchase opens all 10 Multilevel Modelltests (Vorbereitung → Multilevel), unlimited.

Product (offers.ML_PREMIUM_*): plan "ML_PREMIUM", product MULTILEVEL_MODELLTEST_PREMIUM, default price 99 000 UZS; the Super Admin may change the
price or switch the sale off (app_settings["multilevel_premium"], Admin → Payments → Payment Settings, audited). The price is always the server's.

Access = an active user_entitlements row (revoked_at IS NULL) for the product, or a staff role. It is granted only by
  * the Super Admin approving the student's order (manual card transfer: receipt, or "Chek mavjud emas" with date + time) — source PAYMENT, or
  * a 100 % Multilevel promo code (FREE_ACCESS or PERCENT 100) that a Super Admin approved and activated — source PROMO (a zero-amount APPROVED
    order keeps the purchase history like a course promo does).
A pending, rejected or expired order never opens anything. One active entitlement per student (unique index), one open Multilevel order at a
time, the existing rejection block (plans.MAX_REJECTIONS) applies. A refund revokes the entitlement (AdminVizuPayService.refund_order).
"""

from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.app_setting import AppSetting
from app.models.promo_code import PromoCode
from app.models.promo_code_redemption import PromoCodeRedemption
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User
from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, SOURCE_PAYMENT, SOURCE_PROMO, UserEntitlement

from . import offers as offer_config
from . import plans as plan_config

PLAN = offer_config.ML_PREMIUM_PLAN
SETTINGS_KEY = "multilevel_premium"
STATUS_ACTIVE, STATUS_DISABLED = "ACTIVE", "DISABLED"
MIN_PRICE, MAX_PRICE = 1_000, 10_000_000
PAYMENT_METHOD = plan_config.PAYMENT_METHOD_UZCARD  # transfer to the card in plans.PAYMENT_CARDS
TASHKENT = timezone(timedelta(hours=5))  # the student types the transfer time in local time (UTC+5, no DST)
PAID_AT_MAX_AGE_DAYS = 60
MAX_NOTE = 1000


def _err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _naive(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


# ----------------------------------------------------------------------
# Product + settings
# ----------------------------------------------------------------------


def settings(db: Session) -> dict:
    row = db.scalar(select(AppSetting.value).where(AppSetting.key == SETTINGS_KEY))
    value = dict(row or {})
    price = value.get("price")
    status = value.get("status")
    return {"price": price if isinstance(price, int) and not isinstance(price, bool) and MIN_PRICE <= price <= MAX_PRICE else offer_config.ML_PREMIUM_PRICE,
            "status": status if status in (STATUS_ACTIVE, STATUS_DISABLED) else STATUS_ACTIVE}


def product(db: Session) -> dict:
    s = settings(db)
    return {"code": PLAN, "product": offer_config.ML_PREMIUM_PRODUCT, "label": offer_config.ML_PREMIUM_LABEL, "price": s["price"],
            "currency": "UZS", "status": s["status"], "purchasable": s["status"] == STATUS_ACTIVE, "unlimited": True,
            "default_price": offer_config.ML_PREMIUM_PRICE}


def update_settings(db: Session, actor: User, payload: dict, ip: str | None) -> dict:
    """Super Admin: price (MIN_PRICE..MAX_PRICE UZS) and sale status. Existing orders keep the amount they were made with."""
    import json

    current = settings(db)
    clean = dict(current)
    if "price" in payload and payload["price"] is not None:
        price = payload["price"]
        if not isinstance(price, int) or isinstance(price, bool) or not MIN_PRICE <= price <= MAX_PRICE:
            raise _err(422, f"INVALID_PRICE: {MIN_PRICE}–{MAX_PRICE} UZS")
        clean["price"] = price
    if "status" in payload and payload["status"] is not None:
        if payload["status"] not in (STATUS_ACTIVE, STATUS_DISABLED):
            raise _err(422, "INVALID_STATUS")
        clean["status"] = payload["status"]
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY))
    if row is None:
        db.add(AppSetting(key=SETTINGS_KEY, value=clean, updated_by=actor.id))
    else:
        row.value = clean
        row.updated_by = actor.id
    db.commit()
    write_audit(db, str(actor.id), "ml_premium_settings_updated", details=json.dumps({"before": current, "after": clean}), ip_address=ip)
    return product(db)


# ----------------------------------------------------------------------
# Entitlement
# ----------------------------------------------------------------------


def active_entitlement(db: Session, user_id, lock: bool = False) -> UserEntitlement | None:
    query = select(UserEntitlement).where(UserEntitlement.user_id == user_id, UserEntitlement.product == PRODUCT_MULTILEVEL_PREMIUM,
                                          UserEntitlement.revoked_at.is_(None))
    if lock:
        query = query.with_for_update()
    ent = db.scalar(query)
    if ent is not None and ent.expires_at is not None and ent.expires_at <= _now():
        return None
    return ent


def grant_for_order(db: Session, order: SubscriptionOrder, actor: User) -> UserEntitlement:
    """Called inside AdminVizuPayService.approve_order (same transaction, order row locked). Refuses a second access."""
    if active_entitlement(db, order.user_id, lock=True) is not None:
        raise _err(409, "ALREADY_ENTITLED: Der Student hat den Multilevel Premium bereits — Anfrage ablehnen.")
    now = _now()
    order.purchase_date = now
    order.access_start_date = now
    order.access_end_date = None  # unlimited
    ent = UserEntitlement(user_id=order.user_id, product=PRODUCT_MULTILEVEL_PREMIUM, source=SOURCE_PAYMENT, order_id=order.id,
                          promo_code_id=order.promo_code_id, granted_by_id=actor.id, granted_at=now)
    db.add(ent)
    return ent


def revoke_for_order(db: Session, order: SubscriptionOrder, actor: User, reason: str | None) -> None:
    for ent in db.scalars(select(UserEntitlement).where(UserEntitlement.order_id == order.id, UserEntitlement.revoked_at.is_(None))):
        ent.revoked_at = _now()
        ent.revoked_by_id = actor.id
        ent.revoke_reason = (reason or "refund").strip()[:500]


def entitlement_view(ent: UserEntitlement | None) -> dict | None:
    if ent is None:
        return None
    return {"source": ent.source, "granted_at": ent.granted_at, "expires_at": ent.expires_at, "order_id": str(ent.order_id) if ent.order_id else None}


# ----------------------------------------------------------------------
# Student
# ----------------------------------------------------------------------


def _ml_orders(db: Session, user_id):
    return select(SubscriptionOrder).where(SubscriptionOrder.user_id == user_id, SubscriptionOrder.plan == PLAN)


def pending_order(db: Session, user_id) -> SubscriptionOrder | None:
    return db.scalar(_ml_orders(db, user_id).where(SubscriptionOrder.status == plan_config.STATUS_PENDING)
                     .order_by(SubscriptionOrder.created_at.desc()))


def tests_overview(db: Session) -> dict:
    """All Multilevel Modelltests / published ones; `free` = the ones open without the Premium (0 since 2026-11-19), `premium_*` = the ones the
    Premium opens (all of them)."""
    from app.models.model_test import STATUS_PUBLISHED, ModelTest
    from app.services.mock_exam.multilevel_exam_service import _multilevel_level_ids
    from app.services.mock_exam.multilevel_service import free_test

    ids = _multilevel_level_ids(db)
    tests = list(db.scalars(select(ModelTest).where(ModelTest.level_id.in_(ids), ModelTest.status != "ARCHIVED"))) if ids else []
    premium = [t for t in tests if not free_test(t)]
    return {"total": len(tests), "available": sum(t.status == STATUS_PUBLISHED for t in tests), "free": len(tests) - len(premium),
            "premium_total": len(premium), "premium_available": sum(t.status == STATUS_PUBLISHED for t in premium)}


def status(db: Session, user: User) -> dict:
    from .access import has_premium_bypass
    from .service import VizuPayService

    pay = VizuPayService(db)
    ent = active_entitlement(db, user.id)
    pending = pending_order(db, user.id)
    last = db.scalar(_ml_orders(db, user.id).order_by(SubscriptionOrder.created_at.desc()))
    rejected = last if last is not None and last.status == plan_config.STATUS_REJECTED and ent is None and pending is None else None
    return {
        "product": product(db),
        "cards": plan_config.PAYMENT_CARDS,
        "entitled": ent is not None,
        "staff": has_premium_bypass(user),
        "entitlement": entitlement_view(ent),
        "pending_order": pay.serialize_order(pending) if pending is not None else None,
        "last_rejected": {"reason": rejected.rejection_reason, "reviewed_at": rejected.reviewed_at} if rejected is not None else None,
        "blocked": pay.is_user_blocked(user.id),
        "tests": tests_overview(db),
    }


def _is_free(promo: PromoCode) -> bool:
    return promo.discount_type == "FREE_ACCESS" or (promo.discount_type == "PERCENT" and promo.discount_value >= 100)


def _promo_for(db: Session, user: User, code: str, lock: bool = False) -> tuple[PromoCode | None, str | None]:
    """The promo row (or None) and why it cannot be used for the Multilevel Premium (None = usable)."""
    from .service import VizuPayService

    query = select(PromoCode).where(PromoCode.code == code.strip().upper())
    if lock:
        query = query.with_for_update()
    promo = db.scalar(query)
    error = VizuPayService(db)._check_promo(promo, user, PLAN)
    if error is None and promo.discount_type not in ("PERCENT", "FREE_ACCESS"):
        error = "PROMO_WRONG_PRODUCT"
    return promo, error


def _discount(base: int, promo: PromoCode) -> int:
    if _is_free(promo):
        return base
    return min(base * promo.discount_value // 100, base)


def quote(db: Session, user: User, promo_code: str | None) -> dict:
    """What the Multilevel checkout charges (read only — create_order computes it again)."""
    base = product(db)["price"]
    discount, error = 0, None
    if promo_code and promo_code.strip():
        promo, error = _promo_for(db, user, promo_code)
        if error is None:
            discount = _discount(base, promo)
    final = max(base - discount, 0)
    return {"plan": PLAN, "currency": "UZS", "base_amount": base, "promo_discount": discount, "promo_error": error, "final_amount": final,
            "free": error is None and bool(promo_code) and final == 0}


def _paid_at(paid_date: str | None, paid_time: str | None) -> datetime | None:
    if not paid_date and not paid_time:
        return None
    if not paid_date or not paid_time:
        raise _err(422, "PAID_AT_INCOMPLETE")
    try:
        value = datetime.combine(date.fromisoformat(paid_date.strip()), time.fromisoformat(paid_time.strip()[:5]), tzinfo=TASHKENT)
    except ValueError:
        raise _err(422, "PAID_AT_INVALID") from None
    now = _now()
    if value > now + timedelta(minutes=10) or value < now - timedelta(days=PAID_AT_MAX_AGE_DAYS):
        raise _err(422, "PAID_AT_INVALID")
    return value.astimezone(timezone.utc)


async def create_order(db: Session, user: User, *, promo_code: str | None, no_receipt: bool, paid_date: str | None, paid_time: str | None,
                       note: str | None, proof: UploadFile | None, ip: str | None) -> dict:
    """A PENDING Multilevel Premium request: the amount is the server's (price − approved promo), never the client's. A receipt (JPG / PNG /
    PDF, checked by content) is required unless the student ticks "Chek mavjud emas" — then date and time of the transfer are required."""
    from .service import MAX_PROOF_SIZE_BYTES, VizuPayError, VizuPayService

    pay = VizuPayService(db)
    prod = product(db)
    if not prod["purchasable"]:
        raise _err(409, "PRODUCT_NOT_AVAILABLE")
    if pay.is_user_blocked(user.id):
        raise _err(403, "PAYMENT_REQUEST_BLOCKED")
    paid_at = _paid_at(paid_date, paid_time)
    text_ = (note or "").strip()
    if len(text_) > MAX_NOTE:
        raise _err(422, "NOTE_TOO_LONG")
    has_file = proof is not None and bool(proof.filename)
    if no_receipt:
        if has_file:
            raise _err(422, "RECEIPT_AND_NO_RECEIPT")
        if paid_at is None:
            raise _err(422, "PAID_AT_REQUIRED")
    elif not has_file:
        raise _err(422, "RECEIPT_REQUIRED")
    contents = b""
    if has_file:
        contents = await proof.read()
        if not contents:
            raise VizuPayError("Payment proof file is empty.")
        if len(contents) > MAX_PROOF_SIZE_BYTES:
            raise VizuPayError("Payment proof file is too large (max 10MB).")
        await proof.seek(0)

    # serialize this student's requests (row lock until commit): a double submit cannot pass the checks twice
    db.query(User.id).filter(User.id == user.id).with_for_update().first()
    if active_entitlement(db, user.id) is not None:
        raise _err(409, "ALREADY_ENTITLED")
    if pending_order(db, user.id) is not None:
        raise _err(409, "PAYMENT_REQUEST_ALREADY_PENDING")

    base = prod["price"]
    promo, discount = None, 0
    if promo_code and promo_code.strip():
        promo, error = _promo_for(db, user, promo_code, lock=True)
        if error:
            raise _err(422, error)
        discount = _discount(base, promo)
        if base - discount <= 0:
            raise _err(409, "PROMO_FREE_USE_REDEEM")

    order_id = uuid4()
    proof_path = proof_type = None
    if has_file:
        proof_path, proof_type = pay._build_proof_path(order_id, proof, contents)
        await pay.proof_storage.upload(proof, proof_path)
    order = SubscriptionOrder(
        id=order_id, user_id=user.id, plan=PLAN, duration_days=0, included_levels=None, base_amount=base, discount_amount=discount,
        promo_discount_amount=discount, reward_discount_amount=0, final_amount=base - discount, currency="UZS", payment_method=PAYMENT_METHOD,
        status=plan_config.STATUS_PENDING, proof_url=proof_path, proof_type=proof_type, promo_code_id=promo.id if promo else None,
        promo_code_snapshot=promo.code if promo else None, gateway="manual", expires_at=None,  # waits for the admin, never expires by itself
        paid_at=paid_at, no_receipt=bool(no_receipt), student_note=text_ or None,
    )
    db.add(order)
    db.flush()
    if promo is not None:
        promo.used_count += 1  # reserved; a rejection gives the use back (VizuPayService.release_promo_reservation)
        db.add(PromoCodeRedemption(promo_code_id=promo.id, user_id=user.id, order_id=order_id))
    db.commit()
    db.refresh(order)
    write_audit(db, actor_id=user.id, action="order_created", target_user_id=user.id,
                details=f"{PLAN}, final={order.final_amount} UZS, receipt={'no' if no_receipt else 'yes'}"
                        + (f", promo {promo.code}" if promo else ""), ip_address=ip)
    return pay.serialize_order(order)


def redeem(db: Session, user: User, code: str, ip: str | None) -> dict:
    """A 100 % Multilevel promo code: all Modelltests open at once (no card payment). Approved + ACTIVE + limits + category are checked on
    the locked promo row; the student row lock keeps a payment approval and a redemption from both granting access."""
    db.query(User.id).filter(User.id == user.id).with_for_update().first()  # same lock order as create_order: student, then promo
    promo, error = _promo_for(db, user, code, lock=True)
    if error:
        raise _err(422, error)
    if not _is_free(promo):
        raise _err(409, "PROMO_NOT_FREE")
    if active_entitlement(db, user.id) is not None:
        raise _err(409, "ALREADY_ENTITLED")
    if pending_order(db, user.id) is not None:
        raise _err(409, "PAYMENT_REQUEST_ALREADY_PENDING")
    now = _now()
    base = product(db)["price"]
    order = SubscriptionOrder(
        id=uuid4(), user_id=user.id, plan=PLAN, duration_days=0, included_levels=None, base_amount=base, discount_amount=base,
        promo_discount_amount=base, reward_discount_amount=0, final_amount=0, currency="UZS", payment_method=plan_config.PAYMENT_METHOD_PROMO,
        status=plan_config.STATUS_APPROVED, promo_code_id=promo.id, promo_code_snapshot=promo.code, gateway="promo", reviewed_at=_naive(now),
        purchase_date=now, access_start_date=now, access_end_date=None,
    )
    db.add(order)
    db.flush()
    promo.used_count += 1
    db.add(PromoCodeRedemption(promo_code_id=promo.id, user_id=user.id, order_id=order.id))
    db.add(UserEntitlement(user_id=user.id, product=PRODUCT_MULTILEVEL_PREMIUM, source=SOURCE_PROMO, order_id=order.id, promo_code_id=promo.id,
                           granted_at=now))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _err(409, "ALREADY_ENTITLED") from None
    write_audit(db, actor_id=user.id, action="ml_premium_promo_redeemed", target_user_id=user.id, details=f"{promo.code} -> {PLAN}", ip_address=ip)
    return {"premium_until": user.premium_until, "days_granted": 0, "granted_offers": [PLAN]}


# ----------------------------------------------------------------------
# Admin
# ----------------------------------------------------------------------


def list_entitlements(db: Session, search: str | None = None, include_revoked: bool = False, limit: int = 200) -> list[dict]:
    from sqlalchemy import or_

    query = (select(UserEntitlement, User).join(User, UserEntitlement.user_id == User.id)
             .where(UserEntitlement.product == PRODUCT_MULTILEVEL_PREMIUM).order_by(UserEntitlement.granted_at.desc()).limit(limit))
    if not include_revoked:
        query = query.where(UserEntitlement.revoked_at.is_(None))
    if search and search.strip():
        like = f"%{search.strip()}%"
        query = query.where(or_(User.email.ilike(like), User.username.ilike(like)))
    out = []
    for ent, user in db.execute(query).all():
        out.append({"id": str(ent.id), "user_id": str(user.id), "user_email": user.email,
                    "user_name": " ".join(filter(None, [user.first_name, user.last_name])) or user.username, "source": ent.source,
                    "granted_at": ent.granted_at, "order_id": str(ent.order_id) if ent.order_id else None,
                    "promo_code": ent.promo_code.code if ent.promo_code else None, "revoked_at": ent.revoked_at, "revoke_reason": ent.revoke_reason})
    return out
