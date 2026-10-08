"""Werbung-Banner: URL / image validation, CTR, date-range eligibility."""

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from pydantic import ValidationError

from app.schemas.advertisement import AdvertisementCreate
from app.services.advertisement_service import client_hash, is_eligible
from app.services.advertisement_validation import ctr, validate_image_url, validate_target_url

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)


class TestTargetUrl(unittest.TestCase):
    def test_accepts_http_and_https(self):
        self.assertEqual(validate_target_url(" https://vizu.academy/kurse "), "https://vizu.academy/kurse")
        self.assertEqual(validate_target_url("http://example.com/a?b=1"), "http://example.com/a?b=1")

    def test_rejects_dangerous_or_incomplete_urls(self):
        for bad in (
            "javascript:alert(1)",
            "data:text/html,<b>x</b>",
            "//evil.com",
            "/relative/path",
            "ftp://example.com",
            "https://localhost",
            "https://user:pw@example.com",
            "https://exa mple.com",
            "",
            "https://" + "a" * 1000 + ".com",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_target_url(bad)


class TestImageUrl(unittest.TestCase):
    def test_accepts_upload_path_and_https(self):
        self.assertEqual(validate_image_url("/uploads/images/ab12.png"), "/uploads/images/ab12.png")
        self.assertEqual(validate_image_url("https://cdn.example.com/a.jpg"), "https://cdn.example.com/a.jpg")
        self.assertIsNone(validate_image_url(""))
        self.assertIsNone(validate_image_url(None))
        # Real upload paths keep the original file name (spaces / non-ASCII).
        for ok in (
            "/uploads/images/3f2a_Screenshot 2026-10-02 at 21.45.png",
            "/uploads/images/3f2a_Снимок экрана.png",
            "/uploads/images/3f2a_logo..final.png",
        ):
            with self.subTest(ok=ok):
                self.assertEqual(validate_image_url(ok), ok)
        for bad in (
            "/uploads/images/../../etc/passwd",
            "/uploads/images/a/../b.png",
            "/uploads/images/",
            "/uploads/images//a.png",
            "/uploads/images/a\\b.png",
            "/uploads/images/a\nb.png",
            "https://cdn.example.com/a b.jpg",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    validate_image_url(bad)

    def test_rejects_base64_and_other_paths(self):
        for bad in ("data:image/png;base64,AAAA", "/uploads/../secret", "/etc/passwd", "http://insecure.com/a.png", "/uploads/videos/a.mp4"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_image_url(bad)


class TestCtr(unittest.TestCase):
    def test_ctr(self):
        self.assertEqual(ctr(1245, 87), 6.99)
        self.assertEqual(ctr(0, 0), 0.0)
        self.assertEqual(ctr(3, 1), 33.33)


class TestEligibility(unittest.TestCase):
    def ad(self, **kw):
        base = {"is_active": True, "starts_at": None, "ends_at": None}
        base.update(kw)
        return SimpleNamespace(**base)

    def test_date_range_and_active_flag(self):
        self.assertTrue(is_eligible(self.ad(), NOW))
        self.assertFalse(is_eligible(self.ad(is_active=False), NOW))
        self.assertFalse(is_eligible(self.ad(starts_at=NOW + timedelta(hours=1)), NOW))
        self.assertFalse(is_eligible(self.ad(ends_at=NOW - timedelta(seconds=1)), NOW))
        self.assertTrue(is_eligible(self.ad(starts_at=NOW - timedelta(days=1), ends_at=NOW + timedelta(days=1)), NOW))


class TestSchema(unittest.TestCase):
    def test_end_before_start_rejected(self):
        with self.assertRaises(ValidationError):
            AdvertisementCreate(title="A", target_url="https://a.de", starts_at=NOW, ends_at=NOW - timedelta(days=1))

    def test_bad_link_rejected_and_cta_default(self):
        with self.assertRaises(ValidationError):
            AdvertisementCreate(title="A", target_url="javascript:alert(1)")
        self.assertEqual(AdvertisementCreate(title="A", target_url="https://a.de", cta_text="  ").cta_text, "Mehr erfahren")

    def test_client_hash_is_stable_and_not_raw(self):
        h = client_hash("1.2.3.4", "UA")
        self.assertEqual(h, client_hash("1.2.3.4", "UA"))
        self.assertNotIn("1.2.3.4", h)
        self.assertEqual(len(h), 64)



class TestCarouselImpressions(unittest.TestCase):
    """The dashboard rotates through every eligible ad, so an impression counts
    for any eligible ad (not only the top-priority one) — still de-duplicated
    per user, and never for an inactive / scheduled / expired ad."""

    def _ad(self, **kw):
        base = {"id": "ad-2", "is_active": True, "starts_at": None, "ends_at": None}
        base.update(kw)
        return SimpleNamespace(**base)

    def test_second_eligible_ad_is_counted(self):
        from unittest.mock import MagicMock

        from app.services import advertisement_service as svc

        db = MagicMock()
        db.scalar.return_value = None  # no recent impression by this user
        self.assertTrue(svc.record_impression(db, self._ad(), "u1"))
        db.add.assert_called_once()

    def test_dedup_window_still_applies(self):
        from unittest.mock import MagicMock

        from app.services import advertisement_service as svc

        db = MagicMock()
        db.scalar.return_value = "recent-event"
        self.assertFalse(svc.record_impression(db, self._ad(), "u1"))
        db.add.assert_not_called()

    def test_ineligible_ads_never_counted(self):
        from unittest.mock import MagicMock

        from app.services import advertisement_service as svc

        for ad in (self._ad(is_active=False), self._ad(ends_at=datetime(2000, 1, 1, tzinfo=timezone.utc))):
            db = MagicMock()
            self.assertFalse(svc.record_impression(db, ad, "u1"))
            db.add.assert_not_called()

    def test_list_endpoint_is_registered_and_active_unchanged(self):
        from app.api.advertisements.router import router

        paths = {r.path for r in router.routes}
        self.assertIn("/advertisements/active-list", paths)
        self.assertIn("/advertisements/active", paths)


if __name__ == "__main__":
    unittest.main()
