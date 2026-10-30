"""The book-faithful A2 edition (app/scripts/vizu_deutsch_a2_buch): only book
material, no invented limits, counts as in docs/a2-book-content-audit.md,
and optional word limits for writing tasks."""

import json
import re
import unittest
from types import SimpleNamespace

from app.scripts import vizu_deutsch_a2_buch as book
from app.scripts.vizu_deutsch_a2_buch import build
from app.services.content_import.schema import ContentDocument, SchreibenItem
from app.services.lesson_skills.ai_evaluation import word_range_text

# lesson -> (Lesen questions, Hören tasks, Hören questions, Schreiben, Sprechen, words) — audit, 2026-10-27;
# lesson 4 Hören ("Familie Mannsberg") replaced by Text 1-3 outside the import on 2026-10-30
EXPECTED = {
    1: (18, 1, 12, 1, 1, 60), 2: (12, 1, 12, 3, 1, 40), 3: (12, 1, 8, 3, 1, 60), 4: (17, 0, 0, 3, 1, 50),
    5: (16, 1, 10, 4, 1, 0), 6: (19, 1, 12, 3, 1, 0), 7: (12, 1, 15, 3, 1, 0), 8: (10, 1, 12, 4, 1, 0),
    9: (8, 1, 1, 4, 1, 6), 10: (16, 4, 20, 3, 2, 0), 11: (15, 4, 20, 3, 3, 0), 12: (14, 4, 20, 3, 3, 0),
    13: (16, 4, 20, 3, 3, 0),
}
VIZU_MARKERS = re.compile(r"Nemischa|Zuordnung \d|Der, die oder das|Was bedeutet das|Abschlusstest|Unterrichtsblatt|dars varag")


