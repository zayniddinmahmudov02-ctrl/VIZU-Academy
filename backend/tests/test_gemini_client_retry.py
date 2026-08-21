"""Unit tests for app/services/ai_content/gemini_client.py's retry/
fallback logic -- the module the multi-lesson vocabulary generation
script (app/scripts/vocabulary_cleanup_and_generate.py) and the AI
content-generation endpoints both call. Mirrors
tests/test_ai_enrichment_retry.py's coverage since both modules now
share the same retry policy (see gemini_client.py's module docstring
for why they're still two files, not one).

Run from the `backend/` directory:

    python -m unittest tests.test_gemini_client_retry -v
"""

import email.message
import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from app.services.ai_content import gemini_client


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
        url="https://example.test", code=code, msg="error", hdrs=headers,
        fp=io.BytesIO(b'{"error": {"status": "TEST"}}'),
    )


class GeminiClientRetryTests(unittest.TestCase):
    def setUp(self):
        self.mock_sleep = patch("app.services.ai_content.gemini_client.time.sleep").start()
        patch.object(gemini_client.settings, "GEMINI_API_KEY", "test-key").start()
        patch.object(gemini_client.settings, "GEMINI_FALLBACK_MODEL", "").start()
        self.addCleanup(patch.stopall)

    def test_503_then_success(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503), _ok_response("ok")]
            result = gemini_client._call_gemini_sync("hi")
        self.assertEqual(result, "ok")
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_persistent_503_fails_cleanly(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503)] * 4
            with self.assertRaises(gemini_client.AIContentError) as ctx:
                gemini_client._call_gemini_sync("hi")
        self.assertTrue(ctx.exception.transient)
        self.assertEqual(mock_urlopen.call_count, 4)

    def test_429_retried(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(429), _ok_response("ok")]
            result = gemini_client._call_gemini_sync("hi")
        self.assertEqual(result, "ok")

    def test_5xx_variants_retried(self):
        for code in (500, 502, 504):
            with self.subTest(code=code):
                with patch("urllib.request.urlopen") as mock_urlopen:
                    mock_urlopen.side_effect = [_http_error(code), _ok_response("ok")]
                    result = gemini_client._call_gemini_sync("hi")
                self.assertEqual(result, "ok")

    def test_401_fails_immediately(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(401)]
            with self.assertRaises(gemini_client.AIContentError) as ctx:
                gemini_client._call_gemini_sync("hi")
        self.assertFalse(ctx.exception.transient)
        self.assertEqual(mock_urlopen.call_count, 1)
        self.mock_sleep.assert_not_called()

    def test_timeout_retried_then_fails(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("timed out")
            with self.assertRaises(gemini_client.AIContentError):
                gemini_client._call_gemini_sync("hi")
        self.assertEqual(mock_urlopen.call_count, 4)

    def test_retry_after_respected_and_clamped(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503, retry_after="9999"), _ok_response("ok")]
            gemini_client._call_gemini_sync("hi")
        self.assertEqual(self.mock_sleep.call_args[0][0], gemini_client.RETRY_AFTER_MAX_SECONDS)

    def test_fallback_used_when_primary_exhausted_and_configured(self):
        with patch.object(gemini_client.settings, "GEMINI_FALLBACK_MODEL", "configured-fallback"):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = [_http_error(503)] * 4 + [_ok_response("from fallback")]
                result = gemini_client._call_gemini_sync("hi")
        self.assertEqual(result, "from fallback")
        self.assertEqual(mock_urlopen.call_count, 5)

    def test_no_fallback_when_not_configured(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [_http_error(503)] * 4
            with self.assertRaises(gemini_client.AIContentError):
                gemini_client._call_gemini_sync("hi")
        self.assertEqual(mock_urlopen.call_count, 4)

    def test_extract_json_object_still_works_unchanged(self):
        # Confirms the retry hardening didn't touch the unrelated JSON
        # extraction used by the 5 AI content-generation endpoints.
        result = gemini_client.extract_json_object('prose... {"a": 1} ...more prose')
        self.assertEqual(result, {"a": 1})


if __name__ == "__main__":
    unittest.main()
