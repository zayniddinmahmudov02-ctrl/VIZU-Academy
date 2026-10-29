from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest import mock
from uuid import uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.core.security.jwt import (
    create_resource_token,
    create_video_stream_token,
    decode_resource_token_claims,
    decode_video_stream_claims,
)
from app.models.user import User
from app.services.vizu_pay import access
from app.services.vizu_pay.offers import OFFER_ACCESS_MONTHS, access_duration_months
from app.services.vizu_pay.purchases import (
    activate_course_access,
    add_calendar_months,
    course_access_is_active,
    extend_course_access,
)
from app.schemas.vizu_pay.schema import ExtendOrderAccessRequest


UTC = timezone.utc


# unittest, not pytest: the suite runs with `unittest discover` (pytest is not
# installed on the server), and module-level pytest functions are never collected.
class TestCourseAccessTerms(unittest.TestCase):
    def test_calendar_month_addition_clamps_month_end(self):
        cases = [
            (datetime(2024, 1, 31, 12, 30, tzinfo=UTC), 1, datetime(2024, 2, 29, 12, 30, tzinfo=UTC)),
            (datetime(2023, 1, 31, 12, 30, tzinfo=UTC), 1, datetime(2023, 2, 28, 12, 30, tzinfo=UTC)),
            (datetime(2024, 2, 29, 12, 30, tzinfo=UTC), 12, datetime(2025, 2, 28, 12, 30, tzinfo=UTC)),
            (datetime(2026, 11, 30, 12, 30, tzinfo=UTC), 4, datetime(2027, 3, 30, 12, 30, tzinfo=UTC)),
            (datetime(2026, 12, 31, 12, 30, tzinfo=UTC), 9, datetime(2027, 9, 30, 12, 30, tzinfo=UTC)),
        ]
        for start, months, expected in cases:
            with self.subTest(start=start, months=months):
                self.assertEqual(add_calendar_months(start, months), expected)

    def test_course_and_package_durations_are_centrally_configured(self):
        self.assertEqual(OFFER_ACCESS_MONTHS, {
            "A1": 1,
            "A2": 1,
            "B1": 2,
            "B2": 3,
            "C1": 2,
            "A1_B1": 4,
            "A1_C1": 9,
        })
        self.assertEqual(access_duration_months("A1_B1"), 4)
        with self.assertRaises(ValueError):
            access_duration_months("UNKNOWN")

    def test_successful_activation_sets_order_specific_utc_window(self):
        activated = datetime(2024, 1, 31, 9, 15, tzinfo=UTC)
        first = SimpleNamespace(plan="A1", purchase_date=None, access_start_date=None, access_end_date=None)
        second = SimpleNamespace(plan="A1_B1", purchase_date=None, access_start_date=None, access_end_date=None)

        activate_course_access(first, activated)
        activate_course_access(second, activated)

        self.assertEqual(first.purchase_date, activated)
        self.assertEqual(first.access_start_date, activated)
        self.assertEqual(first.access_end_date, datetime(2024, 2, 29, 9, 15, tzinfo=UTC))
        self.assertEqual(second.purchase_date, activated)
        self.assertEqual(second.access_start_date, activated)
        self.assertEqual(second.access_end_date, datetime(2024, 5, 31, 9, 15, tzinfo=UTC))

    def test_access_requires_approved_status_and_uses_exclusive_end(self):
        start = datetime(2026, 1, 31, 10, tzinfo=UTC)
        end = datetime(2026, 2, 28, 10, tzinfo=UTC)
        order = SimpleNamespace(
            status="APPROVED",
            access_start_date=start,
            access_end_date=end,
        )

        self.assertFalse(course_access_is_active(order, start - timedelta(seconds=1)))
        self.assertTrue(course_access_is_active(order, start))
        self.assertTrue(course_access_is_active(order, end - timedelta(seconds=1)))
        self.assertFalse(course_access_is_active(order, end))
        order.status = "REJECTED"
        self.assertFalse(course_access_is_active(order, start))
        order.status = "REFUNDED"
        self.assertFalse(course_access_is_active(order, start))

    def test_repurchase_and_admin_extension_keep_each_order_independent(self):
        now = datetime(2026, 4, 30, 10, tzinfo=UTC)
        first = SimpleNamespace(
            plan="A1",
            status="APPROVED",
            purchase_date=now,
            access_start_date=now,
            access_end_date=datetime(2026, 5, 30, 10, tzinfo=UTC),
        )
        second = SimpleNamespace(plan="A1", purchase_date=None, access_start_date=None, access_end_date=None)

        activate_course_access(second, now)
        extend_course_access(first, 1, now)

        self.assertEqual(first.access_end_date, datetime(2026, 6, 30, 10, tzinfo=UTC))
        self.assertEqual(second.access_end_date, datetime(2026, 5, 30, 10, tzinfo=UTC))
        first.access_end_date = datetime(2026, 4, 1, 10, tzinfo=UTC)
        extend_course_access(first, 1, now)
        self.assertEqual(first.access_end_date, datetime(2026, 5, 30, 10, tzinfo=UTC))

    def test_unapproved_order_cannot_be_extended(self):
        order = SimpleNamespace(
            status="PENDING",
            purchase_date=None,
            access_start_date=None,
            access_end_date=None,
        )
        with self.assertRaises(ValueError):
            extend_course_access(order, 1, datetime(2026, 1, 1, tzinfo=UTC))

    def test_admin_extension_requires_a_nonblank_audit_reason(self):
        self.assertEqual(ExtendOrderAccessRequest(months=2, reason=" Staff correction ").reason, "Staff correction")
        with self.assertRaises(ValueError):
            ExtendOrderAccessRequest(months=2, reason="   ")

    def test_owned_levels_query_requires_an_active_approved_access_window(self):
        with Session() as db:
            user = User(id=uuid4())
            db.add(user)
            rows = SimpleNamespace(all=lambda: ["A1"])
            captured = []

            def scalars(query):
                captured.append(query)
                return rows

            with mock.patch.object(db, "scalars", scalars):
                self.assertEqual(access.owned_levels(user), {"A1"})
            sql = str(captured[0].compile(dialect=postgresql.dialect()))
            self.assertIn("access_start_date <=", sql)
            self.assertIn("access_end_date >", sql)
            self.assertIn("subscription_orders.status =", sql)

    def test_signed_media_tokens_are_user_scoped_for_access_rechecks(self):
        video_token = create_video_stream_token("video-id", "student-id")
        resource_token = create_resource_token("resource-id", "student-id")

        self.assertEqual(decode_video_stream_claims(video_token), ("video-id", "student-id"))
        self.assertEqual(decode_resource_token_claims(resource_token), ("resource-id", "student-id"))
        with self.assertRaises(ValueError):
            decode_video_stream_claims(create_video_stream_token("video-id"))

    def test_naive_timestamp_inputs_are_considered_utc(self):
        naive = datetime(2026, 4, 1, 10)
        self.assertEqual(add_calendar_months(naive, 1), datetime(2026, 5, 1, 10))
        order = SimpleNamespace(
            status="APPROVED",
            access_start_date=naive.replace(tzinfo=UTC),
            access_end_date=datetime(2026, 5, 1, 10, tzinfo=UTC),
        )
        self.assertTrue(course_access_is_active(order, naive))


if __name__ == "__main__":
    unittest.main()
