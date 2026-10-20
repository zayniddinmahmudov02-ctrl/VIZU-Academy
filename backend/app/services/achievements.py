"""Achievements / medals: configurable conditions checked on the server,
idempotent awarding and the order-discount reward.

* A medal is data (models/achievement.py). Its condition is one of
  CONDITION_TYPES with validated params — new medals need no code, new
  condition KINDS do (one function here).
* Awarding: INSERT ... ON CONFLICT DO NOTHING on uq_user_achievement — a
  reload, a repeated or a parallel request can never award twice.
* Lesson completion is the LMS rule (StudentProgress.lesson_completed, set by
  app.services.lms.progress) — opening a lesson never completes it.
* Reward (ORDER_DISCOUNT): fixed UZS off ONE order of the listed offers.
  AVAILABLE -> RESERVED (pending order) -> USED (approved); a rejected /
  expired order releases it again. The checkout price is always computed
  here, on the server (quote()).
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.achievement import (
    REWARD_NONE,
    REWARD_ORDER_DISCOUNT,
    REWARD_STATUS_AVAILABLE,
    REWARD_STATUS_NONE,
    REWARD_STATUS_RESERVED,
    REWARD_STATUS_USED,
    REWARD_TYPES,
    Achievement,
    AchievementCategory,
    UserAchievement,
)
from app.models.lesson import Lesson
from app.models.student_progress import StudentProgress
from app.services.lms import structure

logger = logging.getLogger(__name__)

ICON_PRESETS = ("rocket", "star", "trophy", "book", "flame", "crown")
ICON_COLORS = ("green", "blue", "purple", "gold", "red", "teal")
MAX_REWARD_UZS = 1_000_000


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Conditions
# ============================================================

def _level_lessons(db: Session, level: str) -> list[Lesson]:
    course = structure.level_course(db, level)
    module = structure.main_module(db, course) if course else None
    return structure.level_lessons(db, module, published_only=True)


def _completed_ids(db: Session, user_id, lesson_ids: list) -> set:
    if not lesson_ids:
        return set()
    return set(db.scalars(select(StudentProgress.lesson_id).where(
        StudentProgress.user_id == user_id, StudentProgress.lesson_id.in_(lesson_ids), StudentProgress.lesson_completed.is_(True))))


def _cond_lesson_completed(db: Session, user_id, params: dict) -> bool:
    lesson = next((x for x in _level_lessons(db, params["level"]) if x.number == params["lesson_number"]), None)
    return lesson is not None and lesson.id in _completed_ids(db, user_id, [lesson.id])


def _cond_level_lessons_completed(db: Session, user_id, params: dict) -> bool:
    ids = [x.id for x in _level_lessons(db, params["level"])]
    return len(_completed_ids(db, user_id, ids)) >= params["count"]


def _int_param(name: str, low: int, high: int):
    def check(value):
        if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
            raise ValueError(f"{name}: {low}–{high}")
        return value
    return check


def _level_param(value):
    if value not in structure.LEVELS:
        raise ValueError(f"level: {', '.join(structure.LEVELS)}")
    return value


# type -> params (validator per name), check, texts ({level}, {lesson_number}, {count} filled in)
CONDITION_TYPES: dict[str, dict] = {
    "LESSON_COMPLETED": {
        "params": {"level": _level_param, "lesson_number": _int_param("lesson_number", 1, 100)},
        "check": _cond_lesson_completed,
        "label_de": "Lektion abgeschlossen", "label_uz": "Dars yakunlandi",
        "text_de": "Schließe Lektion {lesson_number} im Kurs {level} erfolgreich ab.",
        "text_uz": "{level} kursining {lesson_number}-darsini muvaffaqiyatli yakunla.",
    },
    "LEVEL_LESSONS_COMPLETED": {
        "params": {"level": _level_param, "count": _int_param("count", 1, 100)},
        "check": _cond_level_lessons_completed,
        "label_de": "Lektionen eines Niveaus abgeschlossen", "label_uz": "Daraja darslari yakunlandi",
        "text_de": "Schließe {count} Lektionen im Kurs {level} erfolgreich ab.",
        "text_uz": "{level} kursida {count} ta darsni muvaffaqiyatli yakunla.",
    },
}


def validate_condition(condition_type: str, params: dict | None) -> dict:
    spec = CONDITION_TYPES.get(condition_type)
    if spec is None:
        raise ValueError(f"condition_type: {', '.join(CONDITION_TYPES)}")
    params = params or {}
    unknown = set(params) - set(spec["params"])
    if unknown:
        raise ValueError(f"unbekannte Parameter: {', '.join(sorted(unknown))}")
    return {name: check(params.get(name)) for name, check in spec["params"].items()}


def condition_texts(a: Achievement) -> dict:
    spec = CONDITION_TYPES.get(a.condition_type)
    if spec is None:
        return {"de": "", "uz": ""}
    p = a.condition_params or {}
    return {"de": spec["text_de"].format(**p), "uz": spec["text_uz"].format(**p)}


def condition_catalogue() -> list[dict]:
    return [{"type": t, "label_de": s["label_de"], "label_uz": s["label_uz"], "params": list(s["params"]),
             "levels": list(structure.LEVELS)} for t, s in CONDITION_TYPES.items()]


def condition_met(db: Session, user_id, a: Achievement) -> bool:
    spec = CONDITION_TYPES.get(a.condition_type)
    if spec is None:
        return False
    try:
        return bool(spec["check"](db, user_id, validate_condition(a.condition_type, a.condition_params)))
    except ValueError:
        logger.warning("achievement %s has invalid condition params", a.key)
        return False


# ============================================================
# Awarding (idempotent)
# ============================================================

def _reward_status(a: Achievement) -> str:
    return REWARD_STATUS_AVAILABLE if a.reward_type == REWARD_ORDER_DISCOUNT and a.reward_value > 0 else REWARD_STATUS_NONE


def award(db: Session, user_id, a: Achievement) -> bool:
    """Awards once; True only for the request that really inserted the row."""
    now = _now()
    stmt = insert(UserAchievement).values(
        id=uuid4(), user_id=user_id, achievement_id=a.id, awarded_at=now, reward_type=a.reward_type, reward_value=a.reward_value,
        reward_offers=list(a.reward_offers or []), reward_status=_reward_status(a), created_at=now, updated_at=now,
    ).on_conflict_do_nothing(constraint="uq_user_achievement").returning(UserAchievement.id)
    inserted = db.execute(stmt).scalar() is not None
    if inserted:
        from app.core.audit import write_audit

        db.commit()
        write_audit(db, None, "achievement_awarded", target_user_id=user_id,
                    details=f"{a.key} reward={a.reward_type}:{a.reward_value} {','.join(a.reward_offers or [])}")
    return inserted


def evaluate_user(db: Session, user_id) -> list[str]:
    """Checks every active medal the student does not have yet; returns the
    keys awarded now. Cheap: a handful of indexed queries."""
    owned = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)))
    new = []
    for a in db.scalars(select(Achievement).where(Achievement.is_active.is_(True))).all():
        if a.id not in owned and condition_met(db, user_id, a) and award(db, user_id, a):
            new.append(a.key)
    db.commit()
    return new


def evaluate_safely(db: Session, user_id) -> None:
    """Hook for progress events: an achievement problem must never break the
    lesson flow (it is evaluated again on the next dashboard visit)."""
    try:
        evaluate_user(db, user_id)
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("achievement evaluation failed for user %s", user_id)


# ============================================================
# Student view
# ============================================================

def _reward_view(type_: str, value: int, offers: list, status: str | None) -> dict | None:
    if type_ != REWARD_ORDER_DISCOUNT or value <= 0:
        return None
    return {"type": type_, "value": value, "offers": list(offers or []), "currency": "UZS", "status": status}


def _medal_view(a: Achievement, ua: UserAchievement | None) -> dict:
    texts = condition_texts(a)
    return {
        "id": str(a.id), "key": a.key,
        "category": {"key": a.category.key, "name_de": a.category.name_de, "name_uz": a.category.name_uz} if a.category else None,
        "name_de": a.name_de, "name_uz": a.name_uz, "description_de": a.description_de, "description_uz": a.description_uz,
        "icon_preset": a.icon_preset, "icon_color": a.icon_color, "image_url": a.image_url,
        "condition_de": texts["de"], "condition_uz": texts["uz"],
        "earned": ua is not None, "awarded_at": ua.awarded_at if ua else None,
        "reward": _reward_view(ua.reward_type, ua.reward_value, ua.reward_offers, ua.reward_status) if ua
        else _reward_view(a.reward_type, a.reward_value, a.reward_offers, None),
    }


def student_view(db: Session, user_id) -> dict:
    evaluate_safely(db, user_id)
    mine = {ua.achievement_id: ua for ua in db.scalars(select(UserAchievement).where(UserAchievement.user_id == user_id))}
    medals = db.scalars(select(Achievement).where((Achievement.is_active.is_(True)) | (Achievement.id.in_(list(mine) or [None])))).all()
    medals = sorted(medals, key=lambda a: ((a.category.order_index if a.category else 0), a.order_index, a.name_de))
    items = [_medal_view(a, mine.get(a.id)) for a in medals]
    return {"earned": sum(1 for i in items if i["earned"]), "total": len(items), "items": items}


# ============================================================
# Reward at checkout
# ============================================================

def _usable_reward(db: Session, user_id, plan: str, with_promo: bool, lock: bool) -> UserAchievement | None:
    q = (select(UserAchievement).join(Achievement, Achievement.id == UserAchievement.achievement_id)
         .where(UserAchievement.user_id == user_id, UserAchievement.reward_status == REWARD_STATUS_AVAILABLE,
                UserAchievement.reward_type == REWARD_ORDER_DISCOUNT, UserAchievement.reward_value > 0)
         .order_by(UserAchievement.reward_value.desc(), UserAchievement.awarded_at))
    if lock:
        q = q.with_for_update(of=UserAchievement)
    for ua in db.scalars(q).all():
        if plan in (ua.reward_offers or []) and (not with_promo or ua.achievement.reward_combine_with_promo):
            return ua
    return None


def quote(db: Session, user_id, plan: str, base_amount: int, promo_discount: int, *, lock: bool = False) -> dict:
    """The server-side price of one order: sale price - promo - medal reward
    (one reward per order, only for the offers it names)."""
    rest = max(base_amount - promo_discount, 0)
    ua = _usable_reward(db, user_id, plan, promo_discount > 0, lock)
    reward = min(ua.reward_value, rest) if ua else 0
    return {
        "base_amount": base_amount, "promo_discount": promo_discount, "reward_discount": reward,
        "final_amount": max(rest - reward, 0), "reward": ua,
        "reward_name": {"de": ua.achievement.name_de, "uz": ua.achievement.name_uz} if ua else None,
    }


def reserve(ua: UserAchievement, order_id) -> None:
    ua.reward_status = REWARD_STATUS_RESERVED
    ua.reward_order_id = order_id


def on_order_status(db: Session, order) -> None:
    """Called inside the transaction that changes an order's status."""
    # FOR UPDATE OF user_achievements only: the eager-loaded medal is an outer join Postgres cannot lock
    ua = db.scalar(select(UserAchievement).where(UserAchievement.reward_order_id == order.id).with_for_update(of=UserAchievement))
    if ua is None:
        return
    if order.status == "APPROVED":
        ua.reward_status = REWARD_STATUS_USED
        ua.reward_used_at = _now()
    elif order.status in ("REJECTED", "EXPIRED", "REFUNDED"):
        ua.reward_status = REWARD_STATUS_AVAILABLE
        ua.reward_order_id = None
        ua.reward_used_at = None


