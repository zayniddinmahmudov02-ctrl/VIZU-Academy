"""Lesson skills: server-side grading, question validation, AI result
validation (server-computed score, no invented errors, pronunciation only
with audio analysis), the overall lesson result rule, and the seeded A1
Modul 1 Lesen content."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.scripts import seed_a1_modul1_lesen as seed
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import ai_evaluation as ai
from app.services.lesson_skills import results
from app.services.lesson_skills import skill_tests as tests


def _q(qid, options, correct, points=1):
    return SimpleNamespace(
        id=qid,
        points=points,
        explanation=f"why {qid}",
        options=[SimpleNamespace(id=f"{qid}-{i}", is_correct=(i == correct), order_index=i, created_at=0, option_text=o) for i, o in enumerate(options)],
    )


class TestGrading(unittest.TestCase):
    def setUp(self):
        self.questions = [_q(f"q{i}", ["A", "B", "C"], i % 3) for i in range(15)]

    def test_all_correct_is_100(self):
        answers = {f"q{i}": f"q{i}-{i % 3}" for i in range(15)}
        result = tests.grade(self.questions, answers)
        self.assertEqual((result["correct_count"], result["score"]), (15, 100))

    def test_equal_weight_proportional_score(self):
        answers = {f"q{i}": f"q{i}-{i % 3}" for i in range(10)}  # 10 of 15
        self.assertEqual(tests.grade(self.questions, answers)["score"], 67)

    def test_foreign_or_missing_option_counts_as_unanswered(self):
        answers = {"q0": "q1-0", "q1": "", "unknown": "x"}
        result = tests.grade(self.questions, answers)
        self.assertEqual(result["correct_count"], 0)
        self.assertIsNone(result["results"][0]["selected_option_id"])

    def test_points_weighting(self):
        qs = [_q("a", ["x", "y"], 0, points=3), _q("b", ["x", "y"], 0, points=1)]
        self.assertEqual(tests.grade(qs, {"a": "a-0"})["score"], 75)

    def test_public_question_never_contains_the_key(self):
        public = tests.public_question(SimpleNamespace(id="q", question="?", question_type="MULTIPLE_CHOICE", points=1,
                                                       options=self.questions[0].options))
        self.assertNotIn("is_correct", str(public))
        self.assertEqual(len(public["options"]), 3)


class TestQuestionValidation(unittest.TestCase):
    def _item(self, **kw):
        base = {"question": "Wie alt ist Tom?", "question_type": "MULTIPLE_CHOICE", "points": 1,
                "options": [{"text": "8", "is_correct": False}, {"text": "10", "is_correct": True}]}
        base.update(kw)
        return base

    def test_valid(self):
        self.assertEqual(len(skill_admin.validate_questions([self._item()])), 1)

    def test_rejections(self):
        for bad in (
            self._item(question=""),
            self._item(options=[{"text": "a", "is_correct": True}]),
            self._item(options=[{"text": "a", "is_correct": True}, {"text": "b", "is_correct": True}]),
            self._item(options=[{"text": "a", "is_correct": False}, {"text": "b", "is_correct": False}]),
            self._item(question_type="TRUE_FALSE", options=[{"text": "R", "is_correct": True}, {"text": "F"}, {"text": "?"}]),
            self._item(question_type="ESSAY"),
            self._item(points=0),
        ):
            with self.subTest(bad=bad), self.assertRaises(HTTPException):
                skill_admin.validate_questions([bad])

    def test_audio_detection_by_content(self):
        self.assertEqual(skill_admin._detect_audio(b"ID3\x04" + b"\x00" * 12), "mp3")
        self.assertEqual(skill_admin._detect_audio(b"RIFF\x00\x00\x00\x00WAVEfmt "), "wav")
        self.assertEqual(skill_admin._detect_audio(b"\x00\x00\x00\x20ftypM4A "), "m4a")
        self.assertIsNone(skill_admin._detect_audio(b"<html><script>"))


class TestAiValidation(unittest.TestCase):
    TEXT = "Ich heisse Tom. Ich bin 10 Jahre alt. Ich wohne in Taschkent."

    def _raw(self, **scores):
        crit = [{"key": c["key"], "score": scores.get(c["key"], c["max"] - 5), "comment": "ok"} for c in ai.DEFAULT_WRITING_RUBRIC]
        return {"criteria": crit, "strengths": ["gut"], "errors": [{"original": "Ich heisse", "correction": "Ich heiße", "explanation": "ß"}],
                "recommendation": "weiter so", "summary": "Gut.", "total": 999}

    def test_score_is_computed_by_the_server(self):
        result = ai.validate_result(self._raw(), ai.DEFAULT_WRITING_RUBRIC, self.TEXT, {c["key"] for c in ai.DEFAULT_WRITING_RUBRIC})
        self.assertEqual((result["points"], result["max_points"], result["score"]), (75, 100, 75))
        self.assertNotIn("total", result)

    def test_scores_are_clamped_and_missing_criterion_fails(self):
        result = ai.validate_result(self._raw(task=500, grammar=-3), ai.DEFAULT_WRITING_RUBRIC, self.TEXT, {c["key"] for c in ai.DEFAULT_WRITING_RUBRIC})
        crit = {c["key"]: c["score"] for c in result["criteria"]}
        self.assertEqual((crit["task"], crit["grammar"]), (25, 0))
        raw = self._raw()
        raw["criteria"] = raw["criteria"][1:]
        with self.assertRaises(ai.InvalidAIResult):
            ai.validate_result(raw, ai.DEFAULT_WRITING_RUBRIC, self.TEXT, {c["key"] for c in ai.DEFAULT_WRITING_RUBRIC})
        raw = self._raw()
        raw["criteria"][0]["score"] = "viel"
        with self.assertRaises(ai.InvalidAIResult):
            ai.validate_result(raw, ai.DEFAULT_WRITING_RUBRIC, self.TEXT, {c["key"] for c in ai.DEFAULT_WRITING_RUBRIC})

    def test_invented_errors_are_dropped(self):
        raw = self._raw()
        raw["errors"].append({"original": "Ich bin Lehrer", "correction": "x", "explanation": "erfunden"})
        result = ai.validate_result(raw, ai.DEFAULT_WRITING_RUBRIC, self.TEXT, {c["key"] for c in ai.DEFAULT_WRITING_RUBRIC})
        self.assertEqual([e["original"] for e in result["errors"]], ["Ich heisse"])

    def test_pronunciation_not_assessed_without_audio_analysis(self):
        rubric = ai.DEFAULT_SPEAKING_RUBRIC
        assessed = {c["key"] for c in rubric} - {"pronunciation"}
        raw = {"criteria": [{"key": c["key"], "score": c["max"], "comment": ""} for c in rubric if c["key"] in assessed]}
        result = ai.validate_result(raw, rubric, "Hallo", assessed)
        pron = next(c for c in result["criteria"] if c["key"] == "pronunciation")
        self.assertEqual((pron["status"], pron["score"]), ("not_assessed", None))
        self.assertEqual((result["max_points"], result["score"]), (80, 100))  # 80/80 of the assessed criteria
        self.assertTrue(result["limitations"])

    def test_rubric_validation(self):
        self.assertEqual(len(ai.validate_rubric(ai.DEFAULT_WRITING_RUBRIC)), 5)
        for bad in ([], [{"key": "a", "name": "A", "max": 0}], [{"key": "a b", "name": "A", "max": 5}],
                    [{"key": "a", "name": "A", "max": 5}, {"key": "a", "name": "B", "max": 5}]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ai.validate_rubric(bad)

    def test_default_rubrics_match_the_spec(self):
        self.assertEqual([(c["key"], c["max"]) for c in ai.DEFAULT_WRITING_RUBRIC],
                         [("task", 25), ("grammar", 25), ("vocabulary", 20), ("coherence", 15), ("spelling", 15)])
        self.assertEqual([(c["key"], c["max"]) for c in ai.DEFAULT_SPEAKING_RUBRIC],
                         [("content", 25), ("grammar", 20), ("vocabulary", 20), ("pronunciation", 20), ("fluency", 15)])
        self.assertEqual(sum(c["max"] for c in ai.DEFAULT_WRITING_RUBRIC), 100)
        self.assertEqual(sum(c["max"] for c in ai.DEFAULT_SPEAKING_RUBRIC), 100)

    def test_gemini_http_error_never_carries_the_url(self):
        import urllib.error

        def boom(*a, **k):
            raise urllib.error.HTTPError("https://x/?key=SECRET", 429, "Too Many Requests", {}, None)

        with patch.object(ai, "_require_api_key", return_value="SECRET"), patch.object(ai.urllib.request, "urlopen", side_effect=boom):
            with self.assertRaises(ai.AIServiceError) as ctx:
                ai.call_gemini_json("prompt")
        self.assertNotIn("SECRET", str(ctx.exception))
        self.assertIn("429", str(ctx.exception))


class TestOverall(unittest.TestCase):
    def _s(self, status, score, available=True):
        return {"available": available, "status": status, "score": score}

    def test_final_only_when_all_graded(self):
        skills = {"lesen": self._s("completed", 80), "hoeren": self._s("completed", 60),
                  "schreiben": self._s("completed", 70), "sprechen": self._s("completed", 90)}
        out = results.overall(skills)
        self.assertEqual((out["status"], out["score"]), ("final", 75))
        self.assertIn("/ 4", out["method"])

    def test_interim_never_counts_missing_as_zero(self):
        skills = {"lesen": self._s("completed", 80), "hoeren": self._s("not_started", None),
                  "schreiben": self._s("pending_evaluation", None), "sprechen": self._s("completed", 60)}
        out = results.overall(skills)
        self.assertEqual((out["status"], out["score"], out["graded_skills"], out["required_skills"]), ("interim", 70, 2, 4))
        self.assertIn("interim", out["method"])

    def test_unavailable_skills_are_not_required(self):
        skills = {"lesen": self._s("completed", 90), "hoeren": self._s("not_available", None, False),
                  "schreiben": self._s("not_available", None, False), "sprechen": self._s("not_available", None, False)}
        self.assertEqual(results.overall(skills)["status"], "final")


class TestSeedContent(unittest.TestCase):
    def test_three_texts_fifteen_questions_one_key_each(self):
        self.assertEqual([t["title"] for t in seed.TEXTS], ["Text 1: Tom", "Text 2: Anna", "Text 3: Tom und Anna"])
        questions = [q for t in seed.TEXTS for q in t["questions"]]
        self.assertEqual(len(questions), 15)
        self.assertTrue(all(len(t["questions"]) == 5 for t in seed.TEXTS))
        for qtype, question, options, correct, _ in questions:
            self.assertIn(qtype, ("MULTIPLE_CHOICE", "TRUE_FALSE"))
            self.assertTrue(0 <= correct < len(options))
            if qtype == "TRUE_FALSE":
                self.assertEqual(options, ["Richtig", "Falsch"])

    def test_book_samples_are_included_with_their_keys(self):
        flat = {(q[1], q[2][q[3]]) for t in seed.TEXTS for q in t["questions"]}
        for sample in (("Wie alt ist Tom?", "10 Jahre"), ("Wo wohnt Tom?", "In Taschkent"), ("Anna ist 9 Jahre alt.", "Richtig"),
                       ("Was mag Anna?", "Malen und Musik"), ("Tom und Anna kommen aus Deutschland.", "Falsch")):
            self.assertIn(sample, flat)

    def test_every_multiple_choice_key_is_stated_in_its_text(self):
        for t in seed.TEXTS:
            for qtype, _, options, correct, _ in t["questions"]:
                if qtype == "MULTIPLE_CHOICE":
                    key = options[correct].replace("In ", "").replace("Aus ", "").split(" und ")[0].split(",")[0].replace(" Jahre", "")
                    self.assertIn(key, t["content"], (options[correct], t["title"]))

    def test_texts_match_the_book(self):
        self.assertIn("Ich heiße Tom und ich bin 10 Jahre alt.", seed.TEXTS[0]["content"])
        self.assertIn("Ich mag Malen und Musik.", seed.TEXTS[1]["content"])
        self.assertIn("Wir mögen Fußball, Malen und Musik.", seed.TEXTS[2]["content"])


if __name__ == "__main__":
    unittest.main()
