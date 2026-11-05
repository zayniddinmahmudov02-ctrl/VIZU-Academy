"""Battle image files.

Word pictures live in app/protected_storage/battle-images, arena backgrounds uploaded by admins in
app/protected_storage/battle-themes — both outside the public /uploads mount, random file names.
Every stored file is decoded with Pillow and re-encoded as WebP (format check, metadata stripped, size
capped), so the bytes on disk are always an image we produced.

A match picture is reached only through a signed URL issued for the running round
(HMAC-SHA256 over match id, round and expiry with SECRET_KEY): it names no word and no image id, and it
stops working shortly after the round."""

import hashlib
import hmac
import io
import time
import uuid
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

IMAGE_ROOT = Path("app/protected_storage/battle-images")
THEME_ROOT = Path("app/protected_storage/battle-themes")
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED = {"JPEG": ("image/jpeg",), "PNG": ("image/png",), "WEBP": ("image/webp",)}
EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
WORD_MAX_SIDE = 960
THEME_MAX_SIDE = {"desktop": 2400, "mobile": 1400}
MIN_SIDE = 300
TOKEN_TTL_S = 90


def normalise(data: bytes, filename: str | None, declared: str | None, max_side: int, min_side: int = MIN_SIDE) -> tuple[bytes, int, int]:
    """Validates extension + declared MIME + real content, returns (webp bytes, width, height)."""
    from PIL import Image, UnidentifiedImageError

    if not data:
        raise HTTPException(422, "IMAGE_EMPTY")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "IMAGE_TOO_LARGE")
    if filename and not filename.lower().endswith(EXTENSIONS):
        raise HTTPException(422, "IMAGE_EXTENSION")
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, "IMAGE_INVALID")
    if fmt not in ALLOWED or (declared and declared not in ALLOWED[fmt] and declared != "application/octet-stream"):
        raise HTTPException(422, "IMAGE_TYPE")
    if min(img.size) < min_side:
        raise HTTPException(422, "IMAGE_TOO_SMALL")
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    out = io.BytesIO()
    img.save(out, "WEBP", quality=82, method=5)
    return out.getvalue(), img.width, img.height


def store(root: Path, data: bytes) -> str:
    root.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.webp"
    (root / name).write_bytes(data)
    return name


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, name: str) -> Path:
    if not name or "/" in name or "\\" in name or ".." in name or not name.endswith(".webp"):
        raise HTTPException(404, "NOT_FOUND")
    path = root / name
    if not path.is_file():
        raise HTTPException(404, "NOT_FOUND")
    return path


def serve(path: Path, private: bool = True) -> FileResponse:
    headers = {"Cache-Control": "private, max-age=300" if private else "public, max-age=86400", "X-Content-Type-Options": "nosniff"}
    return FileResponse(path, media_type="image/webp", headers=headers)


def _sig(payload: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"battle-media:{payload}".encode(), hashlib.sha256).hexdigest()[:32]


def round_token(match_id, round_no: int, now: float | None = None) -> str:
    exp = int((now or time.time()) + TOKEN_TTL_S)
    payload = f"{match_id}.{round_no}.{exp}"
    return f"{payload}.{_sig(payload)}"


def read_token(token: str, now: float | None = None) -> tuple[uuid.UUID, int]:
    try:
        match_id, round_no, exp, sig = token.split(".")
        payload = f"{match_id}.{round_no}.{exp}"
        if not hmac.compare_digest(sig, _sig(payload)) or int(exp) < (now or time.time()):
            raise ValueError
        return uuid.UUID(match_id), int(round_no)
    except (ValueError, TypeError):
        raise HTTPException(404, "NOT_FOUND")