# ============================================================
# Admin
# ============================================================

def _clean_text(value, name: str, required: bool, max_len: int) -> str | None:
    text = " ".join(str(value or "").split()) if max_len <= 160 else str(value or "").strip()
    if required and not text:
        raise ValueError(f"{name} darf nicht leer sein")
    if len(text) > max_len:
        raise ValueError(f"{name}: max. {max_len} Zeichen")
    return text or None


def validate_achievement(data: dict, current: Achievement | None = None) -> dict:
    """Cleans a create / update payload (unknown fields ignored)."""
    from app.services.advertisement_validation import validate_image_url
    from app.services.vizu_pay.offers import OFFERS

    merged = {k: getattr(current, k) for k in ("name_de", "name_uz", "condition_type", "condition_params", "reward_type",
                                                "reward_value", "reward_offers")} if current else {}
    merged.update({k: v for k, v in data.items() if v is not None or k in ("description_de", "description_uz", "image_url")})
    out = {}
    if current is None or "key" in data:
        key = str(data.get("key") or "").strip().lower()
        if not key or len(key) > 60 or not all(c.isalnum() or c in "-_" for c in key):
            raise ValueError("key: a-z, 0-9, - und _ (max. 60)")
        out["key"] = key
    out["name_de"] = _clean_text(merged.get("name_de"), "name_de", True, 120)
    out["name_uz"] = _clean_text(merged.get("name_uz"), "name_uz", True, 120)
    for f in ("description_de", "description_uz"):
        if f in merged:
            out[f] = _clean_text(merged.get(f), f, False, 1000)
    if "icon_preset" in data:
        if data["icon_preset"] not in ICON_PRESETS:
            raise ValueError(f"icon_preset: {', '.join(ICON_PRESETS)}")
        out["icon_preset"] = data["icon_preset"]
    if "icon_color" in data:
        if data["icon_color"] not in ICON_COLORS:
            raise ValueError(f"icon_color: {', '.join(ICON_COLORS)}")
        out["icon_color"] = data["icon_color"]
    if "image_url" in data:
        out["image_url"] = validate_image_url(data.get("image_url"))
    out["condition_type"] = merged.get("condition_type")
    out["condition_params"] = validate_condition(out["condition_type"], merged.get("condition_params"))
    rtype = merged.get("reward_type") or REWARD_NONE
    if rtype not in REWARD_TYPES:
        raise ValueError(f"reward_type: {', '.join(REWARD_TYPES)}")
    out["reward_type"] = rtype
    if rtype == REWARD_ORDER_DISCOUNT:
        value = merged.get("reward_value")
        if not isinstance(value, int) or isinstance(value, bool) or not 0 < value <= MAX_REWARD_UZS:
            raise ValueError(f"reward_value: 1–{MAX_REWARD_UZS} UZS")
        offers = merged.get("reward_offers") or []
        if not isinstance(offers, list) or not offers or any(o not in OFFERS for o in offers):
            raise ValueError(f"reward_offers: mindestens eines von {', '.join(OFFERS)}")
        out["reward_value"], out["reward_offers"] = value, sorted(set(offers), key=list(OFFERS).index)
    else:
        out["reward_value"], out["reward_offers"] = 0, []
    for flag in ("is_active", "reward_combine_with_promo"):
        if flag in data:
            if not isinstance(data[flag], bool):
                raise ValueError(f"{flag}: true / false")
            out[flag] = data[flag]
    if "order_index" in data:
        out["order_index"] = _int_param("order_index", 0, 10_000)(data["order_index"])
    return out


