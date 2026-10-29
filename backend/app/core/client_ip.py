"""The caller's IP for rate limits, audit rows and de-duplication.

Forwarding headers are only believed when the TCP peer is one of our own
proxies (nginx / the Next.js server on this host). Anyone who reaches
uvicorn directly could otherwise send any CF-Connecting-IP / X-Forwarded-For
and get a fresh rate-limit bucket per request.

Order behind a trusted proxy: CF-Connecting-IP (set by Cloudflare), then
X-Real-IP (set by nginx to its own peer), then the LAST X-Forwarded-For hop
(the one our proxy appended; earlier hops are client-controlled).
"""

from fastapi import Request

from app.core.config import settings


def _trusted_proxies() -> set[str]:
    return {ip.strip() for ip in settings.TRUSTED_PROXY_IPS.split(",") if ip.strip()}


def client_ip(request: Request) -> str | None:
    peer = request.client.host if request.client else None
    if peer is None or peer not in _trusted_proxies():
        return peer
    for header in ("cf-connecting-ip", "x-real-ip"):
        value = request.headers.get(header, "").strip()
        if value:
            return value
    hops = [hop.strip() for hop in request.headers.get("x-forwarded-for", "").split(",") if hop.strip()]
    return hops[-1] if hops else peer
