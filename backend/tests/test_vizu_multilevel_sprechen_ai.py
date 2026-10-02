"""VIZU-Multilevel Sprechen — content bank, ladder selection, level table,
score validator, verbatim-error check, JSON repair and the STT service
abstraction (no network; AI calls are stubbed)."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.speech import speech_to_text_service as stt
from app.services.vizu_multilevel import sprechen_content as content
from app.services.vizu_multilevel import sprechen_evaluation_service as ev
from app.services.vizu_multilevel import sprechen_service as svc


class TestContentBank(unittest.TestCase):
    def test_25_variants_5_per_aufgabe(self):
        self.assertEqual(len(content.CONTENT), 25)
        for order in range(1, 6):
            self.assertEqual(sorted(level for o, level in content.CONTENT if o == order), ["A1", "A2", "B1", "B2", "C1"])

    def test_spec_texts_and_durations(self):
        self.assertIn("Stellen Sie sich kurz vor", content.CONTENT[(1, "A1")][0])
        self.assertIn("künstliche Intelligenz", content.CONTENT[(3, "C1")][0])
        self.assertEqual(content.DURATION_BY_LEVEL, {"A1": (30, 60), "A2": (45, 90), "B1": (60, 120), "B2": (90, 150), "C1": (120, 180)})
        self.assertEqual(content._fields(5, "C1")["max_seconds"], 180)
        self.assertEqual(content._fields(1, "A1")["points"], 20)


def _task(order, level, active=True):
    return SimpleNamespace(order_index=order, level=level, is_active=active, id=f"{order}-{level}", points=20)


class TestLadder(unittest.TestCase):
    def test_level_table(self):
        cases = {0: None, 19: None, 20: "A1", 39: "A1", 40: "A2", 59: "A2", 60: "B1", 74: "B1", 75: "B2", 89: "B2", 90: "C1", 100: "C1"}
        for total, level in cases.items():
            with self.subTest(total=total):
                self.assertEqual(svc.level_for_score(total), level)
        self.assertIsNone(svc.level_for_score(None))

    def test_ladder_picks_target_level_then_nearest(self):
        bank = [_task(o, lv) for o in range(1, 6) for lv in svc.LADDER]
        with patch.object(svc, "list_speaking_tasks", return_value=bank):
            chosen = svc.assigned_tasks(None)
        self.assertEqual([(t.order_index, t.level) for t in chosen], [(1, "A1"), (2, "A2"), (3, "B1"), (4, "B2"), (5, "C1")])
        # Aufgabe 3 @ B1 deactivated -> nearest active variant (A2 before B2 on a tie)
        bank = [t for t in bank if not (t.order_index == 3 and t.level == "B1")]
        with patch.object(svc, "list_speaking_tasks", return_value=bank):
            chosen = svc.assigned_tasks(None)
        self.assertEqual((chosen[2].order_index, chosen[2].level), (3, "A2"))

    def test_effective_score_prefers_teacher(self):
        self.assertEqual(svc.effective_score(SimpleNamespace(teacher_score=15, ai_score=12)), 15)
        self.assertEqual(svc.effective_score(SimpleNamespace(teacher_score=None, ai_score=12)), 12)
        self.assertIsNone(svc.effective_score(None))


class TestScoreValidator(unittest.TestCase):
    def test_criteria_clamped_and_score_is_sum(self):
        out = ev.validate_scores(
            {"criteria": {"task_completion": 9, "vocabulary": 3.4, "grammar": -2, "fluency_coherence": 3, "pronunciation_clarity": 4}, "score": 99}
        )
        self.assertEqual(out["criteria"], {"task_completion": 5, "vocabulary": 3, "grammar": 0, "fluency_coherence": 3, "pronunciation_clarity": 4})
        self.assertEqual(out["score"], 15)
        self.assertEqual(sum(m for _k, _l, m in ev.CRITERIA), 20)

    def test_missing_or_bad_criterion_rejected(self):
        with self.assertRaises(ev.EvaluationValidationError):
            ev.validate_scores({"criteria": {"task_completion": 5}})
        with self.assertRaises(ev.EvaluationValidationError):
            ev.validate_scores({"criteria": {k: "viel" for k, _l, _m in ev.CRITERIA}})
        with self.assertRaises(ev.EvaluationValidationError):
            ev.validate_scores({"criteria": "17"})

    def test_task_result_gate(self):
        good = {"score": 3, "criteria": {k: (3 if k == "grammar" else 0) for k, _l, _m in ev.CRITERIA}, "feedback": "x", "strengths": ["y"]}
        self.assertIs(ev.validate_task_result(good), good)
        with self.assertRaises(ev.EvaluationValidationError):
            ev.validate_task_result({**good, "score": 4})
        with self.assertRaises(ev.EvaluationValidationError):
            ev.validate_task_result({**good, "feedback": ""})

    def test_feedback_required_fields(self):
        with self.assertRaises(ev.EvaluationValidationError):
            ev.validate_feedback({"strengths": [], "feedback": "ok", "next_step": "x"})
        out = ev.validate_feedback({"strengths": ["a", "b", "c", "d"], "feedback": " gut ", "next_step": "weil", "improvements": "x"})
        self.assertEqual(out["strengths"], ["a", "b", "c"])
        self.assertEqual(out["improvements"], [])


class TestNoInventedErrors(unittest.TestCase):
    def test_only_verbatim_errors_survive(self):
        transcript = "Ich bin gestern in Kino gegangen und meine Hobbys ist Lesen."
        raw = {
            "errors": [
                {"original": "in Kino", "correction": "ins Kino", "explanation": "Akkusativ"},
                {"original": "Hobbys ist", "correction": "Hobbys sind", "explanation": "Plural"},
                {"original": "ich habe gegesst", "correction": "ich habe gegessen", "explanation": "erfunden"},
            ]
        }
        out = ev.validate_analysis(raw, transcript)
        self.assertEqual([e["original"] for e in out["errors"]], ["in Kino", "Hobbys ist"])


class TestRepairAndPipelinePieces(unittest.TestCase):
    def test_invalid_json_is_repaired(self):
        replies = iter([{"criteria": {"task_completion": 4}}, {"criteria": {k: 2 for k, _l, _m in ev.CRITERIA}}])
        prompts = []

        def fake(prompt):
            prompts.append(prompt)
            return next(replies)

        with patch.object(ev, "_call_json", side_effect=fake):
            out = ev._call_validated("PROMPT", ev.validate_scores)
        self.assertEqual(out["score"], 10)
        self.assertIn("ungültig", prompts[1])

    def test_gives_up_after_max_repairs(self):
        with patch.object(ev, "_call_json", return_value={"criteria": {}}):
            with self.assertRaises(ev.EvaluationValidationError):
                ev._call_validated("PROMPT", ev.validate_scores)

    def test_silence_scores_zero_without_ai(self):
        task = SimpleNamespace(order_index=1, title="T", instruction="I", level="A1", min_seconds=30, max_seconds=60)
        with patch.object(ev, "_call_json", side_effect=AssertionError("AI must not be called")):
            out = ev.evaluate_answer(task, "[unverständlich]", 12, 0.2, None)
        self.assertEqual(out["score"], 0)
        self.assertIn("keine verständliche Antwort", out["feedback"])

    def test_full_answer_pipeline_with_stubbed_agents(self):
        task = SimpleNamespace(order_index=3, title="Meinung", instruction="Sollten ...?", level="B1", min_seconds=60, max_seconds=120)
        transcript = "Ich finde das gut weil man verdient eigenes Geld."
        replies = iter(
            [
                {"errors": [{"original": "weil man verdient eigenes Geld", "correction": "weil man eigenes Geld verdient", "explanation": "Verb am Ende"}], "profile": {"range": "einfach"}},
                {"criteria": {"task_completion": 3, "vocabulary": 2, "grammar": 2, "fluency_coherence": 2, "pronunciation_clarity": 3}, "score": 50},
                {"strengths": ["klare Meinung"], "improvements": ["Verbposition"], "feedback": "Gut verständlich.", "next_step": "Nutzen Sie „deshalb“."},
            ]
        )
        with patch.object(ev, "_call_json", side_effect=lambda _p: next(replies)):
            out = ev.evaluate_answer(task, transcript, 70, 0.9, {"intelligibility": "hoch"})
        self.assertEqual(out["score"], 12)
        self.assertEqual(out["errors"][0]["correction"], "weil man eigenes Geld verdient")
        self.assertEqual(out["next_step"], "Nutzen Sie „deshalb“.")


class TestSpeechToTextService(unittest.TestCase):
    def test_unknown_provider(self):
        with self.assertRaises(stt.SpeechToTextError):
            stt.SpeechToTextService(provider="nope")

    def test_missing_keys_raise_clear_error(self):
        with patch.object(stt.settings, "OPENAI_API_KEY", ""):
            with self.assertRaises(stt.SpeechToTextError):
                stt.SpeechToTextService(provider="openai")
        with patch.object(stt.settings, "GEMINI_API_KEY", ""):
            with self.assertRaises(stt.SpeechToTextError):
                stt.SpeechToTextService(provider="gemini")

    def test_mime_and_confidence_helpers(self):
        from pathlib import Path

        self.assertEqual(stt._clean_mime("audio/webm;codecs=opus", Path("a.webm")), "audio/webm")
        self.assertEqual(stt._clean_mime("audio/x-wav", Path("a.wav")), "audio/wav")
        self.assertEqual(stt._clamp_confidence(1.7), 1.0)
        self.assertIsNone(stt._clamp_confidence("hoch"))

    def test_empty_file_rejected(self):
        import os
        import tempfile

        with patch.object(stt.settings, "GEMINI_API_KEY", "x"):
            service = stt.SpeechToTextService(provider="gemini")
        handle, path = tempfile.mkstemp(suffix=".webm")
        os.close(handle)
        try:
            with self.assertRaises(stt.SpeechToTextError):
                service.transcribe(path, "audio/webm")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
