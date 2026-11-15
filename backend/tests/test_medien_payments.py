"""Book payments (manual card transfer): the student's request (with a receipt, or without one + transfer date / time), the status flow
PENDING → APPROVED / REJECTED / CANCELLED, the Super Admin's decision that is the ONLY thing that opens the book, and the security rules around it:
amount from the server, one open request per book, rate limit, private sanitised receipts, role checks, no double decision (also under a race), no
self-review, audit log. Integration test on a throwaway database (VIZU_WB_TEST_DB_URL)."""

import io
import threading
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from unittest.mock import patch

from tests.medien_base import RECEIPT_PNG as PNG
from tests.medien_base import MedienBase, make_pdf

NOW = lambda: datetime.now(timezone(timedelta(hours=5)))  # noqa: E731  (Uzbekistan time, like the form)


def ago(**kw):
    t = NOW() - timedelta(**kw)
    return t.date().isoformat(), t.strftime("%H:%M")


class TestBookPayments(MedienBase):
    @classmethod
    def extra_setup(cls):
        from app.services.auth import rate_limit

        # the real limits (6 submissions per student / 20 per IP per hour) are tested in test_6; the other tests submit more than that
        cls.limits = [patch.object(rate_limit, "MAX_BOOK_PAYMENTS_PER_USER", 10_000), patch.object(rate_limit, "MAX_BOOK_PAYMENTS_PER_IP", 10_000)]
        [p.start() for p in cls.limits]

    @classmethod
    def tearDownClass(cls):
        [p.stop() for p in cls.limits]
        from sqlalchemy import delete

        from app.models.app_setting import AppSetting
        from app.services.medien import book_payments

        cls.sess.rollback()
        cls.sess.execute(delete(AppSetting).where(AppSetting.key == book_payments.SETTINGS_KEY))
        cls.sess.commit()
        super().tearDownClass()

    def pay(self, who, bid, expect=200, receipt=PNG, name="r.png", **form):
        files = {"receipt": (name, receipt, "application/octet-stream")} if receipt is not None else None
        return self.api("post", f"/medien/books/{bid}/payment-requests", who, expect=expect, files=files, data=form)

    def paid_book(self, name, price=40000, **extra):
        return self.new_book(name, pages=12, access_type="PAID", price=price, **extra)

    def decide(self, who, rid, status, note=None, expect=200):
        return self.api("post", f"/admin/medien/book-payments/{rid}/decision", who, expect=expect, json={"status": status, **({"note": note} if note is not None else {})})

    # ---------- the card ----------
    def test_1_card_info_default_and_admin_settings(self):
        from app.services.vizu_pay import plans

        default = self.api("get", "/medien/book-payment-info", "a").json()
        self.assertEqual((default["card_number"], default["currency"], default["configured"]), (plans.PAYMENT_CARDS[0]["number"], "UZS", True))
        self.api("get", "/medien/book-payment-info", None, expect=401)
        self.api("put", "/admin/medien/book-payment-settings", "a", expect=403, json={"card_number": "1111222233334444"})
        self.api("put", "/admin/medien/book-payment-settings", "admin", expect=403, json={"card_number": "1111222233334444"})  # money: Super Admin only
        self.assertEqual(self.api("get", "/admin/medien/book-payment-settings", "admin").json()["card_number"], default["card_number"])  # staff may read
        self.api("get", "/admin/medien/book-payment-settings", "a", expect=403)
        for bad in ({"card_number": "12345"}, {"card_number": "x" * 40}, {"card_holder": "h" * 81}, {"unknown": 1}):
            self.api("put", "/admin/medien/book-payment-settings", "super", expect=422, json=bad)
        saved = self.api("put", "/admin/medien/book-payment-settings", "super", json={"card_number": "5555 5555 5555 4444", "card_holder": "  Max   Beispiel "}).json()
        self.assertEqual((saved["card_number"], saved["card_holder"]), ("5555555555554444", "Max Beispiel"))
        self.assertEqual(self.api("get", "/medien/book-payment-info", "b").json()["card_number"], "5555555555554444")
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        details = " ".join(d or "" for d in self.sess.scalars(select(AuditLog.details).where(AuditLog.action == "medien_book_payment_settings", AuditLog.actor_id == str(self.users["super"].id))))
        self.assertIn("****4444", details)
        self.assertNotIn("55555555", details, "a card number is never written to the audit log")
        back = self.api("put", "/admin/medien/book-payment-settings", "super", json={"card_number": "", "card_holder": ""}).json()
        self.assertEqual((back["card_number"], back["card_holder"]), (default["card_number"], ""))  # empty = the default card again

    # ---------- the student's request ----------
    def test_2_request_with_a_receipt_gives_no_access_and_the_server_sets_the_amount(self):
        book = self.paid_book("WithReceipt", price=40000)
        r = self.pay("a", book["id"], amount="1", price="1", book_id="x", payment_status="APPROVED").json()  # a client cannot set the amount or the status
        self.assertEqual((r["status"], r["amount"], r["currency"], r["has_receipt"], r["no_receipt"], r["book_title"], r["can_cancel"]), ("PENDING", 40000, "UZS", True, False, self.title("WithReceipt"), True))
        self.assertIsNone(r["admin_note"])
        self.assertNotIn("receipt_key", str(r))
        detail = self.api("get", f"/medien/books/{book['id']}", "a").json()
        self.assertEqual((detail["locked"], detail["can_download"], detail["my_payment"]["status"], detail["my_payment"]["id"]), (True, False, "PENDING", r["id"]))
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/open", "a").json()["mode"], "preview", "a request opens nothing")
        self.api("post", f"/medien/books/{book['id']}/download-link", "a", expect=403)
        self.assertEqual([x["id"] for x in self.api("get", "/medien/book-payments/mine", "a").json() if x["book_id"] == book["id"]], [r["id"]])
        self.assertEqual([x for x in self.api("get", "/medien/book-payments/mine", "b").json() if x["book_id"] == book["id"]], [])
        # one open request per book; another student can request the same book
        self.pay("a", book["id"], expect=409, receipt=PNG)
        self.pay("b", book["id"])
        # cancel (own, pending) -> new request possible; someone else's request cannot be cancelled
        self.api("post", f"/medien/book-payments/{r['id']}/cancel", "b", expect=404)
        cancelled = self.api("post", f"/medien/book-payments/{r['id']}/cancel", "a").json()
        self.assertEqual((cancelled["status"], cancelled["can_cancel"]), ("CANCELLED", False))
        self.api("post", f"/medien/book-payments/{r['id']}/cancel", "a", expect=409)
        again = self.pay("a", book["id"]).json()
        self.assertNotEqual(again["id"], r["id"])
        self.assertEqual(self.api("get", f"/medien/books/{book['id']}", "a").json()["my_payment"]["id"], again["id"])  # the latest one

    def test_3_without_a_receipt_the_transfer_date_and_time_are_required_and_checked(self):
        book = self.paid_book("NoReceipt")
        today, hhmm = ago(minutes=30)
        ok = self.pay("a", book["id"], receipt=None, no_receipt="true", transfer_date=today, transfer_time=hhmm, note="  Mit   Humo ").json()
        self.assertEqual((ok["status"], ok["has_receipt"], ok["no_receipt"], ok["transfer_date"], ok["transfer_time"], ok["note"]), ("PENDING", False, True, today, hhmm, "Mit Humo"))
        self.api("post", f"/medien/book-payments/{ok['id']}/cancel", "a")
        past_date, past_time = ago(days=3)
        cases = [
            (dict(receipt=None), "RECEIPT_OR_NO_RECEIPT"),                                                    # neither a receipt nor "I have none"
            (dict(receipt=None, no_receipt="true"), "TRANSFER_TIME_REQUIRED"),                                 # none given at all
            (dict(receipt=None, no_receipt="true", transfer_date=past_date), "TRANSFER_DATE_AND_TIME_REQUIRED"),
            (dict(receipt=None, no_receipt="true", transfer_time=past_time), "TRANSFER_DATE_AND_TIME_REQUIRED"),
            (dict(receipt=None, no_receipt="true", transfer_date="2026-13-45", transfer_time=past_time), "INVALID_TRANSFER_DATE"),
            (dict(receipt=None, no_receipt="true", transfer_date=past_date, transfer_time="25:99"), "INVALID_TRANSFER_TIME"),
            (dict(receipt=None, no_receipt="true", transfer_date=past_date, transfer_time="9:5"), "INVALID_TRANSFER_TIME"),
            (dict(receipt=None, no_receipt="true", transfer_date=(NOW() + timedelta(days=1)).date().isoformat(), transfer_time="10:00"), "TRANSFER_IN_FUTURE"),
            (dict(receipt=None, no_receipt="true", transfer_date=ago(days=31)[0], transfer_time="10:00"), "TRANSFER_TOO_OLD"),
            (dict(receipt=None, no_receipt="true", transfer_date=past_date, transfer_time=past_time, note="x" * 501), "NOTE_TOO_LONG"),
        ]
        for form, code in cases:
            r = self.pay("a", book["id"], expect=422, **form)
            self.assertTrue(r.json()["message"].startswith(code), f"{form} -> {r.json()['message']}")
        # with a receipt the date / time are optional (but if given they must be valid)
        self.pay("a", book["id"], expect=422, transfer_date=past_date)
        self.pay("a", book["id"], expect=422, transfer_date="nonsense", transfer_time="10:00")
        self.pay("a", book["id"]).json()

    def test_4_requests_only_for_paid_published_books_not_yet_owned(self):
        free = self.new_book("FreeBook")
        self.assertTrue(self.pay("a", free["id"], expect=409).json()["message"].startswith("NOT_PAID"))
        draft = self.paid_book("DraftBook", status="DRAFT")
        self.pay("a", draft["id"], expect=404)
        self.pay("a", str(uuid.uuid4()), expect=404)
        paid = self.paid_book("OwnedAlready")
        self.api("post", "/admin/medien/purchases/grant", "super", json={"kind": "BOOK", "content_id": paid["id"], "user_id": str(self.users["a"].id)})
        self.assertTrue(self.pay("a", paid["id"], expect=409).json()["message"].startswith("ALREADY_OWNED"))
        self.assertTrue(self.pay("super", paid["id"], expect=409).json()["message"].startswith("ALREADY_OWNED"))  # staff need no purchase
        self.api("post", "/medien/purchases", "b", expect=409, json={"kind": "BOOK", "content_id": paid["id"]})   # the generic request is not for books
        self.as_(None)
        self.assertEqual(self.client.post(f"/api/v1/medien/books/{paid['id']}/payment-requests").status_code, 401)

    def test_5_receipts_are_checked_cleaned_and_private(self):
        from PIL import Image

        book = self.paid_book("Receipts")
        before = self.disk()
        for name, data in (("fake.png", b"this is not an image"), ("x.pdf", b"%PDF-1.4\ngarbage that is no pdf"), ("evil.png", PNG[:12] + b"junk"), ("empty.png", b""),
                           ("script.png", b"<script>alert(1)</script>")):
            r = self.pay("a", book["id"], expect=400, receipt=data, name=name)
            self.assertRegex(r.json()["message"], r"^(INVALID_RECEIPT|UNSUPPORTED_FILE)", name)
        self.assertEqual(self.disk(), before, "a refused receipt leaves nothing on disk")
        self.pay("a", book["id"], expect=400, receipt=b"\x00" * (9 * 1024 * 1024) + PNG, name="huge.png")
        # a JPEG with camera / location EXIF and appended data is stored re-encoded: EXIF and the trailing bytes are gone
        image = Image.new("RGB", (40, 30), "red")
        exif = Image.Exif()
        exif[0x010F], exif[0x0110] = "SecretCamera", "Model-X"
        raw = io.BytesIO()
        image.save(raw, "JPEG", exif=exif)
        dirty = raw.getvalue() + b"APPENDED-SECRET-DATA"
        self.assertIn(b"SecretCamera", dirty)
        r = self.pay("a", book["id"], receipt=dirty, name="photo.jpg").json()
        got = self.api("get", f"/medien/book-payments/{r['id']}/receipt", "a")
        self.assertEqual((got.headers["content-type"], got.headers["cache-control"], got.headers["x-content-type-options"]), ("image/jpeg", "private, no-store", "nosniff"))
        self.assertIn("sandbox", got.headers["content-security-policy"])
        self.assertNotIn(b"SecretCamera", got.content)
        self.assertNotIn(b"APPENDED-SECRET-DATA", got.content)
        self.assertEqual(dict(Image.open(io.BytesIO(got.content)).getexif()), {})
        self.assertEqual(Image.open(io.BytesIO(got.content)).size, (40, 30))
        # a PDF receipt (a banking app's) is kept as it is
        self.api("post", f"/medien/book-payments/{r['id']}/cancel", "a")
        pdf = make_pdf(1, "Beleg")
        r2 = self.pay("a", book["id"], receipt=pdf, name="beleg.pdf").json()
        self.assertEqual((r2["receipt_type"] if "receipt_type" in r2 else "pdf"), "pdf")
        stored = self.api("get", f"/medien/book-payments/{r2['id']}/receipt", "a")
        self.assertEqual((stored.headers["content-type"], stored.content), ("application/pdf", pdf))
        # only the owner and the Super Admin see it — not another student, not a normal admin, nobody anonymous; a missing receipt looks the same
        self.api("get", f"/medien/book-payments/{r2['id']}/receipt", "b", expect=404)
        self.api("get", f"/admin/medien/book-payments/{r2['id']}/receipt", "admin", expect=403)
        self.api("get", f"/admin/medien/book-payments/{r2['id']}/receipt", "a", expect=403)
        self.assertEqual(self.api("get", f"/admin/medien/book-payments/{r2['id']}/receipt", "super").content, pdf)
        self.assertEqual(self.api("get", f"/medien/book-payments/{r2['id']}/receipt", "super").status_code, 200)
        self.api("get", f"/medien/book-payments/{uuid.uuid4()}/receipt", "a", expect=404)
        self.as_(None)
        self.assertEqual(self.client.get(f"/api/v1/medien/book-payments/{r2['id']}/receipt").status_code, 401)
        # the receipt file lives in the private storage under a random name
        receipts = [p for p in self.disk() if p.startswith("receipts/")]
        self.assertTrue(receipts and all(len(p) > 40 and "r.png" not in p and "beleg" not in p for p in receipts))
        self.assertEqual(self.client.get(f"/protected_storage/medien/{receipts[0]}").status_code, 404)

    def test_6_rate_limit_per_student(self):
        from sqlalchemy import delete

        from app.models.auth_rate_limit_event import AuthRateLimitEvent
        from app.services.auth import rate_limit

        self.sess.execute(delete(AuthRateLimitEvent).where(AuthRateLimitEvent.email_hash == rate_limit._key("user", str(self.users["rate"].id))))
        self.sess.commit()  # earlier tests also used this student
        book = self.paid_book("RateLimit")
        with patch.object(rate_limit, "MAX_BOOK_PAYMENTS_PER_USER", 6), patch.object(rate_limit, "MAX_BOOK_PAYMENTS_PER_IP", 10_000):
            for i in range(6):
                r = self.pay("rate", book["id"]).json()
                self.api("post", f"/medien/book-payments/{r['id']}/cancel", "rate")
            blocked = self.pay("rate", book["id"], expect=429)
            self.assertTrue(blocked.json()["message"].startswith("RATE_LIMITED"))
            self.assertGreaterEqual(int(blocked.headers["retry-after"]), 1)
            self.pay("b", book["id"])  # other students are not affected
        with patch.object(rate_limit, "MAX_BOOK_PAYMENTS_PER_IP", 1):  # and per IP: everybody behind one address is limited together
            self.pay("a", book["id"], expect=429)

    # ---------- the Super Admin ----------
    def test_7_only_the_super_admin_sees_and_decides(self):
        book = self.paid_book("AdminOnly")
        r = self.pay("a", book["id"]).json()
        for who in ("a", "b", "admin"):
            self.api("get", "/admin/medien/book-payments", who, expect=403)
            self.api("get", f"/admin/medien/book-payments/{r['id']}", who, expect=403)
            self.decide(who, r["id"], "APPROVED", expect=403)
        self.as_(None)
        for method, url in (("get", "/api/v1/admin/medien/book-payments"), ("post", f"/api/v1/admin/medien/book-payments/{r['id']}/decision")):
            self.assertEqual(getattr(self.client, method)(url).status_code, 401, url)
        listing = self.api("get", f"/admin/medien/book-payments?q={self.tag}%20AdminOnly", "super").json()
        row = listing["items"][0]
        self.assertEqual((listing["total"], row["id"], row["user_id"], row["user_name"], row["user_email"], row["book_title"], row["amount"], row["status"], row["has_receipt"]),
                         (1, r["id"], str(self.users["a"].id), "A Tester", self.users["a"].email, self.title("AdminOnly"), 40000, "PENDING", True))
        self.assertEqual(set(listing["counts"]), {"PENDING", "APPROVED", "REJECTED", "CANCELLED"})
        self.assertEqual(self.api("get", f"/admin/medien/book-payments?status=APPROVED&q={self.tag}%20AdminOnly", "super").json()["total"], 0)
        self.api("get", "/admin/medien/book-payments?status=BOGUS", "super", expect=422)
        detail = self.api("get", f"/admin/medien/book-payments/{r['id']}", "super").json()
        self.assertEqual((detail["book_price"], detail["book_exists"], detail["history"]), (40000, True, []))
        self.assertEqual([p for p in detail["purchases"] if p["title"] == self.title("AdminOnly")], [])  # the student's purchases (of other books) are listed, not this one
        self.assertEqual(self.api("get", "/admin/medien/stats", "super").json()["pending_book_payments"] >= 1, True)
        # decisions: only APPROVED / REJECTED
        self.decide("super", r["id"], "GRANTED", expect=422)
        self.api("post", f"/admin/medien/book-payments/{r['id']}/decision", "super", expect=422, json={"status": "APPROVED", "extra": 1})
        self.api("post", f"/admin/medien/book-payments/{uuid.uuid4()}/decision", "super", expect=404, json={"status": "APPROVED"})

    def test_8_approval_opens_the_book_exactly_once(self):
        from sqlalchemy import select

        from app.models.medien import MediaPurchase

        book = self.paid_book("Approve")
        self.api("get", f"/medien/books/{book['id']}", "a")
        r = self.pay("a", book["id"]).json()
        done = self.decide("super", r["id"], "APPROVED", note="Betrag und Beleg geprüft").json()
        self.assertEqual((done["status"], done["reviewed_by_id"], done["admin_note"]), ("APPROVED", str(self.users["super"].id), "Betrag und Beleg geprüft"))
        self.assertIsNotNone(done["reviewed_at"])
        self.assertEqual([p["status"] for p in done["purchases"] if p["title"] == self.title("Approve")], ["GRANTED"])
        # the book is open: full reader, download, no preview limit
        detail = self.api("get", f"/medien/books/{book['id']}", "a").json()
        self.assertEqual((detail["locked"], detail["can_download"], detail["my_payment"]["status"]), (False, True, "APPROVED"))
        opened = self.api("post", f"/medien/books/{book['id']}/open", "a").json()
        self.assertEqual((opened["mode"], opened["preview_pages"], opened["can_download"]), ("full", None, True))
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/download-link", "a").json()["filename"], f"{self.title('Approve')}.pdf")
        # the purchase is linked to the request and carries the amount that was paid
        self.sess.expire_all()
        purchase = self.sess.scalar(select(MediaPurchase).where(MediaPurchase.user_id == self.users["a"].id, MediaPurchase.content_id == uuid.UUID(book["id"])))
        self.assertEqual((purchase.status, purchase.price, str(purchase.payment_request_id), purchase.decided_by_id), ("GRANTED", 40000, r["id"], self.users["super"].id))
        self.assertEqual(self.api("get", "/medien/purchases/mine", "a").json()[0]["status"], "GRANTED")
        # it works once: approve again, reject afterwards, cancel — all refused; still one purchase
        self.decide("super", r["id"], "APPROVED", expect=409)
        self.decide("super", r["id"], "REJECTED", note="zu spät", expect=409)
        self.api("post", f"/medien/book-payments/{r['id']}/cancel", "a", expect=409)
        self.assertEqual(self.sess.scalar(select(__import__("sqlalchemy").func.count()).select_from(MediaPurchase).where(MediaPurchase.user_id == self.users["a"].id, MediaPurchase.content_id == uuid.UUID(book["id"]))), 1)
        # another student's book stays closed
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/open", "b").json()["mode"], "preview")
        # the purchase can still be revoked with the existing tool; the student may pay again
        revoke = next(p for p in self.api("get", "/admin/medien/purchases", "super").json() if p["content_id"] == book["id"] and p["user_id"] == str(self.users["a"].id))
        self.api("post", f"/admin/medien/purchases/{revoke['id']}/decision", "super", json={"status": "REVOKED"})
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/open", "a").json()["mode"], "preview")
        again = self.pay("a", book["id"]).json()
        self.decide("super", again["id"], "APPROVED")
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/open", "a").json()["mode"], "full")

    def test_9_rejection_needs_a_reason_keeps_the_book_closed_and_allows_a_new_request(self):
        book = self.paid_book("Reject")
        r = self.pay("a", book["id"]).json()
        for note in (None, "", "  ", "ab"):
            self.assertTrue(self.decide("super", r["id"], "REJECTED", note=note, expect=422).json()["message"].startswith("REASON_REQUIRED"), note)
        self.decide("super", r["id"], "REJECTED", note="x" * 501, expect=422)
        rej = self.decide("super", r["id"], "REJECTED", note="Der Betrag stimmt nicht").json()
        self.assertEqual((rej["status"], rej["admin_note"]), ("REJECTED", "Der Betrag stimmt nicht"))
        mine = self.api("get", "/medien/book-payments/mine", "a").json()[0]
        self.assertEqual((mine["status"], mine["admin_note"], mine["can_cancel"]), ("REJECTED", "Der Betrag stimmt nicht", False))
        detail = self.api("get", f"/medien/books/{book['id']}", "a").json()
        self.assertEqual((detail["locked"], detail["my_payment"]["status"], detail["my_payment"]["admin_note"]), (True, "REJECTED", "Der Betrag stimmt nicht"))
        self.assertEqual(self.api("post", f"/medien/books/{book['id']}/open", "a").json()["mode"], "preview")
        self.api("post", f"/medien/books/{book['id']}/download-link", "a", expect=403)
        self.decide("super", r["id"], "APPROVED", expect=409)  # a rejected request cannot be approved afterwards
        self.pay("a", book["id"])  # sending again is possible
        # a cancelled request cannot be decided either
        other = self.pay("b", book["id"]).json()
        self.api("post", f"/medien/book-payments/{other['id']}/cancel", "b")
        self.decide("super", other["id"], "APPROVED", expect=409)
        # the reason of another student's rejection is not visible to a stranger; an approval note stays internal
        self.assertEqual(self.api("get", "/medien/book-payments/mine", "b").json()[0]["admin_note"], None)

    def test_10_two_decisions_at_the_same_moment_only_one_wins(self):
        from fastapi import HTTPException
        from sqlalchemy import func, select
        from sqlalchemy.orm import sessionmaker

        from app.models.medien import MediaPurchase
        from app.services.medien import book_payments

        book = self.paid_book("Race")
        r = self.pay("a", book["id"]).json()
        Session = sessionmaker(bind=self.engine)
        results, barrier = [], threading.Barrier(2)

        def work(decision):
            with Session() as db:
                barrier.wait()
                try:
                    book_payments.decide(db, self.users["super"], uuid.UUID(r["id"]), decision, "geprüft")
                    results.append((decision, 200))
                except HTTPException as exc:
                    results.append((decision, exc.status_code))

        threads = [threading.Thread(target=work, args=(d,)) for d in ("APPROVED", "REJECTED")]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(code for _, code in results), [200, 409], results)
        winner = next(d for d, code in results if code == 200)
        self.sess.expire_all()
        count = self.sess.scalar(select(func.count()).select_from(MediaPurchase).where(MediaPurchase.user_id == self.users["a"].id, MediaPurchase.content_id == uuid.UUID(book["id"]),
                                                                                         MediaPurchase.status == "GRANTED"))
        self.assertEqual(count, 1 if winner == "APPROVED" else 0)
        # two approvals at once (the same request): exactly one purchase
        r2 = self.pay("b", book["id"]).json()
        results.clear()
        barrier = threading.Barrier(2)
        threads = [threading.Thread(target=lambda: self._approve(Session, book_payments, r2["id"], results, barrier)) for _ in range(2)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(code for _, code in results), [200, 409])
        self.sess.expire_all()
        self.assertEqual(self.sess.scalar(select(func.count()).select_from(MediaPurchase).where(MediaPurchase.user_id == self.users["b"].id, MediaPurchase.content_id == uuid.UUID(book["id"]))), 1)

    def _approve(self, Session, book_payments, rid, results, barrier):
        from fastapi import HTTPException

        with Session() as db:
            barrier.wait()
            try:
                book_payments.decide(db, self.users["super"], uuid.UUID(rid), "APPROVED", "ok")
                results.append(("APPROVED", 200))
            except HTTPException as exc:
                results.append(("APPROVED", exc.status_code))

    def test_11_nobody_reviews_their_own_request(self):
        from app.models.medien import BookPaymentRequest

        book = self.paid_book("SelfReview")
        row = BookPaymentRequest(user_id=self.users["super"].id, book_id=uuid.UUID(book["id"]), book_title="x", amount=1000, no_receipt=True)
        self.sess.add(row)
        self.sess.commit()
        self.assertTrue(self.decide("super", str(row.id), "APPROVED", expect=403).json()["message"].startswith("SELF_REVIEW_FORBIDDEN"))

    def test_12_an_existing_direct_grant_is_reused_and_the_paid_amount_stays_when_the_price_changes(self):
        from sqlalchemy import func, select

        from app.models.medien import MediaPurchase

        book = self.paid_book("Existing", price=40000)
        r = self.pay("a", book["id"]).json()
        self.api("put", f"/admin/medien/books/{book['id']}", "admin", json={"price": 99000})  # the price changes while the request waits
        self.assertEqual(r["amount"], 40000)
        detail = self.api("get", f"/admin/medien/book-payments/{r['id']}", "super").json()
        self.assertEqual((detail["amount"], detail["book_price"]), (40000, 99000))  # the admin sees both before deciding
        self.api("post", "/admin/medien/purchases/grant", "super", json={"kind": "BOOK", "content_id": book["id"], "user_id": str(self.users["a"].id)})  # a direct grant meanwhile
        self.decide("super", r["id"], "APPROVED")
        self.sess.expire_all()
        rows = self.sess.scalars(select(MediaPurchase).where(MediaPurchase.user_id == self.users["a"].id, MediaPurchase.content_id == uuid.UUID(book["id"]))).all()
        self.assertEqual([(p.status, str(p.payment_request_id)) for p in rows], [("GRANTED", r["id"])], "one purchase, now linked to the payment")

    def test_13_history_survives_a_deleted_book_and_nothing_can_be_approved_for_it(self):
        book = self.paid_book("Vanishing")
        r = self.pay("a", book["id"]).json()
        self.api("delete", f"/admin/medien/books/{book['id']}", "admin", expect=204)
        got = self.api("get", f"/admin/medien/book-payments/{r['id']}", "super").json()
        self.assertEqual((got["book_id"], got["book_title"], got["book_exists"], got["status"]), (None, self.title("Vanishing"), False, "PENDING"))
        self.assertTrue(self.decide("super", r["id"], "APPROVED", expect=409).json()["message"].startswith("BOOK_GONE"))
        self.decide("super", r["id"], "REJECTED", note="Buch nicht mehr vorhanden")
        self.assertEqual(self.api("get", "/medien/book-payments/mine", "a").json()[0]["book_title"], self.title("Vanishing"))

    def test_14_everything_is_in_the_audit_log(self):
        from sqlalchemy import select

        from app.models.audit_log import AuditLog

        book = self.paid_book("Audited")
        r = self.pay("a", book["id"]).json()
        r2 = self.pay("b", book["id"]).json()
        self.decide("super", r["id"], "APPROVED")
        self.decide("super", r2["id"], "REJECTED", note="kein Eingang")
        self.api("post", f"/medien/book-payments/{self.pay('rate', book['id']).json()['id']}/cancel", "rate")
        actions = {(a, d) for a, d in self.sess.execute(select(AuditLog.action, AuditLog.details).where(AuditLog.actor_id.in_([str(u.id) for u in self.users.values()]),
                                                                                                         AuditLog.action.like("book_payment_%")))}
        names = {a for a, _ in actions}
        self.assertTrue({"book_payment_requested", "book_payment_approved", "book_payment_rejected", "book_payment_cancelled"} <= names, names)
        self.assertTrue(any(r["id"] in (d or "") for a, d in actions if a == "book_payment_approved"))
        self.assertFalse(any("5555" in (d or "") or "9860" in (d or "") for _, d in actions), "no card numbers in the log")


if __name__ == "__main__":
    unittest.main()
