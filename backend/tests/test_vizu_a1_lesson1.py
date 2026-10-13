"""VIZU-DEUTSCH A1, Modul 1 (lesson 1): the book content, its answer keys
and the pieces it needs (Schreiben practice sets, import format 1.2)."""

import re
import unittest

from app.scripts.vizu_deutsch_a1 import build, modul_01 as m1
from app.services.content_import import service as importer
from app.services.content_import.schema import ContentDocument
from app.services.lesson_skills import exercises, results

LETTERS = "ABCDEFGHIJKL"


def _questions(item: dict) -> list[dict]:
    out = [q for q in item.get("questions") or [] if isinstance(q, dict)]  # Sprechen / Frage: guiding lines, not questions
    for ex in item.get("exercises") or []:
        out.extend(ex["questions"])
    return out


def _words() -> dict[str, set[str]]:
    """German label ('die Schule', 'ich') -> its translations in the book list."""
    out: dict[str, set[str]] = {}
    for w in m1.WORDS:
        label = f"{w['article']} {w['word']}" if w.get("article") else w["word"]
        out.setdefault(label, set()).add(w["translation"])
    return out


class ModulOneDocumentTests(unittest.TestCase):
    def setUp(self):
        self.doc = build.document(1)
        self.items = {i["content_id"]: i for i in self.doc["items"]}

    def test_document_matches_the_import_schema(self):
        ContentDocument.model_validate(self.doc)
        self.assertEqual(self.doc["schema_version"], "1.2")

    def test_every_competency_of_the_lesson_has_content(self):
        skills = {i["skill"] for i in self.doc["items"]}
        self.assertEqual(skills, {"kompetenz", "frage", "wortschatz", "grammatik", "lesen", "hoeren", "sprechen",
                                  "schreiben_uebungen", "schreiben", "uebungen", "yakuniy"})
        kinds = {i["competency"] for i in self.doc["items"] if i["skill"] == "kompetenz"}
        self.assertEqual(kinds, {"EINFUEHRUNG", "ZUSAMMENFASSUNG"})

    def test_every_question_validates_and_has_a_key(self):
        from app.services.content_import.schema import Question

        for item in self.doc["items"]:
            qs = [Question.model_validate(q) for q in _questions(item)]
            errors: list[str] = []
            payloads = importer._validated_questions(qs, errors)
            self.assertEqual(errors, [], item["content_id"])
            self.assertTrue(all(exercises.has_key(_Q(p)) for p in payloads), item["content_id"])

    def test_lesen_has_only_the_three_book_texts_and_hoeren_the_park_text(self):
        lesen = self.items["vizu-a1-l01-lesen-01"]
        self.assertEqual([p["title"] for p in lesen["passages"]], ["Text 1: Tom", "Text 2: Anna", "Text 3: Tom und Anna"])
        self.assertTrue(all(1 <= q["passage"] <= 3 for q in lesen["questions"]))
        self.assertNotIn("Park", " ".join(p["text"] for p in lesen["passages"]))
        hoeren = self.items["vizu-a1-l01-hoeren-01"]
        self.assertTrue(hoeren["transcript"].startswith("Es ist Samstag. Tom und Anna gehen in den Park."))
        self.assertEqual(hoeren["audio_file"], "A1-1.mp3")
        self.assertFalse(hoeren.get("key_pending", False))
        self.assertEqual(hoeren["max_score"], sum(q["points"] for q in hoeren["questions"]))

    def test_lesen_and_hoeren_answers_are_in_the_text(self):
        """Every correct option / gap answer of Lesen and Hören occurs in the
        text it is about (the book text — no invented facts)."""
        lesen = self.items["vizu-a1-l01-lesen-01"]
        texts = {n: p["text"].split("\n\nO'zbekcha")[0] for n, p in enumerate(lesen["passages"], start=1)}
        hoeren_text = self.items["vizu-a1-l01-hoeren-01"]["transcript"].split("\n\nO'zbekcha")[0]

        def answers(q):
            if q["type"] == "multiple_choice":
                return [q["options"][LETTERS.index(q["correct_answer"])]]
            if q["type"] == "gap_fill":
                return [g["accepted"][0] for g in q["gaps"].values()]
            return []

        def key_words(answer: str) -> list[str]:
            return [w for w in re.findall(r"\w+", answer) if len(w) > 3 or w.isdigit()]

        for q in lesen["questions"]:
            for a in answers(q):
                for w in key_words(a):
                    self.assertIn(w.lower(), texts[q["passage"]].lower(), (q["question"], a))
        for q in self.items["vizu-a1-l01-hoeren-01"]["questions"]:
            for a in answers(q):
                for w in key_words(a.replace("einer", "")):
                    if w not in ("Stunde",):
                        self.assertIn(w.lower()[:6], hoeren_text.lower(), (q["question"], a))

    def test_wortschatz_matching_pairs_follow_the_book_word_list(self):
        words = _words()
        for ex in m1.WORTSCHATZ_SETS:
            for q in ex["questions"]:
                if q["type"] != "matching":
                    continue
                for item_no, letter in q["pairs"].items():
                    left = q["items"][int(item_no) - 1]
                    right = q["targets"][LETTERS.index(letter)]
                    self.assertIn(right, words[left], (ex["title"], left, right))

    def test_article_exercise_follows_the_book_word_list(self):
        articles = {w["word"]: w.get("article") for w in m1.WORDS}
        sets = [ex for ex in m1.WORTSCHATZ_SETS if ex["title"] == "Der, die oder das?"]
        self.assertEqual(len(sets), 1)
        for q in sets[0]["questions"]:
            noun = q["text"].replace("[[1]] ", "").split(" (")[0]
            self.assertEqual(q["gaps"]["1"]["accepted"], [articles[noun]], noun)

    def test_alphabet_names_follow_the_book_table(self):
        names = dict(re.findall(r"<td>([A-ZÄÖÜß]) ?[a-zäöü]?</td><td>([^<]+)</td>", m1._ALPHABET))
        for q in m1.ALPHABET_NAMES["questions"]:
            for item_no, letter in q["pairs"].items():
                self.assertEqual(q["targets"][LETTERS.index(letter)], names[q["items"][int(item_no) - 1]])
        self.assertEqual(len(names), 30)  # A-Z, Ä, Ö, Ü, ß

    def test_case_matching_pairs_upper_with_lower(self):
        q1, q2 = m1.ALPHABET_CASE["questions"][:2]
        for q in (q1, q2):
            for item_no, letter in q["pairs"].items():
                self.assertEqual(q["items"][int(item_no) - 1].lower(), q["targets"][LETTERS.index(letter)])

    def test_schreiben_word_bank_answers_come_from_the_bank(self):
        book_sets = [ex for ex in m1.SCHREIBEN_SETS if ex["source"] == "book"]
        self.assertEqual(len(book_sets), 4)
        for ex in book_sets:
            gap = ex["questions"][0]
            accepted = [g["accepted"][0] for g in gap["gaps"].values()]
            self.assertEqual(sorted(accepted), sorted(gap["gaps"]["1"]["options"]), ex["title"])
            self.assertEqual(gap["points"], 6)

    def test_buchstabieren_spells_the_answer(self):
        names = {"A": "A", "Be": "B", "Ce": "C", "E": "E", "Ef": "F", "En": "N", "Em": "M", "Ha": "H", "I": "I", "El": "L",
                 "O": "O", "Te": "T", "U": "U", "Vau": "V", "We": "W", "Es": "S", "Er": "R", "Zett": "Z"}
        spelled = [q for q in m1.UEBUNGEN_SETS[0]["questions"]]
        for q in spelled:
            letters = q["question"].split(":")[0].split(" – ")
            word = q["options"][LETTERS.index(q["correct_answer"])]
            self.assertEqual("".join(names[x] for x in letters), word.upper(), q["question"])

    def test_only_the_cover_image_no_grammar_images(self):
        """Grammatik is text + tables only; the page images of the other
        competencies would only repeat their own text content."""
        self.assertEqual([(c, f) for f, c, _ in m1.IMAGES], [("EINFUEHRUNG", "01_cover.jpg")])
        for filename, _, title in m1.IMAGES:
            self.assertTrue((build.OUT_DIR / "images" / "modul_01" / filename).is_file(), filename)
            self.assertNotIn(title, m1.RETIRED_IMAGE_TITLES)
        self.assertEqual(sorted(p.name for p in (build.OUT_DIR / "images" / "modul_01").iterdir()), ["01_cover.jpg"])
        grammar = self.items["vizu-a1-l01-grammatik-01"]
        self.assertFalse(any("<img" in r["html"] for r in grammar["rules"]))
        self.assertTrue(all("<table>" in r["html"] for r in grammar["rules"]))

    def test_no_question_appears_twice_in_the_lesson(self):
        seen: dict[str, str] = {}
        for item in self.doc["items"]:
            for q in _questions(item):
                key = re.sub(r"\s+", " ", (q["question"] + " " + q.get("text", "")).lower()).strip()
                if q["type"] == "matching":
                    key += " " + "|".join(q["items"])
                self.assertNotIn(key, seen, f"{item['content_id']} repeats {seen.get(key)}: {q['question']}")
                seen[key] = item["content_id"]
        self.assertFalse(self.items["vizu-a1-l01-wortschatz-01"]["auto_practice"])


