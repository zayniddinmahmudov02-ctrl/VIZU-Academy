"""VIZU-Multilevel: up to 3 attempts per student, independent results,
"Bestes Ergebnis" and certificates for every final result incl. "unter A1".
(Ownership/IDOR and certificate-number uniqueness are additionally covered
against a real database by the HTTP test.)"""

import base64
import re
import unittest
import zlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.vizu_multilevel_attempt import MAX_ATTEMPTS, STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMultilevelAttempt
from app.services.admin import vizu_multilevel_admin_service as admin
from app.services.vizu_multilevel import certificate_pdf as pdf
from app.services.vizu_multilevel import certificate_service as cert
from app.services.vizu_multilevel import lesen_service, service
from app.services.vizu_multilevel.service import SectionFlowError

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


def _attempt(n, status=STATUS_COMPLETED, score=None, level=None, discarded=None, completed_offset=None):
    return VizuMultilevelAttempt(
        user_id="u1",
        attempt_number=n,
        status=status,
        started_at=T0 + timedelta(days=n),
        completed_at=(T0 + timedelta(days=n, hours=2 + (completed_offset or 0))) if status == STATUS_COMPLETED else None,
        result_score=score,
        overall_level=level,
        discarded_reason=discarded,
    )


def _db_with(attempts):
    db = MagicMock()
    db.scalars.return_value = list(attempts)
    return db


def _competencies(score: float) -> list[dict]:
    """All four competencies at `score`/100, levelled by the exam's own table."""
    level = lesen_service.level_for_score(score, 100)
    return [
        {"skill": s, "status": service.R_GRADED, "raw_score": score, "max_score": 100.0, "percentage": float(score), "level": level}
        for s in ("lesen", "hoeren", "schreiben", "sprechen")
    ]


