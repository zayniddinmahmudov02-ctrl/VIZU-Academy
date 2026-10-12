"""VIZU LMS learning resources: audio, PDF, image, document files and links.

Files are checked by their content (magic bytes) AND the declared type, stored
under protected storage as "<lesson_id>/<uuid>.<ext>", and never deleted while
another row still points at the same key."""

import re
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.storage.protected_local import ProtectedLmsResourceStorage
from app.models.lesson import Lesson
from app.models.lms import COMPETENCY_ORDER, RESOURCE_TYPES, LearningResource

storage = ProtectedLmsResourceStorage()

MB = 1024 * 1024
MAX_BYTES = {"AUDIO": 200 * MB, "PDF": 50 * MB, "IMAGE": 10 * MB, "DOCUMENT": 30 * MB}

# extension -> (mime type, accepted declared types)
FORMATS: dict[str, dict[str, tuple[str, set[str]]]] = {
    "AUDIO": {
        "mp3": ("audio/mpeg", {"audio/mpeg", "audio/mp3"}),
        "wav": ("audio/wav", {"audio/wav", "audio/x-wav", "audio/wave"}),
        "m4a": ("audio/mp4", {"audio/mp4", "audio/x-m4a", "audio/m4a", "audio/aac"}),
        "ogg": ("audio/ogg", {"audio/ogg", "application/ogg"}),
    },
    "PDF": {"pdf": ("application/pdf", {"application/pdf"})},
    "IMAGE": {
        "png": ("image/png", {"image/png"}),
        "jpg": ("image/jpeg", {"image/jpeg", "image/jpg"}),
        "webp": ("image/webp", {"image/webp"}),
        "gif": ("image/gif", {"image/gif"}),
    },
    "DOCUMENT": {
        "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
        "pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation",
                 {"application/vnd.openxmlformats-officedocument.presentationml.presentation"}),
        "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}),
        "odt": ("application/vnd.oasis.opendocument.text", {"application/vnd.oasis.opendocument.text"}),
    },
}
ZIP_DOCUMENTS = {"docx", "pptx", "xlsx", "odt"}
URL_RE = re.compile(r"^https://[^\s]{4,990}$")


def _detect(resource_type: str, head: bytes, filename: str) -> str | None:
    ext = Path(filename or "").suffix.lower().lstrip(".")
    if resource_type == "AUDIO":
        if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
            return "mp3"
        if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
            return "wav"
        if head[4:8] == b"ftyp":
            return "m4a"
        if head[:4] == b"OggS":
            return "ogg"
    elif resource_type == "PDF":
        if head[:5] == b"%PDF-":
            return "pdf"
    elif resource_type == "IMAGE":
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        if head[:3] == b"\xff\xd8\xff":
            return "jpg"
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return "webp"
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return "gif"
    elif resource_type == "DOCUMENT":
        if head[:4] == b"PK\x03\x04" and ext in ZIP_DOCUMENTS:
            return ext
    return None


def validate_competency(competency: str | None) -> str | None:
    if competency in (None, ""):
        return None
    value = competency.strip().upper()
    if value not in COMPETENCY_ORDER:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="UNKNOWN_COMPETENCY")
    return value


def validate_type(resource_type: str) -> str:
    value = (resource_type or "").strip().upper()
    if value not in RESOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="UNKNOWN_RESOURCE_TYPE")
    return value


def _next_order(db: Session, lesson_id: UUID, competency: str | None) -> int:
    q = select(func.max(LearningResource.order_index)).where(LearningResource.lesson_id == lesson_id)
    q = q.where(LearningResource.competency.is_(None) if competency is None else LearningResource.competency == competency)
    return (db.scalar(q) or 0) + 1


async def _store(lesson_id: UUID, resource_type: str, file: UploadFile) -> dict:
    declared = (file.content_type or "").split(";")[0].strip().lower()
    head = await file.read(16)
    await file.seek(0)
    ext = _detect(resource_type, head, file.filename or "")
    if ext is None or declared not in FORMATS[resource_type][ext][1]:
        allowed = ", ".join(e.upper() for e in FORMATS[resource_type])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"UNSUPPORTED_FILE: {resource_type} allows {allowed}")
    key = f"{lesson_id}/{uuid4().hex}.{ext}"
    try:
        await storage.upload(file, key, max_bytes=MAX_BYTES[resource_type])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"FILE_TOO_LARGE: max {MAX_BYTES[resource_type] // MB} MB"
        ) from None
    return {
        "storage_key": key,
        "mime_type": FORMATS[resource_type][ext][0],
        "size_bytes": (storage.ROOT / key).stat().st_size,
        "original_filename": (file.filename or "")[:255] or None,
    }


