"""Angebote — course packages (2026-11-14 owner decision): A1 / A2 keep their price, B1 100 000 so'm / 2 months,
A1–B1 200 000 / 6 months, A1–C1 400 000 / 12 months (opens A1–B1 now, B2 / C1 when released), B2 / C1 / B2–C1
"Tez orada". No database here: offers._read_overrides / _read_packages are patched."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.vizu_pay import offers, plans
from app.services.vizu_pay.service import VizuPayService


def config(settings=None, packages=None):
    return patch.multiple(offers, _read_overrides=MagicMock(return_value=settings or {}),
                          _read_packages=MagicMock(return_value=packages))


def pkg(code, **changes):
    return dict(offers.OFFERS[code], **changes)


class TestPackageDefaults(unittest.TestCase):
    def test_prices_durations_and_status(self):
        expected = {
            "A1": (50_000, 30, "ACTIVE", ["A1"]),
            "A2": (99_000, 30, "ACTIVE", ["A2"]),
            "B1": (100_000, 60, "ACTIVE", ["B1"]),
            "A1_B1": (200_000, 180, "ACTIVE", ["A1", "A2", "B1"]),
            "A1_C1": (400_000, 365, "ACTIVE", ["A1", "A2", "B1", "B2", "C1"]),
            "B2": (None, 90, "COMING_SOON", ["B2"]),
            "C1": (None, 60, "COMING_SOON", ["C1"]),
            "B2_C1": (None, 180, "COMING_SOON", ["B2", "C1"]),
        }
        for code, (price, days, status, levels) in expected.items():
            with self.subTest(code=code):
                cfg = offers.OFFERS[code]
                self.assertEqual((cfg["sale_price"], cfg["duration_days"], cfg["status"], cfg["levels"]), (price, days, status, levels))

    def test_a1_a2_original_prices_unchanged(self):
        self.assertEqual((offers.OFFERS["A1"]["original_price"], offers.OFFERS["A1"]["discount_percent"]), (100_000, 50))
        self.assertEqual((offers.OFFERS["A2"]["original_price"], offers.OFFERS["A2"]["discount_percent"]), (200_000, 50))

    def test_purchasable(self):
        with config():
            self.assertEqual({c for c in offers.OFFERS if offers.is_purchasable(c)}, {"A1", "A2", "B1", "A1_B1", "A1_C1"})
            for code in ("B2", "C1", "B2_C1", "MONTH_1", "nonsense"):
                self.assertFalse(offers.is_purchasable(code), code)

    def test_coming_soon_hides_price_and_duration(self):
        with config():
            listed = {o["code"]: o for o in offers.list_offers()}
            for code in ("B2", "C1", "B2_C1"):
                self.assertEqual((listed[code]["status"], listed[code]["sale_price"], listed[code]["duration_days"],
                                  listed[code]["purchasable"]), ("COMING_SOON", None, None, False))
            self.assertEqual(listed["A1_C1"]["available_levels"], ["A1", "A2", "B1"])
            self.assertEqual(listed["B1"]["duration_days"], 60)

    def test_disabled_package_is_not_listed_nor_sold(self):
        with config(packages={"A1": pkg("A1", status="DISABLED", active=False), "B1": pkg("B1")}):
            self.assertEqual([o["code"] for o in offers.list_offers()], ["B1"])
            self.assertFalse(offers.is_purchasable("A1"))
            self.assertTrue(offers.is_offer("A1"))  # still known for old orders

    def test_level_package_needs_released_level(self):
        b2 = {"B2": pkg("B2", status="ACTIVE", sale_price=150_000)}
        with config(packages=b2):
            self.assertFalse(offers.is_purchasable("B2"))
        with config(settings={"levels": {"B2": True}}, packages=b2):
            self.assertTrue(offers.is_purchasable("B2"))

    def test_bundle_of_unreleased_levels_is_not_sold(self):
        with config(packages={"B2_C1": pkg("B2_C1", status="ACTIVE", sale_price=300_000)}):
            self.assertFalse(offers.is_purchasable("B2_C1"))

    def test_sales_flags_no_longer_block_selling(self):
        with config(settings={"sales": {"A2": False, "B1": False}}):
            self.assertTrue(offers.is_purchasable("A2"))
            self.assertTrue(offers.is_purchasable("A1_B1"))

    def test_codes_and_labels(self):
        self.assertTrue(all(len(code) <= 20 for code in offers.OFFERS))
        with config():
            self.assertEqual(plans.plan_label("A1_C1"), "A1 → C1")
            self.assertEqual(plans.plan_label("MONTH_1"), "1 Month")
            self.assertTrue(offers.OFFER_CODES <= offers.offer_codes())
        with config(packages={"X9": dict(offers.OFFERS["A1_B1"], label="X9")}):
            self.assertIn("X9", offers.offer_codes())

    def test_legacy_plans_endpoint_lists_only_purchasable(self):
        with config():
            listed = VizuPayService(MagicMock()).list_plans()
        self.assertEqual({p["plan"]: p["price"] for p in listed},
                         {"A1": 50_000, "A2": 99_000, "B1": 100_000, "A1_B1": 200_000, "A1_C1": 400_000})

    def test_one_free_lesson(self):
        with config():
            self.assertEqual(offers.free_lessons(), 1)
            self.assertTrue(all(o["free_lessons"] == 1 for o in offers.list_offers()))

    def test_settings_validation(self):
        ok = offers.validate_overrides({"offers": {"A1": {"sale_price": 1}}, "levels": {"B2": True}, "free_lessons": 2})
        self.assertNotIn("offers", ok)  # prices are package fields now
        self.assertEqual(ok["levels"], {"B2": True})
        for bad in ({"levels": {"B2": "yes"}}, {"free_lessons": 9}, {"sales": {"A2": 1}}, {"sales": {"Z9": True}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                offers.validate_overrides(bad)


class TestAccessRules(unittest.TestCase):
    def lesson(self, level):
        from types import SimpleNamespace

        return SimpleNamespace(id="l", module_id="m", module=SimpleNamespace(course=SimpleNamespace(id="c", level=level)))

    def access(self, settings, *, owned=(), premium=False, staff=False, free=False, level="A2"):
        from app.services.vizu_pay import access

        with config(settings=settings), \
             patch.object(access, "owned_levels", return_value=set(owned)), \
             patch.object(access, "is_free_lesson", return_value=free), \
             patch.object(access, "has_premium_bypass", return_value=staff), \
             patch.object(access, "is_user_premium", return_value=premium):
            return access.can_access_lesson(object(), self.lesson(level))

    def test_a1_c1_buyer_gets_b2_only_once_released(self):
        owned = {"A1", "A2", "B1", "B2", "C1"}
        self.assertFalse(self.access({}, owned=owned, level="B2"))
        self.assertTrue(self.access({"levels": {"B2": True}}, owned=owned, level="B2"))  # no new payment
        self.assertTrue(self.access({}, owned=owned, level="B1"))

    def test_package_does_not_open_other_levels(self):
        self.assertFalse(self.access({}, owned={"A1"}, level="A2"))
        self.assertTrue(self.access({}, owned={"A2"}, level="A2"))
        self.assertTrue(self.access({}, staff=True, level="B2"))


if __name__ == "__main__":
    unittest.main()
