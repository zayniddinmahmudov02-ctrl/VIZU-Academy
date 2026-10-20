"""Lernserie credit rules + medal configuration / reward arithmetic (pure parts;
the database paths are covered by the API integration check)."""

import unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.services import achievements, learning_activity as la

T0 = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


class TestVideoCredit(unittest.TestCase):
    def test_real_playback_is_credited(self):
        self.assertEqual(la.video_credit(100, 110, T0, T0 + timedelta(seconds=10)), 10)

    def test_no_advance_no_credit(self):
        # page open / paused player / repeated report
        self.assertEqual(la.video_credit(100, 100, T0, T0 + timedelta(minutes=30)), 0)
        self.assertEqual(la.video_credit(100, 40, T0, T0 + timedelta(seconds=10)), 0)  # seek back

    def test_seek_forward_bounded_by_real_time(self):
        self.assertEqual(la.video_credit(0, 600, T0, T0 + timedelta(seconds=8)), 8)

    def test_long_gap_capped(self):
        self.assertEqual(la.video_credit(0, 3000, T0, T0 + timedelta(hours=2)), la.VIDEO_MAX_CREDIT_PER_REPORT)

    def test_first_report_or_clock_skew(self):
        self.assertEqual(la.video_credit(None, 50, None, T0), 0)
        self.assertEqual(la.video_credit(0, 50, T0, T0 - timedelta(seconds=5)), 0)


class TestAttemptCredit(unittest.TestCase):
    def test_capped_and_non_negative(self):
        self.assertEqual(la.attempt_credit(95), 95)
        self.assertEqual(la.attempt_credit(5 * 3600), la.ATTEMPT_MAX_CREDIT)
        self.assertEqual(la.attempt_credit(None), 0)
        self.assertEqual(la.attempt_credit(-3), 0)


class TestStreak(unittest.TestCase):
    def test_consecutive_days(self):
        today = date(2026, 10, 20)
        days = {today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=4)}
        self.assertEqual(la.streak_days(days, today), 3)

    def test_today_not_yet_active_keeps_series(self):
        today = date(2026, 10, 20)
        self.assertEqual(la.streak_days({today - timedelta(days=1), today - timedelta(days=2)}, today), 2)

    def test_broken_series(self):
        today = date(2026, 10, 20)
        self.assertEqual(la.streak_days({today - timedelta(days=2)}, today), 0)
        self.assertEqual(la.streak_days(set(), today), 0)

    def test_timezone_resolution(self):
        self.assertEqual(str(la.resolve_tz("Europe/Berlin")), "Europe/Berlin")
        self.assertEqual(str(la.resolve_tz("Mars/Olympus")), la.DEFAULT_TZ)
        self.assertEqual(str(la.resolve_tz(None)), la.DEFAULT_TZ)
        self.assertEqual(str(la.resolve_tz("../../etc/passwd")), la.DEFAULT_TZ)

    def test_bucket_is_utc_hour(self):
        self.assertEqual(la._bucket(datetime(2026, 10, 20, 23, 59, 30, tzinfo=timezone.utc)), datetime(2026, 10, 20, 23, 0, tzinfo=timezone.utc))


