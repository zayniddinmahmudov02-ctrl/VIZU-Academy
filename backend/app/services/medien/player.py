"""Film player of Medienwelt, student side: the subtitle appearance settings (kept per user = the "profile" part), the per-film
state that "continue watching" restores (subtitle language, dual subtitles, speed, quality) and the previous / next film.

Everything stored is validated against fixed lists here — a request can never put free text into the JSON columns."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medien import STATUS_PUBLISHED, Film, MediaPlayerPrefs
from app.models.user import User

LANGUAGES = ("de", "uz", "en", "ru")
SIZES = ("small", "medium", "large")
POSITIONS = ("bottom", "higher")
FONTS = ("sans", "serif", "mono")
COLORS = ("#ffffff", "#ffe066", "#7dd3fc", "#86efac", "#f9a8d4")
SPEEDS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)

PREF_DEFAULTS = {"enabled": True, "size": "medium", "color": "#ffffff", "bg_opacity": 75, "position": "bottom", "font": "sans",
                 "dual": False, "secondary": "uz"}


def _clean_label(value, limit: int = 20) -> str | None:
    text = str(value or "").strip()
    return text[:limit] if text and all(ch.isalnum() or ch in " ._-" for ch in text) else None


def clean_prefs(raw: dict | None) -> dict:
    """Only the known keys with valid values (anything else is dropped)."""
    raw = raw or {}
    out: dict = {}
    if isinstance(raw.get("enabled"), bool):
        out["enabled"] = raw["enabled"]
    if raw.get("size") in SIZES:
        out["size"] = raw["size"]
    if raw.get("color") in COLORS:
        out["color"] = raw["color"]
    opacity = raw.get("bg_opacity")
    if isinstance(opacity, (int, float)) and not isinstance(opacity, bool) and 0 <= opacity <= 100:
        out["bg_opacity"] = int(round(opacity))
    if raw.get("position") in POSITIONS:
        out["position"] = raw["position"]
    if raw.get("font") in FONTS:
        out["font"] = raw["font"]
    if isinstance(raw.get("dual"), bool):
        out["dual"] = raw["dual"]
    if raw.get("secondary") in LANGUAGES:
        out["secondary"] = raw["secondary"]
    return out


def clean_state(raw: dict | None) -> dict:
    """The per-film state: subtitle ("off" or a language), dual + secondary language, speed (a menu value), quality / audio label."""
    raw = raw or {}
    out: dict = {}
    if raw.get("subtitle") == "off" or raw.get("subtitle") in LANGUAGES:
        out["subtitle"] = raw["subtitle"]
    if isinstance(raw.get("dual"), bool):
        out["dual"] = raw["dual"]
    if raw.get("secondary") in LANGUAGES:
        out["secondary"] = raw["secondary"]
    speed = raw.get("speed")
    if isinstance(speed, (int, float)) and not isinstance(speed, bool) and float(speed) in SPEEDS:
        out["speed"] = float(speed)
    for key in ("quality", "audio"):
        label = _clean_label(raw.get(key))
        if label:
            out[key] = label
    return out


def get_prefs(db: Session, user: User) -> dict:
    row = db.scalar(select(MediaPlayerPrefs).where(MediaPlayerPrefs.user_id == user.id))
    return {**PREF_DEFAULTS, **clean_prefs(row.prefs if row else None)}


def save_prefs(db: Session, user: User, data: dict) -> dict:
    """Merges the given keys into the stored settings (a partial update is fine) and returns the complete, validated set."""
    row = db.scalar(select(MediaPlayerPrefs).where(MediaPlayerPrefs.user_id == user.id).with_for_update())
    merged = {**clean_prefs(row.prefs if row else None), **clean_prefs(data)}
    if row is None:
        db.add(MediaPlayerPrefs(user_id=user.id, prefs=merged))
    else:
        row.prefs = merged
    db.commit()
    return {**PREF_DEFAULTS, **merged}


def neighbors(db: Session, film: Film) -> dict:
    """The film before / after this one in the "new" order of the student list (same category when it has one)."""
    stmt = select(Film.id, Film.title).where(Film.status == STATUS_PUBLISHED)
    if film.category_id:
        stmt = stmt.where(Film.category_id == film.category_id)
    rows = db.execute(stmt.order_by(Film.created_at.desc(), Film.id)).all()
    ids = [r.id for r in rows]
    if film.id not in ids:
        return {"prev": None, "next": None}
    i = ids.index(film.id)
    pick = lambda r: {"id": r.id, "title": r.title}  # noqa: E731
    return {"prev": pick(rows[i - 1]) if i > 0 else None, "next": pick(rows[i + 1]) if i + 1 < len(rows) else None}
