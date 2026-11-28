"""Course access expiry is explained, not hidden (owner 2026-11-25), against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test DB).

* `lms.progress.level_sale` -> `access_until` for an active purchase, `expired_at` (+ owned False, lessons 2+ stay closed) when every
  purchase of the level ran out, nothing once a renewal is active; a purchase of another level never shows up.
* `vizu_pay.expiry_reminders.tick` -> one notification for an order ending within three days, never twice, none for an order ending
  later, none when a newer approved order already continues the level; a pending order never counts."""

import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
PROD_SETTINGS = {"sales": {"A2": True}, "free_lessons": 1}


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestCourseAccessExpiry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.services.vizu_pay import offers

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.patch = patch.object(offers, "_read_overrides", lambda: PROD_SETTINGS)
        cls.patch.start()
        offers.invalidate_cache()

    @classmethod
    def tearDownClass(cls):
        from app.services.vizu_pay import offers

        cls.patch.stop()
        offers.invalidate_cache()
        cls.engine.dispose()

    def setUp(self):
        from app.services.vizu_pay import offers

        offers.invalidate_cache()
        self.db = self.Session()
        self.user_ids: list[str] = []
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        from sqlalchemy import delete

        from app.models.user import User

        self.db.rollback()
        self.db.execute(delete(User).where(User.id.in_(self.user_ids)))  # cascades orders + notifications
        self.db.commit()
        self.db.close()

    # helpers -----------------------------------------------------------
    def student(self):
        from app.models.user import User

        tag = uuid.uuid4().hex[:8]
        u = User(email=f"exp-{tag}@test.local", username=f"exp_{tag}", password_hash="x", is_active=True, is_verified=True,
                 is_superuser=False, role="STUDENT", is_banned=False, preferred_language="uz")
        self.db.add(u)
        self.db.flush()
        self.user_ids.append(u.id)
        return u

    def order(self, user, plan, start_days, end_days, status="APPROVED", levels=None):
        from app.models.subscription_order import SubscriptionOrder

        o = SubscriptionOrder(user_id=user.id, plan=plan, duration_days=30, base_amount=1, final_amount=1, payment_method="UZCARD",
                              status=status, included_levels=levels, access_start_date=self.now + timedelta(days=start_days),
                              access_end_date=self.now + timedelta(days=end_days))
        self.db.add(o)
        self.db.commit()
        return o

    def sale(self, user, level):
        from app.services.lms.progress import level_sale

        self.db.info.clear()  # per-session caches (one request = one session in the app)
        return level_sale(user, level)

    def reminders(self, user):
        from sqlalchemy import select

        from app.models.notification import Notification

        return list(self.db.scalars(select(Notification).where(Notification.user_id == user.id)))

    # level_sale --------------------------------------------------------
    def test_active_purchase_shows_until(self):
        u = self.student()
        o = self.order(u, "A1", -5, 25, levels=["A1"])
        s = self.sale(u, "A1")
        self.assertTrue(s["owned"])
        self.assertEqual(s["access_until"], o.access_end_date)
        self.assertIsNone(s["expired_at"])
        other = self.sale(u, "A2")  # a purchase of another level never shows up
        self.assertEqual((other["owned"], other["access_until"], other["expired_at"]), (False, None, None))

    def test_expired_purchase_says_so_and_stays_closed(self):
        from app.models.lesson import Lesson  # noqa: F401
        from app.services.vizu_pay.access import owns_level

        u = self.student()
        older = self.order(u, "A1", -70, -40, levels=["A1"])
        last = self.order(u, "A1_B1", -35, -1)  # older order without included_levels: the package's levels
        s = self.sale(u, "A1")
        self.assertFalse(s["owned"])
        self.assertIsNone(s["access_until"])
        self.assertEqual(s["expired_at"], last.access_end_date)  # the latest end
        self.assertNotEqual(s["expired_at"], older.access_end_date)
        self.assertEqual(self.sale(u, "B1")["expired_at"], last.access_end_date)
        self.db.info.clear()
        self.assertFalse(owns_level(u, "A1"))  # the gate itself is unchanged: expired = closed

    def test_renewal_clears_expired(self):
        u = self.student()
        self.order(u, "A1", -40, -10, levels=["A1"])
        self.order(u, "A1", -1, 29, status="PENDING", levels=["A1"])  # not approved yet: still expired
        self.assertIsNotNone(self.sale(u, "A1")["expired_at"])
        renewed = self.order(u, "A1", -1, 29, levels=["A1"])
        s = self.sale(u, "A1")
        self.assertEqual((s["owned"], s["access_until"], s["expired_at"]), (True, renewed.access_end_date, None))

    def test_future_start_is_neither_active_nor_expired(self):
        u = self.student()
        self.order(u, "A1", 2, 32, levels=["A1"])
        s = self.sale(u, "A1")
        self.assertEqual((s["owned"], s["access_until"], s["expired_at"]), (False, None, None))

    # reminders ---------------------------------------------------------
    def test_reminder_once_for_order_ending_within_three_days(self):
        from app.models.notification import TYPE_COURSE
        from app.services.vizu_pay import expiry_reminders

        soon, later = self.student(), self.student()
        o = self.order(soon, "A1", -28, 2, levels=["A1"])
        self.order(later, "A1", -20, 10, levels=["A1"])
        self.assertGreaterEqual(expiry_reminders.tick(self.db, now=self.now), 1)
        got = self.reminders(soon)
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0].type, got[0].link_path), (TYPE_COURSE, "/angebote?offer=A1"))
        self.assertIn("A1", got[0].message)
        self.assertEqual(self.reminders(later), [])  # ends in 10 days: not yet
        self.db.refresh(o)
        self.assertIsNotNone(o.expiry_reminder_sent_at)
        expiry_reminders.tick(self.db, now=self.now)
        self.assertEqual(len(self.reminders(soon)), 1)  # never twice

    def test_no_reminder_when_already_renewed(self):
        from app.services.vizu_pay import expiry_reminders

        u = self.student()
        o = self.order(u, "A1", -28, 2, levels=["A1"])
        self.order(u, "A1_B1", 0, 180, levels=["A1", "A2", "B1"])
        expiry_reminders.tick(self.db, now=self.now)
        self.assertEqual(self.reminders(u), [])
        self.db.refresh(o)
        self.assertIsNotNone(o.expiry_reminder_sent_at)  # looked at once

    def test_partial_renewal_names_only_the_ending_levels(self):
        from app.services.vizu_pay import expiry_reminders

        u = self.student()
        self.order(u, "A1_B1", -170, 1, levels=["A1", "A2", "B1"])
        self.order(u, "A1", 0, 30, levels=["A1"])
        expiry_reminders.tick(self.db, now=self.now)
        got = self.reminders(u)
        self.assertEqual(len(got), 1)
        self.assertIn("A2, B1", got[0].message)
        self.assertNotIn("A1,", got[0].message)

    def test_expired_and_pending_orders_get_no_reminder(self):
        from app.services.vizu_pay import expiry_reminders

        u = self.student()
        self.order(u, "A1", -31, -1, levels=["A1"])  # already over: the card explains it
        self.order(u, "A2", -1, 2, status="PENDING", levels=["A2"])
        expiry_reminders.tick(self.db, now=self.now)
        self.assertEqual(self.reminders(u), [])

    # the background round (teacher_market.scheduler) ---------------------
    def _lock_count(self):
        from sqlalchemy import text

        from app.services.teacher_market.scheduler import LOCK_KEY

        with self.engine.connect() as c:
            return c.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND classid = 0 AND objid = :k"),
                             {"k": LOCK_KEY}).scalar()

    def test_scheduler_round_sends_and_releases_its_lock(self):
        from app.db.database import engine as app_engine
        from app.services.teacher_market import scheduler

        if app_engine.url.database != self.engine.url.database:
            self.skipTest("DATABASE_NAME must name the VIZU_WB_TEST_DB_URL database")
        u = self.student()
        self.order(u, "A1", -28, 2, levels=["A1"])
        self.assertTrue(scheduler._round())
        self.assertEqual(len(self.reminders(u)), 1)
        self.assertEqual(self._lock_count(), 0)  # released, on the connection that took it
        self.assertTrue(scheduler._round())  # the next round gets the lock again
        self.assertEqual(len(self.reminders(u)), 1)

    def test_scheduler_round_skips_while_another_process_holds_the_lock(self):
        from sqlalchemy import text

        from app.db.database import engine as app_engine
        from app.services.teacher_market import scheduler

        if app_engine.url.database != self.engine.url.database:
            self.skipTest("DATABASE_NAME must name the VIZU_WB_TEST_DB_URL database")
        u = self.student()
        self.order(u, "A1", -28, 2, levels=["A1"])
        with self.engine.connect() as other:
            other.execute(text("SELECT pg_advisory_lock(:k)"), {"k": scheduler.LOCK_KEY})
            other.commit()
            try:
                self.assertFalse(scheduler._round())
                self.assertEqual(self.reminders(u), [])
            finally:
                other.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": scheduler.LOCK_KEY})
                other.commit()
        self.assertTrue(scheduler._round())
        self.assertEqual(len(self.reminders(u)), 1)

    def test_scheduler_one_failing_job_does_not_stop_the_other(self):
        from app.db.database import engine as app_engine
        from app.services.teacher_market import scheduler, special_lessons

        if app_engine.url.database != self.engine.url.database:
            self.skipTest("DATABASE_NAME must name the VIZU_WB_TEST_DB_URL database")
        u = self.student()
        self.order(u, "A1", -28, 2, levels=["A1"])

        def boom(db):
            raise RuntimeError("special lessons down")

        with patch.object(special_lessons, "tick", boom), self.assertLogs(scheduler.log, "ERROR"):
            self.assertTrue(scheduler._round())
        self.assertEqual(len(self.reminders(u)), 1)
        self.assertEqual(self._lock_count(), 0)


if __name__ == "__main__":
    unittest.main()
