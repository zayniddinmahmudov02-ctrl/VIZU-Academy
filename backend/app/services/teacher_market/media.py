"""Files of the marketplace — every image is decoded and re-encoded by the server (never the client's bytes).

* Teacher photo: 9:16 portrait (720 × 1280 WebP), course image: 16:9 (1280 × 720 WebP). The crop the teacher chose in the
  browser comes as fractions of the image (x, y = left / top, w = width of the crop box); missing = the largest centred box.
  Checks as for profile photos (app.services.profile_photo): ≤ 8 MB, real JPEG / PNG / WebP matching the declared type, size
  limits against decompression bombs, EXIF orientation applied, metadata dropped. Stored under a random name in the public
  `uploads/teacher-market/…` folder (the catalog shows them to every logged-in user, like avatars).
* Certificate file: an image (re-encoded to WebP, max 2000 px) or a PDF (≤ 10 MB, must start with %PDF-), stored under a random
  name in protected storage; it is served only through GET /my-teacher/certificates/{id}/file (verified ones to logged-in users,
  others only to their teacher and admins)."""

import io
import uuid
from pathlib import Path

from app.core.storage.local import LocalStorage
from app.services.teacher_market.common import err

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000
MIN_SIDE = 200
FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
PHOTO = (720, 1280)
COURSE_IMAGE = (1280, 720)
CERT_MAX_SIDE = 2000


class _Public(LocalStorage):
    ROOT = Path("uploads")


class _Certificates(LocalStorage):
    ROOT = Path("app/protected_storage/teacher-certificates")


public_store = _Public()
certificate_store = _Certificates()


def _open_image(data: bytes, filename: str | None, declared: str | None, max_bytes: int):
    from PIL import Image, ImageOps, UnidentifiedImageError

    if not data:
        raise err(400, "FILE_EMPTY")
    if len(data) > max_bytes:
        raise err(413, "FILE_TOO_LARGE")
    if filename and not filename.lower().endswith(IMAGE_EXT):
        raise err(400, "IMAGE_EXTENSION")
    try:
        probe = Image.open(io.BytesIO(data))
        fmt = probe.format
        if probe.width * probe.height > MAX_PIXELS:
            raise err(400, "IMAGE_TOO_LARGE_DIMENSIONS")
        probe.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise err(400, "IMAGE_INVALID") from None
    if fmt not in FORMATS or (declared and FORMATS[fmt] != declared):
        raise err(400, "IMAGE_TYPE_MISMATCH")
    img = ImageOps.exif_transpose(img).convert("RGB")
    if min(img.size) < MIN_SIDE:
        raise err(400, "IMAGE_TOO_SMALL")
    return img


def crop_box(width: int, height: int, ratio: float, x: float | None, y: float | None, w: float | None) -> tuple[int, int, int, int]:
    """Crop with width / height = ratio inside the image. x, y, w are fractions of the image width / height / width."""
    max_w = min(width, round(height * ratio))
    box_w = max_w if w is None else max(1, min(max_w, round(width * min(1.0, max(0.05, w)))))
    box_h = max(1, round(box_w / ratio))
    if box_h > height:
        box_h, box_w = height, max(1, round(height * ratio))
    if x is None or y is None:
        left, top = (width - box_w) // 2, (height - box_h) // 2
    else:
        left, top = round(width * min(1.0, max(0.0, x))), round(height * min(1.0, max(0.0, y)))
    left, top = max(0, min(left, width - box_w)), max(0, min(top, height - box_h))
    return left, top, left + box_w, top + box_h


def _webp(img, size: tuple[int, int] | None = None, max_side: int | None = None) -> bytes:
    from PIL import Image

    if size is not None:
        img = img.resize(size, Image.LANCZOS)
    elif max_side is not None and max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "WEBP", quality=86, method=5)
    return out.getvalue()


def _save_public(folder: str, data: bytes) -> str:
    name = f"teacher-market/{folder}/{uuid.uuid4().hex}.webp"
    target = public_store._inside_root(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return f"/uploads/{name}"


def remove_public(url_path: str | None) -> None:
    """Delete an earlier photo / course image of ours (only paths inside uploads/teacher-market/)."""
    if not url_path or not url_path.startswith("/uploads/teacher-market/"):
        return
    try:
        public_store._inside_root(url_path[len("/uploads/"):]).unlink(missing_ok=True)
    except (OSError, ValueError):
        pass


def save_photo(data: bytes, filename: str | None, declared: str | None, x=None, y=None, w=None) -> str:
    img = _open_image(data, filename, declared, MAX_IMAGE_BYTES)
    img = img.crop(crop_box(img.width, img.height, 9 / 16, x, y, w))
    return _save_public("photos", _webp(img, PHOTO))


def save_course_image(data: bytes, filename: str | None, declared: str | None, x=None, y=None, w=None) -> str:
    img = _open_image(data, filename, declared, MAX_IMAGE_BYTES)
    img = img.crop(crop_box(img.width, img.height, 16 / 9, x, y, w))
    return _save_public("courses", _webp(img, COURSE_IMAGE))


def save_certificate(data: bytes, filename: str | None, declared: str | None) -> tuple[str, str]:
    """(stored file name, file type image|pdf)."""
    lower = (filename or "").lower()
    if declared == "application/pdf" or lower.endswith(".pdf"):
        if not data:
            raise err(400, "FILE_EMPTY")
        if len(data) > MAX_PDF_BYTES:
            raise err(413, "FILE_TOO_LARGE")
        if not data.startswith(b"%PDF-") or (declared and declared != "application/pdf") or not lower.endswith(".pdf"):
            raise err(400, "PDF_INVALID")
        name, kind, payload = f"{uuid.uuid4().hex}.pdf", "pdf", data
    else:
        img = _open_image(data, filename, declared, MAX_IMAGE_BYTES)
        name, kind, payload = f"{uuid.uuid4().hex}.webp", "image", _webp(img, max_side=CERT_MAX_SIDE)
    target = certificate_store._inside_root(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return name, kind


def certificate_path(name: str) -> Path:
    return certificate_store._inside_root(name)


def remove_certificate(name: str) -> None:
    try:
        certificate_store._inside_root(name).unlink(missing_ok=True)
    except (OSError, ValueError):
        pass
