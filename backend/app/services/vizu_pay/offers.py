"""Angebote — the single source of truth for course prices and offers.

Same pattern as plans.py: a central backend configuration, served to the
frontend via GET /vizu-pay/offers (never hard-coded in the UI). The values
below are the official business figures — do not derive or recalculate
them (e.g. `discount_percent` is the advertised "50% CHEGIRMA", not
1 - sale/original).

An offer code is stored as `SubscriptionOrder.plan`. An APPROVED order for
an offer unlocks every lesson of every level in `levels`, permanently
(until the order is refunded). The first lesson of every course is free
for everyone (see access.py).
"""

KIND_LEVEL = "LEVEL"
KIND_PACKAGE = "PACKAGE"

OFFER_A1 = "A1"
OFFER_A2 = "A2"
OFFER_B1 = "B1"
OFFER_B2 = "B2"
OFFER_C1 = "C1"
OFFER_A1_B1 = "A1_B1"
OFFER_A1_C1 = "A1_C1"

FREE_LESSONS_PER_COURSE = 1

OFFERS: dict[str, dict] = {
    OFFER_A1: {
        "kind": KIND_LEVEL,
        "label": "A1",
        "levels": ["A1"],
        "original_price": 100_000,
        "sale_price": 49_000,
        "discount_percent": 50,
        "active": True,
    },
    OFFER_A2: {
        "kind": KIND_LEVEL,
        "label": "A2",
        "levels": ["A2"],
        "original_price": 200_000,
        "sale_price": 99_000,
        "discount_percent": 50,
        "active": True,
    },
    OFFER_B1: {
        "kind": KIND_LEVEL,
        "label": "B1",
        "levels": ["B1"],
        "original_price": 200_000,
        "sale_price": 99_000,
        "discount_percent": 50,
        "active": True,
    },
    OFFER_B2: {
        "kind": KIND_LEVEL,
        "label": "B2",
        "levels": ["B2"],
        "original_price": None,
        "sale_price": None,
        "discount_percent": None,
        "active": False,
    },
    OFFER_C1: {
        "kind": KIND_LEVEL,
        "label": "C1",
        "levels": ["C1"],
        "original_price": None,
        "sale_price": None,
        "discount_percent": None,
        "active": False,
    },
    OFFER_A1_B1: {
        "kind": KIND_PACKAGE,
        "label": "A1 → B1",
        "levels": ["A1", "A2", "B1"],
        "original_price": 300_000,
        "sale_price": 199_000,
        "discount_percent": None,
        "active": True,
    },
    OFFER_A1_C1: {
        "kind": KIND_PACKAGE,
        "label": "A1 → C1",
        "levels": ["A1", "A2", "B1", "B2", "C1"],
        "original_price": 600_000,
        "sale_price": 399_000,
        "discount_percent": None,
        "active": True,
    },
}

OFFER_CODES = set(OFFERS)

ALL_LEVELS = ("A1", "A2", "B1", "B2", "C1")
# Levels whose lessons students can open at all. B2 / C1 are "Tez orada":
# visible as locked cards, no lesson (not even the free first one), no sale
# of the level itself; a package that contains them unlocks them only once
# the admin makes them available.
LEVEL_AVAILABLE_DEFAULT = {"A1": True, "A2": True, "B1": True, "B2": False, "C1": False}

# ----------------------------------------------------------------------
# Admin overrides (app_settings key "angebote", Admin -> Angebote). The
# defaults above stay the source of truth for everything the admin did not
# change. Read through a short cache so the access check of a lesson list
# does not hit the database per lesson; a save invalidates it at once.
# ----------------------------------------------------------------------
SETTINGS_KEY = "angebote"
EDITABLE_OFFER_FIELDS = ("original_price", "sale_price", "discount_percent", "active", "levels")
_CACHE_SECONDS = 30.0
_cache: dict = {"at": -1e9, "value": None}


def _read_overrides() -> dict:
    import time

    now = time.monotonic()
    if _cache["value"] is not None and now - _cache["at"] < _CACHE_SECONDS:
        return _cache["value"]
    value: dict = {}
    try:
        from sqlalchemy import select

        from app.db.session import SessionLocal
        from app.models.app_setting import AppSetting

        with SessionLocal() as db:
            row = db.scalar(select(AppSetting.value).where(AppSetting.key == SETTINGS_KEY))
            value = dict(row or {})
    except Exception:  # no database / table not migrated yet: the code defaults apply
        value = {}
    _cache.update(at=now, value=value)
    return value


def invalidate_cache() -> None:
    _cache.update(at=-1e9, value=None)


