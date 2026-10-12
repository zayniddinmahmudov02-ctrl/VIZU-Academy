"""X-Request-ID: every response carries one (caller's well-formed id or a
fresh one), and an unhandled exception's 500 response + log line carry the
same id — without the query string (stream tokens live there)."""

import unittest

from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.core.exceptions.errors import NotFoundError
from app.core.request_id import RequestIdMiddleware


def build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/missing")
    def missing():
        raise NotFoundError("Video not found")

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaputt")

    return app


async def call(app, path: str, query: str = "", headers: list[tuple[bytes, bytes]] | None = None):
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": query.encode(), "root_path": "",
        "headers": headers or [], "client": ("127.0.0.1", 1), "server": ("testserver", 80),
    }
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    error = None
    try:
        await app(scope, receive, send)
    except Exception as exc:  # ServerErrorMiddleware re-raises after responding
        error = exc
    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), body, error


class TestRequestId(unittest.IsolatedAsyncioTestCase):
    async def test_generated_id_on_success(self):
        status, headers, _, _ = await call(build_app(), "/ok")
        self.assertEqual(status, 200)
        self.assertRegex(headers[b"x-request-id"].decode(), r"^[0-9a-f]{32}$")

    async def test_well_formed_incoming_id_is_kept(self):
        _, headers, _, _ = await call(build_app(), "/ok", headers=[(b"x-request-id", b"nginx-abc12345")])
        self.assertEqual(headers[b"x-request-id"], b"nginx-abc12345")

    async def test_malformed_incoming_id_is_replaced(self):
        _, headers, _, _ = await call(build_app(), "/ok", headers=[(b"x-request-id", b"bad id\nwith newline")])
        self.assertRegex(headers[b"x-request-id"].decode(), r"^[0-9a-f]{32}$")

    async def test_handled_404_keeps_body_and_gets_id(self):
        status, headers, body, _ = await call(build_app(), "/missing")
        self.assertEqual(status, 404)
        self.assertIn(b"Video not found", body)
        self.assertIn(b"x-request-id", headers)

    async def test_unhandled_500_has_id_in_header_body_and_log(self):
        with self.assertLogs("vizu", level="ERROR") as logs:
            status, headers, body, error = await call(build_app(), "/boom", query="token=SECRET123",
                                                      headers=[(b"x-request-id", b"req-500-test")])
        self.assertEqual(status, 500)
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(headers[b"x-request-id"], b"req-500-test")
        self.assertIn(b'"request_id":"req-500-test"', body)
        log = "\n".join(logs.output)
        self.assertIn("request_id=req-500-test", log)
        self.assertIn("GET /boom", log)
        self.assertNotIn("SECRET123", log)


if __name__ == "__main__":
    unittest.main()
