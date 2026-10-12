"""LMS A1-C1: config-based question types (Zuordnung / Lückentext /
Kurzantwort), level rubrics, the configurable overall result and the
Claude/JSON import format (pure parts — the database flow is verified
against a real Postgres separately)."""

import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from app.services.content_import import guide
from app.services.content_import import service as importer
from app.services.content_import.schema import ContentDocument, Question, json_schema
from app.services.lesson_skills import levels
from app.services.lesson_skills import question_types as qt
from app.services.lesson_skills import results
from app.services.lesson_skills import skill_tests as tests

MATCHING = {"items": [{"id": "1", "text": "Anna"}, {"id": "2", "text": "Tom"}],
            "targets": [{"id": "A", "text": "Musik"}, {"id": "B", "text": "Fußball"}, {"id": "C", "text": "Tennis"}],
            "pairs": {"1": "A", "2": "B"}}
GAP = {"text": "Ich [[1]] Anna und ich [[2]] aus Usbekistan.",
       "gaps": {"1": ["heiße"], "2": {"accepted": ["komme"], "options": ["komme", "kommst", "kommt"]}}}


def _cq(qtype, config, qid="q", points=1):
    return SimpleNamespace(id=qid, question_type=qtype, config=qt.validate_config(qtype, config), points=points, explanation=None, options=[])


class TestQuestionConfig(unittest.TestCase):
    def test_matching_valid_and_errors(self):
        self.assertEqual(qt.validate_config("MATCHING", MATCHING)["pairs"], {"1": "A", "2": "B"})
        with self.assertRaises(qt.QuestionConfigError):
            qt.validate_config("MATCHING", {**MATCHING, "pairs": {"1": "A", "2": "Z"}})
        with self.assertRaises(qt.QuestionConfigError):
            qt.validate_config("MATCHING", {**MATCHING, "targets": MATCHING["targets"][:1]})

    def test_gap_fill_valid_and_errors(self):
        cfg = qt.validate_config("GAP_FILL", GAP)
        self.assertEqual(cfg["gaps"]["1"], {"accepted": ["heiße"]})
        with self.assertRaises(qt.QuestionConfigError):
            qt.validate_config("GAP_FILL", {"text": "kein Platzhalter", "gaps": {}})
        with self.assertRaises(qt.QuestionConfigError):  # answer not among options
            qt.validate_config("GAP_FILL", {"text": "[[1]]", "gaps": {"1": {"accepted": ["x"], "options": ["a", "b"]}}})
        with self.assertRaises(qt.QuestionConfigError):  # key for unknown gap
            qt.validate_config("GAP_FILL", {"text": "[[1]]", "gaps": {"1": ["a"], "9": ["b"]}})

    def test_short_answer_requires_key(self):
        with self.assertRaises(qt.QuestionConfigError):
            qt.validate_config("SHORT_ANSWER", {"accepted": []})
        self.assertEqual(qt.validate_config("SHORT_ANSWER", {"accepted": "drei"})["accepted"], ["drei"])

    def test_public_config_hides_key(self):
        q = _cq("MATCHING", MATCHING)
        pub = qt.public_config(q)
        self.assertNotIn("pairs", pub)
        self.assertEqual(len(pub["targets"]), 3)
        g = qt.public_config(_cq("GAP_FILL", GAP))
        self.assertNotIn("accepted", str(g))
        self.assertEqual([x["id"] for x in g["gaps"]], ["1", "2"])
        self.assertEqual(qt.public_config(_cq("SHORT_ANSWER", {"accepted": ["drei"]})), {"max_length": 100})


class TestConfigGrading(unittest.TestCase):
    def test_partial_credit_and_normalisation(self):
        questions = [_cq("MATCHING", MATCHING, "m", 2), _cq("GAP_FILL", GAP, "g"), _cq("SHORT_ANSWER", {"accepted": ["Gleis 3", "drei"]}, "s")]
        answers = tests.clean_answers(questions, {"m": {"1": "A", "2": "C"}, "g": {"1": " Heiße. ", "2": "kommt"}, "s": "DREI!"})
        out = tests.grade(questions, answers)
        self.assertEqual(out["points"], 1.0 + 0.5 + 1.0)
        self.assertEqual(out["correct_count"], 1)
        self.assertEqual(out["results"][0]["details"], {"1": True, "2": False})

    def test_malformed_answers_are_unanswered(self):
        questions = [_cq("MATCHING", MATCHING, "m"), _cq("SHORT_ANSWER", {"accepted": ["x"]}, "s")]
        self.assertEqual(tests.clean_answers(questions, {"m": "A", "s": ["x"], "zzz": "1"}), {})

    def test_empty_gap_never_matches(self):
        q = _cq("GAP_FILL", {"text": "[[1]]", "gaps": {"1": ["a"]}})
        self.assertEqual(qt.grade_config_question(q, {"1": "  "})["fraction"], 0.0)


