"""Multilevel Modelltest Premium + promo approval + course promo requests (2026-11-16).

Pure: route protection (401 without login, 403 for students / staff on every admin route), the amount never comes from the client.
Against PostgreSQL (VIZU_WB_TEST_DB_URL): all 10 Modelltests locked without the Premium (also through the service), 99 000 UZS from the
server, receipt upload / "Chek mavjud emas" with date + time, PENDING until the Super Admin approves, approve opens all 10 (once — a second
approval is refused), reject keeps them closed and allows a new request, refund revokes; promo codes start PENDING and work only when
approved + ACTIVE, product categories never mix (course <-> Multilevel), 100 % Multilevel code opens everything, usage limit, expiry,
personal codes; course promo requests (create / attach a code, reject) open nothing by themselves; overview figures; payment settings."""

import asyncio
import io
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
TASHKENT = timezone(timedelta(hours=5))

ADMIN_ROUTES = [
    ("GET", "/api/v1/admin/vizu-pay/overview"),
    ("GET", "/api/v1/admin/vizu-pay/payment-settings"),
    ("PUT", "/api/v1/admin/vizu-pay/payment-settings"),
    ("GET", "/api/v1/admin/vizu-pay/multilevel-entitlements"),
    ("GET", "/api/v1/admin/vizu-pay/orders?kind=multilevel"),
    ("PATCH", "/api/v1/admin/vizu-pay/orders/00000000-0000-0000-0000-000000000000/note"),
    ("POST", "/api/v1/admin/vizu-pay/orders/00000000-0000-0000-0000-000000000000/approve"),
    ("POST", "/api/v1/admin/vizu-pay/promo-codes/00000000-0000-0000-0000-000000000000/review"),
    ("POST", "/api/v1/admin/vizu-pay/promo-requests/00000000-0000-0000-0000-000000000000/course-review"),
    ("GET", "/api/v1/admin/vizu-pay/promo-requests?kind=COURSE_REQUEST"),
]
STUDENT_ROUTES = [
    ("GET", "/api/v1/vizu-pay/multilevel"),
    ("GET", "/api/v1/vizu-pay/multilevel/quote"),
    ("POST", "/api/v1/vizu-pay/multilevel/orders"),
    ("POST", "/api/v1/vizu-pay/multilevel/redeem"),
    ("POST", "/api/v1/vizu-pay/promo/course-requests"),
]


class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing on the server
            raise unittest.SkipTest("httpx not installed")
        from app.main import app

        cls.app = app
        cls.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_anonymous_gets_401_everywhere(self):
        for method, url in ADMIN_ROUTES + STUDENT_ROUTES:
            self.assertEqual(self.client.request(method, url).status_code, 401, (method, url))

    def test_students_and_other_staff_cannot_use_admin_payment_routes(self):
        from app.api.dependencies.auth import get_current_user

        for role in ("STUDENT", "TEACHER", "SUPPORT", "CONTENT_MANAGER", "PAYMENT_MANAGER", "ADMIN"):
            self.app.dependency_overrides[get_current_user] = lambda role=role: NS(id=uuid.uuid4(), role=role)
            for method, url in ADMIN_ROUTES:
                self.assertEqual(self.client.request(method, url, json={}).status_code, 403, (role, method, url))

    def test_order_form_has_no_amount_field(self):
        """The Multilevel order takes no amount: the price is the server's (offers.ML_PREMIUM_PRICE / payment settings)."""
        import importlib
        import inspect

        student_router = importlib.import_module("app.api.vizu_pay.router")  # the package re-exports the APIRouter as `router`
        names = set(inspect.signature(student_router.multilevel_create_order).parameters)
        self.assertIn("proof", names)
        self.assertTrue(names.isdisjoint({"amount", "final_amount", "price", "base_amount"}), names)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL")
class TestMultilevelPremiumAgainstDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.core.storage.protected_local import ProtectedPaymentProofStorage
        from app.models.certification_provider import CertificationProvider
        from app.models.mock_exam_level import MockExamLevel
        from app.models.model_test import ModelTest
        from app.models.user import User
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.storage = patch.object(ProtectedPaymentProofStorage, "ROOT", Path(cls.tmp.name))
        cls.storage.start()
        tag = uuid.uuid4().hex[:6]
        with cls.Session() as db:
            cls.setting_before = db.execute(__import__("sqlalchemy").text("SELECT value FROM app_settings WHERE key = 'multilevel_premium'")).scalar()
            users = []
            for name, role in (("a", "STUDENT"), ("b", "STUDENT"), ("c", "STUDENT"), ("d", "STUDENT"), ("s", "SUPER_ADMIN")):
                u = User(email=f"mlp-{name}-{tag}@test.local", username=f"mlp_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                         is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz", premium_until=None)
                db.add(u)
                users.append(u)
            provider = CertificationProvider(name=f"MLP {tag}", code=f"MLP{tag}", is_active=True)
            db.add(provider)
            db.flush()
            level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
            db.add(level)
            db.flush()
            tests = [ModelTest(level_id=level.id, title=f"Modelltest {n}", status="PUBLISHED" if n in (1, 7) else "DRAFT", sort_order=n) for n in range(1, 11)]
            db.add_all(tests)
            db.commit()
            cls.user_ids = [u.id for u in users]
            cls.provider_id = provider.id
            cls.test_ids = [t.id for t in tests]
        cls.promo_ids = []

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete, text

        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.promo_code import PromoCode
        from app.models.user import User

        with cls.Session() as db:
            db.execute(delete(PromoCode).where(PromoCode.created_by_id.in_(cls.user_ids)))
            db.execute(delete(PromoCode).where(PromoCode.id.in_(cls.promo_ids)))
            db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_(cls.user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.target_user_id.in_(cls.user_ids)))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))  # orders, entitlements, requests, redemptions cascade
            if cls.setting_before is None:
                db.execute(text("DELETE FROM app_settings WHERE key = 'multilevel_premium'"))
            db.commit()
        cls.storage.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    # ------------------------------------------------------------------ helpers

    def users(self, db):
        from app.models.user import User

        db.info.clear()  # access checks are cached per session
        return [db.get(User, i) for i in self.user_ids]

    def order(self, db, user, *, receipt=True, no_receipt=False, paid=None, promo=None, note=None):
        from starlette.datastructures import Headers, UploadFile

        from app.services.vizu_pay import multilevel_premium as ml

        proof = UploadFile(file=io.BytesIO(PNG), filename="chek.png", headers=Headers({"content-type": "image/png"})) if receipt else None
        paid_date, paid_time = paid if paid else (None, None)
        return asyncio.run(ml.create_order(db, user, promo_code=promo, no_receipt=no_receipt, paid_date=paid_date, paid_time=paid_time,
                                           note=note, proof=proof, ip=None))

    def promo(self, db, admin, code, category, discount_type="PERCENT", value=100, review="approve_activate", **extra):
        from app.services.vizu_pay.admin_service import AdminVizuPayService

        svc = AdminVizuPayService(db)
        created = svc.create_promo(code=code, campaign=None, discount_type=discount_type, discount_value=value,
                                   applicable_course_ids=extra.pop("courses", []), applicable_package_codes=extra.pop("packages", []),
                                   starts_at=None, max_uses=extra.pop("max_uses", 10), max_uses_per_user=1, expires_at=extra.pop("expires_at", None),
                                   actor=admin, product_category=category)
        self.promo_ids.append(uuid.UUID(created["id"]))
        self.assertEqual((created["approval_status"], created["is_active"]), ("PENDING", False))  # creating never activates
        if review:
            created = svc.review_promo(created["id"], review, None, admin, None)
        return created

    def mine(self, db, user):
        from app.services.mock_exam import multilevel_exam_service as exam

        return [e for e in exam.list_exams(db, user) if e["model_test_id"] in self.test_ids]

    def code(self, prefix):
        return f"{prefix}{uuid.uuid4().hex[:6].upper()}"

    # ------------------------------------------------------------------ tests

    def test_1_all_ten_locked_and_payment_flow(self):
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.vizu_pay import multilevel_premium as ml
        from app.services.vizu_pay.admin_service import AdminVizuPayService
        from app.services.vizu_pay.service import VizuPayError

        with self.Session() as db:
            a, b, c, d, admin = self.users(db)
            cards = self.mine(db, a)
            self.assertEqual([e["number"] for e in cards], list(range(1, 11)))
            # Modelltest 1–6 are free for every student (2026-11-18); 7–10 need the Premium
            self.assertEqual([e["number"] for e in cards if e["is_locked"]], [7, 8, 9, 10])
            self.assertEqual([e["number"] for e in cards if e["available"]], [1, 7])  # the others: "Tayyorlanmoqda", no fake content
            with self.assertRaises(HTTPException) as ctx:
                exam.start_attempt(db, a, self.test_ids[6])
            self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (403, "PREMIUM_REQUIRED"))
            with self.assertRaises(HTTPException) as ctx:  # a free test passes the gate (this fixture test has no content)
                exam.start_attempt(db, a, self.test_ids[0])
            self.assertEqual(ctx.exception.detail, "EXAM_NOT_READY")

            status = ml.status(db, a)
            self.assertEqual((status["product"]["price"], status["product"]["currency"], status["entitled"]), (99_000, "UZS", False))
            mine = {k: status["tests"][k] for k in ("free", "premium_total", "premium_available")}
            self.assertEqual(mine["free"], 6)
            self.assertGreaterEqual(mine["premium_total"], 4)
            self.assertEqual(status["cards"][0]["number"], "9860040114063742")
            self.assertEqual(ml.quote(db, a, None)["final_amount"], 99_000)

            # receipt required unless "Chek mavjud emas"; then date + time are required and checked
            for kwargs, detail in (({"receipt": False}, "RECEIPT_REQUIRED"), ({"receipt": False, "no_receipt": True}, "PAID_AT_REQUIRED"),
                                   ({"receipt": True, "no_receipt": True, "paid": ("2026-11-16", "10:00")}, "RECEIPT_AND_NO_RECEIPT"),
                                   ({"receipt": False, "no_receipt": True, "paid": ("2026-11-16", None)}, "PAID_AT_INCOMPLETE"),
                                   ({"receipt": False, "no_receipt": True, "paid": ("2099-01-01", "10:00")}, "PAID_AT_INVALID")):
                with self.assertRaises(HTTPException, msg=kwargs) as ctx:
                    self.order(db, a, **kwargs)
                self.assertEqual(ctx.exception.detail, detail)

            out = self.order(db, a, note="Kapitalbank orqali")
            self.assertEqual((out["status"], out["plan"], out["final_amount"], out["product_category"], out["has_proof"]),
                             ("PENDING", "ML_PREMIUM", 99_000, "MULTILEVEL", True))
            with self.assertRaises(HTTPException) as ctx:  # one open request at a time
                self.order(db, a)
            self.assertEqual(ctx.exception.detail, "PAYMENT_REQUEST_ALREADY_PENDING")
            self.assertEqual([e["number"] for e in self.mine(db, self.users(db)[0]) if e["is_locked"]], [7, 8, 9, 10])  # pending opens nothing
            self.assertEqual(ml.status(db, a)["pending_order"]["id"], out["id"])
            self.assertIsNone(ml.status(db, b)["pending_order"])  # never someone else's request

            admin_svc = AdminVizuPayService(db)
            listed = admin_svc.list_orders(kind="multilevel", status="PENDING")["items"]
            self.assertIn(out["id"], [o["id"] for o in listed])
            noted = admin_svc.set_order_note(out["id"], "Chek tekshirildi", admin, None)
            self.assertEqual(noted["admin_note"], "Chek tekshirildi")
            approved = admin_svc.approve_order(out["id"], admin, None)
            self.assertEqual((approved["status"], approved["access_end_date"]), ("APPROVED", None))  # unlimited
            with self.assertRaises(VizuPayError):  # approval never runs twice
                admin_svc.approve_order(out["id"], admin, None)
            a = self.users(db)[0]
            self.assertTrue(ml.status(db, a)["entitled"])
            self.assertFalse(any(e["is_locked"] for e in self.mine(db, a)))  # all 10 open
            with self.assertRaises(HTTPException) as ctx:  # Modelltest 7 now passes the gate; this fixture test has no content
                exam.start_attempt(db, a, self.test_ids[6])
            self.assertEqual(ctx.exception.detail, "EXAM_NOT_READY")
            with self.assertRaises(HTTPException) as ctx:  # already owned: no second purchase
                self.order(db, a)
            self.assertEqual(ctx.exception.detail, "ALREADY_ENTITLED")

            # no receipt, date + time; rejected with a reason -> still locked -> may send a new request
            paid_at = datetime.now(TASHKENT) - timedelta(hours=2)
            out_b = self.order(db, b, receipt=False, no_receipt=True, paid=(paid_at.date().isoformat(), paid_at.strftime("%H:%M")))
            self.assertEqual((out_b["no_receipt"], out_b["has_proof"], out_b["paid_at"] is not None), (True, False, True))
            admin_svc.reject_order(out_b["id"], "To'lov topilmadi", admin, None)
            b = self.users(db)[1]
            st = ml.status(db, b)
            self.assertEqual((st["entitled"], st["last_rejected"]["reason"]), (False, "To'lov topilmadi"))
            self.assertEqual([e["number"] for e in self.mine(db, b) if e["is_locked"]], [7, 8, 9, 10])
            self.assertEqual(self.order(db, b)["status"], "PENDING")

            # refund revokes the access (the row stays as history)
            admin_svc.refund_order(out["id"], "test refund", admin, None)
            a = self.users(db)[0]
            self.assertFalse(ml.status(db, a)["entitled"])
            self.assertEqual([e["number"] for e in self.mine(db, a) if e["is_locked"]], [7, 8, 9, 10])
            holders = ml.list_entitlements(db, include_revoked=True)
            self.assertTrue(any(h["user_id"] == str(a.id) and h["revoked_at"] is not None for h in holders))

    def test_2_promo_approval_categories_limits_expiry(self):
        from app.services.vizu_pay import multilevel_premium as ml
        from app.services.vizu_pay.admin_service import AdminVizuPayService
        from app.services.vizu_pay.service import VizuPayError, VizuPayService

        with self.Session() as db:
            a, b, c, d, admin = self.users(db)
            admin_svc = AdminVizuPayService(db)
            # PENDING: does nothing anywhere
            pending = self.promo(db, admin, self.code("MLP"), "MULTILEVEL", "FREE_ACCESS", review=None)
            self.assertEqual(ml.quote(db, c, pending["code"])["promo_error"], "PROMO_NOT_ACTIVE")
            with self.assertRaises(HTTPException) as ctx:
                ml.redeem(db, c, pending["code"], None)
            self.assertEqual(ctx.exception.detail, "PROMO_NOT_ACTIVE")
            # APPROVED but not switched on: still nothing; ACTIVE: works
            approved = admin_svc.review_promo(pending["id"], "approve", "ok", admin, None)
            self.assertEqual(approved["approval_status"], "APPROVED")
            self.assertEqual(ml.quote(db, c, pending["code"])["promo_error"], "PROMO_NOT_ACTIVE")
            with self.assertRaises(VizuPayError):  # a code can be activated only from APPROVED / DISABLED
                admin_svc.review_promo(pending["id"], "approve", None, admin, None)
            admin_svc.review_promo(pending["id"], "activate", None, admin, None)
            q = ml.quote(db, c, pending["code"].lower())
            self.assertEqual((q["promo_error"], q["final_amount"], q["free"]), (None, 0, True))
            with self.assertRaises(HTTPException) as ctx:  # 100 % codes are redeemed, never sent as a 0 UZS card payment
                self.order(db, c, promo=pending["code"])
            self.assertEqual(ctx.exception.detail, "PROMO_FREE_USE_REDEEM")
            ml.redeem(db, c, pending["code"], None)
            c = self.users(db)[2]
            st = ml.status(db, c)
            self.assertEqual((st["entitled"], st["entitlement"]["source"]), (True, "PROMO"))
            self.assertFalse(any(e["is_locked"] for e in self.mine(db, c)))
            with self.assertRaises(HTTPException) as ctx:
                ml.redeem(db, c, pending["code"], None)  # never twice (per-user limit of the code, or the access already exists)
            self.assertIn(ctx.exception.status_code, (409, 422))

            # a percentage Multilevel code: server price minus the discount, reserved on the order
            pct = self.promo(db, admin, self.code("MLQ"), "MULTILEVEL", "PERCENT", 30)
            self.assertEqual(ml.quote(db, d, pct["code"])["final_amount"], 69_300)
            out = self.order(db, d, promo=pct["code"])
            self.assertEqual((out["final_amount"], out["discount_amount"], out["promo_code"]), (69_300, 29_700, pct["code"]))
            admin_svc.reject_order(out["id"], "no", admin, None)  # the reserved use comes back
            self.assertEqual(next(p for p in admin_svc.list_promos() if p["id"] == pct["id"])["used_count"], 0)

            # categories never mix
            course_code = self.promo(db, admin, self.code("CRS"), "PACKAGES", "PERCENT", 10, packages=["A1_B1"])
            self.assertEqual(ml.quote(db, d, course_code["code"])["promo_error"], "PROMO_WRONG_PRODUCT")
            with self.assertRaises(HTTPException):
                ml.redeem(db, d, course_code["code"], None)
            pay = VizuPayService(db)
            self.assertEqual(pay.quote(d, "A1_B1", pct["code"])["promo_error"], "PROMO_WRONG_PRODUCT")
            self.assertEqual(pay.quote(d, "A1_B1", course_code["code"])["promo_discount"], 20_000)
            # unknown code
            self.assertEqual(ml.quote(db, d, "NOPE-" + pct["code"])["promo_error"], "Promo code not found.")

            # usage limit: max_uses 1 -> the second student is refused
            single = self.promo(db, admin, self.code("ONE"), "MULTILEVEL", "FREE_ACCESS", max_uses=1)
            ml.redeem(db, self.users(db)[3], single["code"], None)
            self.assertIn("limit", ml.quote(db, self.users(db)[1], single["code"])["promo_error"])
            # expiry
            old = self.promo(db, admin, self.code("OLD"), "MULTILEVEL", "PERCENT", 50, review="approve",
                             expires_at=datetime.now(timezone.utc) + timedelta(seconds=1))
            from app.models.promo_code import PromoCode

            row = db.get(PromoCode, uuid.UUID(old["id"]))
            row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
            db.commit()
            with self.assertRaises(VizuPayError):  # an expired code cannot be switched on
                admin_svc.review_promo(old["id"], "activate", None, admin, None)
            self.assertEqual(next(p for p in admin_svc.list_promos() if p["id"] == old["id"])["status"], "EXPIRED")

            # a material change sends an active code back to PENDING
            changed = admin_svc.update_promo(pct["id"], {"discount_value": 40}, admin)
            self.assertEqual((changed["approval_status"], changed["is_active"]), ("PENDING", False))
            with self.assertRaises(VizuPayError):  # switching it on again needs an approval
                admin_svc.update_promo(pct["id"], {"is_active": True}, admin)

    def test_3_course_promo_request(self):
        from app.models.subscription_order import SubscriptionOrder
        from app.services.vizu_pay.admin_service import AdminVizuPayService
        from app.services.vizu_pay.service import VizuPayService

        with self.Session() as db:
            a, b, c, d, admin = self.users(db)
            pay, admin_svc = VizuPayService(db), AdminVizuPayService(db)
            req = pay.create_course_request(b, "A1_B1", "Talaba, chegirma kerak", None)
            self.assertEqual((req["kind"], req["status"], req["code"]), ("COURSE_REQUEST", "PENDING_APPROVAL", ""))
            self.assertEqual(pay.create_course_request(b, "A1_B1", None, None)["id"], req["id"])  # idempotent
            with self.assertRaises(HTTPException):
                pay.create_course_request(b, "ML_PREMIUM", None, None)  # courses / packages only
            listed = admin_svc.list_promo_requests(kind="COURSE_REQUEST", status="PENDING_APPROVAL", search="mlp_b_")["items"]
            self.assertEqual([r["id"] for r in listed], [req["id"]])
            orders_before = db.query(SubscriptionOrder).filter(SubscriptionOrder.user_id == b.id).count()
            done = admin_svc.review_course_request(req["id"], True, "ok", admin, None, mode="create", discount_type="PERCENT", discount_value=50)
            self.assertEqual(done["status"], "APPROVED")
            code = done["code"]
            self.assertTrue(code.startswith("REQ-"))
            mine = [r for r in pay.my_promo_requests(b) if r["id"] == req["id"]][0]
            self.assertEqual((mine["code"], mine["discount"]["type"], mine["discount"]["value"]), (code, "PERCENT", 50))
            # approval opens / buys nothing
            self.assertEqual(db.query(SubscriptionOrder).filter(SubscriptionOrder.user_id == b.id).count(), orders_before)
            # the personal code works for this student and this package only
            self.assertEqual(pay.quote(b, "A1_B1", code)["promo_discount"], 100_000)
            self.assertEqual(pay.quote(d, "A1_B1", code)["promo_error"], "Promo code not found.")
            self.assertEqual(pay.quote(b, "A1_C1", code)["promo_discount"], 0)
            from app.services.vizu_pay import multilevel_premium as ml

            self.assertEqual(ml.quote(db, b, code)["promo_error"], "PROMO_WRONG_PRODUCT")
            # reject, and the student may ask again; attach an existing approved code
            req2 = pay.create_course_request(d, "A1_B1", None, None)
            admin_svc.review_course_request(req2["id"], False, "Hozircha yo'q", admin, None)
            self.assertEqual([r for r in pay.my_promo_requests(d) if r["id"] == req2["id"]][0]["status"], "REJECTED")
            req3 = pay.create_course_request(d, "A1_B1", "yana", None)
            shared = self.promo(db, admin, self.code("SHR"), "PACKAGES", "PERCENT", 15, packages=["A1_B1"])
            wrong = self.promo(db, admin, self.code("WRG"), "MULTILEVEL", "PERCENT", 15)
            with self.assertRaises(Exception):
                admin_svc.review_course_request(req3["id"], True, None, admin, None, mode="attach", promo_code_id=wrong["id"])
            attached = admin_svc.review_course_request(req3["id"], True, None, admin, None, mode="attach", promo_code_id=shared["id"])
            self.assertEqual(attached["code"], shared["code"])

    def test_4_overview_and_settings(self):
        from app.services.vizu_pay import multilevel_premium as ml
        from app.services.vizu_pay.admin_service import AdminVizuPayService

        with self.Session() as db:
            a, b, c, d, admin = self.users(db)
            ov = AdminVizuPayService(db).payments_overview()
            for key in ("payments", "pending", "course_purchases", "multilevel_purchases", "multilevel_active", "promo_accesses", "revenue",
                        "promo_codes", "promo_requests_open"):
                self.assertIn(key, ov)
            self.assertEqual(ov["payments"]["total"], sum(ov["payments"][k] for k in ("approved", "pending", "rejected", "expired", "refunded")))
            prod = ml.update_settings(db, admin, {"price": 120_000, "status": "ACTIVE"}, None)
            self.assertEqual(prod["price"], 120_000)
            self.assertEqual(ml.quote(db, b, None)["base_amount"], 120_000)
            with self.assertRaises(HTTPException):
                ml.update_settings(db, admin, {"price": 5}, None)
            ml.update_settings(db, admin, {"status": "DISABLED"}, None)
            with self.assertRaises(HTTPException) as ctx:
                self.order(db, self.users(db)[3])
            self.assertEqual(ctx.exception.detail, "PRODUCT_NOT_AVAILABLE")
            ml.update_settings(db, admin, {"price": 99_000, "status": "ACTIVE"}, None)


if __name__ == "__main__":
    unittest.main()
