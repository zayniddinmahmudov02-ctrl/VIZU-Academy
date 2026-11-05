"""Profile photos: every upload is decoded and re-encoded on the server, so the stored file is always an
image we produced (never the client's bytes).

Checks: size ≤ MAX_BYTES, real content decoded by Pillow, format JPEG / PNG / WebP and matching the declared
MIME type, MIN_SIDE ≤ each side, at most MAX_PIXELS (decompression bombs). Then EXIF orientation is applied,
the square crop chosen in the browser (fractions of the image, see `crop_box`) or the centre square is cut
out, scaled to OUTPUT×OUTPUT and saved as WebP without metadata under a random name in `uploads/avatars/`
(the existing public avatar folder; `users.profile_image` keeps its URL)."""

import io
import uuid

from fastapi import HTTPException, UploadFile

MAX_BYTES = 5 * 1024 * 1024
MIN_SIDE = 96
MAX_PIXELS = 40_000_000
OUTPUT = 512
FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
FOLDER = "avatars"


def crop_box(width: int, height: int, x: float | None, y: float | None, size: float | None) -> tuple[int, int, int, int]:
    """Square crop in pixels. x / y = left / top as a fraction of width / height, size = side as a fraction of
    the shorter side; missing values = centred square. Values are clamped so the box always lies inside."""
    short = min(width, height)
    side = short if size is None else max(1, round(short * min(1.0, max(0.05, size))))
    if x is None or y is None:
        left, top = (width - side) // 2, (height - side) // 2
    else:
        left, top = round(width * min(1.0, max(0.0, x))), round(height * min(1.0, max(0.0, y)))
    left, top = min(left, width - side), min(top, height - side)
    return left, top, left + side, top + side


def process(data: bytes, filename: str | None, declared: str | None, x: float | None = None, y: float | None = None,
            size: float | None = None) -> bytes:
    from PIL import Image, ImageOps, UnidentifiedImageError

    if not data:
        raise HTTPException(400, "PHOTO_EMPTY")
    if len(data) > MAX_BYTES:
        raise HTTPException(400, f"Image exceeds the maximum upload size of {MAX_BYTES // (1024 * 1024)}MB")
    if filename and not filename.lower().endswith(EXTENSIONS):
        raise HTTPException(400, "PHOTO_EXTENSION")
    try:
        probe = Image.open(io.BytesIO(data))
        fmt = probe.format
        if probe.width * probe.height > MAX_PIXELS:
            raise HTTPException(400, "PHOTO_TOO_LARGE_DIMENSIONS")
        probe.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(400, "PHOTO_INVALID")
    if fmt not in FORMATS or (declared and FORMATS[fmt] != declared):
        raise HTTPException(400, "PHOTO_TYPE_MISMATCH")
    img = ImageOps.exif_transpose(img)
    if min(img.size) < MIN_SIDE:
        raise HTTPException(400, "PHOTO_TOO_SMALL")
    img = img.convert("RGB").crop(crop_box(img.width, img.height, x, y, size)).resize((OUTPUT, OUTPUT), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "WEBP", quality=86, method=5)
    return out.getvalue()


def as_upload(webp: bytes) -> UploadFile:
    """The processed photo as an UploadFile for app.services.upload (random name, .webp)."""
    return UploadFile(file=io.BytesIO(webp), filename=f"{uuid.uuid4().hex}.webp", size=len(webp))