class TestLevels(unittest.TestCase):
    def test_every_level_rubric_totals_100(self):
        for lv in levels.LEVELS:
            self.assertEqual(sum(c["max"] for c in levels.writing_rubric(lv)), 100, lv)
            self.assertEqual(sum(c["max"] for c in levels.speaking_rubric(lv)), 100, lv)

    def test_unknown_level_falls_back_to_a1(self):
        self.assertEqual(levels.normalise_level("x9"), "A1")
        self.assertEqual(levels.normalise_level(" b2 "), "B2")


class TestResultConfig(unittest.TestCase):
    @staticmethod
    def _skills(**scores):
        return {k: {"available": True, "status": "completed" if scores.get(k) is not None else "not_started", "score": scores.get(k)}
                for k in results.SKILL_KEYS}

    def test_default_is_equal_average_and_interim_until_all_graded(self):
        o = results.overall(self._skills(lesen=80, hoeren=60))
        self.assertEqual((o["status"], o["score"]), ("interim", 70))
        o = results.overall(self._skills(lesen=80, hoeren=60, schreiben=100, sprechen=40))
        self.assertEqual((o["status"], o["score"]), ("final", 70))

    def test_weights_and_required(self):
        cfg = results.validate_result_config({"weights": {"lesen": 3, "hoeren": 1, "schreiben": 0, "sprechen": 0}, "required": ["lesen", "hoeren"]})
        o = results.overall(self._skills(lesen=100, hoeren=0), cfg)
        self.assertEqual((o["status"], o["score"]), ("final", 75))

    def test_invalid_config_rejected(self):
        for bad in ({"weights": {}, "required": []}, {"weights": {"lesen": 0}, "required": ["lesen"]}, {"weights": {"lesen": 101}, "required": ["lesen"]}, "x"):
            with self.assertRaises(ValueError):
                results.validate_result_config(bad)


class TestImportFormat(unittest.TestCase):
    def test_examples_of_every_level_match_the_schema(self):
        for lv in levels.LEVELS:
            doc = ContentDocument.model_validate(guide.example(lv))
            self.assertEqual({i.skill for i in doc.items}, {"lesen", "hoeren", "schreiben", "sprechen"})
            self.assertTrue(all(i.level == lv for i in doc.items))

    def test_unknown_fields_and_levels_rejected(self):
        doc = guide.example("A1")
        doc["items"][0]["secret"] = 1
        with self.assertRaises(ValidationError):
            ContentDocument.model_validate(doc)
        doc = guide.example("A1")
        doc["items"][0]["level"] = "C2"
        with self.assertRaises(ValidationError):
            ContentDocument.model_validate(doc)

    def test_json_schema_published(self):
        s = json_schema()
        self.assertEqual(s["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("LesenItem", s["$defs"])

    def test_correct_answer_forms(self):
        mc = {"type": "multiple_choice", "question": "?", "options": ["a", "b", "c"]}
        for answer in ("B", "b", 2, "2", "b "):
            payload = importer.question_payload(Question(**mc, correct_answer=answer))
            self.assertEqual([o["is_correct"] for o in payload["options"]], [False, True, False], answer)
        for answer in ("D", 0, "x"):
            with self.assertRaises(ValueError):
                importer.question_payload(Question(**mc, correct_answer=answer))
        tf = importer.question_payload(Question(type="true_false", question="?", correct_answer="falsch"))
        self.assertEqual([(o["text"], o["is_correct"]) for o in tf["options"]], [("Richtig", False), ("Falsch", True)])
        with self.assertRaises(ValueError):
            importer.question_payload(Question(type="true_false", question="?"))

    def test_matching_letters_converted_to_config(self):
        p = importer.question_payload(Question(type="matching", question="?", items=["x", "y"], targets=["p", "q", "r"], pairs={"1": "c", "2": "A"}))
        self.assertEqual(p["config"]["pairs"], {"1": "C", "2": "A"})
        self.assertEqual(qt.validate_config("MATCHING", p["config"])["pairs"], {"1": "C", "2": "A"})

    def test_passage_text_is_escaped(self):
        out = importer.text_to_html("<script>x</script>\n\nZwei")
        self.assertNotIn("<script>", out)
        self.assertEqual(out.count("<p>"), 2)


if __name__ == "__main__":
    unittest.main()