class TestEdition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {n: build.document(n) for n in build.LESSONS}

    def test_documents_validate(self):
        for n, doc in self.docs.items():
            with self.subTest(lesson=n):
                ContentDocument.model_validate(doc)

    def test_counts_match_the_audit(self):
        for n, doc in self.docs.items():
            items = doc["items"]
            got = (
                sum(len(i["questions"]) for i in items if i["skill"] == "lesen"),
                sum(1 for i in items if i["skill"] == "hoeren"),
                sum(len(i["questions"]) for i in items if i["skill"] == "hoeren"),
                sum(1 for i in items if i["skill"] == "schreiben"),
                sum(1 for i in items if i["skill"] == "sprechen"),
                sum(len(i["words"]) for i in items if i["skill"] == "wortschatz"),
            )
            with self.subTest(lesson=n):
                self.assertEqual(got, EXPECTED[n])

    def test_only_book_material(self):
        for n, doc in self.docs.items():
            for item in doc["items"]:
                with self.subTest(item=item["content_id"]):
                    self.assertTrue(item["content_id"].startswith("vizu-a2buch-"))
                    self.assertEqual(item["source"], "book")
                    self.assertNotEqual(item["skill"], "yakuniy")
                    self.assertNotIn(item.get("competency"), ("EINFUEHRUNG", "ZUSAMMENFASSUNG"))
                    self.assertTrue(all(e.get("source") != "vizu" for e in item.get("exercises", [])))
                    self.assertIsNone(VIZU_MARKERS.search(json.dumps(item, ensure_ascii=False)))

    def test_no_invented_limits(self):
        for doc in self.docs.values():
            for item in doc["items"]:
                old_id = item["content_id"].replace("vizu-a2buch-", "vizu-a2-")
                if item["skill"] == "schreiben":
                    self.assertNotIn("time_limit", item)
                    self.assertNotIn("support_phrases", item)
                    self.assertEqual((item["min_words"], item["max_words"]), book.BOOK_WORDS.get(old_id, (None, None)), old_id)
                if item["skill"] in ("sprechen", "frage"):
                    self.assertEqual((item["min_duration"], item["max_duration"]),
                                     book.BOOK_DURATIONS.get(old_id, (0, book.RECORDER_CAP_SECONDS)), old_id)

    def test_book_word_counts(self):
        items = {i["content_id"]: i for d in self.docs.values() for i in d["items"]}
        self.assertEqual((items["vizu-a2buch-l02-schreiben-01"]["min_words"], items["vizu-a2buch-l02-schreiben-01"]["max_words"]), (30, 40))
        self.assertEqual(items["vizu-a2buch-l12-schreiben-01"]["max_words"], 30)
        self.assertIsNone(items["vizu-a2buch-l01-schreiben-01"]["min_words"])

    def test_every_auto_graded_book_question_has_a_key(self):
        for doc in self.docs.values():
            for item in doc["items"]:
                if item["skill"] != "lesen":
                    continue
                for q in item["questions"]:
                    with self.subTest(item=item["content_id"], q=q["question"][:40]):
                        self.assertTrue(q.get("correct_answer") or q.get("pairs"))

    def test_keyless_hoeren_stays_pending(self):
        items = {i["content_id"]: i for d in self.docs.values() for i in d["items"] if i["skill"] == "hoeren"}
        for cid in ("vizu-a2buch-l06-hoeren-01", "vizu-a2buch-l07-hoeren-01", "vizu-a2buch-l13-hoeren-01"):
            self.assertTrue(items[cid].get("key_pending"), cid)

    def test_lesson_4_familie_mannsberg_is_not_imported_again(self):
        # replaced by Text 1 / 2 / 3 (services/a2_audio/lesson4_hoeren.py, docs/a2-lesson-4-hoeren-update.md)
        lesson4 = [i for i in self.docs[4]["items"] if i["skill"] == "hoeren"]
        self.assertEqual(lesson4, [])
        self.assertNotIn("Mannsberg", json.dumps(self.docs[4], ensure_ascii=False))

    def test_fixes(self):
        items = {i["content_id"]: i for d in self.docs.values() for i in d["items"]}
        self.assertIn("Architekt ist.", items["vizu-a2buch-l01-hoeren-01"]["transcript"])
        self.assertIn("Kompletter Beispieltext", items["vizu-a2buch-l01-schreiben-01"]["prompt"])
        self.assertNotIn("Erdgeschoss:", items["vizu-a2buch-l10-lesen-02"]["passages"][0]["text"])
        self.assertIn("A) Wort in der richtigen Form", items["vizu-a2buch-l08-schreiben-02"]["prompt"])
        self.assertNotIn("gegenüber (", items["vizu-a2buch-l07-grammatik-01"]["rules"][0]["html"])
        self.assertEqual(sum(1 for q in items["vizu-a2buch-l11-sprechen-01"]["questions"] if q.startswith("Kandidat 2")), 4)
        self.assertIn("vizu-a2buch-l05-schreiben-05", items)
        martin = [q["question"] for q in items["vizu-a2buch-l04-lesen-01"]["questions"] if q.get("passage") == 3]
        self.assertEqual([m.split(".")[0] for m in martin], ["19", "20", "21", "23", "24"])

    def test_editorial_corrections_keep_the_book_wording(self):
        items = {i["content_id"]: i for d in self.docs.values() for i in d["items"]}
        for cid in ("vizu-a2buch-l03-grammatik-01", "vizu-a2buch-l08-grammatik-01", "vizu-a2buch-l10-grammatik-01",
                    "vizu-a2buch-l12-grammatik-01", "vizu-a2buch-l13-grammatik-01", "vizu-a2buch-l09-schreiben-02",
                    "vizu-a2buch-l13-schreiben-01", "vizu-a2buch-l13-schreiben-03"):
            with self.subTest(item=cid):
                self.assertTrue(items[cid]["metadata"]["book_original"])
                shown = json.dumps(items[cid].get("rules") or items[cid].get("prompt"), ensure_ascii=False)
                self.assertRegex(shown, r"Redaktioneller Hinweis|Hinweis: (Die Tabelle|Im Buch steht)")
        self.assertIn("Verbstamm + e/Ø", items["vizu-a2buch-l03-grammatik-01"]["rules"][0]["html"])
        self.assertIn("Der Konjunktiv II", items["vizu-a2buch-l13-grammatik-01"]["rules"][0]["html"])

    def test_lesson_14(self):
        self.assertEqual(book.items(14), [])
        self.assertEqual(book.lesson_title(14), "Wiederholung")
        self.assertEqual(book.lesson_title(1), "Beruf, Karriere und Ziele")

    def test_track_labels_point_at_existing_items(self):
        ids = {i["content_id"] for d in self.docs.values() for i in d["items"]}
        self.assertTrue(set(book.AUDIO_LABELS) <= ids)


