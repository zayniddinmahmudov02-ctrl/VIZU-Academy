import re

from app.core.config import settings

# Single source of truth for which origins are allowed — shared by the
# normal CORSMiddleware setup (main.py) AND the exception handlers
# (core/exceptions/handlers.py). CORSMiddleware only attaches
# Access-Control-Allow-* headers to responses that flow back through it
# normally; a response built and returned directly by an
# @app.exception_handler(...) (including the catch-all Exception handler)
# does not pass back through that logic, so an error response for an
# otherwise-legitimate cross-origin request has no CORS headers at all —
# the browser then reports a generic "blocked by CORS policy" for what is
# actually an unrelated backend error. Reusing this exact allow-list/regex
# for error responses fixes that without ever echoing "*" (required since
# allow_credentials=True).
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    *settings.cors_origins,
]

ALLOWED_ORIGIN_REGEX = re.compile(r"https?://(localhost|127\.0\.0\.1)(:\d+)?")


def is_allowed_origin(origin: str | None) -> bool:
    if not origin:
        return False
    return origin in ALLOWED_ORIGINS or bool(ALLOWED_ORIGIN_REGEX.fullmatch(origin))


def cors_headers_for(origin: str | None) -> dict[str, str]:
    """Headers to attach to a response for the given request Origin, if
    that origin is allowed — echoes back the specific validated origin
    (never "*") plus Vary: Origin so caches don't leak one origin's
    CORS-approved response to another."""
    if not is_allowed_origin(origin):
        return {}

    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }
