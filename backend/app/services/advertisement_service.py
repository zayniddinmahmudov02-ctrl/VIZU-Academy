"""Werbung-Banner: selection of the dashboard advertisement, real impression
/ click tracking with de-duplication, admin CRUD and analytics."""

import hashlib
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.advertisement import EVENT_CLICK, EVENT_IMPRESSION, Advertisement, AdvertisementEvent
from app.services.advertisement_validation import ctr

# A student who keeps the dashboard open / navigates back and forth is
# counted at most once per window; a click is counted at most once per
# window per browser — repeated legitimate visits later still count.
IMPRESSION_DEDUP_WINDOW = timedelta(minutes=30)
CLICK_DEDUP_WINDOW = timedelta(seconds=10)
SERIES_DAYS = 14


def _now() -> datetime:
    return datetime.now(timezone.utc)


def eligible_filter(now: datetime):
    """Active and inside its (optional) date range."""
    return and_(
        Advertisement.is_active.is_(True),
        or_(Advertisement.starts_at.is_(None), Advertisement.starts_at <= now),
        or_(Advertisement.ends_at.is_(None), Advertisement.ends_at > now),
    )


def get_current(db: Session) -> Advertisement | None:
    """The single advertisement students see: highest priority among the
    eligible ones, most recently updated on a tie."""
    now = _now()
    return db.scalar(
        select(Advertisement)
        .where(eligible_filter(now))
        .order_by(Advertisement.priority.desc(), Advertisement.updated_at.desc())
        .limit(1)
    )


def is_eligible(ad: Advertisement, now: datetime | None = None) -> bool:
    now = now or _now()
    return bool(
        ad.is_active
        and (ad.starts_at is None or ad.starts_at <= now)
        and (ad.ends_at is None or ad.ends_at > now)
    )


def to_public(ad: Advertisement) -> dict:
    return {
        "id": ad.id,
        "title": ad.title,
        "description": ad.description,
        "image_url": ad.image_url,
        "cta_text": ad.cta_text,
        "click_path": f"/api/v1/advertisements/{ad.id}/click",
    }


def client_hash(ip: str | None, user_agent: str | None) -> str:
    return hashlib.sha256(f"{ip or ''}|{user_agent or ''}".encode("utf-8")).hexdigest()


# ============================================================
# Tracking
# ============================================================


def record_impression(db: Session, ad: Advertisement, user_id: UUID) -> bool:
    """Counts an impression of the CURRENT dashboard ad, at most once per
    user per IMPRESSION_DEDUP_WINDOW. Returns whether it was counted."""
    current = get_current(db)
    if current is None or current.id != ad.id:
        return False
    recent = db.scalar(
        select(AdvertisementEvent.id).where(
            AdvertisementEvent.advertisement_id == ad.id,
            AdvertisementEvent.event_type == EVENT_IMPRESSION,
            AdvertisementEvent.user_id == user_id,
            AdvertisementEvent.created_at > _now() - IMPRESSION_DEDUP_WINDOW,
        ).limit(1)
    )
    if recent is not None:
        return False
    db.add(AdvertisementEvent(advertisement_id=ad.id, event_type=EVENT_IMPRESSION, user_id=user_id))
    db.commit()
    return True


def record_click(db: Session, ad: Advertisement, client: str) -> bool:
    """Counts a click unless the same browser clicked this ad within
    CLICK_DEDUP_WINDOW (double clicks / immediate re-opens)."""
    recent = db.scalar(
        select(AdvertisementEvent.id).where(
            AdvertisementEvent.advertisement_id == ad.id,
            AdvertisementEvent.event_type == EVENT_CLICK,
            AdvertisementEvent.client_hash == client,
            AdvertisementEvent.created_at > _now() - CLICK_DEDUP_WINDOW,
        ).limit(1)
    )
    if recent is not None:
        return False
    db.add(AdvertisementEvent(advertisement_id=ad.id, event_type=EVENT_CLICK, client_hash=client))
    db.commit()
    return True


# ============================================================
# Admin
# ============================================================


def _counts(db: Session, ad_ids: list[UUID]) -> dict[UUID, tuple[int, int]]:
    if not ad_ids:
        return {}
    rows = db.execute(
        select(
            AdvertisementEvent.advertisement_id,
            func.sum(case((AdvertisementEvent.event_type == EVENT_IMPRESSION, 1), else_=0)),
            func.sum(case((AdvertisementEvent.event_type == EVENT_CLICK, 1), else_=0)),
        )
        .where(AdvertisementEvent.advertisement_id.in_(ad_ids))
        .group_by(AdvertisementEvent.advertisement_id)
    ).all()
    return {row[0]: (int(row[1] or 0), int(row[2] or 0)) for row in rows}


