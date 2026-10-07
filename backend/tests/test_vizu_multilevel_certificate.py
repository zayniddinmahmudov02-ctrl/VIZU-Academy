"""VIZU-Multilevel PDF certificate: eligibility, data rules, and the PDF
itself for all five level themes (content read back from the PDF streams)."""

import base64
import re
import unittest
import zlib
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.services.vizu_multilevel import certificate_pdf as pdf
from app.services.vizu_multilevel import certificate_service as cert
from app.services.vizu_multilevel import service

LEVELS = ["A1", "A2", "B1", "B2", "C1"]


def _pdf_text(raw: bytes) -> str:
    """All text-show strings of a reportlab PDF (WinAnsi), decompressed."""
    chunks = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\n?endstream", raw, re.S):
        body = match.group(1).strip()
        if body.endswith(b"~>"):  # reportlab: /ASCII85Decode then /FlateDecode
            body = base64.a85decode(body[:-2])
        try:
            body = zlib.decompress(body)
        except zlib.error:
            pass
        chunks.append(body.decode("latin-1"))
    content = "\n".join(chunks)
    strings = []
    for m in re.finditer(r"\(((?:\\.|[^\\)])*)\)\s*Tj", content):
        s = m.group(1)
        s = re.sub(r"\\([0-7]{3})", lambda o: chr(int(o.group(1), 8)), s)
        s = s.replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\")
        strings.append(s)
    return "\n".join(strings)


def _data(level: str, name="Björn Schäfer-Größmann", total=84) -> cert.CertificateData:
    return cert.CertificateData(
        student_name=name,
        level=level,
        total_score=total,
        competencies=(
            cert.CompetencyLine("Lesen", 18.0),
            cert.CompetencyLine("Hören", 21.0),
            cert.CompetencyLine("Schreiben", 22.5),
            cert.CompetencyLine("Sprechen", 23.0),
        ),
        completed_at=datetime(2026, 10, 7, 9, 30, tzinfo=timezone.utc),
        certificate_number="VIZU-ML-2026-000123",
    )


class TestPdfAllThemes(unittest.TestCase):
    def test_every_level_renders_a_complete_german_certificate(self):
        for level in LEVELS:
            with self.subTest(level=level):
                raw = pdf.render_certificate_pdf(_data(level))
                self.assertTrue(raw.startswith(b"%PDF-") and raw.rstrip().endswith(b"%%EOF"))
                # A4 landscape: 841.89 x 595.28 pt
                self.assertRegex(raw, rb"/MediaBox \[ 0 0 841\.88\d* 595\.27\d* \]")
                text = _pdf_text(raw)
                for expected in (
                    "ZERTIFIKAT",
                    "VIZU-AKADEMIE",
                    "Hiermit wird bestätigt, dass",
                    "Björn Schäfer-Größmann",
                    "die VIZU-Multilevel-Prüfung erfolgreich abgelegt und das",
                    f"Niveau {level}",
                    "erreicht hat.",
                    "VIZU-Multilevel-Prüfung",
                    "LESEN", "HÖREN", "SCHREIBEN", "SPRECHEN",
                    "18 / 25", "22,5 / 25",
                    "Gesamtergebnis: 84 / 100 Punkte",
                    "Ausgestellt am: 07. Oktober 2026",
                    "Zertifikatsnummer: VIZU-ML-2026-000123",
                    "Director of VIZU-Academy",
                    "Zayniddinkhuja Makhmudov",
                    "https://vizu-deutsch.com",
                ):
                    self.assertIn(expected, text)
                self.assertNotIn("Level ", text)
                # clickable website link
                self.assertIn(b"/URI (https://vizu-deutsch.com)", raw)
                # no QR code / no raster images at all
                self.assertNotIn(b"/Subtype /Image", raw)
                self.assertNotIn(b"/XObject", raw)
                self.assertNotIn("QR", text.upper())

    def test_umlauts_are_real_winansi_characters(self):
        text = _pdf_text(pdf.render_certificate_pdf(_data("B1", name="Ärzte Öl Übung äöüß")))
        self.assertIn("Ärzte Öl Übung äöüß", text)

    def test_five_visually_different_themes(self):
        renders = {level: pdf.render_certificate_pdf(_data(level)) for level in LEVELS}
        self.assertEqual(len({len(r) for r in renders.values()}), 5)
        themes = pdf.CERTIFICATE_THEMES
        self.assertEqual(set(themes), set(LEVELS))
        signature = {(t.frame, t.corners, t.seal, t.guilloche, t.watermark) for t in themes.values()}
        self.assertEqual(len(signature), 5)
        self.assertEqual(themes["C1"].seal, "rosette")
        self.assertTrue(themes["C1"].watermark)
        self.assertEqual(themes["A1"].corners, "none")

    def test_long_names_are_shrunk_to_fit(self):
        name = "Maximiliane Österreicher-Überall von Straßburg und Hohenzollern"
        size = pdf._fit_size(name, pdf.SERIF_BOLD, 560, 31, 16)
        self.assertLess(size, 31)
        self.assertLessEqual(pdf.stringWidth(name, pdf.SERIF_BOLD, size), 560)

    def test_no_qr_library_used(self):
        import inspect

        source = inspect.getsource(pdf) + inspect.getsource(cert)
        self.assertNotIn("import qrcode", source)
        self.assertNotIn("from qrcode", source)


