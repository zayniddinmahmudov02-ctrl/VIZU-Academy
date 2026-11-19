"""AI subtitles of Medienwelt films — the pure parts and the providers, without a database or network (`services/medien/subtitle_ai.py`):
pauses from ffmpeg, piece borders at pauses, time formats, segment cleaning, cue building (order, overlaps, minimum length, end of video,
wrapping, duplicates at piece borders), snapping onto the speech, SRT export, JSON extraction; the Gemini / OpenAI / Google calls with a
stubbed transport (the key travels in a header, never in the URL; retries; model fallback; key refused; cut-off answer; wrong count);
the test provider is refused outside APP_ENV=test; the status never shows a key."""

import json
import unittest
from unittest.mock import patch

from app.core.config import settings
from app.services.medien import subtitle_ai as ai
from app.services.medien import subtitle_jobs as jobs
from app.services.medien.subtitles import Cue

SILENCE_LOG = """
[silencedetect @ 0x1] silence_start: 0
[silencedetect @ 0x1] silence_end: 1.25 | silence_duration: 1.25
size=N/A time=00:00:05.00 bitrate=N/A
[silencedetect @ 0x1] silence_start: 3.5
[silencedetect @ 0x1] silence_end: 4.1 | silence_duration: 0.6
[silencedetect @ 0x1] silence_start: 9.75
"""


