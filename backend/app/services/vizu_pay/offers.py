"""Angebote — the single source of truth for course packages, prices and access terms.

Packages (single levels "A1" … and bundles "A1_B1", "A1_C1", "B2_C1") live in the table `course_packages` (Admin ->
Angebote -> Pakete; app/services/vizu_pay/packages.py validates edits). The dict OFFERS below holds the code defaults,
used only when the table cannot be read (tests without a database, a not yet migrated database). Served to the
frontend via GET /vizu-pay/offers — never hard-coded in the UI.

A package code is stored as `SubscriptionOrder.plan`. An APPROVED order opens the levels it was bought with
(`SubscriptionOrder.included_levels`, fixed at checkout; older orders: the package's levels) for `duration_days`
from the approval (purchases.activate_course_access). A level that is not released yet ("Tez orada", B2 / C1) opens
for its buyers automatically once the admin releases it — no new payment (access.py).

Status: ACTIVE = sold; COMING_SOON = shown as "Tez orada" without price or buy button; DISABLED = hidden from sale.
The server refuses an order for anything that is not purchasable (VizuPayService.create_order).
"""

KIND_LEVEL = "LEVEL"
KIND_PACKAGE = "PACKAGE"

STATUS_ACTIVE = "ACTIVE"
STATUS_COMING_SOON = "COMING_SOON"
STATUS_DISABLED = "DISABLED"
STATUSES = (STATUS_ACTIVE, STATUS_COMING_SOON, STATUS_DISABLED)

OFFER_A1 = "A1"
OFFER_A2 = "A2"
OFFER_B1 = "B1"
OFFER_B2 = "B2"
OFFER_C1 = "C1"
OFFER_A1_B1 = "A1_B1"
OFFER_A1_C1 = "A1_C1"
OFFER_B2_C1 = "B2_C1"

FREE_LESSONS_PER_COURSE = 1

# Legacy: calendar-month terms of orders approved before course_packages existed (duration_days = 0 on those orders).
OFFER_ACCESS_MONTHS = {
    OFFER_A1: 1,
    OFFER_A2: 1,
    OFFER_B1: 2,
    OFFER_B2: 3,
    OFFER_C1: 2,
    OFFER_A1_B1: 4,
    OFFER_A1_C1: 9,
    OFFER_B2_C1: 6,
}


def _default(kind, label, levels, sale, original, discount, days, status, sort):
    return {"kind": kind, "label": label, "levels": levels, "sale_price": sale, "original_price": original,
            "discount_percent": discount, "duration_days": days, "status": status, "active": status == STATUS_ACTIVE,
            "description": {}, "sort_order": sort}


# Code defaults = the seed of migration c7e1f3a9b2d5 (A1 / A2 there keep the admin's price in force).
OFFERS: dict[str, dict] = {
    OFFER_A1: _default(KIND_LEVEL, "A1", ["A1"], 50_000, 100_000, 50, 30, STATUS_ACTIVE, 10),
    OFFER_A2: _default(KIND_LEVEL, "A2", ["A2"], 99_000, 200_000, 50, 30, STATUS_ACTIVE, 20),
    OFFER_B1: _default(KIND_LEVEL, "B1", ["B1"], 100_000, None, None, 60, STATUS_ACTIVE, 30),
    OFFER_B2: _default(KIND_LEVEL, "B2", ["B2"], None, None, None, 90, STATUS_COMING_SOON, 40),
    OFFER_C1: _default(KIND_LEVEL, "C1", ["C1"], None, None, None, 60, STATUS_COMING_SOON, 50),
    OFFER_A1_B1: _default(KIND_PACKAGE, "A1 → B1", ["A1", "A2", "B1"], 200_000, None, None, 180, STATUS_ACTIVE, 60),
    OFFER_A1_C1: _default(KIND_PACKAGE, "A1 → C1", ["A1", "A2", "B1", "B2", "C1"], 400_000, None, None, 365, STATUS_ACTIVE, 70),
    OFFER_B2_C1: _default(KIND_PACKAGE, "B2 → C1", ["B2", "C1"], None, None, None, 180, STATUS_COMING_SOON, 80),
}

OFFER_CODES = set(OFFERS)  # default codes; use offer_codes() for the current set (admin-created packages included)

