"""Course access reminders (owner 2026-11-25: course access stays time-limited, but students must not be surprised).

* Three days before the access of an APPROVED course / package order ends, its student gets ONE notification (uz / de) with the
  date and a link to renew the same package (`/angebote?offer=<plan>`).
* Nothing is sent when a newer approved order of the same student already covers every level of the ending one beyond its end
  (renewed in time) — the order is still marked, so it is looked at only once.
* `subscription_orders.expiry_reminder_sent_at` makes it once per order (migration a4c9e1f7b2d6). Orders that ended before this
  existed get no reminder: the course card itself says "access ended on …" (lms.progress.level_sale -> expired_at).
* Runs in the background round of app.services.teacher_market.scheduler (every 30 s, one worker via an advisory lock); every run
  is cheap (an indexed query over approved orders ending in the next three days)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import TYPE_COURSE, Notification
from app.models.subscription_order import SubscriptionOrder

from . import offers
from .plans import STATUS_APPROVED

REMIND_BEFORE = timedelta(days=3)
TASHKENT = timezone(timedelta(hours=5))


def _levels(order: SubscriptionOrder) -> set[str]:
    return set(order.included_levels or offers.offer_levels(order.plan))


def tick(db: Session, now: datetime | None = None) -> int:
    """Send the due reminders; returns how many notifications were written. Commits."""
    now = now or datetime.now(timezone.utc)
    codes = list(offers.offer_codes())
    due = list(db.scalars(
        select(SubscriptionOrder).where(
            SubscriptionOrder.status == STATUS_APPROVED, SubscriptionOrder.plan.in_(codes),
            SubscriptionOrder.expiry_reminder_sent_at.is_(None),
            SubscriptionOrder.access_end_date > now, SubscriptionOrder.access_end_date <= now + REMIND_BEFORE,
        ).with_for_update(skip_locked=True)
    ))
    sent = 0
    for order in due:
        order.expiry_reminder_sent_at = now
        later = db.scalars(select(SubscriptionOrder).where(
            SubscriptionOrder.user_id == order.user_id, SubscriptionOrder.status == STATUS_APPROVED, SubscriptionOrder.plan.in_(codes),
            SubscriptionOrder.id != order.id, SubscriptionOrder.access_end_date > order.access_end_date))
        covered: set[str] = set()
        for other in later:
            covered |= _levels(other)
        ending = sorted(_levels(order) - covered)
        if not ending:
            continue  # renewed in time: a newer order runs on
        when = order.access_end_date.astimezone(TASHKENT).strftime("%d.%m.%Y %H:%M")
        names = ", ".join(ending)
        db.add(Notification(
            user_id=order.user_id, type=TYPE_COURSE, link_path=f"/angebote?offer={order.plan}"[:300],
            title="Kurs muddati tugayapti / Kurszugang läuft ab",
            message=(f"{names} kursiga kirishingiz {when} da tugaydi. Davom ettirish uchun uzaytiring. / "
                     f"Ihr Zugang zu {names} endet am {when}. Jetzt verlängern, um weiterzulernen."),
        ))
        sent += 1
    db.commit()
    return sent