class TestDataRules(unittest.TestCase):
    def test_german_date_from_completion(self):
        self.assertEqual(cert.german_date(datetime(2026, 10, 7, 9, 30, tzinfo=timezone.utc)), "07. Oktober 2026")
        self.assertEqual(cert.german_date(datetime(2026, 3, 1, 22, 0, tzinfo=timezone.utc)), "02. März 2026")  # UTC+5

    def test_points_format(self):
        self.assertEqual(cert.format_points(21.0), "21")
        self.assertEqual(cert.format_points(22.5), "22,5")
        self.assertEqual(cert.format_points(None), "—")

    def test_summary_matches_result_page(self):
        comps = [
            {"skill": "lesen", "status": service.R_GRADED, "percentage": 72.0},
            {"skill": "hoeren", "status": service.R_GRADED, "percentage": 84.0},
            {"skill": "schreiben", "status": service.R_GRADED, "percentage": 90.0},
            {"skill": "sprechen", "status": service.R_GRADED, "percentage": 92.0},
        ]
        total, lines = cert.summarize(comps)
        self.assertEqual(total, 85)  # (72+84+90+92)/4 = 84.5 -> 85 (half up, like Math.round)
        self.assertEqual([l.points for l in lines], [18.0, 21.0, 22.5, 23.0])
        comps[3] = {"skill": "sprechen", "status": service.R_NO_CONTENT, "percentage": None}
        total, lines = cert.summarize(comps)
        self.assertEqual(total, 82)  # average of the graded three
        self.assertIsNone(lines[3].points)

    def test_student_name_fallback(self):
        self.assertEqual(cert.student_name(SimpleNamespace(first_name="Anna", last_name="Schmidt", username="a")), "Anna Schmidt")
        self.assertEqual(cert.student_name(SimpleNamespace(first_name=None, last_name="", username="anna_s")), "anna_s")


def _attempt(status="COMPLETED", completed=True, discarded=None):
    return SimpleNamespace(
        status=status,
        completed_at=datetime(2026, 10, 7, tzinfo=timezone.utc) if completed else None,
        discarded_reason=discarded,
    )


class TestEligibility(unittest.TestCase):
    """The certificate level is the exam's existing FINAL overall level."""

    def _result(self, status, level):
        return {"overall": {"status": status, "level": level}, "competencies": []}

    def test_each_final_level_is_certified(self):
        for level in LEVELS:
            with self.subTest(level=level), patch.object(service, "build_result", return_value=self._result(service.O_FINAL, level)):
                self.assertEqual(cert.eligibility(None, _attempt())["overall"]["level"], level)

    def test_below_a1_has_no_certificate(self):
        with patch.object(service, "build_result", return_value=self._result(service.O_BELOW_A1, None)):
            with self.assertRaises(cert.CertificateUnavailable) as ctx:
                cert.eligibility(None, _attempt())
        self.assertEqual(ctx.exception.reason, cert.BELOW_A1)
        with self.assertRaises(cert.CertificateUnavailable) as ctx:
            cert.eligibility(None, _attempt(discarded="BELOW_A1"))
        self.assertEqual(ctx.exception.reason, cert.BELOW_A1)

    def test_incomplete_attempt_has_no_certificate(self):
        for attempt in (_attempt(status="IN_PROGRESS"), _attempt(completed=False)):
            with self.assertRaises(cert.CertificateUnavailable) as ctx:
                cert.eligibility(None, attempt)
            self.assertEqual(ctx.exception.reason, cert.NOT_COMPLETED)

    def test_missing_or_pending_result_has_no_certificate(self):
        for status, level in ((service.O_PENDING_REVIEW, None), (service.O_IN_PROGRESS, None), (service.O_NO_CONTENT, None), (service.O_FINAL, None)):
            with self.subTest(status=status), patch.object(service, "build_result", return_value=self._result(status, level)):
                with self.assertRaises(cert.CertificateUnavailable):
                    cert.eligibility(None, _attempt())


if __name__ == "__main__":
    unittest.main()
