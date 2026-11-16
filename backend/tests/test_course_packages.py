"""Course packages + purchase + promo approval against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test database):
seeded packages, closed packages refused by the API, order snapshots (price, days, levels), access only after approval,
expiry, A1–C1 opening B2 / C1 once released, idempotent approval, promo codes that need an admin, limits, admin
package edits (validation, audit). The real service code runs; only the receipt storage is a temp dir."""

import asyncio
import io
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 64


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestCoursePackages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.user import User

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        tag = uuid.uuid4().hex[:6]
        with cls.Session() as db:
            users = []
            for name, role in (("s1", "STUDENT"), ("s2", "STUDENT"), ("s3", "STUDENT"), ("adm", "SUPER_ADMIN")):
                u = User(email=f"pk-{name}-{tag}@test.local", username=f"pk_{name}_{tag}", password_hash="x", is_active=True,
                         is_verified=True, is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz")
                db.add(u)
                users.append(u)
            db.commit()
            cls.user_ids = [u.id for u in users]
        cls.tmp = tempfile.TemporaryDirectory()
        from app.services.vizu_pay.service import VizuPayService

        cls.patch = patch.object(type(VizuPayService(None).proof_storage), "ROOT", Path(cls.tmp.name))
        cls.patch.start()
        cls.promo_ids = []

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete, update

        from app.models.audit_log import AuditLog
        from app.models.course_package import CoursePackage
        from app.models.promo_code import PromoCode
        from app.models.user import User
        from app.services.vizu_pay import offers

        with cls.Session() as db:
            db.execute(delete(PromoCode).where(PromoCode.id.in_(cls.promo_ids)))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in cls.user_ids])))
            db.execute(delete(AuditLog).where(AuditLog.target_user_id.in_([str(i) for i in cls.user_ids])))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))  # cascades orders + requests
            db.execute(delete(CoursePackage).where(CoursePackage.code == "ZTEST"))
            db.execute(update(CoursePackage).where(CoursePackage.code == "B1").values(price=100_000, status="ACTIVE", duration_days=60))
            db.commit()
        offers.invalidate_cache()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def setUp(self):
        from app.services.vizu_pay import offers

        offers.invalidate_cache()
        self.db = self.Session()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def users(self):
        from app.models.user import User

        return [self.db.get(User, i) for i in self.user_ids]

    def order(self, user, plan, promo=None):
        from starlette.datastructures import Headers, UploadFile

        from app.services.vizu_pay.service import VizuPayService

        proof = UploadFile(io.BytesIO(PNG), filename="r.png", headers=Headers({"content-type": "image/png"}))
        return asyncio.run(VizuPayService(self.db).create_order(user, plan=plan, payment_method="UZCARD", promo_code=promo,
                                                                 proof_file=proof, ip=None))

    def approve(self, order_id, admin):
        from app.services.vizu_pay.admin_service import AdminVizuPayService

        return AdminVizuPayService(self.db).approve_order(order_id, admin, None)

    def test_1_seeded_packages(self):
        from app.services.vizu_pay import offers

        listed = {o["code"]: o for o in offers.list_offers()}
        for code, price, days in (("B1", 100_000, 60), ("A1_B1", 200_000, 180), ("A1_C1", 400_000, 365)):
            self.assertEqual((listed[code]["sale_price"], listed[code]["duration_days"], listed[code]["purchasable"]), (price, days, True))
        self.assertEqual(listed["A2"]["duration_days"], 30)
        for code in ("B2", "C1", "B2_C1"):
            self.assertEqual((listed[code]["status"], listed[code]["sale_price"], listed[code]["purchasable"]), ("COMING_SOON", None, False))

    def test_2_closed_packages_refused_and_order_snapshot(self):
        s1, _, _, admin = self.users()
        for code in ("B2", "C1", "B2_C1"):
            with self.assertRaises(HTTPException) as ctx:
                self.order(s1, code)
            self.assertEqual(ctx.exception.detail, "OFFER_NOT_AVAILABLE")
        out = self.order(s1, "A1_C1")
        from app.models.subscription_order import SubscriptionOrder
        from app.services.vizu_pay.access import owned_levels

        order = self.db.get(SubscriptionOrder, uuid.UUID(out["id"]))
        self.assertEqual((order.base_amount, order.duration_days, order.included_levels, order.status),
                         (400_000, 365, ["A1", "A2", "B1", "B2", "C1"], "PENDING"))
        self.assertEqual(owned_levels(s1), set())  # nothing opens before approval
        with self.assertRaises(HTTPException):  # one open request at a time
            self.order(s1, "A2")
        before = datetime.now(timezone.utc)
        self.approve(out["id"], admin)
        from app.services.vizu_pay.service import VizuPayError

        with self.assertRaises(VizuPayError):  # second approval: refused, nothing granted twice
            self.approve(out["id"], admin)
        self.db.expire_all()
        self.db.info.clear()  # owned_levels caches per session (one request = one session in the app)
        order = self.db.get(SubscriptionOrder, uuid.UUID(out["id"]))
        self.assertAlmostEqual((order.access_end_date - order.access_start_date).days, 365)
        self.assertGreaterEqual(order.access_start_date, before - timedelta(seconds=5))
        s1 = self.users()[0]
        self.assertEqual(owned_levels(s1), {"A1", "A2", "B1", "B2", "C1"})

        # editing the package later never changes what this buyer bought
        from app.services.vizu_pay import packages

        packages.update_package(self.db, admin, "A1_C1", {"included_levels": ["A1", "A2", "B1"]})
        try:
            self.db.expire_all()
            self.db.info.clear()
            self.assertEqual(owned_levels(self.users()[0]), {"A1", "A2", "B1", "B2", "C1"})
        finally:
            packages.update_package(self.db, admin, "A1_C1", {"included_levels": ["A1", "A2", "B1", "B2", "C1"]})

        # expiry (server time): access ends by itself
        order = self.db.get(SubscriptionOrder, uuid.UUID(out["id"]))
        order.access_end_date = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.db.commit()
        self.db.expire_all()
        self.db.info.clear()
        self.assertEqual(owned_levels(self.users()[0]), set())

    def test_3_promo_code_needs_approval(self):
        from app.models.promo_code import PromoCode
        from app.models.promo_code_request import PromoCodeRequest
        from app.services.vizu_pay.admin_service import AdminVizuPayService
        from app.services.vizu_pay.service import VizuPayError, VizuPayService

        _, s2, s3, admin = self.users()
        code = f"APR{uuid.uuid4().hex[:6].upper()}"
        promo = AdminVizuPayService(self.db).create_promo(code=code, campaign=None, discount_type="PERCENT", discount_value=10,
                                                          applicable_course_ids=[], applicable_package_codes=["A1_B1"], starts_at=None,
                                                          max_uses=1, max_uses_per_user=1, expires_at=None, actor=admin, requires_approval=True,
                                                          product_category="PACKAGES")
        self.promo_ids.append(uuid.UUID(promo["id"]))
        pay = VizuPayService(self.db)
        # a new code is PENDING: it does nothing until a Super Admin approves and activates it
        self.assertEqual((promo["approval_status"], promo["is_active"]), ("PENDING", False))
        self.assertEqual(pay.quote(s2, "A1_B1", code)["promo_error"], "PROMO_NOT_ACTIVE")
        AdminVizuPayService(self.db).review_promo(promo["id"], "approve_activate", None, admin, None)
        self.assertEqual(pay.quote(s2, "A1_B1", code)["promo_error"], "PROMO_APPROVAL_REQUIRED")
        self.assertEqual(pay.validate_promo(code, s2, "A1_B1")["approval_status"], "PROMO_APPROVAL_REQUIRED")
        req = pay.request_promo(s2, code, "A1_B1", None)
        self.assertEqual(req["status"], "PENDING_APPROVAL")
        self.assertEqual(pay.request_promo(s2, code, "A1_B1", None)["id"], req["id"])  # idempotent
        q = pay.quote(s2, "A1_B1", code)
        self.assertEqual((q["promo_error"], q["promo_discount"], q["final_amount"]), ("PROMO_APPROVAL_PENDING", 0, 200_000))
        with self.assertRaises(HTTPException) as ctx:  # no discount while pending, also not via the API directly
            self.order(s2, "A1_B1", promo=code)
        self.assertEqual(ctx.exception.detail, "PROMO_APPROVAL_PENDING")
        with self.assertRaises(VizuPayError):  # wrong package for this code
            pay.request_promo(s2, code, "A1", None)
        with self.assertRaises(VizuPayError):  # unknown code
            pay.request_promo(s2, "NOPE-" + code, "A1_B1", None)

        admin_svc = AdminVizuPayService(self.db)
        self.assertEqual(admin_svc.list_promo_requests(status="PENDING_APPROVAL", promo_id=promo["id"])["total"], 1)
        admin_svc.review_promo_request(req["id"], True, None, admin, None)
        with self.assertRaises(VizuPayError):
            admin_svc.review_promo_request(req["id"], False, "x", admin, None)  # already reviewed
        q = pay.quote(self.users()[1], "A1_B1", code)
        self.assertEqual((q["promo_error"], q["promo_discount"], q["final_amount"]), (None, 20_000, 180_000))
        out = self.order(self.users()[1], "A1_B1", promo=code)
        self.assertEqual((out["final_amount"], out["discount_amount"]), (180_000, 20_000))
        self.db.expire_all()
        self.assertEqual(self.db.get(PromoCodeRequest, uuid.UUID(req["id"])).status, "USED")

        # limit reached (max_uses 1): another student cannot use it
        self.assertIn("limit", pay.validate_promo(code, self.users()[2], "A1_B1")["message"])
        # rejected request: no discount
        code2 = f"REJ{uuid.uuid4().hex[:6].upper()}"
        p2 = admin_svc.create_promo(code=code2, campaign=None, discount_type="FIXED", discount_value=5_000, applicable_course_ids=[],
                                    applicable_package_codes=["A1_B1"], starts_at=None, max_uses=None, max_uses_per_user=1,
                                    expires_at=None, actor=admin, requires_approval=True, product_category="PACKAGES")
        self.promo_ids.append(uuid.UUID(p2["id"]))
        admin_svc.review_promo(p2["id"], "approve_activate", None, admin, None)
        r2 = VizuPayService(self.db).request_promo(self.users()[2], code2, "A1_B1", None)
        AdminVizuPayService(self.db).review_promo_request(r2["id"], False, "nicht berechtigt", admin, None)
        self.assertEqual(VizuPayService(self.db).quote(self.users()[2], "A1_B1", code2)["promo_error"], "PROMO_REJECTED")
        # expired code
        promo2 = self.db.get(PromoCode, uuid.UUID(p2["id"]))
        promo2.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        self.db.commit()
        self.assertIn("expired", VizuPayService(self.db).validate_promo(code2, self.users()[2], "A1_B1")["message"])
        stats = AdminVizuPayService(self.db).discount_statistics()
        self.assertGreaterEqual(stats["requests"]["REJECTED"], 1)
        # a used code cannot be deleted
        with self.assertRaises(VizuPayError):
            AdminVizuPayService(self.db).delete_promo(promo["id"], admin)

    def test_4_admin_package_edits(self):
        from app.models.audit_log import AuditLog
        from app.services.vizu_pay import offers, packages

        admin = self.users()[3]
        for bad in ({"status": "ACTIVE", "price": None}, {"included_levels": ["A2"]}, {"duration_days": 0}, {"price": -1},
                    {"description": {"xx": "a"}}, {"status": "SOLD"}):
            with self.subTest(bad=bad), self.assertRaises(HTTPException):
                packages.update_package(self.db, admin, "B1", bad)
            self.db.rollback()
        out = packages.update_package(self.db, admin, "B1", {"price": 110_000, "duration_days": 61, "description": {"uz": "B1 kursi"}})
        self.assertEqual((out["price"], out["duration_days"]), (110_000, 61))
        self.assertEqual(offers.offer("B1")["sale_price"], 110_000)  # cache invalidated: in force at once
        packages.update_package(self.db, admin, "B1", {"status": "COMING_SOON"})
        self.assertFalse(offers.is_purchasable("B1"))
        packages.update_package(self.db, admin, "B1", {"status": "ACTIVE", "price": 100_000, "duration_days": 60})
        self.assertTrue(self.db.query(AuditLog).filter(AuditLog.action == "course_package_updated", AuditLog.actor_id == str(admin.id)).count() >= 3)
        new = packages.create_package(self.db, admin, {"code": "ztest", "name": "Z Test", "package_type": "PACKAGE",
                                                       "included_levels": ["A1", "A2"], "price": 1_000, "duration_days": 10, "status": "ACTIVE"})
        self.assertEqual(new["code"], "ZTEST")
        self.assertTrue(offers.is_purchasable("ZTEST"))
        with self.assertRaises(HTTPException):
            packages.create_package(self.db, admin, {"code": "ZTEST", "name": "x", "package_type": "PACKAGE", "included_levels": ["A1"],
                                                     "duration_days": 10, "status": "COMING_SOON"})


if __name__ == "__main__":
    unittest.main()