def _pdf_text(raw: bytes) -> str:
    chunks = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\n?endstream", raw, re.S):
        body = match.group(1).strip()
        if body.endswith(b"~>"):
            body = base64.a85decode(body[:-2])
        try:
            body = zlib.decompress(body)
        except zlib.error:
            pass
        chunks.append(body.decode("latin-1"))
    strings = []
    for m in re.finditer(r"\(((?:\\.|[^\\)])*)\)\s*Tj", "\n".join(chunks)):
        s = re.sub(r"\\([0-7]{3})", lambda o: chr(int(o.group(1), 8)), m.group(1))
        strings.append(s.replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\"))
    return "\n".join(strings)


# ============================================================
# Attempt limit
# ============================================================


class TestAttemptLimit(unittest.TestCase):
    def test_max_is_three(self):
        self.assertEqual(MAX_ATTEMPTS, 3)

    def test_first_second_third_attempt_allowed_and_numbered(self):
        history = []
        for expected in (1, 2, 3):
            with self.subTest(attempt=expected):
                db = _db_with(history)
                attempt = service.create_attempt(db, user_id="u1")
                self.assertEqual(attempt.attempt_number, expected)
                self.assertEqual(attempt.status, STATUS_IN_PROGRESS)
                db.add.assert_called_once_with(attempt)
                attempt.status = STATUS_COMPLETED  # student finishes it
                history.append(attempt)

    def test_fourth_attempt_rejected(self):
        db = _db_with([_attempt(n) for n in (1, 2, 3)])
        with self.assertRaises(SectionFlowError) as ctx:
            service.create_attempt(db, user_id="u1")
        self.assertEqual(ctx.exception.code, "MAX_ATTEMPTS_REACHED")
        db.add.assert_not_called()
        db.rollback.assert_called_once()  # releases the advisory lock

    def test_fourth_attempt_is_a_403(self):
        from app.api.vizu_multilevel.router import _flow_error

        self.assertEqual(_flow_error(SectionFlowError("MAX_ATTEMPTS_REACHED")).status_code, 403)
        self.assertEqual(_flow_error(SectionFlowError("ATTEMPT_ALREADY_EXISTS")).status_code, 409)

    def test_incomplete_attempt_must_be_finished_first_and_counts(self):
        db = _db_with([_attempt(1), _attempt(2, status=STATUS_IN_PROGRESS)])
        with self.assertRaises(SectionFlowError) as ctx:
            service.create_attempt(db, user_id="u1")
        self.assertEqual(ctx.exception.code, "ATTEMPT_ALREADY_EXISTS")
        db.add.assert_not_called()

    def test_existing_students_keep_their_remaining_attempts(self):
        for used, remaining in ((0, 3), (1, 2), (2, 1), (3, 0)):
            with self.subTest(used=used):
                attempts = [_attempt(n, score=50, level="A2") for n in range(1, used + 1)]
                with patch.object(service, "list_attempts", return_value=attempts):
                    summary = service.my_results(MagicMock(), "u1")
                self.assertEqual(summary["attempts_used"], used)
                self.assertEqual(summary["attempts_remaining"], remaining)
                self.assertEqual(summary["can_start"], remaining > 0)

    def test_old_attempts_remain_unchanged_when_a_new_one_starts(self):
        old = [_attempt(1, score=61, level="B1"), _attempt(2, score=78, level="B2")]
        snapshot = [(a.attempt_number, a.status, a.result_score, a.overall_level, a.completed_at) for a in old]
        db = _db_with(old)
        new = service.create_attempt(db, user_id="u1")
        self.assertEqual(new.attempt_number, 3)
        self.assertEqual(snapshot, [(a.attempt_number, a.status, a.result_score, a.overall_level, a.completed_at) for a in old])
        db.add.assert_called_once_with(new)  # only the new row is written


# ============================================================
# Best result
# ============================================================


class TestBestResult(unittest.TestCase):
    def test_best_of_61_78_72_is_78_not_the_last(self):
        attempts = [_attempt(1, score=61, level="B1"), _attempt(2, score=78, level="B2"), _attempt(3, score=72, level="B1")]
        best = service.best_attempt(attempts)
        self.assertEqual((best.attempt_number, best.result_score, service.result_level(best)), (2, 78, "B2"))

    def test_only_one_completed_attempt(self):
        best = service.best_attempt([_attempt(1, score=44, level="A2")])
        self.assertEqual(best.result_score, 44)

    def test_equal_scores_pick_the_latest_completed(self):
        best = service.best_attempt([_attempt(1, score=70, level="B1"), _attempt(2, score=70, level="B1"), _attempt(3, score=50, level="A2")])
        self.assertEqual(best.attempt_number, 2)

    def test_incomplete_or_pending_attempts_are_ignored(self):
        attempts = [_attempt(1, score=40, level="A2"), _attempt(2, status=STATUS_IN_PROGRESS), _attempt(3, score=None)]
        self.assertEqual(service.best_attempt(attempts).attempt_number, 1)
        self.assertIsNone(service.best_attempt([_attempt(1, status=STATUS_IN_PROGRESS)]))

    def test_below_a1_result_counts_with_its_level(self):
        below = _attempt(1, score=12, discarded="BELOW_A1")
        self.assertEqual(service.result_level(below), "BELOW_A1")
        self.assertEqual(service.best_attempt([below]).result_score, 12)

    def test_admin_row_shows_best_and_last_attempt(self):
        user = SimpleNamespace(id="u1", first_name="Zayniddin", last_name="Makhmudov", username="z", email="z@example.com")
        attempts = [_attempt(1, score=61, level="B1"), _attempt(2, score=84, level="B2"), _attempt(3, score=72, level="B1")]
        row = admin._student_row(user, attempts)
        self.assertEqual((row["attempts_used"], row["attempts_remaining"]), (3, 0))
        self.assertEqual((row["best_score"], row["best_level"], row["best_attempt_number"]), (84, "B2", 2))
        self.assertEqual((row["last_attempt_score"], row["last_attempt_level"], row["last_attempt_number"]), (72, "B1", 3))
        self.assertEqual(row["student_name"], "Zayniddin Makhmudov")

    def test_admin_sorting_default_best_score_desc_and_others(self):
        rows = [
            {"student_name": "A", "best_score": 61, "best_level": "B1", "attempts_used": 3, "last_attempt_date": T0},
            {"student_name": "B", "best_score": None, "best_level": None, "attempts_used": 1, "last_attempt_date": T0 + timedelta(days=3)},
            {"student_name": "C", "best_score": 84, "best_level": "B2", "attempts_used": 2, "last_attempt_date": T0 + timedelta(days=1)},
            {"student_name": "D", "best_score": 12, "best_level": "BELOW_A1", "attempts_used": 1, "last_attempt_date": T0 + timedelta(days=2)},
        ]
        names = lambda sort, desc=True: [r["student_name"] for r in admin._sorted_rows(rows, sort, desc)]  # noqa: E731
        self.assertEqual(names("best_score"), ["C", "A", "D", "B"])  # no result always last
        self.assertEqual(names("best_score", False), ["D", "A", "C", "B"])
        self.assertEqual(names("level"), ["C", "A", "D", "B"])
        self.assertEqual(names("attempts"), ["A", "C", "D", "B"])
        self.assertEqual(names("date"), ["B", "D", "C", "A"])

    def test_student_summary_is_built_from_own_attempts_only(self):
        db = MagicMock()
        with patch.object(service, "list_attempts", return_value=[_attempt(1, score=78, level="B2")]) as listing:
            summary = service.my_results(db, "student-1")
        listing.assert_called_once_with(db, "student-1")
        self.assertEqual(summary["best"]["result_score"], 78)


# ============================================================
# Stored Gesamtergebnis = the unchanged result calculation
# ============================================================


class TestResultScore(unittest.TestCase):
    def test_gesamtergebnis_is_the_average_of_graded_percentages(self):
        comps = _competencies(60)
        comps[0]["percentage"] = 70.0
        self.assertEqual(service.gesamtergebnis(comps), 63)  # (70+60+60+60)/4 = 62.5 -> 63 (half up)

    def test_sync_stores_only_final_results(self):
        attempt = _attempt(1)
        final = {"overall": {"status": service.O_FINAL, "level": "B1"}, "competencies": _competencies(61)}
        service.sync_result_score(MagicMock(), attempt, final)
        self.assertEqual(attempt.result_score, 61)

        pending = {"overall": {"status": service.O_PENDING_REVIEW, "level": None},
                   "competencies": [{**_competencies(61)[0], "status": service.R_PENDING_REVIEW}]}
        service.sync_result_score(MagicMock(), attempt, pending)
        self.assertIsNone(attempt.result_score)

        running = _attempt(2, status=STATUS_IN_PROGRESS)
        service.sync_result_score(MagicMock(), running, final)
        self.assertIsNone(running.result_score)


# ============================================================
# Certificates
# ============================================================


class TestCertificates(unittest.TestCase):
    def _certify(self, score: int) -> tuple[str, int, str]:
        comps = _competencies(score)
        result = {"overall": service.overall_result(comps), "competencies": comps}
        attempt = SimpleNamespace(status=STATUS_COMPLETED, completed_at=T0, discarded_reason=None)
        with patch.object(service, "build_result", return_value=result):
            eligible = cert.eligibility(None, attempt)
        level = cert.certificate_level(eligible)
        total, lines = cert.summarize(eligible["competencies"])
        data = cert.CertificateData("Erika Muster", level, total, lines, T0, "VIZU-ML-2026-000123")
        return level, total, _pdf_text(pdf.render_certificate_pdf(data))

    def test_score_bands_give_the_matching_certificate(self):
        for score, level, label in (
            (0, "BELOW_A1", "Niveau unter A1"),
            (19, "BELOW_A1", "Niveau unter A1"),
            (20, "A1", "Niveau A1"),
            (40, "A2", "Niveau A2"),
            (60, "B1", "Niveau B1"),
            (75, "B2", "Niveau B2"),
            (90, "C1", "Niveau C1"),
        ):
            with self.subTest(score=score):
                got_level, total, text = self._certify(score)
                self.assertEqual(got_level, level)
                self.assertEqual(total, score)
                self.assertIn(label, text)
                self.assertIn(f"Gesamtergebnis: {score} / 100 Punkte", text)

    def test_below_a1_certificate_content_and_wording(self):
        _, _, text = self._certify(12)
        for expected in ("ZERTIFIKAT", "VIZU-AKADEMIE", "VIZU-Multilevel-Prüfung", "Erika Muster", "Niveau unter A1",
                         "Gesamtergebnis: 12 / 100 Punkte", "https://vizu-deutsch.com", "Director of VIZU-Academy",
                         "Zayniddinkhuja Makhmudov"):
            self.assertIn(expected, text)
        self.assertNotIn("nicht bestanden", text.lower())
        self.assertNotIn("erfolgreich", text)  # neutral wording below A1
        self.assertEqual(pdf.CERTIFICATE_THEMES["BELOW_A1"].frame, "soft")

    def test_incomplete_attempt_has_no_certificate(self):
        with self.assertRaises(cert.CertificateUnavailable):
            cert.eligibility(None, SimpleNamespace(status=STATUS_IN_PROGRESS, completed_at=None, discarded_reason=None))

    def test_certificate_number_is_stable_on_re_download(self):
        attempt = SimpleNamespace(certificate_number="VIZU-ML-2026-000124", completed_at=T0, id="a1")
        db = MagicMock()
        self.assertEqual(cert.ensure_certificate_number(db, attempt), "VIZU-ML-2026-000124")
        db.scalar.assert_not_called()  # no new sequence value
        db.execute.assert_not_called()

    def test_each_attempt_gets_its_own_number(self):
        db = MagicMock()
        db.scalar.side_effect = [123, 124, 125]
        numbers = []
        for i in range(3):
            attempt = SimpleNamespace(certificate_number=None, completed_at=T0, id=f"a{i}")
            db.refresh.side_effect = lambda a, _n=None: None
            # the guarded UPDATE "wins"; emulate the stored value
            with patch.object(cert, "update") as upd:
                upd.return_value.where.return_value.values.side_effect = lambda certificate_number, _a=attempt: setattr(
                    _a, "certificate_number", certificate_number
                )
                numbers.append(cert.ensure_certificate_number(db, attempt))
        self.assertEqual(numbers, ["VIZU-ML-2026-000123", "VIZU-ML-2026-000124", "VIZU-ML-2026-000125"])

    def test_pdf_filename_for_below_a1(self):
        data = cert.CertificateData("X", "BELOW_A1", 5, (), T0, "VIZU-ML-2026-000001")
        self.assertEqual(cert.pdf_filename(data), "VIZU-Zertifikat-unter-A1-VIZU-ML-2026-000001.pdf")


if __name__ == "__main__":
    unittest.main()
