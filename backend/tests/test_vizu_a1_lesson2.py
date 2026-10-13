"""VIZU-DEUTSCH A1, Modul 2 (lesson 2): book content, answer keys, no
repeated questions, Hören keys left to the admin where only the audio
decides."""

import re
import unittest

from app.scripts.vizu_deutsch_a1 import build, modul_02 as m2
from app.services.content_import import service as importer
from app.services.content_import.schema import ContentDocument, Question
from tests.test_vizu_a1_lesson1 import LETTERS, _Q, _questions


def _words() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for w in m2.WORDS:
        label = f"{w['article']} {w['word']}" if w.get("article") else w["word"]
        out.setdefault(label, set()).add(w["translation"])
    return out


class ModulTwoDocumentTests(unittest.TestCase):
    def setUp(self):
        self.doc = build.document(2)
        self.items = {i["content_id"]: i for i in self.doc["items"]}

    def test_document_matches_the_import_schema(self):
        ContentDocument.model_validate(self.doc)
        skills = {i["skill"] for i in self.doc["items"]}
        self.assertEqual(skills, {"kompetenz", "frage", "wortschatz", "grammatik", "lesen", "hoeren", "sprechen",
                                  "schreiben_uebungen", "schreiben", "uebungen", "yakuniy"})
        self.assertEqual({i["competency"] for i in self.doc["items"] if i["skill"] == "kompetenz"}, {"EINFUEHRUNG", "ZUSAMMENFASSUNG"})

    def test_every_question_is_keyed_except_the_hoeren_audio_gaps(self):
        for item in self.doc["items"]:
            pending = item["skill"] == "hoeren"
            qs = [Question.model_validate(q) for q in _questions(item)]
            errors: list[str] = []
            payloads = importer._validated_questions(qs, errors, allow_pending=pending)
            self.assertEqual(errors, [], item["content_id"])
            if not pending:
                from app.services.lesson_skills import exercises

                self.assertTrue(all(exercises.has_key(_Q(p)) for p in payloads), item["content_id"])

    def test_hoeren_keys_only_what_the_text_decides(self):
        h = self.items["vizu-a1-l02-hoeren-01"]
        self.assertTrue(h["key_pending"])
        self.assertEqual(h["audio_file"], "A1-2.mp3")
        gaps = {gid: g for q in h["questions"] for gid, g in q["gaps"].items()}
        self.assertEqual(sorted(gaps, key=int), [str(i) for i in range(1, 26)])
        keyed = {gid for gid, g in gaps.items() if g}
        self.assertEqual(keyed, {"3", "4", "9", "10", "14", "17", "18", "22", "23", "24", "25"})
        self.assertEqual(gaps["2"], [], "'Ich ___ in Berlin' is not decided by the text / word list")
        for gid in keyed:
            self.assertIn(gaps[gid][0], m2.HOEREN_WORDLIST)

    def test_lesen_is_the_books_four_texts_and_15_questions(self):
        lesen = self.items["vizu-a1-l02-lesen-01"]
        self.assertEqual([p["title"] for p in lesen["passages"]], ["Herr Müller", "Frau Müller", "Tom", "Anna"])
        self.assertEqual(len(lesen["questions"]), 15)
        self.assertTrue(all("O'zbekcha tarjima:" in p["text"] for p in lesen["passages"]))
        texts = {n: p["text"].split("\n\nO'zbekcha")[0] for n, p in enumerate(lesen["passages"], start=1)}
        for q in lesen["questions"]:
            answer = q["options"][LETTERS.index(q["correct_answer"])]
            quote = q["explanation"].strip("„“")
            self.assertIn(quote.replace("…", "").strip(" .“")[:20], texts[q["passage"]], q["question"])
            if answer not in ("Ja",):
                for w in re.findall(r"\w+", answer):
                    if len(w) > 4 and w not in ("Fahrrad", "fahren", "spielen", "hören", "lesen", "Musik", "Märchen"):
                        self.assertIn(w.lower()[:3], texts[q["passage"]].lower(), (q["question"], answer))

    def test_book_test_question_9_accepts_both_correct_forms(self):
        q9 = m2.TEST[8]
        self.assertEqual(q9["type"], "gap_fill")
        self.assertEqual(sorted(q9["gaps"]["1"]["accepted"]), ["spielen", "spielt"])

    def test_book_written_exercise_answers(self):
        expected = ["arbeite", "wartest", "redet", "lernen", "tanzt", None, "atme", "stauchst", "regnet", "heißen", "fährst", "schläft",
                    "lese", "siehst", "fangen an", "kommt mit", "tanzt", "heißt", "mache", None]
        for q, want in zip(m2.WRITTEN, expected):
            accepted = q["gaps"]["1"]
            if want is None:
                self.assertEqual(sorted(accepted), ["öffnen", "öffnet"])
            else:
                self.assertEqual(accepted[0], want, q["text"])
        self.assertNotIn("stauchest", str(m2.WRITTEN))

    def test_wortschatz_follows_the_book_word_list(self):
        words = _words()
        self.assertEqual(len(m2.WORDS), 38)
        for ex in m2.WORTSCHATZ_SETS:
            for q in ex["questions"]:
                if q["type"] == "matching":
                    for item_no, letter in q["pairs"].items():
                        self.assertIn(q["targets"][LETTERS.index(letter)], words[q["items"][int(item_no) - 1]], ex["title"])
                if q["type"] == "gap_fill" and ex["title"] == "Der oder die?":
                    noun = q["text"].replace("[[1]] ", "").split(" (")[0]
                    self.assertIn(f"{q['gaps']['1']['accepted'][0]} {noun}", words)
        self.assertFalse(self.items["vizu-a1-l02-wortschatz-01"]["auto_practice"])

    def test_no_question_appears_twice_in_the_lesson(self):
        seen: dict[str, str] = {}
        for item in self.doc["items"]:
            for q in _questions(item):
                key = re.sub(r"\s+", " ", (q["question"] + " " + q.get("text", "")).lower()).strip()
                if q["type"] == "matching":
                    key += " " + "|".join(q["items"])
                self.assertNotIn(key, seen, f"{item['content_id']} repeats {seen.get(key)}: {q['question']}")
                seen[key] = item["content_id"]

    def test_only_the_cover_image(self):
        self.assertEqual([(c, f) for f, c, _ in m2.IMAGES], [("EINFUEHRUNG", "01_cover.jpg")])
        self.assertEqual(sorted(p.name for p in (build.OUT_DIR / "images" / "modul_02").iterdir()), ["01_cover.jpg"])
        grammar = self.items["vizu-a1-l02-grammatik-01"]
        self.assertFalse(any("<img" in r["html"] for r in grammar["rules"]))
        self.assertTrue(all("<table>" in r["html"] for r in grammar["rules"]))


if __name__ == "__main__":
    unittest.main()
