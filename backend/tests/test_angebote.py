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
            "A1": (100_000, 50_000, 50),
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
        from unittest.mock import patch

        # default sales policy: only A1 is sold (A2 / B1 / packages wait for admin approval)
        with patch.object(offers, "_read_overrides", return_value={}):
            purchasable = {c for c in offers.OFFERS if offers.is_purchasable(c)}
            self.assertEqual(purchasable, {"A1"})
            self.assertFalse(offers.is_purchasable("MONTH_1"))
            self.assertFalse(offers.is_purchasable("nonsense"))

    def test_sales_default_only_a1(self):
        self.assertEqual(offers.LEVEL_SALES_DEFAULT, {"A1": True, "A2": False, "B1": False, "B2": False, "C1": False})

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
        from unittest.mock import patch

        with patch.object(offers, "_read_overrides", return_value={}):
            listed = VizuPayService(MagicMock()).list_plans()
        self.assertEqual({p["plan"] for p in listed}, {"A1"})
        self.assertEqual({p["plan"]: p["price"] for p in listed}["A1"], 50_000)


class TestAdminOverrides(unittest.TestCase):
    """Admin -> Angebote settings over the code defaults (no database here:
    _read_overrides is patched)."""

    def with_overrides(self, value):
        from unittest.mock import patch

        return patch.object(offers, "_read_overrides", return_value=value)

    def test_defaults_without_overrides(self):
        with self.with_overrides({}):
            self.assertEqual(offers.offer("A1")["sale_price"], 50_000)
            self.assertEqual(offers.offer("A1")["original_price"], 100_000)
            self.assertTrue(offers.level_sales_enabled("A1"))
            for lv in ("A2", "B1", "B2", "C1", None, "X"):
                self.assertFalse(offers.level_sales_enabled(lv))
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
        b2 = {"offers": {"B2": {"active": True, "sale_price": 149_000}}, "sales": {"B2": True}}
        with self.with_overrides(b2):
            self.assertFalse(offers.is_purchasable("B2"))
        with self.with_overrides(dict(b2, levels={"B2": True})):
            self.assertTrue(offers.is_purchasable("B2"))

    def test_level_not_sold_until_sales_approved(self):
        with self.with_overrides({}):
            self.assertFalse(offers.is_purchasable("A2"))
            self.assertFalse(offers.is_purchasable("B1"))
        with self.with_overrides({"sales": {"A2": True}}):
            self.assertTrue(offers.is_purchasable("A2"))
            self.assertFalse(offers.is_purchasable("B1"))
        # an inactive offer stays unsold even when its level is approved
        with self.with_overrides({"sales": {"A2": True}, "offers": {"A2": {"active": False}}}):
            self.assertFalse(offers.is_purchasable("A2"))
        # closing A1 for sale is possible too
        with self.with_overrides({"sales": {"A1": False}}):
            self.assertFalse(offers.is_purchasable("A1"))

    def test_package_needs_every_level_approved(self):
        with self.with_overrides({}):
            self.assertFalse(offers.is_purchasable("A1_B1"))
            self.assertFalse(offers.is_purchasable("A1_C1"))
        with self.with_overrides({"sales": {"A2": True}}):
            self.assertFalse(offers.is_purchasable("A1_B1"))
        with self.with_overrides({"sales": {"A2": True, "B1": True}}):
            self.assertTrue(offers.is_purchasable("A1_B1"))
            self.assertFalse(offers.is_purchasable("A1_C1"))

    def test_a1_c1_package_lists_available_and_sales_levels(self):
        with self.with_overrides({}):
            pkg = next(o for o in offers.list_offers() if o["code"] == "A1_C1")
            self.assertFalse(pkg["purchasable"])
            self.assertEqual(pkg["available_levels"], ["A1", "A2", "B1"])
            self.assertEqual(pkg["sales_levels"], ["A1"])

    def test_validation(self):
        ok = offers.validate_overrides({"offers": {"A1": {"sale_price": 59_000}}, "levels": {"B2": True}, "free_lessons": 2})
        self.assertEqual(ok["offers"]["A1"]["sale_price"], 59_000)
        for bad in ({"offers": {"X": {}}}, {"offers": {"A1": {"sale_price": -5}}}, {"offers": {"A1": {"sale_price": "1"}}},
                    {"offers": {"A1": {"levels": ["A2"]}}}, {"offers": {"A1_B1": {"levels": ["Z9"]}}}, {"levels": {"B2": "yes"}},
                    {"free_lessons": 9}, {"offers": {"B2": {"active": True}}}, {"sales": {"A2": 1}}, {"sales": {"Z9": True}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                offers.validate_overrides(bad)
        self.assertEqual(offers.validate_overrides({"sales": {"A2": True}})["sales"], {"A2": True})
        self.assertNotIn("sales", offers.validate_overrides({"levels": {"B2": True}}))


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


class TestSalesClosedAccess(unittest.TestCase):
    """A level not approved for sale: paid lessons closed for everyone except
    staff and an APPROVED order naming the level; free lessons stay open."""

    lesson = TestComingSoonAccess.lesson

    def check(self, overrides, *, owned=(), premium=False, staff=False, free=False, level="A2"):
        from unittest.mock import patch

        from app.services.vizu_pay import access

        with patch.object(offers, "_read_overrides", return_value=overrides), \
             patch.object(access, "owned_levels", return_value=set(owned)), \
             patch.object(access, "is_free_lesson", return_value=free), \
             patch.object(access, "has_premium_bypass", return_value=staff), \
             patch.object(access, "is_user_premium", return_value=premium):
            return access.can_access_lesson(object(), self.lesson(level)), access.is_level_sales_closed(self.lesson(level))

    def test_not_approved_level_paid_lesson(self):
        self.assertEqual(self.check({}), (False, True))
        self.assertEqual(self.check({}, premium=True), (False, True))  # legacy Premium does not open it
        self.assertEqual(self.check({}, owned={"A1"}), (False, True))  # A1 purchase does not open A2
        self.assertEqual(self.check({}, owned={"A2"}), (True, True))  # bought A2 earlier: kept
        self.assertEqual(self.check({}, staff=True), (True, True))

    def test_free_lesson_stays_open(self):
        self.assertEqual(self.check({}, free=True), (True, True))

    def test_approved_level_restores_premium(self):
        self.assertEqual(self.check({"sales": {"A2": True}}, premium=True), (True, False))
        self.assertEqual(self.check({"sales": {"A2": True}}), (False, False))

    def test_a1_rules(self):
        self.assertEqual(self.check({}, level="A1"), (False, False))
        self.assertEqual(self.check({}, level="A1", owned={"A1"}), (True, False))
        self.assertEqual(self.check({}, level="A1", premium=True), (True, False))
        self.assertEqual(self.check({}, level="A1", free=True), (True, False))

    def test_level_content_books(self):
        from unittest.mock import patch

        from app.services.vizu_pay import access

        with patch.object(offers, "_read_overrides", return_value={}), \
             patch.object(access, "has_premium_bypass", return_value=False), \
             patch.object(access, "is_user_premium", return_value=True), \
             patch.object(access, "owned_levels", return_value=set()):
            self.assertTrue(access.can_access_level_content(object(), "A1"))
            self.assertFalse(access.can_access_level_content(object(), "B1"))


if __name__ == "__main__":
    unittest.main()
