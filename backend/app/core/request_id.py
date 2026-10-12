"""Per-request correlation id.

Every response carries an `X-Request-ID` header — the caller's own id when
it sent a well-formed one (e.g. nginx `$request_id`), otherwise a fresh one.
The same id is logged with every unhandled exception (handlers.py), so a
failed request seen in the browser (Network tab / ApiError.requestId) can be
found in `journalctl -u vizu-backend` without logging tokens, cookies,
bodies or query strings."""

import re
import uuid

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
_VALID = re.compile(r"[A-Za-z0-9._-]{8,64}")


def request_id_of(request: Request) -> str | None:
    """The id RequestIdMiddleware assigned — also readable from the
    catch-all 500 handler, which Starlette runs outside user middleware."""
    state = request.scope.get("state")
    value = state.get("request_id") if isinstance(state, dict) else None
    return value if isinstance(value, str) else None


def _incoming_id(scope: Scope) -> str | None:
    for name, value in scope.get("headers", []):
        if name == b"x-request-id":
            candidate = value.decode("latin-1").strip()
            return candidate if _VALID.fullmatch(candidate) else None
    return None


class RequestIdMiddleware:
    """Pure ASGI (not BaseHTTPMiddleware) so streaming responses — the video
    stream, audio, file downloads — pass through untouched."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_id(scope) or uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"]
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_id)
