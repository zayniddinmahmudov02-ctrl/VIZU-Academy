"""Broadcast notification rules + support validation (pure parts; DB paths
are covered by the API integration check)."""

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import HTTPException

from app.services import support
from app.services.notification import admin, feed

BASE = {"title_de": "Hallo", "title_uz": "Salom", "message_de": "Text", "message_uz": "Matn", "type": "INFO", "audience_type": "ALL"}


def actor(role):
    return SimpleNamespace(role=role, id="a")


class TestAudienceRoles(unittest.TestCase):
    def test_roles(self):
        self.assertEqual(admin.allowed_audiences(actor("SUPER_ADMIN")), ["ALL", "LEVEL", "LANGUAGE", "USER"])
        self.assertEqual(admin.allowed_audiences(actor("SUPPORT")), ["USER"])
        self.assertEqual(admin.allowed_audiences(actor("TEACHER")), [])
        self.assertEqual(admin.allowed_audiences(actor("STUDENT")), [])
        with self.assertRaises(HTTPException):
            admin.require_notification_admin(actor("STUDENT"))

    def test_support_role_cannot_broadcast(self):
        with self.assertRaises(PermissionError):
            admin.validate(None, dict(BASE), actor("SUPPORT"))


class TestValidation(unittest.TestCase):
    def ok(self, **patch):
        return admin.validate(None, {**BASE, **patch}, actor("ADMIN"))

    def test_valid(self):
        self.assertEqual(self.ok()["audience_value"], None)
        self.assertEqual(self.ok(audience_type="LEVEL", audience_value="A1")["audience_value"], "A1")
        self.assertEqual(self.ok(audience_type="LANGUAGE", audience_value="uz")["audience_value"], "uz")
        self.assertEqual(self.ok(link_type="EXTERNAL", external_url="https://vizu-deutsch.com/x")["external_url"], "https://vizu-deutsch.com/x")
        self.assertEqual(self.ok(link_type="INTERNAL", internal_route="kurse_level", internal_params={"level": "a1"})["internal_params"], {"level": "a1"})

    def test_invalid(self):
        for patch in ({"title_de": " "}, {"message_uz": ""}, {"title_de": "x" * 200}, {"type": "SPAM"}, {"audience_type": "EVERYONE"},
                      {"audience_type": "LEVEL", "audience_value": "Z9"}, {"audience_type": "LANGUAGE", "audience_value": "en"},
                      {"link_type": "EXTERNAL", "external_url": "javascript:alert(1)"}, {"link_type": "EXTERNAL", "external_url": "ftp://a.com"},
                      {"link_type": "INTERNAL", "internal_route": "admin"}, {"link_type": "WHATEVER"}, {"is_important": "yes"}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.ok(**patch)


class TestPublishRules(unittest.TestCase):
    def item(self, **kw):
        return SimpleNamespace(**{"status": "DRAFT", "is_important": False, "audience_type": "ALL", "publish_at": None, **kw})

    def test_mass_or_important_needs_confirmation(self):
        with self.assertRaises(HTTPException):
            admin.publish(self.item(), None, confirm=False)
        with self.assertRaises(HTTPException):
            admin.publish(self.item(audience_type="USER", is_important=True), None, confirm=False)
        single = self.item(audience_type="USER")
        admin.publish(single, None, confirm=False)
        self.assertEqual(single.status, "PUBLISHED")

    def test_schedule_and_archive(self):
        b = self.item()
        future = datetime.now(timezone.utc) + timedelta(days=1)
        admin.publish(b, future, confirm=True)
        self.assertEqual((b.status, b.publish_at), ("PUBLISHED", future))
        self.assertTrue(admin.editable(b))  # still scheduled
        b.publish_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        self.assertFalse(admin.editable(b))  # visible to students now
        admin.archive(b)
        with self.assertRaises(HTTPException):
            admin.publish(b, None, confirm=True)


class TestFeedHelpers(unittest.TestCase):
    def test_parse_id(self):
        self.assertEqual(feed._parse_id("b:00000000-0000-0000-0000-000000000001")[0], "b")
        for bad in ("x:1", "b:not-a-uuid", "", "p"):
            self.assertIsNone(feed._parse_id(bad))

    def test_personal_link_only_same_site_paths(self):
        self.assertEqual(feed._personal_link(SimpleNamespace(link_path="/support/1")), {"type": "INTERNAL", "path": "/support/1"})
        for bad in ("//evil.com", "https://evil.com", "javascript:alert(1)", None):
            self.assertIsNone(feed._personal_link(SimpleNamespace(link_path=bad)))


class TestSupportValidation(unittest.TestCase):
    def test_text_limits(self):
        self.assertEqual(support._clean("  Hallo  ", "subject", 3, 160), "Hallo")
        with self.assertRaises(HTTPException) as ctx:
            support._clean("ab", "subject", 3, 160)
        self.assertEqual(ctx.exception.detail, "SUBJECT_TOO_SHORT")
        with self.assertRaises(HTTPException) as ctx:
            support._clean("x" * 5001, "message", 10, 5000)
        self.assertEqual(ctx.exception.detail, "MESSAGE_TOO_LONG")

    def test_request_id(self):
        self.assertIsNone(support._request_id("  "))
        self.assertEqual(len(support._request_id("x" * 100)), 64)

    def test_roles(self):
        self.assertIn("SUPPORT", support.SUPPORT_ROLES)
        self.assertNotIn("TEACHER", support.SUPPORT_ROLES)
        with self.assertRaises(HTTPException):
            support.require_support_staff(SimpleNamespace(role="CONTENT_MANAGER"))


if __name__ == "__main__":
    unittest.main()