def sync_unused_rewards(db: Session, a: Achievement) -> int:
    """After an admin changes a medal's reward: already awarded but unused
    (AVAILABLE) rewards follow the new value; reserved / used ones keep the
    value they were granted with (an order was created with it)."""
    rows = db.scalars(select(UserAchievement).where(UserAchievement.achievement_id == a.id,
                                                    UserAchievement.reward_status.in_((REWARD_STATUS_AVAILABLE, REWARD_STATUS_NONE)))).all()
    for ua in rows:
        ua.reward_type, ua.reward_value, ua.reward_offers = a.reward_type, a.reward_value, list(a.reward_offers or [])
        ua.reward_status = _reward_status(a)
    return len(rows)


def admin_item(db: Session, a: Achievement) -> dict:
    counts = dict(db.execute(select(UserAchievement.reward_status, func.count()).where(UserAchievement.achievement_id == a.id)
                             .group_by(UserAchievement.reward_status)).all())
    return {
        "id": str(a.id), "key": a.key, "category_id": str(a.category_id),
        "category": {"key": a.category.key, "name_de": a.category.name_de, "name_uz": a.category.name_uz} if a.category else None,
        "name_de": a.name_de, "name_uz": a.name_uz, "description_de": a.description_de, "description_uz": a.description_uz,
        "icon_preset": a.icon_preset, "icon_color": a.icon_color, "image_url": a.image_url,
        "condition_type": a.condition_type, "condition_params": a.condition_params, **{f"condition_{k}": v for k, v in condition_texts(a).items()},
        "reward_type": a.reward_type, "reward_value": a.reward_value, "reward_offers": a.reward_offers,
        "reward_combine_with_promo": a.reward_combine_with_promo, "is_active": a.is_active, "order_index": a.order_index,
        "awarded_count": sum(counts.values()), "reward_counts": counts, "created_at": a.created_at, "updated_at": a.updated_at,
    }


def category_or_422(db: Session, category_id) -> AchievementCategory:
    try:
        cat = db.get(AchievementCategory, category_id)
    except Exception:  # noqa: BLE001 - malformed id
        cat = None
    if cat is None:
        raise HTTPException(status_code=422, detail="category_id: unbekannte Kategorie")
    return cat
