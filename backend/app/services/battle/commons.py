"""Wikimedia Commons search and download for battle pictures (no API key). Only files whose licence is
CC0, public domain, CC BY or CC BY-SA are offered; title, author, licence and page URL are kept with the
image. Stdlib HTTP only (the server has no httpx)."""

import html
import json
import re
import urllib.parse
import urllib.request

from fastapi import HTTPException

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "VIZU-Academy-Battle/1.0 (https://vizu-deutsch.com)"
ALLOWED_LICENSE = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?\d(\.\d)?( [a-z]{2,})?)$", re.I)
TIMEOUT_S = 20
MAX_BYTES = 12 * 1024 * 1024


def _strip(s: str | None) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def _get(url: str, params: dict | None = None) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    if not url.startswith("https://commons.wikimedia.org/") and not url.startswith("https://upload.wikimedia.org/"):
        raise HTTPException(422, "COMMONS_URL_INVALID")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            data = r.read(MAX_BYTES + 1)
    except OSError:
        raise HTTPException(502, "COMMONS_UNREACHABLE")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "IMAGE_TOO_LARGE")
    return data


def _item(page: dict) -> dict | None:
    ii = (page.get("imageinfo") or [{}])[0]
    md = ii.get("extmetadata") or {}
    lic = _strip((md.get("LicenseShortName") or {}).get("value"))
    if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp") or not ALLOWED_LICENSE.match(lic) or min(ii.get("width", 0), ii.get("height", 0)) < 300:
        return None
    return {
        "title": page["title"], "page_url": ii.get("descriptionurl"), "thumb_url": ii.get("thumburl"), "license": lic,
        "license_url": _strip((md.get("LicenseUrl") or {}).get("value")) or None,
        "author": _strip((md.get("Artist") or {}).get("value"))[:300] or None, "width": ii.get("width"), "height": ii.get("height"),
    }


def search(q: str, limit: int = 18) -> list[dict]:
    q = (q or "").strip()
    if not 2 <= len(q) <= 80:
        raise HTTPException(422, "QUERY_INVALID")
    data = json.loads(_get(API, {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} filetype:bitmap", "gsrnamespace": 6,
        "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 480,
    }))
    pages = sorted(((data.get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99))
    return [i for i in (_item(p) for p in pages) if i]


def fetch(title: str, width: int = 960) -> tuple[dict, bytes]:
    if not title.startswith("File:") or len(title) > 300:
        raise HTTPException(422, "COMMONS_TITLE_INVALID")
    data = json.loads(_get(API, {"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                                 "iiprop": "url|extmetadata|size|mime", "iiurlwidth": width}))
    pages = list(((data.get("query") or {}).get("pages") or {}).values())
    item = _item(pages[0]) if pages else None
    if item is None:
        raise HTTPException(422, "COMMONS_LICENSE_NOT_ALLOWED")
    return item, _get(item["thumb_url"])
