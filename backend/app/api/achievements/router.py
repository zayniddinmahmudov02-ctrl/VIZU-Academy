"""Achievements / medals — student view (own medals only) and admin CMS.

Students can only READ their medals; awarding happens exclusively on the
server (app.services.achievements, on lesson completion and on this read).
Admin changes are Super-Admin only (a medal can carry a money reward) and
audited."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_super_admin
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.achievement import Achievement, AchievementCategory, UserAchievement
from app.models.subscription_order import SubscriptionOrder
from app.models.user import User
from app.services import achievements as service

router = APIRouter(prefix="/achievements", tags=["Achievements"])


@router.get("/me")
def my_achievements(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """The caller's medals (earned + still open, with conditions and rewards).
    Newly met conditions are awarded here too (idempotent)."""
    return service.student_view(db, current_user.id)


admin_router = APIRouter(prefix="/admin/achievements", tags=["Admin - Achievements"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _422(exc: ValueError):
    raise HTTPException(status_code=422, detail=f"INVALID_ACHIEVEMENT: {exc}") from None


# ---- catalogue (condition types, icons, offers) ----

@admin_router.get("/meta")
def meta(_: User = Depends(require_super_admin)):
    from app.services.vizu_pay.offers import OFFERS

    return {"conditions": service.condition_catalogue(), "icon_presets": list(service.ICON_PRESETS), "icon_colors": list(service.ICON_COLORS),
            "reward_types": ["NONE", "ORDER_DISCOUNT"], "offers": [{"code": c, "label": o["label"]} for c, o in OFFERS.items()],
            "max_reward": service.MAX_REWARD_UZS}


# ---- categories ----

class CategoryIn(BaseModel):
    key: str | None = Field(default=None, max_length=60)
    name_de: str | None = Field(default=None, max_length=120)
    name_uz: str | None = Field(default=None, max_length=120)
    order_index: int | None = Field(default=None, ge=0, le=10_000)
    is_active: bool | None = None


def _category(c: AchievementCategory, count: int = 0) -> dict:
    return {"id": str(c.id), "key": c.key, "name_de": c.name_de, "name_uz": c.name_uz, "order_index": c.order_index,
            "is_active": c.is_active, "achievement_count": count}


@admin_router.get("/categories")
def list_categories(db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    cats = db.scalars(select(AchievementCategory).order_by(AchievementCategory.order_index, AchievementCategory.name_de)).all()
    counts = {}
    for a in db.scalars(select(Achievement)).all():
        counts[a.category_id] = counts.get(a.category_id, 0) + 1
    return [_category(c, counts.get(c.id, 0)) for c in cats]


@admin_router.post("/categories", status_code=201)
def create_category(data: CategoryIn, request: Request, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    key = (data.key or "").strip().lower()
    if not key or not all(ch.isalnum() or ch in "-_" for ch in key) or not (data.name_de or "").strip() or not (data.name_uz or "").strip():
        raise HTTPException(status_code=422, detail="INVALID_CATEGORY: key (a-z, 0-9, -, _), name_de and name_uz required")
    if db.scalar(select(AchievementCategory).where(AchievementCategory.key == key)):
        raise HTTPException(status_code=409, detail="CATEGORY_KEY_EXISTS")
    cat = AchievementCategory(key=key, name_de=data.name_de.strip(), name_uz=data.name_uz.strip(), order_index=data.order_index or 0,
                              is_active=True if data.is_active is None else data.is_active)
    db.add(cat)
    db.commit()
    write_audit(db, str(user.id), "achievement_category_created", details=key, ip_address=_ip(request))
    return _category(cat)


@admin_router.put("/categories/{category_id}")
def update_category(category_id: UUID, data: CategoryIn, request: Request, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    cat = db.get(AchievementCategory, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    for field in ("name_de", "name_uz"):
        value = getattr(data, field)
        if value is not None:
            if not value.strip():
                raise HTTPException(status_code=422, detail=f"INVALID_CATEGORY: {field} required")
            setattr(cat, field, value.strip())
    if data.order_index is not None:
        cat.order_index = data.order_index
    if data.is_active is not None:
        cat.is_active = data.is_active
    db.commit()
    write_audit(db, str(user.id), "achievement_category_updated", details=cat.key, ip_address=_ip(request))
    return _category(cat)


# ---- medals ----

@admin_router.get("")
def list_achievements(category_id: UUID | None = None, db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    q = select(Achievement).order_by(Achievement.order_index, Achievement.name_de)
    if category_id:
        q = q.where(Achievement.category_id == category_id)
    return [service.admin_item(db, a) for a in db.scalars(q).all()]


@admin_router.post("", status_code=201)
def create_achievement(payload: dict, request: Request, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    cat = service.category_or_422(db, payload.get("category_id"))
    try:
        clean = service.validate_achievement(payload)
    except ValueError as exc:
        _422(exc)
    if db.scalar(select(Achievement).where(Achievement.key == clean["key"])):
        raise HTTPException(status_code=409, detail="ACHIEVEMENT_KEY_EXISTS")
    a = Achievement(category_id=cat.id, **clean)
    db.add(a)
    db.commit()
    db.refresh(a)
    write_audit(db, str(user.id), "achievement_created", details=json.dumps(service.admin_item(db, a), default=str)[:4000], ip_address=_ip(request))
    return service.admin_item(db, a)


@admin_router.put("/{achievement_id}")
def update_achievement(achievement_id: UUID, payload: dict, request: Request, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    a = db.get(Achievement, achievement_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Achievement not found.")
    before = service.admin_item(db, a)
    payload = {k: v for k, v in payload.items() if k != "key"}  # the key is the stable identifier
    try:
        clean = service.validate_achievement(payload, current=a)
    except ValueError as exc:
        _422(exc)
    if "category_id" in payload:
        a.category_id = service.category_or_422(db, payload["category_id"]).id
    reward_changed = any(clean.get(f) != getattr(a, f) for f in ("reward_type", "reward_value", "reward_offers"))
    for field, value in clean.items():
        setattr(a, field, value)
    synced = service.sync_unused_rewards(db, a) if reward_changed else 0
    db.commit()
    db.refresh(a)
    after = service.admin_item(db, a)
    write_audit(db, str(user.id), "achievement_updated", ip_address=_ip(request),
                details=json.dumps({"before": before, "after": after, "unused_rewards_updated": synced}, default=str)[:4000])
    return after


@admin_router.get("/{achievement_id}/awards")
def list_awards(achievement_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    """Who has this medal, since when, and what happened to the reward."""
    if db.get(Achievement, achievement_id) is None:
        raise HTTPException(status_code=404, detail="Achievement not found.")
    rows = db.execute(
        select(UserAchievement, User, SubscriptionOrder)
        .join(User, User.id == UserAchievement.user_id)
        .outerjoin(SubscriptionOrder, SubscriptionOrder.id == UserAchievement.reward_order_id)
        .where(UserAchievement.achievement_id == achievement_id)
        .order_by(UserAchievement.awarded_at.desc())
    ).all()
    return [{
        "id": str(ua.id), "user_id": str(u.id), "email": u.email, "name": " ".join(x for x in (u.first_name, u.last_name) if x) or u.username,
        "awarded_at": ua.awarded_at, "reward_type": ua.reward_type, "reward_value": ua.reward_value, "reward_status": ua.reward_status,
        "reward_used_at": ua.reward_used_at,
        "order": {"id": str(o.id), "plan": o.plan, "status": o.status, "final_amount": o.final_amount} if o else None,
    } for ua, u, o in rows]