def effective() -> dict:
    """The configuration in force: {"offers": {code: cfg}, "free_lessons":
    int, "levels": {level: available}} = defaults + admin overrides."""
    overrides = _read_overrides()
    offers = {}
    for code, cfg in OFFERS.items():
        merged = dict(cfg, levels=list(cfg["levels"]))
        for field, val in (overrides.get("offers", {}).get(code) or {}).items():
            if field in EDITABLE_OFFER_FIELDS:
                merged[field] = list(val) if field == "levels" else val
        offers[code] = merged
    levels = dict(LEVEL_AVAILABLE_DEFAULT)
    levels.update({k: bool(v) for k, v in (overrides.get("levels") or {}).items() if k in levels})
    free = overrides.get("free_lessons", FREE_LESSONS_PER_COURSE)
    return {"offers": offers, "free_lessons": int(free) if isinstance(free, int) else FREE_LESSONS_PER_COURSE, "levels": levels}


def offer(code: str) -> dict | None:
    return effective()["offers"].get(code)


def free_lessons() -> int:
    return effective()["free_lessons"]


def level_available(level: str | None) -> bool:
    return bool(level) and effective()["levels"].get(level, False)


def is_offer(code: str) -> bool:
    return code in OFFERS


def is_purchasable(code: str) -> bool:
    cfg = offer(code)
    if not (cfg and cfg["active"] and cfg["sale_price"]):
        return False
    # a single level is sold only when it is available ("Tez orada" is not for sale)
    return cfg["kind"] != KIND_LEVEL or all(level_available(lv) for lv in cfg["levels"])


def offer_levels(code: str) -> list[str]:
    cfg = offer(code)
    return list(cfg["levels"]) if cfg else []


def offer_label(code: str) -> str | None:
    cfg = OFFERS.get(code)
    return cfg["label"] if cfg else None


def list_offers() -> list[dict]:
    eff = effective()
    return [
        {
            "code": code,
            "kind": cfg["kind"],
            "label": cfg["label"],
            "levels": list(cfg["levels"]),
            # levels of the package students can open today (B2 / C1 "Tez orada" are not)
            "available_levels": [lv for lv in cfg["levels"] if eff["levels"].get(lv)],
            "original_price": cfg["original_price"],
            "sale_price": cfg["sale_price"],
            "discount_percent": cfg["discount_percent"],
            "active": cfg["active"],
            "purchasable": is_purchasable(code),
            "free_lessons": eff["free_lessons"],
            "currency": "UZS",
        }
        for code, cfg in eff["offers"].items()
    ]


def validate_overrides(value: dict) -> dict:
    """Clean an admin's settings document; raises ValueError with a reason."""
    out: dict = {"offers": {}, "levels": {}}
    for code, cfg in (value.get("offers") or {}).items():
        if code not in OFFERS:
            raise ValueError(f"unknown offer {code}")
        clean = {}
        for field, val in (cfg or {}).items():
            if field not in EDITABLE_OFFER_FIELDS:
                continue
            if field in ("original_price", "sale_price"):
                if val is not None and (not isinstance(val, int) or isinstance(val, bool) or not 0 < val <= 100_000_000):
                    raise ValueError(f"{code}.{field}: price in UZS between 1 and 100 000 000, or empty")
            elif field == "discount_percent":
                if val is not None and (not isinstance(val, int) or isinstance(val, bool) or not 0 <= val <= 100):
                    raise ValueError(f"{code}.discount_percent: 0-100 or empty")
            elif field == "active":
                if not isinstance(val, bool):
                    raise ValueError(f"{code}.active: true / false")
            elif field == "levels":
                if not isinstance(val, list) or not val or any(lv not in ALL_LEVELS for lv in val) or len(set(val)) != len(val):
                    raise ValueError(f"{code}.levels: a non-empty list of {', '.join(ALL_LEVELS)}")
                if OFFERS[code]["kind"] == KIND_LEVEL and val != OFFERS[code]["levels"]:
                    raise ValueError(f"{code}.levels: a single-level offer always covers its own level")
                val = [lv for lv in ALL_LEVELS if lv in val]
            clean[field] = val
        if clean.get("active") and not clean.get("sale_price", OFFERS[code]["sale_price"]):
            raise ValueError(f"{code}: an active offer needs a sale price")
        out["offers"][code] = clean
    for level, available in (value.get("levels") or {}).items():
        if level not in ALL_LEVELS or not isinstance(available, bool):
            raise ValueError(f"levels.{level}: true / false")
        out["levels"][level] = available
    if "free_lessons" in value:
        free = value["free_lessons"]
        if not isinstance(free, int) or isinstance(free, bool) or not 0 <= free <= 5:
            raise ValueError("free_lessons: 0-5")
        out["free_lessons"] = free
    return out
