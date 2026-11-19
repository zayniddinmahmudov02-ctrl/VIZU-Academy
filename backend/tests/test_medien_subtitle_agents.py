"""The subtitle agents (`services/medien/subtitle_agents.py`) without a database or network: the checker's rules, the repair path (fast model →
strong model → split at a pause → gap), service problems that must stop the job instead of leaving gaps, the proofreader (same count only,
never blocking) — and the answer formats seen live on 2026-11-19 (a bare JSON array from the fast model, a line break inside a string, a used-up
quota)."""

import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from app.core.config import settings
from app.services.medien import subtitle_agents as agents
from app.services.medien import subtitle_ai as ai


def seg(start, end, text, speaker="A"):
    return {"start": start, "end": end, "text": text, "speaker": speaker}


GOOD = [seg(0.5, 2.0, "Hallo Welt."), seg(2.4, 4.0, "Wie geht es dir?", "B"), seg(4.5, 6.0, "Gut, danke.")]
LOOPING = [seg(i, i + 1, "Ja.") for i in range(8)]


class ScriptedProvider:
    """A listener whose answers are scripted per call: a list of segment lists or exceptions; records (seconds, strong)."""

    name, model = "scripted", "scripted-model"

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def transcribe(self, data, mime, language, seconds, strong=False):
        self.calls.append((round(seconds, 1), strong))
        answer = self.answers.pop(0) if self.answers else GOOD
        if isinstance(answer, Exception):
            raise answer
        return ai.Transcript("de", answer, "strong-model" if strong else "fast-model")


def cut(start, length):
    return b"audio", "audio/mp3"