class TestOptionalWordLimits(unittest.TestCase):
    def test_import_schema_accepts_no_limit(self):
        item = SchreibenItem(content_id="x-test-1", level="A2", module=1, lesson=1, skill="schreiben", title="T", prompt="P")
        self.assertIsNone(item.min_words)
        self.assertIsNone(item.max_words)

    def test_ai_prompt_never_invents_a_range(self):
        self.assertEqual(word_range_text(None, None), "So'zlar soni topshiriqda belgilanmagan.")
        self.assertEqual(word_range_text(80, None), "So'zlar soni: kamida 80.")
        self.assertEqual(word_range_text(20, 30), "So'zlar soni: 20-30.")

    def test_submit_without_limits_is_not_rejected(self):
        from unittest.mock import MagicMock, patch

        from app.services.student_writing import service as svc

        writing = SimpleNamespace(id="w", lesson_id="l", is_published=True, min_words=None, max_words=None)
        s = svc.StudentWritingService.__new__(svc.StudentWritingService)
        s.db = MagicMock()
        s.db.get.side_effect = lambda model, _id: writing if model is svc.Writing else object()
        s.repository = MagicMock()
        s.repository.get_by_user_and_writing.side_effect = RuntimeError("past the word check")
        with patch.object(svc, "ensure_lesson_open"):
            with self.assertRaises(RuntimeError):  # reached the next step: no 400 for the word count
                s.submit("u", "w", "ein Wort", submit_final=True)

    def test_submit_with_book_minimum_is_enforced(self):
        from unittest.mock import MagicMock, patch

        from fastapi import HTTPException

        from app.services.student_writing import service as svc

        writing = SimpleNamespace(id="w", lesson_id="l", is_published=True, min_words=80, max_words=None)
        s = svc.StudentWritingService.__new__(svc.StudentWritingService)
        s.db = MagicMock()
        s.db.get.side_effect = lambda model, _id: writing if model is svc.Writing else object()
        with patch.object(svc, "ensure_lesson_open"), self.assertRaises(HTTPException) as ctx:
            s.submit("u", "w", "zu kurz", submit_final=True)
        self.assertEqual(ctx.exception.status_code, 400)


class TestRenameVideos(unittest.TestCase):
    """Only the "[Archiv] IMG_…" title changes; the old title is archived first."""

    def setUp(self):
        import tempfile
        from pathlib import Path

        from app.models.video import Video

        self.tmp = tempfile.TemporaryDirectory()
        self.archive = Path(self.tmp.name) / "a2buch_competency_texts.jsonl"
        self.video = Video(id=__import__("uuid").uuid4(), lesson_id="l", title="[Archiv] IMG_0321", storage_key="videos/l/a.mp4",
                           duration_seconds=60, order_index=0, is_preview=False, is_published=True)
        self.addCleanup(self.tmp.cleanup)

    def _run(self, dry_run: bool):
        from unittest.mock import MagicMock

        from app.scripts import import_vizu_deutsch_a2_buch as cli

        db = MagicMock()
        db.scalars.return_value = [self.video]
        return db, cli.rename_videos(db, SimpleNamespace(id="l"), "Reisen", self.archive, dry_run)

    def test_dry_run_writes_nothing(self):
        db, out = self._run(dry_run=True)
        self.assertEqual(out, ["„[Archiv] IMG_0321“ -> „Video: Reisen“"])
        self.assertEqual(self.video.title, "[Archiv] IMG_0321")
        db.commit.assert_not_called()
        self.assertFalse(self.archive.with_name("a2buch_video_titles.jsonl").exists())

    def test_rename_keeps_everything_else_and_archives_the_old_title(self):
        db, _ = self._run(dry_run=False)
        self.assertEqual((self.video.title, self.video.storage_key, self.video.is_published), ("Video: Reisen", "videos/l/a.mp4", True))
        saved = json.loads(self.archive.with_name("a2buch_video_titles.jsonl").read_text(encoding="utf-8"))
        self.assertEqual((saved["id"], saved["title"]), (str(self.video.id), "[Archiv] IMG_0321"))
        _, again = self._run(dry_run=False)  # re-run: the title no longer starts with [Archiv]
        self.assertEqual(again, [])


if __name__ == "__main__":
    unittest.main()