def gemini_answer(payload: dict, finish: str = "STOP") -> dict:
    return {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": "```json\n" + json.dumps(payload) + "\n```"}]}}]}


class Recorder:
    """A transport stub: answers (or raises) from a list and records what was sent."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def __call__(self, url, body, headers, timeout=300):
        self.calls.append({"url": url, "body": body, "headers": headers})
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


class TestPureHelpers(unittest.TestCase):
    def test_parse_silences(self):
        self.assertEqual(ai.parse_silences(SILENCE_LOG), [(0.0, 1.25), (3.5, 4.1)])  # the open pause at the end is dropped

    def test_choose_cuts_moves_borders_into_pauses(self):
        cuts = ai.choose_cuts(700, [(170.0, 171.0), (178.0, 182.0), (355.0, 356.0), (530.0, 531.0)], 180, 25)
        self.assertEqual(cuts[0], 0.0)
        self.assertEqual(cuts[1], 180.0)  # the pause closest to 180 s (178–182, middle 180)
        self.assertAlmostEqual(cuts[2], 355.5)
        self.assertEqual(cuts[-1], 700)
        self.assertTrue(all(b > a for a, b in zip(cuts, cuts[1:])))
        # no pause near the aim: cut at the aim; a short tail is joined to the last piece
        self.assertEqual(ai.choose_cuts(400, [], 180), [0.0, 180.0, 400])
        self.assertEqual(ai.choose_cuts(200, [], 180), [0.0, 200])
        self.assertEqual(ai.pieces([0.0, 180.0, 400]), [(0.0, 180.0), (180.0, 400)])

    def test_time_formats_and_languages(self):
        for raw, want in ((12.5, 12.5), ("12,5", 12.5), ("0:12.5", 12.5), ("00:01:02,250", 62.25), ("1:00:00.000", 3600.0)):
            self.assertAlmostEqual(ai.to_seconds(raw), want)
        for bad in (None, "", "abc", True, "1:2:3:4"):
            self.assertIsNone(ai.to_seconds(bad))
        self.assertEqual([ai.normalize_language(x) for x in ("German", "deu", "EN", "uzbek", "ru-RU", "", None)], ["de", "de", "en", "uz", "ru", None, None])

    def test_parse_segments_cleans_and_clamps(self):
        raw = {"segments": [{"start": "0:01.5", "end": 3, "text": "<i>Grüß</i> Gott,  Jürgen!", "speaker": "A"},
                            {"start": 5, "end": 2, "text": "Kein Ende"}, {"start": 1, "end": 2, "text": "   "}, "junk",
                            {"start": 100, "end": 120, "text": "zu spät"}]}
        segs = ai.parse_segments(raw, 60)
        self.assertEqual(segs[0], {"start": 1.5, "end": 3.0, "text": "Grüß Gott, Jürgen!", "speaker": "A"})
        self.assertGreater(segs[1]["end"], segs[1]["start"])  # no valid end: a reading time is given
        self.assertEqual(len(segs), 3)
        self.assertEqual((segs[2]["start"], segs[2]["end"]), (60, 60.5))  # clamped into the piece

    def test_wrap(self):
        self.assertEqual(ai.wrap_text("kurz"), "kurz")
        wrapped = ai.wrap_text("Ich möchte heute Abend mit meinen Freunden ins Kino gehen")
        self.assertEqual(wrapped.count("\n"), 1)
        self.assertTrue(all(len(line) <= 42 for line in wrapped.split("\n")))
        self.assertEqual(ai.wrap_text("eins\nzwei drei vier fünf sechs sieben acht neun zehn elf"), "eins\nzwei drei vier fünf sechs sieben acht neun zehn elf")

    def test_build_cues(self):
        segs = [{"start": 5.0, "end": 9.0, "text": "Zweiter Satz"}, {"start": 1.0, "end": 6.0, "text": "Erster Satz"},
                {"start": 9.02, "end": 9.1, "text": "Ja"}, {"start": 9.5, "end": 10.0, "text": "Ja"}, {"start": 30, "end": 40, "text": "nach dem Video"}]
        cues = ai.build_cues(segs, video_ms=12_000)
        self.assertEqual([c.text for c in cues], ["Erster Satz", "Zweiter Satz", "Ja"])  # sorted, duplicate at a border merged, beyond the video dropped
        self.assertEqual(cues[0].end, 5000 - ai.GAP_MS)  # no overlap
        self.assertGreaterEqual(cues[2].end - cues[2].start, ai.MIN_CUE_MS)  # readable minimum
        self.assertLessEqual(cues[-1].end, 12_000)

    def test_build_cues_drops_placeholders_and_caps_the_length(self):
        # seen live 2026-11-19: "..." for 176 s and "[…]" for unclear passages
        segs = [{"start": 1.0, "end": 2.5, "text": "Kommen Sie!"}, {"start": 3.0, "end": 179.0, "text": "..."}, {"start": 180.0, "end": 182.0, "text": "[…]"},
                {"start": 190.0, "end": 290.0, "text": "Maul, komm!"}, {"start": 300.0, "end": 301.0, "text": "- 42"}]
        cues = ai.build_cues(segs)
        self.assertEqual([c.text for c in cues], ["Kommen Sie!", "Maul, komm!", "- 42"])
        self.assertEqual((cues[1].start, cues[1].end), (190_000, 190_000 + ai.MAX_CUE_MS))

    def test_snap_to_speech(self):
        cues = [Cue(1000, 3000, "a"), Cue(3600, 8000, "b"), Cue(9000, 9300, "c")]
        snapped = ai.snap_to_speech(cues, [(0.8, 1.4), (2.6, 3.7)])
        self.assertEqual(snapped[0].start, 1400)  # the voice starts when the pause ends
        self.assertEqual(snapped[0].end, 2600 + ai.TAIL_MS)  # … and stops when the next pause starts
        self.assertEqual(snapped[1].start, 3700)
        self.assertEqual((snapped[2].start, snapped[2].end), (9000, 9300))  # nothing near: unchanged
        self.assertEqual(ai.snap_to_speech(cues, []), cues)  # music under the speech: nothing moves
        far = ai.snap_to_speech([Cue(1000, 4000, "x")], [(0.0, 2.5)])
        self.assertEqual(far[0].start, 1000)  # 1.5 s away: too far to move

    def test_srt_and_json(self):
        srt = ai.to_srt([Cue(500, 1500, "Hallo\nWelt"), Cue(3_723_004, 3_724_000, "Tschüss")]).decode("utf-8")
        self.assertTrue(srt.startswith("1\n00:00:00,500 --> 00:00:01,500\nHallo\nWelt\n\n2\n01:02:03,004 --> 01:02:04,000\nTschüss"))
        self.assertEqual(ai.extract_json('Hier: ```json {"a": [1]} ```'), {"a": [1]})
        with self.assertRaises(ai.SubtitleAIError):
            ai.extract_json('{"a": [1')

    def test_majority(self):
        self.assertEqual(ai.majority_language(["de", None, "en", "de"]), "de")
        self.assertIsNone(ai.majority_language([None]))


class TestProviders(unittest.TestCase):
    def setUp(self):
        # no fast model: these tests are about the strong order (model-a, then model-b); the fast-first order is in test_medien_subtitle_agents
        self.patches = [patch.object(settings, "GEMINI_API_KEY", "test-key-123"), patch.object(settings, "SUBTITLE_AI_MODEL", ""),
                        patch.object(settings, "SUBTITLE_FAST_MODEL", ""),
                        patch.object(settings, "GEMINI_MODEL", "model-a"), patch.object(settings, "GEMINI_FALLBACK_MODEL", "model-b"),
                        patch.object(ai, "RETRY_PAUSE", 0)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def test_gemini_transcribe_key_in_header_and_segments(self):
        rec = Recorder(gemini_answer({"language": "German", "segments": [{"start": 0.5, "end": 2.0, "speaker": "A", "text": "Guten Tag"}]}))
        with patch.object(ai, "transport", rec):
            out = ai.GeminiSTT().transcribe(b"ID3audio", "audio/mp3", None, 30.0)
        self.assertEqual((out.language, out.model), ("de", "model-a"))
        self.assertEqual(out.segments, [{"start": 0.5, "end": 2.0, "text": "Guten Tag", "speaker": "A"}])
        call = rec.calls[0]
        self.assertNotIn("test-key-123", call["url"])
        self.assertEqual(call["headers"]["x-goog-api-key"], "test-key-123")
        body = json.loads(call["body"])
        self.assertIn("Detect the spoken language", body["contents"][0]["parts"][1]["text"])
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")

    def test_gemini_retries_then_falls_back_to_the_next_model(self):
        busy = ai.SubtitleAIError("AI_HTTP_503", "busy", retryable=True)
        models = lambda rec: [c["url"].split("/models/")[1].split(":")[0] for c in rec.calls]  # noqa: E731
        # the strong path (minutes per answer): one try per model, then the next one
        rec = Recorder(busy, gemini_answer({"language": "en", "segments": []}))
        with patch.object(ai, "transport", rec):
            out = ai.GeminiSTT().transcribe(b"x", "audio/mp3", "en", 10, strong=True)
        self.assertEqual((out.model, models(rec)), ("model-b", ["model-a", "model-b"]))
        # the normal path without a fast model set: the same order, asked more patiently (5 tries)
        rec = Recorder(busy, busy, busy, busy, busy, gemini_answer({"language": "en", "segments": []}))
        with patch.object(ai, "transport", rec):
            out = ai.GeminiSTT().transcribe(b"x", "audio/mp3", "en", 10)
        self.assertEqual((out.model, models(rec)), ("model-b", ["model-a"] * 5 + ["model-b"]))

    def test_rate_limit_waits_longer_than_a_busy_service(self):
        waits = []
        limited = ai.SubtitleAIError("AI_HTTP_429", "quota", retryable=True)
        busy = ai.SubtitleAIError("AI_HTTP_503", "busy", retryable=True)
        with patch.object(ai, "RETRY_PAUSE", 1), patch.object(ai.time, "sleep", waits.append), \
                patch.object(ai, "transport", Recorder(limited, limited, busy, busy, gemini_answer({"language": "de", "segments": []}))):
            out = ai.GeminiSTT().transcribe(b"x", "audio/mp3", "de", 10)
        self.assertEqual(out.model, "model-a")  # model-a: 429, 429, 503, 503, ok
        self.assertEqual(waits, [4, 8, 3, 4])

    def test_gemini_refused_key_and_cut_off_answer_stop_at_once(self):
        with patch.object(ai, "transport", Recorder(ai.SubtitleAIError("AI_KEY_REJECTED", "no"))):
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                ai.GeminiSTT().transcribe(b"x", "audio/mp3", "de", 10)
        self.assertEqual(ctx.exception.code, "AI_KEY_REJECTED")
        with patch.object(ai, "transport", Recorder(gemini_answer({"segments": []}, finish="MAX_TOKENS"))):
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                ai.GeminiSTT().transcribe(b"x", "audio/mp3", "de", 10)
        self.assertEqual(ctx.exception.code, "AI_ANSWER_TOO_LONG")

    def test_not_configured_and_test_provider_guard(self):
        with patch.object(settings, "GEMINI_API_KEY", ""), patch.object(settings, "SUBTITLE_STT_PROVIDER", "gemini"):
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                ai.stt_provider()
            self.assertEqual(ctx.exception.code, "AI_NOT_CONFIGURED")
            status = ai.status()
            self.assertFalse(status["speech_to_text"]["configured"])
            self.assertNotIn("test-key", json.dumps(status))
        with patch.object(settings, "APP_ENV", "production"), patch.object(settings, "SUBTITLE_STT_PROVIDER", "fake"), \
                patch.object(settings, "SUBTITLE_TRANSLATE_PROVIDER", "fake"):
            for factory in (ai.stt_provider, ai.translator):
                with self.assertRaises(ai.SubtitleAIError):
                    factory()
        with patch.object(settings, "OPENAI_API_KEY", ""), patch.object(settings, "SUBTITLE_STT_PROVIDER", "openai"):
            with self.assertRaises(ai.SubtitleAIError):
                ai.stt_provider()
        with patch.object(settings, "GOOGLE_TRANSLATE_API_KEY", ""), patch.object(settings, "SUBTITLE_TRANSLATE_PROVIDER", "google"):
            self.assertFalse(ai.status()["translation"]["configured"])

    def test_openai_whisper_segments(self):
        rec = Recorder({"language": "german", "segments": [{"start": 0.0, "end": 1.2, "text": " Hallo zusammen "}]})
        with patch.object(settings, "OPENAI_API_KEY", "sk-test"), patch.object(ai, "transport", rec):
            out = ai.OpenAISTT().transcribe(b"ID3", "audio/mp3", "de", 20)
        self.assertEqual((out.language, out.segments[0]["text"]), ("de", "Hallo zusammen"))
        self.assertIn(b'name="language"\r\n\r\nde', rec.calls[0]["body"])
        self.assertEqual(rec.calls[0]["headers"]["Authorization"], "Bearer sk-test")

    def test_translators(self):
        rec = Recorder(gemini_answer({"t": ["Men bugun kinoga bormoqchiman.", "Xayr"]}))
        with patch.object(ai, "transport", rec):
            out = ai.GeminiTranslator().translate(["Ich möchte heute ins Kino gehen.", "Tschüss"], "de", "uz")
        self.assertEqual(out, ["Men bugun kinoga bormoqchiman.", "Xayr"])
        self.assertIn("Uzbek (Latin script)", json.loads(rec.calls[0]["body"])["contents"][0]["parts"][0]["text"])
        with patch.object(ai, "transport", Recorder(gemini_answer({"t": ["nur eins"]}))):
            with self.assertRaises(ai.SubtitleAIError) as ctx:
                ai.GeminiTranslator().translate(["a", "b"], "de", "en")
        self.assertEqual(ctx.exception.code, "AI_TRANSLATION_COUNT")
        rec = Recorder({"data": {"translations": [{"translatedText": "Men &quot;bugun&quot;"}]}})
        with patch.object(settings, "GOOGLE_TRANSLATE_API_KEY", "g-key"), patch.object(ai, "transport", rec):
            self.assertEqual(ai.GoogleTranslator().translate(["Ich heute"], "de", "uz"), ['Men "bugun"'])
        self.assertEqual(json.loads(rec.calls[0]["body"]), {"q": ["Ich heute"], "source": "de", "target": "uz", "format": "text"})
        self.assertNotIn("g-key", rec.calls[0]["url"])

    def test_translate_lines_splits_on_wrong_count(self):
        class Picky:
            calls = 0

            def translate(self, lines, source, target):
                Picky.calls += 1
                if len(lines) > 2:
                    raise ai.SubtitleAIError("AI_TRANSLATION_COUNT", "wrong", retryable=True)
                return [f"{target}:{x}" for x in lines]

        out = jobs.translate_lines(Picky(), ["a", "b", "c", "d", "e"], "de", "uz")
        self.assertEqual(out, ["uz:a", "uz:b", "uz:c", "uz:d", "uz:e"])


if __name__ == "__main__":
    unittest.main()