ALL_LEVELS = ("A1", "A2", "B1", "B2", "C1")
# Levels whose lessons students can open at all. B2 / C1 are "Tez orada": visible as locked cards, no lesson (not even
# the free first one); a package that contains them opens them for its buyers only once the admin releases them.
LEVEL_AVAILABLE_DEFAULT = {"A1": True, "A2": True, "B1": True, "B2": False, "C1": False}

# Lesson-access gate per level (Admin -> Angebote, "Verkauf"): when off, the level's paid lessons open only for buyers
# of an order that names the level (and staff) — not for legacy time-based Premium. Since 2026-11-14 selling is
# decided by the package status alone; this flag no longer blocks a purchase.
LEVEL_SALES_DEFAULT = {"A1": True, "A2": False, "B1": False, "B2": False, "C1": False}

# ----------------------------------------------------------------------
# Admin settings (app_settings key "angebote": levels / sales / free_lessons) and the package rows, read through one
# short cache so the access check of a lesson list does not hit the database per lesson; a save invalidates it at once.
# ----------------------------------------------------------------------
SETTINGS_KEY = "angebote"
_CACHE_SECONDS = 30.0
_cache: dict = {"at": -1e9, "value": None}


def _package_row(p) -> dict:
    return {"kind": p.package_type, "label": p.name, "levels": [lv for lv in ALL_LEVELS if lv in (p.included_levels or [])],
            "sale_price": p.price, "original_price": p.original_price, "discount_percent": p.discount_percent,
            "duration_days": p.duration_days, "status": p.status, "active": p.status == STATUS_ACTIVE,
            "description": dict(p.description or {}), "sort_order": p.sort_order}


def _read() -> dict:
    import time

    now = time.monotonic()
    if _cache["value"] is not None and now - _cache["at"] < _CACHE_SECONDS:
        return _cache["value"]
    value: dict = {"settings": {}, "packages": None}
    try:
        from sqlalchemy import select

        from app.db.session import SessionLocal
        from app.models.app_setting import AppSetting
        from app.models.course_package import CoursePackage

        with SessionLocal() as db:
            row = db.scalar(select(AppSetting.value).where(AppSetting.key == SETTINGS_KEY))
            value["settings"] = dict(row or {})
            try:
                rows = list(db.scalars(select(CoursePackage).order_by(CoursePackage.sort_order, CoursePackage.code)))
                value["packages"] = {p.code: _package_row(p) for p in rows} or None
            except Exception:  # table not migrated yet: the code defaults apply
                db.rollback()
    except Exception:  # no database: the code defaults apply
        pass
    _cache.update(at=now, value=value)
    return value


def invalidate_cache() -> None:
    _cache.update(at=-1e9, value=None)


def _read_overrides() -> dict:
    """app_settings["angebote"] (levels / sales / free_lessons)."""
    return _read()["settings"]


def _read_packages() -> dict | None:
    """course_packages rows by code, or None (no table / no rows: the code defaults apply)."""
    return _read()["packages"]


def effective() -> dict:
    """The configuration in force: {"offers": {code: cfg}, "free_lessons": int, "levels": {level: available},
    "sales": {level: bool}}."""
    settings = _read_overrides()
    source = _read_packages() or OFFERS
    offers = {code: dict(cfg, levels=list(cfg["levels"]), description=dict(cfg.get("description") or {})) for code, cfg in source.items()}
    levels = dict(LEVEL_AVAILABLE_DEFAULT)
    levels.update({k: bool(v) for k, v in (settings.get("levels") or {}).items() if k in levels})
    sales = dict(LEVEL_SALES_DEFAULT)
    sales.update({k: bool(v) for k, v in (settings.get("sales") or {}).items() if k in sales})
    free = settings.get("free_lessons", FREE_LESSONS_PER_COURSE)
    return {"offers": offers, "free_lessons": int(free) if isinstance(free, int) else FREE_LESSONS_PER_COURSE, "levels": levels,
            "sales": sales}


def offer(code: str) -> dict | None:
    return effective()["offers"].get(code)


def offer_codes() -> set[str]:
    """Every package code that ever existed for orders: current packages plus the code defaults."""
    return set(effective()["offers"]) | OFFER_CODES


