"""Angebote (formerly VIZU-Pay) — the offer configuration is the single
source of truth for course prices; these values are business figures and
must be exactly these (no recalculation)."""

import unittest
from unittest.mock import MagicMock

from app.services.vizu_pay import offers, plans
from app.services.vizu_pay.service import VizuPayService


class TestOfferConfiguration(unittest.TestCase):
    def test_exact_level_prices(self):
        expected = {
            "A1": (100_000, 49_000, 50),
            "A2": (200_000, 99_000, 50),
            "B1": (200_000, 99_000, 50),
        }
        for code, (original, sale, discount) in expected.items():
            with self.subTest(code=code):
                cfg = offers.OFFERS[code]
                self.assertEqual(cfg["original_price"], original)
                self.assertEqual(cfg["sale_price"], sale)
                self.assertEqual(cfg["discount_percent"], discount)
                self.assertTrue(cfg["active"])
                self.assertEqual(cfg["levels"], [code])

    def test_exact_package_prices_and_contents(self):
        self.assertEqual(offers.OFFERS["A1_B1"]["original_price"], 300_000)
        self.assertEqual(offers.OFFERS["A1_B1"]["sale_price"], 199_000)
        self.assertEqual(offers.OFFERS["A1_B1"]["levels"], ["A1", "A2", "B1"])
        self.assertEqual(offers.OFFERS["A1_C1"]["original_price"], 600_000)
        self.assertEqual(offers.OFFERS["A1_C1"]["sale_price"], 399_000)
        self.assertEqual(offers.OFFERS["A1_C1"]["levels"], ["A1", "A2", "B1", "B2", "C1"])

    def test_b2_c1_are_inactive_and_not_purchasable(self):
        for code in ("B2", "C1"):
            with self.subTest(code=code):
                self.assertFalse(offers.OFFERS[code]["active"])
                self.assertFalse(offers.is_purchasable(code))
                self.assertIsNone(offers.OFFERS[code]["sale_price"])

    def test_purchasable_offers(self):
        purchasable = {c for c in offers.OFFERS if offers.is_purchasable(c)}
        self.assertEqual(purchasable, {"A1", "A2", "B1", "A1_B1", "A1_C1"})
        self.assertFalse(offers.is_purchasable("MONTH_1"))
        self.assertFalse(offers.is_purchasable("nonsense"))

    def test_one_free_lesson_everywhere(self):
        self.assertEqual(offers.FREE_LESSONS_PER_COURSE, 1)
        self.assertTrue(all(o["free_lessons"] == 1 for o in offers.list_offers()))

    def test_offer_codes_fit_order_plan_column(self):
        # SubscriptionOrder.plan is String(20)
        self.assertTrue(all(len(code) <= 20 for code in offers.OFFERS))

    def test_labels_and_revenue(self):
        self.assertEqual(plans.plan_label("A1_C1"), "A1 → C1")
        self.assertEqual(plans.plan_label("MONTH_1"), "1 Month")  # history still resolves
        self.assertTrue(offers.OFFER_CODES <= plans.REVENUE_PLANS)
        self.assertTrue(plans.PAID_PLANS <= plans.REVENUE_PLANS)

    def test_legacy_plans_endpoint_lists_only_purchasable_offers(self):
        listed = VizuPayService(MagicMock()).list_plans()
        self.assertEqual({p["plan"] for p in listed}, {"A1", "A2", "B1", "A1_B1", "A1_C1"})
        self.assertEqual({p["plan"]: p["price"] for p in listed}["A1_C1"], 399_000)


class TestAdminOverrides(unittest.TestCase):
    """Admin -> Angebote settings over the code defaults (no database here:
    _read_overrides is patched)."""

    def with_overrides(self, value):
        from unittest.mock import patch

        return patch.object(offers, "_read_overrides", return_value=value)

    def test_defaults_without_overrides(self):
        with self.with_overrides({}):
            self.assertEqual(offers.offer("A1")["sale_price"], 49_000)
            self.assertEqual(offers.free_lessons(), 1)
            self.assertTrue(offers.level_available("A1"))
            self.assertFalse(offers.level_available("B2"))
            self.assertFalse(offers.level_available("C1"))

    def test_price_and_sale_status_override(self):
        with self.with_overrides({"offers": {"A2": {"sale_price": 89_000}, "B1": {"active": False}}}):
            self.assertEqual(offers.offer("A2")["sale_price"], 89_000)
            self.assertFalse(offers.is_purchasable("B1"))
            self.assertEqual(offers.OFFERS["A2"]["sale_price"], 99_000)  # defaults untouched

    def test_coming_soon_level_is_not_sold_until_available(self):
        with self.with_overrides({"offers": {"B2": {"active": True, "sale_price": 149_000}}}):
            self.assertFalse(offers.is_purchasable("B2"))
        with self.with_overrides({"offers": {"B2": {"active": True, "sale_price": 149_000}}, "levels": {"B2": True}}):
            self.assertTrue(offers.is_purchasable("B2"))

    def test_a1_c1_package_is_sold_but_lists_only_available_levels(self):
        with self.with_overrides({}):
            pkg = next(o for o in offers.list_offers() if o["code"] == "A1_C1")
            self.assertTrue(pkg["purchasable"])
            self.assertEqual(pkg["available_levels"], ["A1", "A2", "B1"])

    def test_validation(self):
        ok = offers.validate_overrides({"offers": {"A1": {"sale_price": 59_000}}, "levels": {"B2": True}, "free_lessons": 2})
        self.assertEqual(ok["offers"]["A1"]["sale_price"], 59_000)
        for bad in ({"offers": {"X": {}}}, {"offers": {"A1": {"sale_price": -5}}}, {"offers": {"A1": {"sale_price": "1"}}},
                    {"offers": {"A1": {"levels": ["A2"]}}}, {"offers": {"A1_B1": {"levels": ["Z9"]}}}, {"levels": {"B2": "yes"}},
                    {"free_lessons": 9}, {"offers": {"B2": {"active": True}}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                offers.validate_overrides(bad)


class TestComingSoonAccess(unittest.TestCase):
    def lesson(self, level):
        from types import SimpleNamespace

        return SimpleNamespace(id="l", module_id="m", module=SimpleNamespace(course=SimpleNamespace(id="c", level=level)))

    def test_coming_soon_blocks_premium_and_package_but_not_staff(self):
        from unittest.mock import patch

        from app.services.vizu_pay import access

        with patch.object(offers, "_read_overrides", return_value={}), \
             patch.object(access, "owned_levels", return_value={"A1", "A2", "B1", "B2", "C1"}), \
             patch.object(access, "is_free_lesson", return_value=False):
            for staff, premium, level, expected in ((False, True, "B2", False), (False, False, "C1", False), (True, False, "B2", True),
                                                    (False, False, "A2", True), (False, True, "A1", True)):
                with self.subTest(staff=staff, premium=premium, level=level), \
                     patch.object(access, "has_premium_bypass", return_value=staff), \
                     patch.object(access, "is_user_premium", return_value=premium):
                    self.assertEqual(access.can_access_lesson(object(), self.lesson(level)), expected)


if __name__ == "__main__":
    unittest.main()
