"""Shared rules of VIZU Medienwelt (Bibliothek, Musik, Filme).

Access: staff (admin-panel roles) see everything; a student gets the file of PUBLISHED content that is FREE or that they
bought (a GRANTED `media_purchases` row). Everything else is cover + text + price. The cover is the only public file.
Uploads are checked by content (magic bytes), size and a random storage name; files are never returned as paths.
Streaming: `signed_url` hands out a short-lived token URL after the access check, the stream endpoint checks again."""

import re
import unicodedata
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.jwt import create_access_token, decode_access_token
from app.core.security.roles import UserRole
from app.core.storage.local import UploadTooLarge
from app.core.storage.protected_local import ProtectedMedienStorage
from app.models.medien import (ACCESS_PAID, KIND_BOOK, KIND_FILM, KIND_SONG, PURCHASE_GRANTED, STATUS_PUBLISHED, Film, MediaBook,
                               MediaPurchase, Song)
from app.models.user import User

storage = ProtectedMedienStorage()
MODELS = {KIND_BOOK: MediaBook, KIND_SONG: Song, KIND_FILM: Film}
PURPOSE = "medien_stream"
MB = 1024 * 1024
MAX_COVER, MAX_BOOK, MAX_AUDIO, MAX_VIDEO_SINGLE, MAX_SUBTITLE = 8 * MB, 300 * MB, 100 * MB, 90 * MB, 2 * MB
MAX_RECEIPT = 8 * MB
MAX_VIDEO = 8 * 1024 * MB
LEVELS = ("A1", "A2", "B1", "B2", "C1")


def err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def is_staff(user: User | None) -> bool:
    return user is not None and user.role in UserRole.ADMIN_PANEL_ROLES


# ---------------- file sniffing ----------------


def sniff_image(head: bytes) -> str | None:
    if head[:3] == b"\xff\xd8\xff":
        return "jpg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def sniff_pdf(head: bytes) -> str | None:
    return "pdf" if head[:5] == b"%PDF-" else None


def sniff_audio(head: bytes) -> str | None:
    """MP3, WAV, M4A, AAC (raw ADTS), OGG, FLAC — by content, never by the file name."""
    if head[:3] == b"ID3":
        return "mp3"
    if head[:4] == b"fLaC":
        return "flac"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[4:8] == b"ftyp":
        return "m4a"
    if head[:4] == b"OggS":
        return "ogg"
    if len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:  # an MPEG frame sync: layer bits 00 mean ADTS AAC, anything else MP3
        return "aac" if (head[1] & 0x06) == 0 else "mp3"
    return None


def sniff_receipt(head: bytes) -> str | None:
    """A payment receipt: JPEG, PNG, WebP or PDF by content."""
    return sniff_image(head) or sniff_pdf(head)


def sniff_video(head: bytes) -> str | None:
    if head[4:8] == b"ftyp":
        return "mov" if head[8:12] == b"qt  " else "mp4"
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    return None


CONTENT_TYPES = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp", "pdf": "application/pdf", "mp3": "audio/mpeg",
                 "wav": "audio/wav", "m4a": "audio/mp4", "ogg": "audio/ogg", "flac": "audio/flac", "aac": "audio/aac", "mp4": "video/mp4",
                 "mov": "video/quicktime", "webm": "video/webm", "vtt": "text/vtt"}
# headers for private files: never cached, never sniffed into another type
PRIVATE_HEADERS = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}


def safe_filename(title: str | None, ext: str = "pdf") -> str:
    """A download name from a book title: letters / digits / spaces / dashes only, no path or header characters, at most 100 characters."""
    text = unicodedata.normalize("NFC", str(title or "")).strip()
    text = re.sub(r"[^\w .,'()&+-]", " ", text, flags=re.UNICODE)
    text = " ".join(text.replace("_", " ").split())[:100].strip(" .-") or "Buch"
    return f"{text}.{ext}"