def free_lessons() -> int:
    return effective()["free_lessons"]


def level_available(level: str | None) -> bool:
    return bool(level) and effective()["levels"].get(level, False)


def level_sales_enabled(level: str | None) -> bool:
    """Lesson-access gate of a level (Admin -> Angebote, "Verkauf"), see LEVEL_SALES_DEFAULT."""
    return bool(level) and effective()["sales"].get(level, False)


def is_offer(code: str) -> bool:
    return code in offer_codes()


def is_purchasable(code: str) -> bool:
    """ACTIVE, priced, and it opens something today: a single level must be released; a bundle needs at least one
    released level (A1–C1 opens A1–B1 now, B2 / C1 later without a new payment)."""
    cfg = offer(code)
    if not (cfg and cfg["status"] == STATUS_ACTIVE and cfg["sale_price"]):
        return False
    released = [lv for lv in cfg["levels"] if level_available(lv)]
    if cfg["kind"] == KIND_LEVEL:
        return len(released) == len(cfg["levels"])
    return bool(released)


def offer_levels(code: str) -> list[str]:
    cfg = offer(code)
    return list(cfg["levels"]) if cfg else []


def offer_label(code: str) -> str | None:
    cfg = offer(code) or OFFERS.get(code)
    return cfg["label"] if cfg else None


def duration_days(code: str) -> int:
    """Access term of a new order in days (0 = legacy calendar-month term, see access_duration_months)."""
    cfg = offer(code)
    if not cfg:
        raise ValueError(f"Offer {code!r} has no configured access duration")
    return int(cfg.get("duration_days") or 0)


def access_duration_months(code: str) -> int:
    """Legacy term of old orders (approved before durations were stored per order)."""
    try:
        return OFFER_ACCESS_MONTHS[code]
    except KeyError:
        raise ValueError(f"Offer {code!r} has no configured access duration") from None


def list_offers() -> list[dict]:
    eff = effective()
    out = []
    for code, cfg in sorted(eff["offers"].items(), key=lambda kv: (kv[1].get("sort_order", 0), kv[0])):
        if cfg["status"] == STATUS_DISABLED:
            continue
        sold = cfg["status"] == STATUS_ACTIVE
        days = int(cfg["duration_days"])
        out.append({
            "code": code,
            "kind": cfg["kind"],
            "label": cfg["label"],
            "levels": list(cfg["levels"]),
            # levels of the package students can open today (B2 / C1 "Tez orada" are not)
            "available_levels": [lv for lv in cfg["levels"] if eff["levels"].get(lv)],
            "sales_levels": [lv for lv in cfg["levels"] if eff["levels"].get(lv)],
            # a COMING_SOON package shows neither price nor duration
            "original_price": cfg["original_price"] if sold else None,
            "sale_price": cfg["sale_price"] if sold else None,
            "discount_percent": cfg["discount_percent"] if sold else None,
            "active": sold,
            "status": cfg["status"],
            "duration_days": days if sold else None,
            "duration_months": max(1, round(days / 30)) if sold else 0,
            "description": cfg.get("description") or {},
            "purchasable": is_purchasable(code),
            "free_lessons": eff["free_lessons"],
            "currency": "UZS",
        })
    return out


def validate_overrides(value: dict) -> dict:
    """Clean an admin's settings document (levels / sales / free_lessons); raises ValueError with a reason. Prices,
    durations and contents are package fields now (packages.py) — an "offers" part is ignored."""
    out: dict = {"levels": {}}
    for level, available in (value.get("levels") or {}).items():
        if level not in ALL_LEVELS or not isinstance(available, bool):
            raise ValueError(f"levels.{level}: true / false")
        out["levels"][level] = available
    if "sales" in value:
        out["sales"] = {}
        for level, enabled in (value.get("sales") or {}).items():
            if level not in ALL_LEVELS or not isinstance(enabled, bool):
                raise ValueError(f"sales.{level}: true / false")
            out["sales"][level] = enabled
    if "free_lessons" in value:
        free = value["free_lessons"]
        if not isinstance(free, int) or isinstance(free, bool) or not 0 <= free <= 5:
            raise ValueError("free_lessons: 0-5")
        out["free_lessons"] = free
    return out