def _to_admin(ad: Advertisement, counts: tuple[int, int], current_id: UUID | None) -> dict:
    impressions, clicks = counts
    return {
        "id": ad.id,
        "title": ad.title,
        "description": ad.description,
        "image_url": ad.image_url,
        "target_url": ad.target_url,
        "cta_text": ad.cta_text,
        "is_active": ad.is_active,
        "priority": ad.priority,
        "starts_at": ad.starts_at,
        "ends_at": ad.ends_at,
        "created_at": ad.created_at,
        "updated_at": ad.updated_at,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr(impressions, clicks),
        "is_current": ad.id == current_id,
    }


def list_admin(db: Session) -> list[dict]:
    ads = list(db.scalars(select(Advertisement).order_by(Advertisement.priority.desc(), Advertisement.updated_at.desc())))
    counts = _counts(db, [a.id for a in ads])
    current = get_current(db)
    return [_to_admin(a, counts.get(a.id, (0, 0)), current.id if current else None) for a in ads]


def get(db: Session, ad_id: UUID) -> Advertisement | None:
    return db.scalar(select(Advertisement).where(Advertisement.id == ad_id))


def get_admin(db: Session, ad_id: UUID) -> dict | None:
    ad = get(db, ad_id)
    if ad is None:
        return None
    current = get_current(db)
    return _to_admin(ad, _counts(db, [ad.id]).get(ad.id, (0, 0)), current.id if current else None)


def create(db: Session, data) -> dict:
    ad = Advertisement(**data.model_dump())
    db.add(ad)
    db.commit()
    return get_admin(db, ad.id)


def update(db: Session, ad_id: UUID, data) -> dict | None:
    ad = get(db, ad_id)
    if ad is None:
        return None
    updates = data.model_dump(exclude_unset=True)
    starts = updates.get("starts_at", ad.starts_at)
    ends = updates.get("ends_at", ad.ends_at)
    if starts and ends and ends <= starts:
        raise ValueError("Enddatum muss nach dem Startdatum liegen.")
    for field, value in updates.items():
        if field in ("title", "target_url", "cta_text") and value is None:
            continue  # required fields cannot be cleared
        setattr(ad, field, value)
    db.commit()
    return get_admin(db, ad_id)


def delete(db: Session, ad_id: UUID) -> bool:
    ad = get(db, ad_id)
    if ad is None:
        return False
    db.delete(ad)
    db.commit()
    return True


def analytics(db: Session, ad_id: UUID) -> dict | None:
    ad = get(db, ad_id)
    if ad is None:
        return None
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)
    series_start = today_start - timedelta(days=SERIES_DAYS - 1)

    def count(event: str, since: datetime | None = None) -> int:
        query = select(func.count(AdvertisementEvent.id)).where(
            AdvertisementEvent.advertisement_id == ad_id, AdvertisementEvent.event_type == event
        )
        if since is not None:
            query = query.where(AdvertisementEvent.created_at >= since)
        return int(db.scalar(query) or 0)

    day = func.date_trunc("day", AdvertisementEvent.created_at)
    rows = db.execute(
        select(day, AdvertisementEvent.event_type, func.count(AdvertisementEvent.id))
        .where(AdvertisementEvent.advertisement_id == ad_id, AdvertisementEvent.created_at >= series_start)
        .group_by(day, AdvertisementEvent.event_type)
    ).all()
    by_day: dict[date, dict[str, int]] = {}
    for bucket, event, n in rows:
        by_day.setdefault(bucket.date(), {})[event] = int(n)
    series = []
    for i in range(SERIES_DAYS):
        d = (series_start + timedelta(days=i)).date()
        series.append(
            {
                "date": d.isoformat(),
                "impressions": by_day.get(d, {}).get(EVENT_IMPRESSION, 0),
                "clicks": by_day.get(d, {}).get(EVENT_CLICK, 0),
            }
        )

    impressions, clicks = count(EVENT_IMPRESSION), count(EVENT_CLICK)
    return {
        "advertisement_id": ad_id,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr(impressions, clicks),
        "impressions_today": count(EVENT_IMPRESSION, today_start),
        "clicks_today": count(EVENT_CLICK, today_start),
        "impressions_week": count(EVENT_IMPRESSION, week_start),
        "clicks_week": count(EVENT_CLICK, week_start),
        "series": series,
    }
