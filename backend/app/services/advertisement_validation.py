"""Pure validators for the Werbung-Banner (kept free of DB imports so the
schemas can use them and they are trivially unit-testable)."""

from urllib.parse import urlparse

MAX_URL_LENGTH = 1000


def validate_target_url(value: str) -> str:
    """Only absolute http(s) URLs with a real host — never javascript:,
    data:, protocol-relative or relative URLs (the click endpoint redirects
    to this value, so it must not become an open-redirect/XSS vector)."""
    value = (value or "").strip()
    if not value or len(value) > MAX_URL_LENGTH:
        raise ValueError("Link fehlt oder ist zu lang.")
    if any(ch in value for ch in ("\n", "\r", "\t", " ", "\\")):
        raise ValueError("Link enthält ungültige Zeichen.")
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if parsed.scheme not in ("http", "https") or "." not in host or parsed.username or parsed.password:
        raise ValueError("Link muss eine vollständige http(s)-Adresse sein, z. B. https://example.com.")
    return value


def validate_image_url(value: str | None) -> str | None:
    """Images come from the existing media-library upload (/uploads/images/...)
    or an absolute https URL. No base64/data: URLs, no other local paths."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > 500 or any(ch in value for ch in ("\n", "\r", " ", "\\")):
        raise ValueError("Ungültige Bild-URL.")
    if value.startswith("/uploads/images/") and ".." not in value:
        return value
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc:
        return value
    raise ValueError("Bild muss über den Upload (/uploads/images/...) oder als https-URL angegeben werden.")


def ctr(impressions: int, clicks: int) -> float:
    """CTR = clicks / impressions x 100, rounded to 2 decimals (0 without impressions)."""
    return round(clicks / impressions * 100, 2) if impressions else 0.0