def _clean_duration(value: int | None) -> int | None:
    return value if value and 0 < value < 24 * 3600 else None


async def create_file_resource(
    db: Session, lesson: Lesson, *, resource_type: str, file: UploadFile, title: str, competency: str | None,
    description: str | None, duration_seconds: int | None, actor_id,
) -> LearningResource:
    resource_type = validate_type(resource_type)
    if resource_type == "LINK":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="LINK_HAS_NO_FILE")
    competency = validate_competency(competency)
    stored = await _store(lesson.id, resource_type, file)
    resource = LearningResource(
        lesson_id=lesson.id, competency=competency, resource_type=resource_type, title=title.strip()[:255],
        description=(description or "").strip() or None, duration_seconds=_clean_duration(duration_seconds),
        order_index=_next_order(db, lesson.id, competency), is_published=False, created_by=actor_id, **stored,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def create_link_resource(
    db: Session, lesson: Lesson, *, url: str, title: str, competency: str | None, description: str | None, actor_id
) -> LearningResource:
    url = (url or "").strip()
    if not URL_RE.match(url):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="INVALID_URL: https:// links only")
    competency = validate_competency(competency)
    resource = LearningResource(
        lesson_id=lesson.id, competency=competency, resource_type="LINK", title=title.strip()[:255],
        description=(description or "").strip() or None, external_url=url,
        order_index=_next_order(db, lesson.id, competency), is_published=False, created_by=actor_id,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def _key_in_use_elsewhere(db: Session, key: str, resource_id: UUID) -> bool:
    return db.scalar(select(func.count()).select_from(LearningResource).where(LearningResource.storage_key == key, LearningResource.id != resource_id)) > 0


async def _delete_file_if_unused(db: Session, key: str | None, resource_id: UUID) -> bool:
    if not key or _key_in_use_elsewhere(db, key, resource_id):
        return False
    await storage.delete(key)
    return True


async def replace_file(db: Session, resource: LearningResource, file: UploadFile, duration_seconds: int | None) -> LearningResource:
    if resource.resource_type == "LINK":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="LINK_HAS_NO_FILE")
    stored = await _store(resource.lesson_id, resource.resource_type, file)
    old_key = resource.storage_key
    for k, v in stored.items():
        setattr(resource, k, v)
    if duration_seconds is not None:
        resource.duration_seconds = _clean_duration(duration_seconds)
    db.commit()
    await _delete_file_if_unused(db, old_key, resource.id)
    db.refresh(resource)
    return resource


async def delete_resource(db: Session, resource: LearningResource) -> None:
    key, rid = resource.storage_key, resource.id
    db.delete(resource)
    db.commit()
    await _delete_file_if_unused(db, key, rid)


def file_path(resource: LearningResource) -> Path | None:
    """Absolute path of the resource file inside the storage root (None for
    links, a key escaping the root, or a missing file)."""
    if not resource.storage_key:
        return None
    root = storage.ROOT.resolve()
    path = (storage.ROOT / resource.storage_key).resolve()
    if root not in path.parents or not path.is_file():
        return None
    return path


def serialize(resource: LearningResource, *, admin: bool = False) -> dict:
    out = {
        "id": resource.id,
        "lesson_id": resource.lesson_id,
        "competency": resource.competency,
        "resource_type": resource.resource_type,
        "title": resource.title,
        "description": resource.description,
        "mime_type": resource.mime_type,
        "size_bytes": resource.size_bytes,
        "duration_seconds": resource.duration_seconds,
        "order_index": resource.order_index,
        "external_url": resource.external_url,
        "file_url": f"/api/v1/lms/resources/{resource.id}/file" if resource.storage_key else None,
    }
    if admin:
        path = file_path(resource)
        out.update(
            {
                "is_published": resource.is_published,
                "original_filename": resource.original_filename,
                "storage_key": resource.storage_key,
                "file_status": None if resource.resource_type == "LINK" else ("ok" if path else "missing"),
                "preview_url": f"/api/v1/admin/lms/resources/{resource.id}/file" if resource.storage_key else None,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            }
        )
    return out


def lesson_resources(db: Session, lesson_id: UUID, *, published_only: bool) -> list[LearningResource]:
    q = select(LearningResource).where(LearningResource.lesson_id == lesson_id)
    if published_only:
        q = q.where(LearningResource.is_published.is_(True))
    rows = list(db.scalars(q))
    order = {k: i for i, k in enumerate(COMPETENCY_ORDER)}
    return sorted(rows, key=lambda r: (order.get(r.competency, -1), r.order_index, r.created_at))
