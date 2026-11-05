"""Arena themes (one per stage A1 … C1, C1+): city background for desktop and mobile, accent colour,
overlay strength, attribution, active flag.

Admins write a draft (`battle_themes.draft`), preview it, then publish — publishing copies the draft into
the live columns. A theme cannot be published without author + licence (no unlicensed picture goes live).
Images are either shipped with the frontend ("static:/battle/themes/<file>.webp") or uploaded by an admin
("asset:<random>.webp", app/protected_storage/battle-themes, served publicly — backgrounds are not secret).
Defaults: app/data/battle/themes.json, written by app.scripts.battle_seed."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.battle import BattleTheme
from app.models.user import User
from app.services.battle import config, media

DEFAULTS = Path(__file__).resolve().parents[2] / "data" / "battle" / "themes.json"
FIELDS = ("city", "title", "subtitle", "desktop_image", "mobile_image", "accent", "overlay", "attribution", "is_active")
STATIC_RE = re.compile(r"^static:/battle/themes/[a-z0-9][a-z0-9_-]{0,80}\.(webp|jpg|avif)$")
ASSET_RE = re.compile(r"^asset:[0-9a-f]{32}\.webp$")
ACCENT_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
ATTRIBUTION_KEYS = ("title", "author", "license", "license_url", "source_url")


def defaults() -> list[dict]:
    return json.loads(DEFAULTS.read_text(encoding="utf-8"))["themes"]


def _live(t: BattleTheme) -> dict:
    return {f: getattr(t, f) for f in FIELDS}


def view(t: BattleTheme, admin: bool = False) -> dict:
    out = {"stage": t.level, **_live(t), "published_at": t.published_at.isoformat() if t.published_at else None}
    if admin:
        out["draft"] = t.draft
    return out


def public_list(db: Session) -> list[dict]:
    rows = {t.level: t for t in db.execute(select(BattleTheme)).scalars()}
    out = []
    for d in defaults():
        t = rows.get(d["stage"])
        if t is not None and t.is_active and t.published_at is not None:
            out.append(view(t))
        else:
            out.append({"stage": d["stage"], **{f: d.get(f) for f in FIELDS}, "is_active": True, "published_at": None})
    return out


def for_stage(db: Session, stage: str) -> dict:
    return next(t for t in public_list(db) if t["stage"] == stage)


def admin_list(db: Session) -> list[dict]:
    rows = {t.level: t for t in db.execute(select(BattleTheme)).scalars()}
    return [view(rows[s], admin=True) if s in rows else {"stage": s, "missing": True} for s in config.STAGES]


def _check_image(ref: str | None) -> None:
    if ref is None or ref == "":
        return
    if STATIC_RE.match(ref):
        return
    if ASSET_RE.match(ref):
        media.safe_path(media.THEME_ROOT, ref.split(":", 1)[1])
        return
    raise HTTPException(422, "THEME_IMAGE_INVALID")


def validate(data: dict) -> dict:
    clean = {}
    for k, v in data.items():
        if k not in FIELDS:
            raise HTTPException(422, f"THEME_FIELD_UNKNOWN: {k}")
        clean[k] = v
    for k in ("desktop_image", "mobile_image"):
        if k in clean:
            _check_image(clean[k])
    if "accent" in clean and not ACCENT_RE.match(str(clean["accent"])):
        raise HTTPException(422, "THEME_ACCENT_INVALID")
    if "overlay" in clean and not (isinstance(clean["overlay"], int) and 0 <= clean["overlay"] <= 90):
        raise HTTPException(422, "THEME_OVERLAY_INVALID")
    if "attribution" in clean:
        a = clean["attribution"] or {}
        if not isinstance(a, dict) or set(a) - set(ATTRIBUTION_KEYS):
            raise HTTPException(422, "THEME_ATTRIBUTION_INVALID")
        clean["attribution"] = {k: str(a.get(k) or "")[:500] for k in ATTRIBUTION_KEYS}
    for k, limit in (("city", 60), ("title", 120), ("subtitle", 200)):
        if k in clean:
            clean[k] = (str(clean[k] or "")).strip()[:limit]
            if k != "subtitle" and not clean[k]:
                raise HTTPException(422, f"THEME_{k.upper()}_REQUIRED")
    if "is_active" in clean:
        clean["is_active"] = bool(clean["is_active"])
    return clean


def _get(db: Session, stage: str) -> BattleTheme:
    if stage not in config.STAGES:
        raise HTTPException(404, "THEME_NOT_FOUND")
    t = db.execute(select(BattleTheme).where(BattleTheme.level == stage).with_for_update()).scalar_one_or_none()
    if t is None:
        raise HTTPException(404, "THEME_NOT_FOUND: run app.scripts.battle_seed")
    return t


def save_draft(db: Session, actor: User, stage: str, data: dict) -> dict:
    t = _get(db, stage)
    t.draft = {**_live(t), **(t.draft or {}), **validate(data)}
    t.updated_by = actor.id
    write_audit(db, str(actor.id), "battle_theme_draft", details=json.dumps({"stage": stage, "fields": sorted(data)}))
    db.commit()
    return view(t, admin=True)


def publish(db: Session, actor: User, stage: str) -> dict:
    t = _get(db, stage)
    if not t.draft:
        raise HTTPException(409, "THEME_NO_DRAFT")
    d = {**_live(t), **validate(t.draft)}
    a = d.get("attribution") or {}
    if (d.get("desktop_image") or d.get("mobile_image")) and not (a.get("author") and a.get("license")):
        raise HTTPException(422, "THEME_ATTRIBUTION_REQUIRED: Autor und Lizenz sind Pflicht")
    for f in FIELDS:
        setattr(t, f, d[f])
    t.draft = None
    t.published_at = datetime.now(timezone.utc)
    t.updated_by = actor.id
    write_audit(db, str(actor.id), "battle_theme_publish", details=json.dumps({"stage": stage}))
    db.commit()
    return view(t, admin=True)


def discard(db: Session, actor: User, stage: str) -> dict:
    t = _get(db, stage)
    t.draft = None
    db.commit()
    return view(t, admin=True)


def upload_asset(db: Session, actor: User, data: bytes, filename: str | None, content_type: str | None, kind: str) -> dict:
    if kind not in media.THEME_MAX_SIDE:
        raise HTTPException(422, "THEME_KIND_INVALID")
    webp, w, h = media.normalise(data, filename, content_type, media.THEME_MAX_SIDE[kind], min_side=600)
    name = media.store(media.THEME_ROOT, webp)
    write_audit(db, str(actor.id), "battle_theme_asset_upload", details=json.dumps({"name": name, "kind": kind, "width": w, "height": h}))
    db.commit()
    return {"ref": f"asset:{name}", "width": w, "height": h, "size_bytes": len(webp)}


def serve_asset(name: str):
    if not ASSET_RE.match(f"asset:{name}"):
        raise HTTPException(404, "NOT_FOUND")
    return media.serve(media.safe_path(media.THEME_ROOT, name), private=False)
