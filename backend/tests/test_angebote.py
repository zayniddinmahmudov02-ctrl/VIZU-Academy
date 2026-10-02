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


if __name__ == "__main__":
    unittest.main()
