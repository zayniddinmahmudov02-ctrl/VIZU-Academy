"""Unified certificate view (services/certificate/registry): filtering, labels
and the PDF path guard — pure logic, no database."""

import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services.certificate import registry


def item(**kw):
    base = {"id": "c:1", "source": "COURSE", "level": "A1", "status": "valid", "certificate_number": "VIZU-1",
            "issued_at": datetime(2026, 10, 1, tzinfo=timezone.utc), "course": {"title": "A1 Kurs"},
            "user": {"name": "Ali Valiyev", "email": "ali@example.com", "username": "ali"}}
    base.update(kw)
    return base


class TestFilter(unittest.TestCase):
    items = [item(), item(id="ml:2", source="VIZU_MULTILEVEL", level="B1", status="available", certificate_number=None,
                          issued_at=datetime(2026, 10, 15, tzinfo=timezone.utc), course=None,
                          user={"name": "Zarina", "email": "z@example.com", "username": "z"})]

    def ids(self, **f):
        return [i["id"] for i in registry.filter_items(self.items, **f)]

    def test_filters(self):
        self.assertEqual(self.ids(level="B1"), ["ml:2"])
        self.assertEqual(self.ids(source="COURSE"), ["c:1"])
        self.assertEqual(self.ids(status="available"), ["ml:2"])
        self.assertEqual(self.ids(q="zarina"), ["ml:2"])
        self.assertEqual(self.ids(q="VIZU-1"), ["c:1"])
        self.assertEqual(self.ids(date_from=date(2026, 10, 10)), ["ml:2"])
        self.assertEqual(self.ids(date_to=date(2026, 10, 10)), ["c:1"])
        self.assertEqual(self.ids(), ["c:1", "ml:2"])

    def test_level_label(self):
        self.assertEqual(registry.level_label("BELOW_A1"), "unter A1")
        self.assertEqual(registry.level_label("B2"), "B2")


class TestAttemptItem(unittest.TestCase):
    def test_multilevel_item(self):
        a = SimpleNamespace(id="a1", overall_level=None, discarded_reason="BELOW_A1", certificate_number=None,
                            completed_at=datetime(2026, 10, 2), result_score=31, attempt_number=2)
        i = registry._from_attempt(a, None)
        self.assertEqual((i["id"], i["level"], i["status"], i["source"]), ("ml:a1", "BELOW_A1", "available", "VIZU_MULTILEVEL"))
        self.assertEqual(i["issued_at"].tzinfo, timezone.utc)
        a.certificate_number, a.overall_level = "VIZU-ML-2026-000001", "A2"
        self.assertEqual((registry._from_attempt(a, None)["status"], registry._from_attempt(a, None)["level"]), ("issued", "A2"))


class TestPdfGuard(unittest.TestCase):
    def test_only_files_inside_the_certificates_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "uploads" / "certificates"
            root.mkdir(parents=True)
            inside = root / "VIZU-1.pdf"
            inside.write_bytes(b"%PDF")
            outside = Path(tmp) / "secret.pdf"
            outside.write_bytes(b"%PDF")
            with patch.object(registry, "PDF_DIR", root):
                self.assertEqual(registry.course_pdf_path(SimpleNamespace(pdf_url=str(inside))), inside.resolve())
                self.assertIsNone(registry.course_pdf_path(SimpleNamespace(pdf_url=str(outside))))
                self.assertIsNone(registry.course_pdf_path(SimpleNamespace(pdf_url=str(root / ".." / ".." / "secret.pdf"))))
                self.assertIsNone(registry.course_pdf_path(SimpleNamespace(pdf_url=None)))


if __name__ == "__main__":
    unittest.main()
