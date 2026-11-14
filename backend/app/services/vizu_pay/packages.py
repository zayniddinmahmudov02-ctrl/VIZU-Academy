"""Admin management of course packages (table course_packages, rules in offers.py): list, create, update. A package
is never deleted (orders reference its code) — set it DISABLED instead. Every change is audited and takes effect at once
(offers cache invalidated). Prices / durations of orders already created never change (amount and duration_days /
included_levels are stored on the order)."""

import json
import re

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.course_package import CoursePackage
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User

from . import offers as offer_config
from . import plans as plan_config

CODE_RE = re.compile(r"^[A-Z0-9_]{1,20}$")
LANGS = ("uz", "de", "en", "ru")
FIELDS = ("name", "package_type", "included_levels", "price", "original_price", "discount_percent", "duration_days", "status",
          "description", "sort_order")


def _err(detail: str) -> HTTPException:
    return HTTPException(status_code=422, detail=f"INVALID_PACKAGE: {detail}")


def serialize(p: CoursePackage, stats: dict | None = None) -> dict:
    s = (stats or {}).get(p.code, {})
    return {"code": p.code, "name": p.name, "package_type": p.package_type, "included_levels": list(p.included_levels or []),
            "price": p.price, "original_price": p.original_price, "discount_percent": p.discount_percent,
            "duration_days": p.duration_days, "status": p.status, "description": dict(p.description or {}), "sort_order": p.sort_order,
            "purchasable": offer_config.is_purchasable(p.code), "approved_orders": s.get("approved", 0), "pending_orders": s.get("pending", 0),
            "created_at": p.created_at, "updated_at": p.updated_at}


def _order_stats(db: Session) -> dict:
    rows = db.execute(select(SubscriptionOrder.plan, SubscriptionOrder.status, func.count())
                      .where(SubscriptionOrder.status.in_([plan_config.STATUS_APPROVED, plan_config.STATUS_PENDING]))
                      .group_by(SubscriptionOrder.plan, SubscriptionOrder.status)).all()
    out: dict = {}
    for plan, status, n in rows:
        out.setdefault(plan, {})["approved" if status == plan_config.STATUS_APPROVED else "pending"] = int(n)
    return out


def list_packages(db: Session) -> list[dict]:
    stats = _order_stats(db)
    rows = db.scalars(select(CoursePackage).order_by(CoursePackage.sort_order, CoursePackage.code))
    return [serialize(p, stats) for p in rows]


def _int_or_none(value, field: str, low: int, high: int):
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise _err(f"{field}: {low}–{high} or empty")
    return value


def _clean(data: dict, code: str, current: CoursePackage | None) -> dict:
    merged = {f: getattr(current, f) for f in FIELDS} if current else {}
    merged.update({k: v for k, v in data.items() if k in FIELDS})
    out = {}
    name = (merged.get("name") or "").strip()
    if not 1 <= len(name) <= 120:
        raise _err("name: 1–120 characters")
    out["name"] = name
    kind = merged.get("package_type")
    if kind not in (offer_config.KIND_LEVEL, offer_config.KIND_PACKAGE):
        raise _err("package_type: LEVEL or PACKAGE")
    out["package_type"] = kind
    levels = merged.get("included_levels")
    if not isinstance(levels, list) or not levels or len(set(levels)) != len(levels) or any(lv not in offer_config.ALL_LEVELS for lv in levels):
        raise _err(f"included_levels: a non-empty list of {', '.join(offer_config.ALL_LEVELS)}")
    levels = [lv for lv in offer_config.ALL_LEVELS if lv in levels]
    if kind == offer_config.KIND_LEVEL and (len(levels) != 1 or (code in offer_config.ALL_LEVELS and levels != [code])):
        raise _err("a single-level package covers exactly its own level")
    out["included_levels"] = levels
    out["price"] = _int_or_none(merged.get("price"), "price", 1, 100_000_000)
    out["original_price"] = _int_or_none(merged.get("original_price"), "original_price", 1, 100_000_000)
    if out["original_price"] is not None and out["price"] is not None and out["original_price"] < out["price"]:
        raise _err("original_price must not be lower than price")
    out["discount_percent"] = _int_or_none(merged.get("discount_percent"), "discount_percent", 0, 100)
    days = merged.get("duration_days")
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 3650:
        raise _err("duration_days: 1–3650")
    out["duration_days"] = days
    status = merged.get("status")
    if status not in offer_config.STATUSES:
        raise _err("status: ACTIVE, COMING_SOON or DISABLED")
    if status == offer_config.STATUS_ACTIVE:
        if not out["price"]:
            raise _err("an ACTIVE package needs a price")
        released = [lv for lv in levels if offer_config.level_available(lv)]
        if kind == offer_config.KIND_LEVEL and not released:
            raise _err(f"release level {levels[0]} first (Angebote -> Niveaus) before selling it")
        if not released:
            raise _err("a bundle needs at least one released level to be sold")
    out["status"] = status
    desc = merged.get("description") or {}
    if not isinstance(desc, dict) or any(k not in LANGS or not isinstance(v, str) or len(v) > 1000 for k, v in desc.items()):
        raise _err("description: {uz, de, en, ru} texts up to 1000 characters")
    out["description"] = {k: v.strip() for k, v in desc.items() if v.strip()}
    sort = merged.get("sort_order", 0)
    if not isinstance(sort, int) or isinstance(sort, bool) or not -1000 <= sort <= 1000:
        raise _err("sort_order: -1000–1000")
    out["sort_order"] = sort
    return out


def create_package(db: Session, actor: User, data: dict, ip: str | None = None) -> dict:
    code = (data.get("code") or "").strip().upper()
    if not CODE_RE.match(code):
        raise _err("code: A–Z, 0–9, _ (max 20)")
    # a code once used by orders (or a legacy Premium plan code) can never be reused for different content
    used = db.scalar(select(func.count()).select_from(SubscriptionOrder).where(SubscriptionOrder.plan == code))
    if db.scalar(select(CoursePackage).where(CoursePackage.code == code)) is not None or used or code in plan_config.PLAN_CONFIG:
        raise HTTPException(status_code=409, detail="PACKAGE_CODE_EXISTS")
    clean = _clean(data, code, None)
    pkg = CoursePackage(code=code, updated_by=actor.id, **clean)
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    offer_config.invalidate_cache()
    write_audit(db, str(actor.id), "course_package_created", details=json.dumps({"code": code, **clean}, ensure_ascii=False)[:4000], ip_address=ip)
    return serialize(pkg, _order_stats(db))


def update_package(db: Session, actor: User, code: str, data: dict, ip: str | None = None) -> dict:
    pkg = db.scalar(select(CoursePackage).where(CoursePackage.code == code).with_for_update())
    if pkg is None:
        raise HTTPException(status_code=404, detail="PACKAGE_NOT_FOUND")
    before = {f: getattr(pkg, f) for f in FIELDS}
    clean = _clean(data, code, pkg)
    for field, value in clean.items():
        setattr(pkg, field, value)
    pkg.updated_by = actor.id
    db.commit()
    db.refresh(pkg)
    offer_config.invalidate_cache()
    changed = {f: {"before": before[f], "after": clean[f]} for f in FIELDS if before[f] != clean[f]}
    write_audit(db, str(actor.id), "course_package_updated", details=json.dumps({"code": code, "changes": changed}, ensure_ascii=False, default=str)[:4000],
                ip_address=ip)
    return serialize(pkg, _order_stats(db))
