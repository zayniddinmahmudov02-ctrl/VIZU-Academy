"""Internal-link registry (app.services.student_routes) + the Werbung link
type rules: only real student pages, only whitelisted parameters, a removed
route falls back safely, external links stay http(s) only."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from app.schemas.advertisement import AdvertisementCreate, apply_link_rules
from app.services import advertisement_service, student_routes

APP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "app", "(dashboard)")


class TestRegistry(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(APP_DIR), "frontend sources not present")
    def test_every_route_is_a_real_student_page(self):
        for key, route in student_routes.STUDENT_ROUTES.items():
            # "/kurse/{level}" -> (dashboard)/kurse/[level]/page.tsx
            parts = [f"[{p[1:-1]}]" if p.startswith("{") else p for p in route["path"].strip("/").split("/")]
            with self.subTest(key=key):
                self.assertTrue(os.path.isfile(os.path.join(APP_DIR, *parts, "page.tsx")), route["path"])

    def test_resolve(self):
        self.assertEqual(student_routes.resolve("kurse", {}), ("/kurse", True))
        self.assertEqual(student_routes.resolve("kurse_level", {"level": "a1"}), ("/kurse/a1", True))
        self.assertEqual(student_routes.resolve("angebote_offer", {"offer": "A1"}), ("/angebote?offer=A1", True))

    def test_removed_route_or_bad_params_fall_back(self):
        fallback = (student_routes.FALLBACK_PATH, False)
        self.assertEqual(student_routes.resolve("gone", {}), fallback)
        self.assertEqual(student_routes.resolve(None, None), fallback)
        self.assertEqual(student_routes.resolve("kurse_level", {"level": "../admin"}), fallback)
        self.assertEqual(student_routes.resolve("kurse_level", {}), fallback)
        self.assertEqual(student_routes.resolve("kurse", {"x": "1"}), fallback)

    def test_validate_rejects(self):
        for key, params in (("nope", {}), ("kurse_level", {"level": "z9"}), ("kurse_level", {"level": 1}),
                            ("angebote_offer", {"offer": "javascript:alert(1)"}), ("dashboard", {"next": "//evil.com"})):
            with self.subTest(key=key, params=params), self.assertRaises(ValueError):
                student_routes.validate(key, params)

    def test_catalogue_grouped(self):
        cat = student_routes.catalogue()
        self.assertTrue(all({"key", "group", "label", "path", "params"} <= set(r) for r in cat))
        level = next(r for r in cat if r["key"] == "kurse_level")
        self.assertEqual(level["params"], [{"name": "level", "choices": ["a1", "a2", "b1", "b2", "c1"]}])
        # no admin page is ever offered
        self.assertFalse(any(r["path"].startswith("/admin") for r in cat))


class TestLinkRules(unittest.TestCase):
    def test_external_needs_valid_url(self):
        ad = AdvertisementCreate(title="T", target_url="https://vizu-deutsch.com/x")
        self.assertEqual(ad.link_type, "EXTERNAL")
        self.assertIsNone(ad.internal_route)
        for bad in (None, "javascript:alert(1)", "data:text/html,x", "//evil.com", "/kurse"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                AdvertisementCreate(title="T", target_url=bad)

    def test_internal_needs_registered_page(self):
        ad = AdvertisementCreate(title="T", link_type="INTERNAL", internal_route="kurse_level", internal_params={"level": "a1"},
                                 target_url="https://ignored.example.com")
        self.assertIsNone(ad.target_url)
        self.assertEqual(ad.internal_params, {"level": "a1"})
        for route, params in (("admin", {}), (None, None), ("kurse_level", {"level": "x"})):
            with self.subTest(route=route), self.assertRaises(ValidationError):
                AdvertisementCreate(title="T", link_type="INTERNAL", internal_route=route, internal_params=params)
        with self.assertRaises(ValidationError):
            AdvertisementCreate(title="T", link_type="OTHER", target_url="https://a.com")

    def test_switching_type_keeps_fields_consistent(self):
        link = {"link_type": "EXTERNAL", "target_url": "https://a.com", "internal_route": "kurse", "internal_params": {}}
        apply_link_rules(link)
        self.assertIsNone(link["internal_route"])
        link = {"link_type": "INTERNAL", "target_url": "https://a.com", "internal_route": "kurse", "internal_params": {}}
        apply_link_rules(link)
        self.assertIsNone(link["target_url"])
        with self.assertRaises(ValueError):
            apply_link_rules({"link_type": "EXTERNAL", "target_url": None})

    def test_service_update_merges_link(self):
        ad = SimpleNamespace(id="x", link_type="EXTERNAL", target_url="https://a.com", internal_route=None, internal_params=None,
                             starts_at=None, ends_at=None, title="T", cta_text="C")
        from app.schemas.advertisement import AdvertisementUpdate

        with patch.object(advertisement_service, "get", return_value=ad), \
             patch.object(advertisement_service, "get_admin", return_value={"ok": True}):
            db = SimpleNamespace(commit=lambda: None)
            advertisement_service.update(db, "x", AdvertisementUpdate(link_type="INTERNAL", internal_route="kurse"))
            self.assertEqual((ad.link_type, ad.target_url, ad.internal_route, ad.internal_params), ("INTERNAL", None, "kurse", {}))
            with self.assertRaises(ValueError):  # back to external without a URL
                advertisement_service.update(db, "x", AdvertisementUpdate(link_type="EXTERNAL"))
            advertisement_service.update(db, "x", AdvertisementUpdate(title="New"))  # link untouched
            self.assertEqual((ad.title, ad.link_type), ("New", "INTERNAL"))

    def test_public_payload(self):
        ad = SimpleNamespace(id="i", title="T", description=None, image_url=None, cta_text="C", link_type="INTERNAL",
                             internal_route="removed_page", internal_params={}, target_url=None)
        pub = advertisement_service.to_public(ad)
        self.assertEqual((pub["link_type"], pub["internal_path"]), ("INTERNAL", "/dashboard"))
        self.assertNotIn("target_url", pub)
        ad.link_type, ad.target_url = "EXTERNAL", "https://a.com"
        self.assertIsNone(advertisement_service.to_public(ad)["internal_path"])


if __name__ == "__main__":
    unittest.main()
