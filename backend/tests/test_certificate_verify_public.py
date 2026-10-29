"""The public certificate check returned the whole row (user_id, pdf/qr file paths)."""

import importlib
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

cert_router = importlib.import_module("app.api.v1.certificate.router")


class TestPublicVerify(unittest.TestCase):
    def test_only_public_fields_are_returned(self):
        cert = SimpleNamespace(
            id="c1", user_id="secret-user", course_id="course", pdf_url="/opt/x.pdf", qr_code_url="/opt/x.png",
            certificate_number="VIZU-1", verification_code="ABC", provider="VIZU", level="A1", source="LMS",
            lesen_score=20, hoeren_score=20, schreiben_score=20, sprechen_score=20, score=80,
            issued_at=datetime(2026, 1, 1, tzinfo=timezone.utc), is_valid=True,
        )
        with mock.patch.object(cert_router, "CertificateVerificationService") as svc:
            svc.return_value.verify.return_value = cert
            out = cert_router.verify_certificate("ABC", db=None)
        self.assertEqual(set(out), set(cert_router.PUBLIC_VERIFY_FIELDS))
        for leaked in ("user_id", "pdf_url", "qr_code_url", "course_id", "id"):
            self.assertNotIn(leaked, out)
        self.assertEqual(out["score"], 80)

    def test_unknown_code_is_404(self):
        from fastapi import HTTPException

        with mock.patch.object(cert_router, "CertificateVerificationService") as svc:
            svc.return_value.verify.return_value = None
            with self.assertRaises(HTTPException) as ctx:
                cert_router.verify_certificate("nope", db=None)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
