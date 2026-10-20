"""Shared purchase rule (vizu_pay/purchases.py) + dashboard Trends buckets."""

import unittest
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.dialects import postgresql


def _sql(clause) -> str:
    return str(clause.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


class TestPurchaseRule(unittest.TestCase):
    def test_revenue_counts_only_approved_real_money_plans(self):
        from app.services.vizu_pay import plans, purchases

        status, plan = purchases.revenue_conditions()
        self.assertIn("'APPROVED'", _sql(status))
        plan_sql = _sql(plan)
        for code in plans.REVENUE_PLANS:
            self.assertIn(f"'{code}'", plan_sql)
        for code in ("TRIAL", "PROMO"):
            self.assertNotIn(f"'{code}'", plan_sql)

    def test_course_purchase_is_approved_offer_only(self):
        from app.services.vizu_pay import offers, purchases

        status, plan = purchases.course_purchase_conditions()
        self.assertIn("'APPROVED'", _sql(status))
        for bad in ("PENDING", "REJECTED", "REFUNDED", "EXPIRED"):
            self.assertNotIn(bad, _sql(status))
        plan_sql = _sql(plan)
        for code in offers.OFFER_CODES:
            self.assertIn(f"'{code}'", plan_sql)
        self.assertNotIn("'MONTH_1'", plan_sql)

    def test_naive_utc(self):
        from app.services.vizu_pay.purchases import _naive_utc

        aware = datetime(2026, 10, 20, 5, 0, tzinfo=timezone(timedelta(hours=5)))
        self.assertEqual(_naive_utc(aware), datetime(2026, 10, 20, 0, 0))
        self.assertEqual(_naive_utc(datetime(2026, 1, 1)), datetime(2026, 1, 1))
        self.assertIsNone(_naive_utc(None))

    def test_paying_clause_is_premium_or_buyer(self):
        from app.services.vizu_pay import purchases

        sql = _sql(purchases.is_paying_clause(datetime(2026, 10, 20)))
        self.assertIn("premium_until", sql)
        self.assertIn("EXISTS", sql)
        self.assertIn("'APPROVED'", sql)


class TestTrendBuckets(unittest.TestCase):
    def test_day_buckets_cover_exactly_the_range(self):
        from app.services.admin.enterprise_dashboard_service import trend_buckets

        first, keys = trend_buckets("7d", "day", date(2026, 10, 20))
        self.assertEqual(first, date(2026, 10, 14))
        self.assertEqual(keys[0], "2026-10-14")
        self.assertEqual(keys[-1], "2026-10-20")
        self.assertEqual(len(keys), 7)
        self.assertEqual(len(trend_buckets("30d", "day", date(2026, 10, 20))[1]), 30)

    def test_week_buckets_start_monday(self):
        from app.services.admin.enterprise_dashboard_service import trend_buckets

        first, keys = trend_buckets("30d", "week", date(2026, 10, 20))
        self.assertEqual(first.weekday(), 0)
        self.assertEqual(keys[-1], "2026-10-19")  # Monday of the current week
        self.assertEqual(len(keys), len(set(keys)))

    def test_month_buckets_cross_year(self):
        from app.services.admin.enterprise_dashboard_service import trend_buckets

        _, keys = trend_buckets("1y", "month", date(2026, 1, 31))
        self.assertEqual(keys[0], "2025-02")
        self.assertEqual(keys[-1], "2026-01")
        self.assertEqual(len(keys), 12)

    def test_granularity_falls_back_to_allowed(self):
        from app.services.admin.enterprise_dashboard_service import resolve_granularity

        self.assertEqual(resolve_granularity("7d", "month"), "day")
        self.assertEqual(resolve_granularity("1y", "day"), "month")
        self.assertEqual(resolve_granularity("90d", None), "week")
        self.assertEqual(resolve_granularity("30d", "week"), "week")


if __name__ == "__main__":
    unittest.main()
