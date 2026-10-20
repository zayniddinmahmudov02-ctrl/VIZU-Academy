"""Whitelist of the student pages an internal link (Werbung-Banner) may point
to — the single registry the admin picks from (GET /admin/advertisements/
internal-routes) and the server resolves at display time. Only real pages of
the student panel (frontend/src/app/(dashboard), checked by
tests/test_student_routes.py); parameters only from fixed choices, so a
stored link can never become an arbitrary path or an open redirect.

A link to a page does not grant access: every page keeps its own rules
(paid lessons stay closed, a course not for sale cannot be bought).

A route removed from this registry later (or a parameter value no longer
allowed) does not break a stored advertisement: `resolve()` falls back to
FALLBACK_PATH and the admin list marks the link as invalid."""

from urllib.parse import quote, urlencode

from app.services.vizu_pay.offers import ALL_LEVELS, OFFERS

FALLBACK_PATH = "/dashboard"

# {key: {group, label, path, params: {name: (choices...)}, query: {name: (choices...)}}}
# `path` placeholders ({level}) are filled from `params`; `query` becomes ?name=value.
STUDENT_ROUTES: dict[str, dict] = {
    "dashboard": {"group": "Allgemein", "label": "Dashboard", "path": "/dashboard"},
    "informationen": {"group": "Allgemein", "label": "Informationen", "path": "/informationen"},
    "profile": {"group": "Allgemein", "label": "Profil", "path": "/profile"},
    "settings": {"group": "Allgemein", "label": "Einstellungen", "path": "/settings"},
    "kurse": {"group": "Kurse", "label": "Alle Kurse (A1–C1)", "path": "/kurse"},
    "kurse_level": {
        "group": "Kurse",
        "label": "Kurs eines Niveaus",
        "path": "/kurse/{level}",
        "params": {"level": tuple(lv.lower() for lv in ALL_LEVELS)},
    },
    "woerterbuch": {"group": "Lernen", "label": "Wörterbuch", "path": "/woerterbuch"},
    "certificates": {"group": "Lernen", "label": "Zertifikate", "path": "/certificates"},
    "vorbereitung": {"group": "Prüfungsvorbereitung", "label": "Vorbereitung", "path": "/vorbereitung"},
    "vizu_multilevel": {"group": "Prüfungsvorbereitung", "label": "VIZU-Multilevel", "path": "/vizu-multilevel"},
    "angebote": {"group": "Angebote", "label": "Angebote & Preise", "path": "/angebote"},
    "angebote_offer": {
        "group": "Angebote",
        "label": "Angebot direkt öffnen (Checkout)",
        "path": "/angebote",
        "query": {"offer": tuple(OFFERS)},
    },
}


def _spec(route: dict) -> dict[str, tuple]:
    return {**route.get("params", {}), **route.get("query", {})}


def validate(key: str | None, params: dict | None) -> dict:
    """Clean params for a registered route; raises ValueError with a reason."""
    route = STUDENT_ROUTES.get(key or "")
    if route is None:
        raise ValueError("Unbekannte Seite — bitte eine Seite aus der Liste wählen.")
    params = params or {}
    if not isinstance(params, dict):
        raise ValueError("Ungültige Parameter.")
    spec = _spec(route)
    unknown = set(params) - set(spec)
    if unknown:
        raise ValueError(f"Unbekannter Parameter: {', '.join(sorted(unknown))}.")
    clean = {}
    for name, choices in spec.items():
        value = params.get(name)
        if not isinstance(value, str) or value not in choices:
            raise ValueError(f"Parameter „{name}“: bitte einen der Werte {', '.join(choices)} wählen.")
        clean[name] = value
    return clean


def resolve(key: str | None, params: dict | None) -> tuple[str, bool]:
    """(path, valid). An unknown route or a no longer allowed parameter gives
    (FALLBACK_PATH, False) — never an unchecked path."""
    try:
        clean = validate(key, params)
    except ValueError:
        return FALLBACK_PATH, False
    route = STUDENT_ROUTES[key]
    path = route["path"].format(**{k: quote(clean[k], safe="") for k in route.get("params", {})})
    query = {k: clean[k] for k in route.get("query", {})}
    return (f"{path}?{urlencode(query)}" if query else path), True


def catalogue() -> list[dict]:
    """For the admin picker: grouped, with each parameter's allowed values."""
    return [
        {
            "key": key,
            "group": route["group"],
            "label": route["label"],
            "path": route["path"],
            "params": [{"name": name, "choices": list(choices)} for name, choices in _spec(route).items()],
        }
        for key, route in STUDENT_ROUTES.items()
    ]