class _Q:
    """has_key() works on ORM questions; adapt an import payload."""

    def __init__(self, payload: dict):
        self.question_type = payload["question_type"]
        self.config = payload.get("config")
        self.options = [type("O", (), {"is_correct": o["is_correct"]})() for o in payload.get("options") or []]


class SchreibenPracticeTests(unittest.TestCase):
    def test_schreiben_is_an_exercise_skill(self):
        self.assertEqual(exercises.skill_from_slug("schreiben"), "SCHREIBEN")
        self.assertIn("SCHREIBEN", exercises.EXERCISE_SKILLS)

    def _part(self, status, score=None, **kw):
        return {"available": True, "status": status, "score": score, "attempts": kw.get("attempts", 1), "tasks": [{"id": status}],
                "can_retry": kw.get("can_retry", False), "submitted_at": kw.get("submitted_at")}

    def test_merge_needs_both_parts_for_completion(self):
        writing = self._part(results.PENDING_EVALUATION)
        practice = self._part(results.COMPLETED, 90)
        merged = results._merge_parts(writing, practice)
        self.assertEqual(merged["status"], results.PENDING_EVALUATION)
        self.assertEqual(merged["score"], 90)
        self.assertTrue(merged["interim"])
        self.assertEqual(len(merged["tasks"]), 2)

    def test_merge_score_is_the_mean_of_both_parts(self):
        merged = results._merge_parts(self._part(results.COMPLETED, 70), self._part(results.COMPLETED, 91))
        self.assertEqual(merged["status"], results.COMPLETED)
        self.assertEqual(merged["score"], 81)  # 80.5 rounded half up
        self.assertFalse(merged["interim"])

    def test_merge_with_one_part_returns_that_part(self):
        missing = {"available": False, "status": results.NOT_AVAILABLE, "score": None}
        part = self._part(results.IN_PROGRESS)
        self.assertIs(results._merge_parts(part, missing), part)
        self.assertIs(results._merge_parts(missing, part), part)

    def test_merge_not_started(self):
        merged = results._merge_parts(self._part(results.NOT_STARTED, attempts=0), self._part(results.NOT_STARTED, attempts=0))
        self.assertEqual(merged["status"], results.NOT_STARTED)


if __name__ == "__main__":
    unittest.main()
