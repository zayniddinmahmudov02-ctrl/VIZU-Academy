from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.vizu_pay.admin_service import AdminVizuPayService
from app.models.promo_code import PromoCode
from app.models.promo_code_redemption import PromoCodeRedemption
from app.services.vizu_pay.service import VizuPayError, VizuPayService


class TestPromoPricing(unittest.TestCase):
    def setUp(self):
        self.service = VizuPayService(MagicMock())

    def promo(self, discount_type, discount_value):
        return SimpleNamespace(discount_type=discount_type, discount_value=discount_value)

    def test_percentage_discount_uses_integer_uzs(self):
        self.assertEqual(self.service._apply_discount(99_000, self.promo("PERCENT", 20)), 19_800)

    def test_special_price_is_final_offer_price(self):
        promo = self.promo("SPECIAL_PRICE", 49_000)
        self.assertEqual(self.service._apply_discount(100_000, promo), 51_000)

    def test_special_price_above_current_offer_is_rejected(self):
        with self.assertRaises(VizuPayError):
            self.service._apply_discount(50_000, self.promo("SPECIAL_PRICE", 50_001))

    def test_legacy_fixed_discount_remains_a_discount_amount(self):
        self.assertEqual(self.service._apply_discount(50_000, self.promo("FIXED", 9_000)), 9_000)

    def test_quote_uses_server_offer_price_and_applies_matching_promo(self):
        user = SimpleNamespace(id="student")
        promo = SimpleNamespace(
            id="promo",
            is_active=True,
            starts_at=None,
            expires_at=None,
            max_uses=None,
            used_count=0,
            max_uses_per_user=1,
            discount_type="PERCENT",
            discount_value=20,
            applicable_course_ids=[],
            applicable_package_codes=["A1_B1"],
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.first.return_value = None
        service = VizuPayService(db)
        service._find_promo = MagicMock(return_value=promo)

        def offer(code):
            is_package = code in {"A1_B1", "A1_C1"}
            return {
                "kind": "PACKAGE" if is_package else "LEVEL",
                "levels": ["A1", "A2", "B1"] if code == "A1_B1" else [code],
                "sale_price": 199_000,
                "original_price": 300_000,
            }

        with (
            patch("app.services.vizu_pay.service.offer_config.is_purchasable", return_value=True),
            patch("app.services.vizu_pay.service.offer_config.offer", side_effect=offer),
            patch(
                "app.services.vizu_pay.service.achievements.quote",
                side_effect=lambda _db, _user, _plan, base, discount: {
                    "promo_discount": discount,
                    "reward_discount": 0,
                    "reward_name": None,
                    "final_amount": base - discount,
                },
            ),
        ):
            quote = service.quote(user, "A1_B1", "SAVE20")
            mismatch = service.quote(user, "A1", "SAVE20")
        self.assertEqual(quote["base_amount"], 199_000)
        self.assertEqual(quote["promo_discount"], 39_800)
        self.assertEqual(quote["final_amount"], 159_200)
        self.assertEqual(mismatch["promo_discount"], 0)
        self.assertIn("does not apply", mismatch["promo_error"])


class TestPromoValidation(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = VizuPayService(self.db)
        self.user = SimpleNamespace(id="student")
        self.db.query.return_value.filter.return_value.count.return_value = 0
        self.db.query.return_value.filter.return_value.first.return_value = None

    def promo(self, **overrides):
        fields = {
            "id": "promo",
            "is_active": True,
            "starts_at": None,
            "expires_at": None,
            "max_uses": None,
            "used_count": 0,
            "max_uses_per_user": 1,
            "discount_type": "PERCENT",
            "discount_value": 20,
            "applicable_course_ids": [],
            "applicable_package_codes": [],
        }
        fields.update(overrides)
        return SimpleNamespace(**fields)

    def test_future_start_and_expiry_are_enforced(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        future = now + timedelta(days=1)
        self.assertEqual(
            self.service._check_promo(self.promo(starts_at=future), self.user),
            "Promo code is not active yet.",
        )
        expired = now - timedelta(days=1)
        self.assertEqual(
            self.service._check_promo(self.promo(expires_at=expired), self.user),
            "Promo code has expired.",
        )

    def test_per_user_limit_counts_pending_and_successful_redemptions(self):
        self.db.query.return_value.filter.return_value.count.return_value = 1
        self.assertIn(
            "per-user",
            self.service._check_promo(self.promo(max_uses_per_user=1), self.user),
        )

    def test_global_limit_counts_pending_reservations(self):
        promo = self.promo(max_uses=3, used_count=3)
        self.assertEqual(
            self.service._check_promo(promo, self.user),
            "Promo code usage limit reached.",
        )

    def test_releasing_failed_order_returns_its_promo_reservation(self):
        redemption = SimpleNamespace(order_id="order", promo_code_id="promo")
        promo = SimpleNamespace(used_count=2)
        db = MagicMock()

        def query(model):
            query_result = MagicMock()
            if model is PromoCodeRedemption:
                query_result.filter.return_value.first.return_value = redemption
            elif model is PromoCode:
                query_result.filter.return_value.with_for_update.return_value.first.return_value = promo
            return query_result

        db.query.side_effect = query
        service = VizuPayService(db)
        service.release_promo_reservation(SimpleNamespace(promo_code_id="promo", id="order"))
        self.assertEqual(promo.used_count, 1)
        db.delete.assert_called_once_with(redemption)

    def test_package_scope_does_not_match_another_package_or_course(self):
        promo = self.promo(applicable_package_codes=["A1_B1"])
        self.assertIsNone(self.service._check_promo(promo, self.user, "A1_B1"))
        self.assertIn(
            "does not apply",
            self.service._check_promo(promo, self.user, "A1_C1"),
        )
        self.assertIn(
            "does not apply",
            self.service._check_promo(promo, self.user, "A1"),
        )

    def test_selected_course_scope_matches_only_its_level(self):
        self.db.query.return_value.filter.return_value.all.return_value = [
            ("course-id",),
            ("another-course-at-level",),
        ]
        partial_scope = self.promo(applicable_course_ids=["course-id"])
        full_scope = self.promo(applicable_course_ids=["course-id", "another-course-at-level"])
        self.assertIn("does not apply", self.service._check_promo(partial_scope, self.user, "A1"))
        self.assertIsNone(self.service._check_promo(full_scope, self.user, "A1"))


class TestPromoAdminValidation(unittest.TestCase):
    def setUp(self):
        self.service = AdminVizuPayService(MagicMock())

    def test_admin_rejects_negative_pricing_and_empty_paid_scope(self):
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("SPECIAL_PRICE", -1, [], [], None, 1, None, None)
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("PERCENT", 20, [], [], None, 1, None, None)

    def test_special_price_and_multiple_package_targets_are_valid(self):
        with patch("app.services.vizu_pay.admin_service.offer_config._read_overrides", return_value={}):
            course_ids, package_codes = self.service._validate_promo_fields(
                "SPECIAL_PRICE", 49_000, [], ["A1_B1", "A1_C1"], 25, 3, None, None
            )
        self.assertEqual(course_ids, [])
        self.assertEqual(package_codes, ["A1_B1", "A1_C1"])

    def test_free_days_cannot_target_checkout_products(self):
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("FREE_DAYS", 7, [], ["A1_B1"], None, 1, None, None)

    def test_admin_statistics_include_only_approved_orders(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [("A1", 2, 12_000)]
        service = AdminVizuPayService(db)
        promo = SimpleNamespace(
            id="promo",
            code="SAVE",
            campaign=None,
            discount_type="PERCENT",
            discount_value=20,
            starts_at=None,
            max_uses=10,
            used_count=3,
            max_uses_per_user=1,
            applicable_course_ids=["course-id"],
            applicable_package_codes=[],
            expires_at=None,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        result = service._serialize_promo(promo)
        self.assertEqual(result["successful_uses"], 2)
        self.assertEqual(result["successful_discount_amount"], 12_000)
        self.assertEqual(result["successful_products"][0]["product_code"], "A1")
        self.assertEqual(result["remaining_uses"], 7)


class TestPromoOrderReservation(unittest.IsolatedAsyncioTestCase):
    async def test_order_creation_locks_promo_before_reserving_global_limit(self):
        promo = SimpleNamespace(
            id="promo",
            code="SAVE",
            is_active=True,
            starts_at=None,
            expires_at=None,
            max_uses=1,
            used_count=0,
            max_uses_per_user=1,
            discount_type="PERCENT",
            discount_value=20,
            applicable_course_ids=[],
            applicable_package_codes=[],
        )
        user_query = MagicMock()
        user_query.filter.return_value.with_for_update.return_value.first.return_value = ("student",)
        promo_query = MagicMock()
        promo_query.filter.return_value.with_for_update.return_value.first.return_value = promo
        redemption_query = MagicMock()
        redemption_query.filter.return_value.count.return_value = 0
        db = MagicMock()

        def query(model):
            if model is PromoCode:
                return promo_query
            if model is PromoCodeRedemption:
                return redemption_query
            return user_query

        db.query.side_effect = query
        service = VizuPayService(db)
        service._sweep_expired = MagicMock()
        service.is_user_blocked = MagicMock(return_value=False)
        service._has_open_order = MagicMock(return_value=False)
        service._build_proof_path = MagicMock(return_value=("receipt.pdf", "pdf"))
        service.serialize_order = MagicMock(return_value={"status": "PENDING"})
        service.proof_storage.upload = AsyncMock()
        user = SimpleNamespace(id="student")
        proof = SimpleNamespace(
            filename="receipt.pdf",
            read=AsyncMock(return_value=b"%PDF-1.7"),
            seek=AsyncMock(),
        )

        with (
            patch("app.services.vizu_pay.service.offer_config.is_offer", return_value=True),
            patch("app.services.vizu_pay.service.offer_config.is_purchasable", return_value=True),
            patch("app.services.vizu_pay.service.offer_config.offer_levels", return_value=["A1"]),
            patch("app.services.vizu_pay.service.offer_config.offer", return_value={"sale_price": 50_000}),
            patch("app.services.vizu_pay.service.owned_levels", return_value=set()),
            patch(
                "app.services.vizu_pay.service.achievements.quote",
                return_value={"reward": None, "reward_discount": 0, "final_amount": 40_000},
            ),
            patch("app.services.vizu_pay.service.write_audit"),
        ):
            result = await service.create_order(
                user,
                plan="A1",
                payment_method="UZCARD",
                promo_code="SAVE",
                proof_file=proof,
                ip=None,
            )

        promo_query.filter.return_value.with_for_update.assert_called_once()
        self.assertEqual(promo.used_count, 1)
        self.assertEqual(result["status"], "PENDING")


if __name__ == "__main__":
    unittest.main()
