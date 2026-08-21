"""Unit tests for the Gemini retry/fallback/validation logic in
app/services/vocabulary/ai_enrichment.py — the flow behind the admin
"Bulk Wortschatz erstellen" dialog.

Uses only the standard library (unittest + unittest.mock) so it runs
with zero new dependencies -- this repo's requirements.txt does not
currently include pytest. Run from the `backend/` directory:

    python -m unittest tests.test_ai_enrichment_retry -v

Every test mocks urllib.request.urlopen directly (no real network
call) and patches time.sleep to a no-op so the suite runs in
milliseconds despite exercising multi-attempt backoff logic.
"""

import email.message
import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from app.services.vocabulary import ai_enrichment


def _ok_response(text: str) -> MagicMock:
    body = json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = body
    return cm


def _http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(
        url="https://example.test",
        code=code,
        msg="error",
        hdrs=headers,
        fp=io.BytesIO(b'{"error": {"status": "TEST"}}'),
    )


ARRAY_PROMPT_RESPONSE = json.dumps(
    [{"input": "Haus", "word_type": "NOMEN", "article": "das", "base_word": "Haus",
      "plural": "Häuser", "translation": "uy", "example_sentence": "Das ist mein Haus.",
      "example_translation": "Bu mening uyim."}]
)


class GeminiRetryTests(unittest.TestCase):
    def setUp(self):
        self.mock_sleep = patch("app.services.vocabulary.ai_enrichment.time.sleep").start()
        patch.object(ai_enrichment.settings, "GEMINI_API_KEY", "test-key").start()
        patch.object(ai_enrichment.settings, "GEMINI_FALLBACK_MODEL", "").start()
        self.addCleanup(patch.stopall)

    # A. 503 on first request -> retry -> success
    def test_503_then_success(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503), _ok_response("ok")]
            result = ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(result, "ok")
        self.assertEqual(mock_urlopen.call_count, 2)
        self.mock_sleep.assert_called_once()

    # B. 503 on first 3 attempts -> success on the 4th (last) attempt
    def test_503_three_times_then_success_on_last_attempt(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [
                _http_error(503), _http_error(503), _http_error(503), _ok_response("ok"),
            ]
            result = ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(result, "ok")
        self.assertEqual(mock_urlopen.call_count, 4)
        self.assertEqual(self.mock_sleep.call_count, 3)

    # C. persistent 503 -> raises, transient=True, exactly 4 attempts total
    def test_persistent_503_fails_cleanly_after_all_retries(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503)] * 4
            with self.assertRaises(ai_enrichment.AIServiceError) as ctx:
                ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertTrue(ctx.exception.transient)
        self.assertEqual(mock_urlopen.call_count, 4)
        self.assertEqual(self.mock_sleep.call_count, 3)

    # D. 429 -> retried the same as 503
    def test_429_is_retried(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(429), _ok_response("ok")]
            result = ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(result, "ok")
        self.assertEqual(mock_urlopen.call_count, 2)

    # 500/502/504 are retried too (expanded transient set per this task's spec)
    def test_5xx_variants_are_retried(self):
        for code in (500, 502, 504):
            with self.subTest(code=code):
                with patch("urllib.request.urlopen") as mock_urlopen:
                    mock_urlopen.side_effect = [_http_error(code), _ok_response("ok")]
                    result = ai_enrichment._call_gemini([{"text": "hi"}])
                self.assertEqual(result, "ok")
                self.assertEqual(mock_urlopen.call_count, 2)

    # E. 401/403 -> immediate failure, zero retries
    def test_401_fails_immediately_without_retry(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(401)]
            with self.assertRaises(ai_enrichment.AIServiceError) as ctx:
                ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertFalse(ctx.exception.transient)
        self.assertEqual(mock_urlopen.call_count, 1)
        self.mock_sleep.assert_not_called()

    def test_403_fails_immediately_without_retry(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(403)]
            with self.assertRaises(ai_enrichment.AIServiceError):
                ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_400_validation_error_fails_immediately(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(400)]
            with self.assertRaises(ai_enrichment.AIServiceError) as ctx:
                ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertFalse(ctx.exception.transient)
        self.assertEqual(mock_urlopen.call_count, 1)

    # F. network/timeout error -> retried, eventually fails cleanly if persistent
    def test_network_timeout_retried_then_fails_cleanly(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("timed out")
            with self.assertRaises(ai_enrichment.AIServiceError) as ctx:
                ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertTrue(ctx.exception.transient)
        self.assertEqual(mock_urlopen.call_count, 4)

    def test_network_timeout_then_success(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [urllib.error.URLError("timed out"), _ok_response("ok")]
            result = ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(result, "ok")

    # G. malformed response -> rejected cleanly, not retried indefinitely
    def test_malformed_json_array_rejected_cleanly(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _ok_response("this is not a JSON array at all")
            with self.assertRaises(ai_enrichment.AIServiceError):
                ai_enrichment._extract_json_array("this is not a JSON array at all")

    def test_word_count_mismatch_rejected_cleanly(self):
        # enrich_words refuses to guess pairing when the model returns a
        # different count than requested -- confirms this still raises
        # (non-transient) rather than silently misaligning results.
        import asyncio

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _ok_response(ARRAY_PROMPT_RESPONSE)
            with self.assertRaises(ai_enrichment.AIServiceError) as ctx:
                asyncio.run(ai_enrichment.enrich_words(["Haus", "Wohnung"], "A1"))
        self.assertFalse(ctx.exception.transient)

    # Retry-After header is respected instead of the fixed backoff
    def test_retry_after_header_used_instead_of_fixed_delay(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503, retry_after="7"), _ok_response("ok")]
            ai_enrichment._call_gemini([{"text": "hi"}])
        waited = self.mock_sleep.call_args[0][0]
        self.assertEqual(waited, 7.0)

    def test_retry_after_clamped_to_max(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503, retry_after="9999"), _ok_response("ok")]
            ai_enrichment._call_gemini([{"text": "hi"}])
        waited = self.mock_sleep.call_args[0][0]
        self.assertEqual(waited, ai_enrichment.RETRY_AFTER_MAX_SECONDS)

    # Model fallback: primary exhausts retries, fallback (when configured) succeeds
    def test_fallback_model_used_when_primary_exhausted(self):
        with patch.object(ai_enrichment.settings, "GEMINI_FALLBACK_MODEL", "configured-fallback-model"):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = [_http_error(503)] * 4 + [_ok_response("from fallback")]
                result = ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(result, "from fallback")
        self.assertEqual(mock_urlopen.call_count, 5)

    def test_no_fallback_attempted_when_not_configured(self):
        # GEMINI_FALLBACK_MODEL is "" in setUp -- primary exhausting
        # retries must raise, never attempt a second model.
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503)] * 4
            with self.assertRaises(ai_enrichment.AIServiceError):
                ai_enrichment._call_gemini([{"text": "hi"}])
        self.assertEqual(mock_urlopen.call_count, 4)

    def test_fallback_not_attempted_for_permanent_error(self):
        # A 401 on the primary model must not trigger a fallback attempt
        # at all -- retrying a bad API key against a second model is
        # pointless and would just double the wasted request.
        with patch.object(ai_enrichment.settings, "GEMINI_FALLBACK_MODEL", "configured-fallback-model"):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = [_http_error(401)]
                with self.assertRaises(ai_enrichment.AIServiceError):
                    ai_enrichment._call_gemini([{"text": "hi"}])
            self.assertEqual(mock_urlopen.call_count, 1)


if __name__ == "__main__":
    unittest.main()
