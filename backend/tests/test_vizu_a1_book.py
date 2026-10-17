"""The lesson standard for every rebuilt VIZU-DEUTSCH A1 module: import
schema, answer keys (only audio-decided Hören gaps may stay open), no
question twice in a lesson, cover image only, Grammatik as text, the
competency texts, vocabulary exercises that follow the book's word list."""

import re
import unittest

from app.scripts.vizu_deutsch_a1 import build
from app.services.content_import import service as importer
from app.services.content_import.schema import ContentDocument, Question
from app.services.lesson_skills import exercises as ex_service
from tests.test_vizu_a1_lesson1 import LETTERS, _Q, _questions

STANDARD_MODULES = [n for n in range(1, 15) if hasattr(build.importlib.import_module(f"app.scripts.vizu_deutsch_a1.modul_{n:02d}"), "LESSON_TITLE")]


class BookModuleStandardTests(unittest.TestCase):
    def test_rebuilt_modules_are_listed(self):
        self.assertGreaterEqual(len(STANDARD_MODULES), 3)

    def _each(self):
        for n in STANDARD_MODULES:
            mod = build.importlib.import_module(f"app.scripts.vizu_deutsch_a1.modul_{n:02d}")
            doc = build.document(n)
            yield n, mod, doc, {i["content_id"]: i for i in doc["items"]}

    def test_schema_and_competency_texts(self):
        for n, mod, doc, items in self._each():
            with self.subTest(modul=n):
                ContentDocument.model_validate(doc)
                kinds = {i["competency"] for i in doc["items"] if i["skill"] == "kompetenz"}
                self.assertEqual(kinds, {"EINFUEHRUNG", "ZUSAMMENFASSUNG"})
                skills = {i["skill"] for i in doc["items"]}
                self.assertTrue({"wortschatz", "grammatik", "lesen", "hoeren", "sprechen", "schreiben", "uebungen", "yakuniy"} <= skills, skills)
                self.assertTrue(mod.LESSON_TITLE and mod.LESSON_DESCRIPTION)

    def test_answer_keys(self):
        for n, _, doc, _ in self._each():
            for item in doc["items"]:
                with self.subTest(modul=n, item=item["content_id"]):
                    pending = item["skill"] == "hoeren" and item.get("key_pending", False)
                    qs = [Question.model_validate(q) for q in _questions(item)]
                    errors: list[str] = []
                    payloads = importer._validated_questions(qs, errors, allow_pending=pending)
                    self.assertEqual(errors, [])
                    if not pending:
                        self.assertTrue(all(ex_service.has_key(_Q(p)) for p in payloads))

    def test_no_question_twice_in_a_lesson(self):
        dups: list[str] = []
        for n, _, doc, _ in self._each():
            seen: dict[str, str] = {}
            for item in doc["items"]:
                for q in _questions(item):
                    # the sentence a student sees: a gap text ([[1]] -> ___) or the question
                    sentence = re.sub(r"\[\[\d+\]\]", "___", q["text"]) if q["type"] == "gap_fill" else q["question"]
                    key = re.sub(r"\s+", " ", sentence.lower()).strip()
                    if q["type"] == "matching":
                        key += " " + "|".join(q["items"])
                    if key in seen:
                        dups.append(f"modul {n}: {sentence!r} in {item['content_id']} and {seen[key]}")
                    seen[key] = item["content_id"]
        self.assertEqual(dups, [])

    def test_every_lesen_text_has_at_least_three_questions(self):
        for n, _, _, items in self._each():
            for item in items.values():
                if item["skill"] != "lesen":
                    continue
                per_text = {p: sum(q.get("passage", 1) == p for q in item["questions"]) for p in range(1, len(item["passages"]) + 1)}
                with self.subTest(modul=n, item=item["content_id"]):
                    self.assertTrue(all(c >= 3 for c in per_text.values()), per_text)
                    self.assertEqual(item.get("max_score", sum(q["points"] for q in item["questions"])), sum(q["points"] for q in item["questions"]))

    def test_cover_only_and_grammar_as_text(self):
        for n, mod, _, items in self._each():
            with self.subTest(modul=n):
                self.assertEqual([(c, f) for f, c, _ in mod.IMAGES], [("EINFUEHRUNG", "01_cover.jpg")])
                folder = build.OUT_DIR / "images" / f"modul_{n:02d}"
                self.assertEqual(sorted(p.name for p in folder.iterdir()), ["01_cover.jpg"])
                grammar = [i for i in items.values() if i["skill"] == "grammatik"]
                self.assertTrue(grammar)
                for g in grammar:
                    self.assertFalse(any("<img" in r["html"] for r in g.get("rules", [])))

    def test_wortschatz_follows_the_word_list(self):
        for n, mod, _, items in self._each():
            ws = items[f"vizu-a1-l{n:02d}-wortschatz-01"]
            self.assertFalse(ws.get("auto_practice", True), n)
            labels: dict[str, set[str]] = {}
            for w in ws["words"]:
                labels.setdefault(f"{w['article']} {w['word']}" if w.get("article") else w["word"], set()).add(w["translation"])
            for ex in ws["exercises"]:
                for q in ex["questions"]:
                    if q["type"] == "matching" and q["question"].startswith("Was passt zusammen? ("):
                        for item_no, letter in q["pairs"].items():
                            with self.subTest(modul=n, item=q["items"][int(item_no) - 1]):
                                self.assertIn(q["targets"][LETTERS.index(letter)], labels[q["items"][int(item_no) - 1]])


if __name__ == "__main__":
    unittest.main()
