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


def is_offer(code: str) -> bool:
    return code in OFFERS


def is_purchasable(code: str) -> bool:
    offer = OFFERS.get(code)
    return bool(offer and offer["active"] and offer["sale_price"])


def offer_levels(code: str) -> list[str]:
    offer = OFFERS.get(code)
    return list(offer["levels"]) if offer else []


def offer_label(code: str) -> str | None:
    offer = OFFERS.get(code)
    return offer["label"] if offer else None


def list_offers() -> list[dict]:
    return [
        {
            "code": code,
            "kind": cfg["kind"],
            "label": cfg["label"],
            "levels": list(cfg["levels"]),
            "original_price": cfg["original_price"],
            "sale_price": cfg["sale_price"],
            "discount_percent": cfg["discount_percent"],
            "active": cfg["active"],
            "free_lessons": FREE_LESSONS_PER_COURSE,
            "currency": "UZS",
        }
        for code, cfg in OFFERS.items()
    ]