async def save_upload(file: UploadFile, folder: str, sniff, max_bytes: int, what: str) -> tuple[str, str, int]:
    """Validate by content and store under a random name; returns (storage key, extension, size)."""
    head = await file.read(16)
    await file.seek(0)
    ext = sniff(head)
    if ext is None:
        raise err(400, f"UNSUPPORTED_FILE: {what} has an unsupported or unreadable format.")
    key = f"{folder}/{uuid4().hex}.{ext}"
    try:
        await storage.upload(file, key, max_bytes=max_bytes)
    except UploadTooLarge:
        raise err(400, f"FILE_TOO_LARGE: {what} is larger than {max_bytes // MB} MB.") from None
    return key, ext, (storage.ROOT / key).stat().st_size


def file_path(key: str | None) -> Path | None:
    """The stored file when it exists inside the storage root, else None."""
    if not key:
        return None
    try:
        path = storage._inside_root(key).resolve()
    except ValueError:
        return None
    return path if path.is_file() else None


async def remove_file(key: str | None) -> None:
    """Best effort after the DB row changed: a file that cannot be removed is reported by the admin file_status check
    (row without file / file without row never block a student)."""
    if key:
        try:
            await storage.delete(key)
        except (OSError, ValueError):
            pass


# ---------------- access ----------------


def item_or_404(db: Session, kind: str, item_id: UUID, user: User | None = None):
    item = db.get(MODELS[kind], item_id)
    if item is None or (item.status != STATUS_PUBLISHED and not is_staff(user)):
        raise err(404, "NOT_FOUND")
    return item


def owned_ids(db: Session, user: User | None, kind: str) -> set:
    if user is None:
        return set()
    return set(db.scalars(select(MediaPurchase.content_id).where(MediaPurchase.user_id == user.id, MediaPurchase.content_type == kind,
                                                                  MediaPurchase.status == PURCHASE_GRANTED)))


def can_access(db: Session, user: User | None, kind: str, item) -> bool:
    if is_staff(user):
        return True
    if item.status != STATUS_PUBLISHED:
        return False
    if item.access_type != ACCESS_PAID:
        return True
    return user is not None and item.id in owned_ids(db, user, kind)


def require_access(db: Session, user: User, kind: str, item) -> None:
    if not can_access(db, user, kind, item):
        raise err(403, "PURCHASE_REQUIRED")


# ---------------- signed stream URLs ----------------


def signed_url(path: str, subject: UUID, user: User, what: str = "file") -> str:
    token = create_access_token({"sub": str(subject), "purpose": PURPOSE, "what": what, "user_id": str(user.id)},
                                expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES)
    return f"{path}?token={token}"


def read_token_any(db: Session, token: str, subject: UUID, whats: tuple[str, ...]) -> tuple[User, str]:
    """Like `read_token` for a token that may be one of several kinds (e.g. a book's "file" or "preview" token); returns (user, kind)."""
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise err(401, "Invalid or expired stream token") from None
    what = payload.get("what")
    if payload.get("purpose") != PURPOSE or payload.get("sub") != str(subject) or what not in whats:
        raise err(403, "Token does not authorize this file")
    try:
        user = db.get(User, UUID(payload.get("user_id", "")))
    except ValueError:
        user = None
    if user is None or not user.is_active:
        raise err(401, "Stream token user no longer exists")
    return user, what


def read_token(db: Session, token: str, subject: UUID, what: str = "file") -> User:
    return read_token_any(db, token, subject, (what,))[0]


# ---------------- public serialization (never a file key) ----------------


def cover_url(kind: str, item) -> str | None:
    if not getattr(item, "cover_key", None):
        return None
    return f"/api/v1/medien/cover/{kind}/{item.id}?v={int(item.updated_at.timestamp())}"


def discount_percent(item) -> int | None:
    if item.price and item.old_price and item.old_price > item.price:
        return round(100 * (item.old_price - item.price) / item.old_price)
    return None


def base_card(kind: str, item, owned: set | None = None, staff: bool = False) -> dict:
    has = staff or item.access_type != ACCESS_PAID or (owned is not None and item.id in owned)
    return {"id": item.id, "kind": kind, "title": item.title, "description": item.description, "cover_url": cover_url(kind, item),
            "language": item.language, "level": item.level, "access_type": item.access_type, "price": item.price,
            "old_price": item.old_price, "discount_percent": discount_percent(item), "is_special_offer": item.is_special_offer,
            "is_featured": item.is_featured, "owned": has, "locked": not has, "status": item.status, "currency": "UZS"}