class TestChecker(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(agents.check_segments(GOOD, 10), [])
        self.assertEqual(agents.check_segments([], 10), [])  # silence is fine
        self.assertEqual(agents.check_segments([seg(0, 2, "x" * 400)], 10), ["TOO_DENSE"])
        self.assertEqual(agents.check_segments(LOOPING, 20), ["LOOP"])
        self.assertEqual(agents.check_segments([seg(0, 5, "nein " * 14)], 20), ["LOOP"])
        self.assertEqual(agents.check_segments([seg(0, 30, "Eins."), seg(0, 30, "Zwei."), seg(0, 30, "Drei.")], 100), ["NO_TIMING"])

    def test_split_point_prefers_a_pause_near_the_middle(self):
        self.assertEqual(agents.split_point(0, 180, [(40, 41), (88, 90), (95, 96)]), 89.0)
        self.assertEqual(agents.split_point(0, 180, []), 90.0)
        self.assertEqual(agents.split_point(0, 180, [(10, 12)]), 90.0)  # too far away


class TestRepairPath(unittest.TestCase):
    def test_fast_answer_accepted_and_shifted_onto_the_film_clock(self):
        p = ScriptedProvider(GOOD)
        r = agents.listen_and_check(p, cut, 100, 160, "de", [])
        self.assertEqual(p.calls, [(60.0, False)])
        self.assertEqual(r.steps, ["fast:ok"])
        self.assertEqual(r.segments[0]["start"], 100.5)
        self.assertEqual(r.model, "fast-model")

    def test_a_bad_fast_answer_is_repaired_by_the_strong_model(self):
        p = ScriptedProvider(LOOPING, GOOD)
        r = agents.listen_and_check(p, cut, 0, 60, "de", [])
        self.assertEqual([c[1] for c in p.calls], [False, True])
        self.assertEqual(r.steps, ["fast:LOOP", "strong:ok"])
        self.assertEqual(r.model, "strong-model")

    def test_both_bad_the_piece_is_split_and_a_last_failure_becomes_a_gap(self):
        bad = ai.SubtitleAIError("AI_BAD_ANSWER", "x", retryable=True)
        # 120 s: fast + strong bad → split at the pause (61) → first half fine, second half bad twice → split again? 59 s ≥ 40: yes → both quarters ok
        p = ScriptedProvider(bad, LOOPING, GOOD, LOOPING, LOOPING, GOOD, GOOD)
        r = agents.listen_and_check(p, cut, 0, 120, "de", [(60.5, 61.5)])
        self.assertIn("split", r.steps)
        self.assertEqual(r.gaps, [])
        self.assertEqual([c[0] for c in p.calls], [120.0, 120.0, 61.0, 59.0, 59.0, 29.5, 29.5])
        # a short piece that stays bad: a gap with its time range, nothing invented
        p = ScriptedProvider(LOOPING, LOOPING)
        r = agents.listen_and_check(p, cut, 30, 50, "de", [])
        self.assertEqual((r.segments, r.gaps), ([], [{"start": 30, "end": 50, "reason": "LOOP"}]))

    def test_service_problems_stop_the_job_instead_of_leaving_gaps(self):
        quota = ai.SubtitleAIError("AI_QUOTA", "used up")
        with self.assertRaises(ai.SubtitleAIError):
            agents.listen_and_check(ScriptedProvider(quota), cut, 0, 60, "de", [])
        # the STRONG model used up: a bad fast answer is split instead
        r = agents.listen_and_check(ScriptedProvider(LOOPING, quota, GOOD, GOOD), cut, 0, 60, "de", [])
        self.assertIn("split", r.steps)
        self.assertEqual(len(r.segments), 6)

    def test_silence_gets_a_second_fast_listen_never_the_slow_strong_model(self):
        p = ScriptedProvider([], [])  # credits / music: believed after the second listen
        r = agents.listen_and_check(p, cut, 0, 60, "de", [])
        self.assertEqual((p.calls, r.segments, r.gaps, r.steps), ([(60.0, False), (60.0, False)], [], [], ["fast:EMPTY", "quiet"]))
        p = ScriptedProvider([], GOOD)  # the second listen hears the speech
        r = agents.listen_and_check(p, cut, 0, 60, "de", [])
        self.assertEqual((len(r.segments), r.steps, [c[1] for c in p.calls]), (3, ["fast:EMPTY", "fast2:ok"], [False, False]))
        p = ScriptedProvider([], LOOPING)  # a looping second answer is not taken: still quiet
        self.assertEqual(agents.listen_and_check(p, cut, 0, 60, "de", []).segments, [])
        with self.assertRaises(ai.SubtitleAIError):  # a used-up quota on the second listen stops the job like on the first
            agents.listen_and_check(ScriptedProvider([], ai.SubtitleAIError("AI_QUOTA", "used up")), cut, 0, 60, "de", [])

    def test_a_busy_fast_model_goes_up_to_the_job_not_to_the_strong_model(self):
        for code in ("AI_HTTP_503", "AI_HTTP_500", "AI_HTTP_429", "AI_NETWORK"):
            p = ScriptedProvider(ai.SubtitleAIError(code, "busy", retryable=True))
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                agents.listen_and_check(p, cut, 0, 60, "de", [])
            self.assertEqual((ctx.exception.code, p.calls), (code, [(60.0, False)]))
        # a busy STRONG model (asked only after a bad fast answer) is a step like any other: the piece is split
        r = agents.listen_and_check(ScriptedProvider(LOOPING, ai.SubtitleAIError("AI_HTTP_503", "busy", retryable=True), GOOD, GOOD), cut, 0, 60, "de", [])
        self.assertEqual(r.steps[:3], ["fast:LOOP", "strong:AI_HTTP_503", "split"])
        self.assertEqual(r.gaps, [])

    def test_transient_errors(self):
        transient = [ai.is_transient(ai.SubtitleAIError(c, "x")) for c in ("AI_HTTP_503", "AI_HTTP_502", "AI_HTTP_429", "AI_NETWORK")]
        lasting = [ai.is_transient(ai.SubtitleAIError(c, "x")) for c in ("AI_QUOTA", "AI_KEY_REJECTED", "AI_BAD_ANSWER", "AI_HTTP_400", "AI_EMPTY_ANSWER")]
        self.assertEqual((transient, lasting), ([True] * 4, [False] * 5))


class TestProofreader(unittest.TestCase):
    class Proof:
        def __init__(self, answer):
            self.answer = answer

        def proofread(self, lines):
            if isinstance(self.answer, Exception):
                raise self.answer
            return self.answer(lines)

    def test_corrections_counted_count_mismatch_and_errors_ignored(self):
        piece = agents.PieceResult(segments=[seg(0, 1, "fur dich"), seg(1, 2, "Danke.")], steps=["fast:ok"])
        r = agents.proofread(piece, self.Proof(lambda lines: ["für dich", "Danke."]))
        self.assertEqual(([s["text"] for s in r.segments], r.corrected, r.steps[-1]), (["für dich", "Danke."], 1, "proofread:1"))
        piece = agents.PieceResult(segments=[seg(0, 1, "fur dich")])
        self.assertEqual(agents.proofread(piece, self.Proof(lambda lines: ["a", "b"])).segments[0]["text"], "fur dich")
        piece = agents.PieceResult(segments=[seg(0, 1, "fur dich")])
        r = agents.proofread(piece, self.Proof(ai.SubtitleAIError("AI_QUOTA", "x")))
        self.assertEqual((r.segments[0]["text"], r.steps[-1]), ("fur dich", "proofread:skipped-quota"))
        self.assertIs(agents.proofread(piece, None), piece)


class TestAnswerFormats(unittest.TestCase):
    def test_bare_array_and_line_breaks_inside_strings(self):
        bare = '[{"start": 1.0, "end": 2.0, "text": "Hallo"}, {"start": 2.5, "end": 3.0, "text": "Welt"}]'
        answer = ai.extract_json(bare)
        self.assertEqual(ai.as_object(answer, "segments")["segments"][1]["text"], "Welt")
        self.assertEqual(ai.extract_json('{"t": ["Zeile eins\nZeile zwei"]}')["t"][0], "Zeile eins\nZeile zwei")
        self.assertEqual(ai.extract_json('Hier:\n```json\n{"segments": []}\n```'), {"segments": []})

    def test_fast_model_first_and_schema_sent(self):
        sent = []

        def transport(url, body, headers, timeout=300):
            sent.append((url, json.loads(body)))
            return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '[{"start": 0.5, "end": 1.5, "text": "Hallo"}]'}]}}]}

        with patch.object(settings, "GEMINI_API_KEY", "k"), patch.object(settings, "SUBTITLE_FAST_MODEL", "fast-x"), \
                patch.object(settings, "SUBTITLE_AI_MODEL", ""), patch.object(settings, "GEMINI_MODEL", "strong-y"), patch.object(ai, "transport", transport):
            out = ai.GeminiSTT().transcribe(b"x", "audio/mp3", "de", 10)
            self.assertEqual((out.model, out.segments[0]["text"]), ("fast-x", "Hallo"))  # the bare list is accepted
            ai.GeminiSTT().transcribe(b"x", "audio/mp3", "de", 10, strong=True)
        self.assertIn("/fast-x:", sent[0][0])
        self.assertIn("/strong-y:", sent[1][0])
        self.assertEqual(sent[0][1]["generationConfig"]["responseSchema"]["required"], ["segments"])

    def test_a_busy_fast_model_is_asked_patiently_and_never_falls_through_to_the_strong_one(self):
        sent = []

        def busy(url, body, headers, timeout=300):
            sent.append(url)
            raise ai.SubtitleAIError("AI_HTTP_503", "busy", retryable=True)

        with patch.object(settings, "GEMINI_API_KEY", "k"), patch.object(settings, "SUBTITLE_FAST_MODEL", "fast-x"), \
                patch.object(settings, "SUBTITLE_AI_MODEL", ""), patch.object(settings, "GEMINI_MODEL", "strong-y"), \
                patch.object(ai, "transport", busy), patch.object(ai, "RETRY_PAUSE", 0):
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                ai.GeminiSTT().transcribe(b"x", "audio/mp3", "de", 10)
            self.assertEqual(ctx.exception.code, "AI_HTTP_503")
            self.assertEqual(len(sent), 5)
            self.assertTrue(all("/fast-x:" in u for u in sent))
            sent.clear()
            with self.assertRaises(ai.SubtitleAIError):
                ai.GeminiProofreader().proofread(["eins"])
            self.assertEqual((len(sent), all("/fast-x:" in u for u in sent)), (4, True))
            sent.clear()
            with self.assertRaises(ai.SubtitleAIError):  # the translator (text only) may still use the strong order
                ai.GeminiTranslator().translate(["eins"], "de", "uz")
            self.assertTrue(any("/strong-y:" in u for u in sent))

    def test_used_up_quota_is_its_own_error(self):
        body = json.dumps({"error": {"message": "You exceeded your current quota, please check your plan and billing details."}}).encode()
        err = urllib.error.HTTPError("https://x", 429, "Too Many Requests", {}, io.BytesIO(body))
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                ai._post("https://x", b"{}", {})
        self.assertEqual((ctx.exception.code, ctx.exception.retryable), ("AI_QUOTA", False))

    def test_a_per_minute_limit_is_retried_only_a_daily_quota_stops(self):
        def answer(quota_id, extra=None):
            msg = "You exceeded your current quota, please check your plan and billing details."
            details = [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": quota_id}]}, *(extra or [])]
            body = json.dumps({"error": {"code": 429, "message": msg, "details": details}}).encode()
            return urllib.error.HTTPError("https://x", 429, "Too Many Requests", {}, io.BytesIO(body))

        cases = [(answer("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "17s"}]),
                  ("AI_HTTP_429", True)),
                 (answer("GenerateRequestsPerDayPerProjectPerModel-FreeTier"), ("AI_QUOTA", False))]
        for err, expected in cases:
            with patch("urllib.request.urlopen", side_effect=err):
                with self.assertRaises(ai.SubtitleAIError) as ctx:
                    ai._post("https://x", b"{}", {})
            self.assertEqual((ctx.exception.code, ctx.exception.retryable), expected)
        self.assertTrue(ai.is_transient(ai.SubtitleAIError("AI_HTTP_429", "x")))


if __name__ == "__main__":
    unittest.main()
