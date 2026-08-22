"""Regression test for the CORS/Books production incident: exception
handlers registered via @app.exception_handler(...) (including the
catch-all Exception handler) do NOT pass back through CORSMiddleware's
header-injection logic in this app, so an error response for an
otherwise-legitimate cross-origin request previously had zero
Access-Control-Allow-* headers — the browser then reported a generic
"blocked by CORS policy" for what was actually an unrelated backend
exception (e.g. a 500 from a missing table), masking the real error.
Verifies app.core.cors's shared allow-list/regex helpers, and that all
four registered exception handlers attach the correct headers for an
allowed origin, no headers for a disallowed one, and never echo "*"
(required since allow_credentials=True everywhere in this app)."""

import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI, HTTPException

from app.core.cors import cors_headers_for, is_allowed_origin
from app.core.exceptions import register_exception_handlers
from app.core.exceptions.errors import DomainError, NotFoundError


class TestIsAllowedOrigin(unittest.TestCase):
    def test_localhost_dev_origins_allowed(self):
        self.assertTrue(is_allowed_origin("http://localhost:3000"))
        self.assertTrue(is_allowed_origin("http://127.0.0.1:5173"))

    def test_random_origin_not_allowed_by_default(self):
        self.assertFalse(is_allowed_origin("https://evil.example.com"))

    def test_none_or_empty_origin_not_allowed(self):
        self.assertFalse(is_allowed_origin(None))
        self.assertFalse(is_allowed_origin(""))


class TestCorsHeadersFor(unittest.TestCase):
    def test_allowed_origin_gets_headers_without_wildcard(self):
        headers = cors_headers_for("http://localhost:3000")
        self.assertEqual(headers["Access-Control-Allow-Origin"], "http://localhost:3000")
        self.assertEqual(headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(headers["Vary"], "Origin")
        # Never "*" — allow_credentials=True is incompatible with a
        # wildcard origin per the CORS spec and the browser itself.
        self.assertNotEqual(headers["Access-Control-Allow-Origin"], "*")

    def test_disallowed_origin_gets_no_headers(self):
        self.assertEqual(cors_headers_for("https://evil.example.com"), {})

    def test_missing_origin_gets_no_headers(self):
        self.assertEqual(cors_headers_for(None), {})


def make_request(origin: str | None) -> MagicMock:
    request = MagicMock()
    request.headers.get.return_value = origin
    return request


class TestExceptionHandlersAttachCorsHeaders(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = FastAPI()
        register_exception_handlers(self.app)

    async def test_http_exception_handler_attaches_headers_for_allowed_origin(self):
        handler = self.app.exception_handlers[HTTPException]
        response = await handler(make_request("http://localhost:3000"), HTTPException(status_code=404, detail="nope"))
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    async def test_http_exception_handler_no_headers_for_disallowed_origin(self):
        handler = self.app.exception_handlers[HTTPException]
        response = await handler(make_request("https://evil.example.com"), HTTPException(status_code=404, detail="nope"))
        self.assertNotIn("access-control-allow-origin", response.headers)

    async def test_not_found_handler_attaches_headers(self):
        handler = self.app.exception_handlers[NotFoundError]
        response = await handler(make_request("http://localhost:3000"), NotFoundError("missing"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    async def test_domain_error_handler_attaches_headers(self):
        handler = self.app.exception_handlers[DomainError]
        response = await handler(make_request("http://localhost:3000"), DomainError("bad"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    async def test_catch_all_internal_exception_handler_attaches_headers(self):
        # This is the exact handler that produced the live production
        # symptom: a real 500 (e.g. missing "books" table) reached this
        # handler, which built a response with no CORS headers at all —
        # the browser then reported "blocked by CORS policy" instead of
        # surfacing the actual 500.
        handler = self.app.exception_handlers[Exception]
        response = await handler(make_request("http://localhost:3000"), RuntimeError("relation books does not exist"))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    async def test_catch_all_internal_exception_handler_no_headers_for_disallowed_origin(self):
        handler = self.app.exception_handlers[Exception]
        response = await handler(make_request("https://evil.example.com"), RuntimeError("boom"))
        self.assertNotIn("access-control-allow-origin", response.headers)


if __name__ == "__main__":
    unittest.main()
