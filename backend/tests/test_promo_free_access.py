from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from app.models.promo_code_redemption import PromoCodeRedemption
from app.models.subscription_order import SubscriptionOrder
from app.services.vizu_pay import service as pay_service
from app.services.vizu_pay.admin_service import AdminVizuPayService
from app.services.vizu_pay.service import VizuPayError, VizuPayService


def free_promo(**overrides):
    values = dict(
        id="promo-1", code="GIFT", is_active=True, starts_at=None, expires_at=None, max_uses=None,
        used_count=0, max_uses_per_user=1, discount_type="FREE_ACCESS", discount_value=100,
        applicable_course_ids=[], applicable_package_codes=["A1_B1"],
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def service_for(promo, user_uses=0):
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = user_uses
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = promo
    return VizuPayService(db), db


def added(db, model):
    return [call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], model)]


class TestFreeAccessRedeem(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(id="student", premium_until=None)
        patches = [
            patch.object(pay_service, "write_audit"),
            patch.object(pay_service, "owned_levels", return_value=set()),
            patch.object(pay_service.offer_config, "level_available", return_value=True),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def test_redeem_grants_approved_zero_amount_order_with_access_window(self):
        promo = free_promo()
        service, db = service_for(promo)
        result = service.redeem_promo("gift", self.user, None)

        self.assertEqual(result["granted_offers"], ["A1_B1"])
        (order,) = added(db, SubscriptionOrder)
        self.assertEqual(order.final_amount, 0)
        self.assertEqual(order.discount_amount, order.base_amount)
        self.assertEqual(order.status, "APPROVED")
        self.assertEqual(order.payment_method, "PROMO")
        self.assertEqual(order.gateway, "promo")
        self.assertIsNone(order.proof_url)  # no fake payment proof / transaction
        self.assertGreater(order.access_end_date, order.access_start_date)
        self.assertEqual(promo.used_count, 1)
        self.assertEqual(len(added(db, PromoCodeRedemption)), 1)
        db.commit.assert_called_once()

    def test_package_and_level_scope_is_resolved_on_server(self):
        promo = free_promo(applicable_package_codes=[], applicable_course_ids=["c-a1"])
        service, db = service_for(promo)
        db.query.return_value.filter.return_value.all.return_value = [("A1",)]
        service.redeem_promo("GIFT", self.user, None)
        (order,) = added(db, SubscriptionOrder)
        self.assertEqual(order.plan, "A1")

    def test_invalid_expired_exhausted_or_inactive_codes_grant_nothing(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cases = [
            free_promo(is_active=False),
            free_promo(expires_at=now - timedelta(days=1)),
            free_promo(starts_at=now + timedelta(days=1)),
            free_promo(max_uses=3, used_count=3),
        ]
        for promo in cases:
            service, db = service_for(promo)
            with self.assertRaises(VizuPayError):
                service.redeem_promo("GIFT", self.user, None)
            self.assertEqual(added(db, SubscriptionOrder), [])
            db.commit.assert_not_called()

    def test_unknown_code_and_per_user_limit_are_rejected(self):
        service, db = service_for(None)
        with self.assertRaises(VizuPayError):
            service.redeem_promo("NOPE", self.user, None)
        service, db = service_for(free_promo(), user_uses=1)
        with self.assertRaises(VizuPayError):
            service.redeem_promo("GIFT", self.user, None)
        self.assertEqual(added(db, SubscriptionOrder), [])

    def test_already_owned_levels_are_not_granted_again(self):
        with patch.object(pay_service, "owned_levels", return_value={"A1", "A2", "B1"}):
            service, db = service_for(free_promo())
            with self.assertRaises(VizuPayError):
                service.redeem_promo("GIFT", self.user, None)
        self.assertEqual(added(db, SubscriptionOrder), [])

    def test_unscoped_free_access_code_grants_nothing(self):
        service, db = service_for(free_promo(applicable_package_codes=[], applicable_course_ids=[]))
        with self.assertRaises(VizuPayError):
            service.redeem_promo("GIFT", self.user, None)
        self.assertEqual(added(db, SubscriptionOrder), [])

    def test_checkout_never_treats_free_access_as_a_payable_discount(self):
        service, _ = service_for(free_promo())
        service._find_promo = MagicMock(return_value=free_promo())
        result = service.validate_promo("GIFT", self.user, "A1_B1")
        self.assertFalse(result["valid"])
        self.assertEqual(result["discount_type"], "FREE_ACCESS")

    def test_percent_codes_still_cannot_be_redeemed_directly(self):
        service, _ = service_for(free_promo(discount_type="PERCENT", discount_value=20))
        with self.assertRaises(VizuPayError):
            service.redeem_promo("GIFT", self.user, None)


class TestFreeAccessAdminValidation(unittest.TestCase):
    def setUp(self):
        self.service = AdminVizuPayService(MagicMock())

    def test_free_access_with_package_scope_is_accepted(self):
        ids, packages = self.service._validate_promo_fields("FREE_ACCESS", 100, [], ["A1_B1"], 5, 1, None, None)
        self.assertEqual((ids, packages), ([], ["A1_B1"]))

    def test_free_access_requires_a_target_even_for_legacy_unscoped_edits(self):
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("FREE_ACCESS", 100, [], [], None, 1, None, None, allow_unscoped=True)

    def test_free_access_respects_limits_and_dates(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("FREE_ACCESS", 100, [], ["A1_B1"], 0, 1, None, None)
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("FREE_ACCESS", 100, [], ["A1_B1"], None, 0, None, None)
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("FREE_ACCESS", 100, [], ["A1_B1"], None, 1, now, now - timedelta(days=1))

    def test_unknown_type_is_rejected_server_side(self):
        with self.assertRaises(VizuPayError):
            self.service._validate_promo_fields("FREE_FOREVER", 100, [], ["A1_B1"], None, 1, None, None)


if __name__ == "__main__":
    unittest.main()