class TestConditions(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(achievements.validate_condition("LESSON_COMPLETED", {"level": "A1", "lesson_number": 1}), {"level": "A1", "lesson_number": 1})
        self.assertEqual(achievements.validate_condition("LEVEL_LESSONS_COMPLETED", {"level": "B1", "count": 5}), {"level": "B1", "count": 5})

    def test_invalid(self):
        for ctype, params in (("NOPE", {}), ("LESSON_COMPLETED", {"level": "Z9", "lesson_number": 1}),
                              ("LESSON_COMPLETED", {"level": "A1", "lesson_number": 0}), ("LESSON_COMPLETED", {"level": "A1", "lesson_number": "1"}),
                              ("LESSON_COMPLETED", {"level": "A1", "lesson_number": 1, "x": 1}), ("LEVEL_LESSONS_COMPLETED", {"level": "A1"})):
            with self.subTest(ctype=ctype, params=params), self.assertRaises(ValueError):
                achievements.validate_condition(ctype, params)

    def test_condition_texts_both_languages(self):
        a = SimpleNamespace(condition_type="LESSON_COMPLETED", condition_params={"level": "A1", "lesson_number": 1})
        texts = achievements.condition_texts(a)
        self.assertIn("Lektion 1", texts["de"])
        self.assertIn("A1 kursining 1-darsini", texts["uz"])


class TestAchievementValidation(unittest.TestCase):
    base = {"key": "starter", "name_de": "Starter", "name_uz": "Starter", "condition_type": "LESSON_COMPLETED",
            "condition_params": {"level": "A1", "lesson_number": 1}, "reward_type": "ORDER_DISCOUNT", "reward_value": 5000, "reward_offers": ["A1"]}

    def test_valid_reward(self):
        clean = achievements.validate_achievement(dict(self.base))
        self.assertEqual((clean["reward_value"], clean["reward_offers"]), (5000, ["A1"]))

    def test_invalid(self):
        for patch_ in ({"reward_value": 0}, {"reward_value": -5}, {"reward_value": "5000"}, {"reward_value": 10_000_000},
                       {"reward_offers": []}, {"reward_offers": ["Z9"]}, {"reward_type": "CASH"}, {"key": "bad key!"}, {"name_uz": "  "},
                       {"icon_preset": "skull"}, {"icon_color": "pink"}, {"image_url": "javascript:alert(1)"}, {"is_active": "yes"}):
            with self.subTest(patch_=patch_), self.assertRaises(ValueError):
                achievements.validate_achievement({**self.base, **patch_})

    def test_no_reward_clears_values(self):
        clean = achievements.validate_achievement({**self.base, "reward_type": "NONE"})
        self.assertEqual((clean["reward_value"], clean["reward_offers"]), (0, []))


class TestQuote(unittest.TestCase):
    def ua(self, value=5000, offers=("A1",), combine=False):
        return SimpleNamespace(reward_value=value, reward_offers=list(offers),
                               achievement=SimpleNamespace(reward_combine_with_promo=combine, name_de="Starter", name_uz="Starter"))

    def quote(self, plan, base, promo, reward):
        with patch.object(achievements, "_usable_reward", return_value=reward):
            return achievements.quote(None, "u", plan, base, promo)

    def test_starter_on_a1(self):
        q = self.quote("A1", 50_000, 0, self.ua())
        self.assertEqual((q["base_amount"], q["reward_discount"], q["final_amount"]), (50_000, 5_000, 45_000))

    def test_no_reward(self):
        q = self.quote("A1", 50_000, 0, None)
        self.assertEqual((q["reward_discount"], q["final_amount"]), (0, 50_000))

    def test_never_below_zero(self):
        q = self.quote("A1", 3_000, 0, self.ua())
        self.assertEqual((q["reward_discount"], q["final_amount"]), (3_000, 0))

    def test_usable_reward_filters_plan_and_promo(self):
        rows = [self.ua(offers=("A1",))]

        class FakeDB:
            def scalars(self, _q):
                return SimpleNamespace(all=lambda: rows)

        self.assertIsNotNone(achievements._usable_reward(FakeDB(), "u", "A1", False, False))
        self.assertIsNone(achievements._usable_reward(FakeDB(), "u", "A2", False, False))
        self.assertIsNone(achievements._usable_reward(FakeDB(), "u", "A1_B1", False, False))
        self.assertIsNone(achievements._usable_reward(FakeDB(), "u", "A1", True, False))  # promo used, not combinable
        rows[0] = self.ua(combine=True)
        self.assertIsNotNone(achievements._usable_reward(FakeDB(), "u", "A1", True, False))


class TestOrderStatusTransitions(unittest.TestCase):
    def run_status(self, status, ua):
        db = SimpleNamespace(scalar=lambda _q: ua)
        achievements.on_order_status(db, SimpleNamespace(id="o1", status=status))
        return ua

    def test_approve_uses_reject_releases(self):
        ua = self.run_status("APPROVED", SimpleNamespace(reward_status="RESERVED", reward_order_id="o1", reward_used_at=None))
        self.assertEqual(ua.reward_status, "USED")
        self.assertIsNotNone(ua.reward_used_at)
        for status in ("REJECTED", "EXPIRED", "REFUNDED"):
            ua = self.run_status(status, SimpleNamespace(reward_status="RESERVED", reward_order_id="o1", reward_used_at=None))
            self.assertEqual((ua.reward_status, ua.reward_order_id), ("AVAILABLE", None))


class TestCard(unittest.TestCase):
    def test_new_payment_card(self):
        from app.services.vizu_pay import plans

        numbers = [c["number"] for c in plans.PAYMENT_CARDS]
        self.assertIn("9860040114063742", numbers)
        self.assertNotIn("9860350144907192", numbers)


if __name__ == "__main__":
    unittest.main()
