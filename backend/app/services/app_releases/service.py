"""VIZU DEUTSCH app release management (Android APK). See docs/ai-context/apk-release-management.md.

Rules
* Upload (Super Admin): .apk, ≤ MAX_APK_BYTES, a real signed APK of package ANDROID_PACKAGE. Version code /
  name / min SDK are READ FROM THE APK (form fields cannot lie). Debug-signed APKs are refused. Every APK must be
  signed with the same certificate as the releases before it (a new key would break updates for every user).
  A new upload is a draft: not downloadable.
* Publish: the version code must be higher than the current latest; the release becomes the only `is_latest`.
* Archive: no longer downloadable (if it was latest, no APK is offered until another one is published).
  Delete is only for drafts (file removed). Published history is archived, never deleted.
* Public: metadata of the latest release + the APK stream (`application/vnd.android.package-archive`,
  attachment, no-cache) with a plain download counter. No user or device data is stored."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import qrcode
import qrcode.image.svg
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.storage.protected_local import ProtectedAppReleaseStorage
from app.models.app_release import AppRelease
from app.models.user import User
from app.services.app_releases.apk import ANDROID_VERSIONS, ApkError, inspect_apk

ANDROID_PACKAGE = "com.vizu.deutsch"
MAX_APK_BYTES = 150 * 1024 * 1024
ALLOWED_MIME = {"application/vnd.android.package-archive", "application/octet-stream", "application/zip",
                "application/x-zip-compressed", ""}
APK_MEDIA_TYPE = "application/vnd.android.package-archive"
storage = ProtectedAppReleaseStorage()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _path(release: AppRelease) -> Path:
    return storage._inside_root(release.storage_name)


def android_version(min_sdk: int | None) -> str:
    return ANDROID_VERSIONS.get(min_sdk or 24, f"API {min_sdk}")


def public_view(r: AppRelease) -> dict:
    return {
        "platform": r.platform, "version_name": r.version_name, "version_code": r.version_code,
        "min_android_version": r.min_android_version, "release_notes": r.release_notes, "size_bytes": r.size_bytes,
        "sha256": r.sha256, "published_at": r.published_at,
        "download_url": f"{settings.API_V1_PREFIX}/app/android/latest.apk", "page_url": "/download",
    }


def admin_view(r: AppRelease) -> dict:
    return {**public_view(r), "id": str(r.id), "status": r.status, "is_latest": r.is_latest, "original_name": r.original_name,
            "signer_sha256": r.signer_sha256, "download_count": r.download_count, "created_at": r.created_at,
            "archived_at": r.archived_at}


def latest(db: Session, platform: str = "android") -> AppRelease | None:
    return db.scalar(select(AppRelease).where(AppRelease.platform == platform, AppRelease.is_latest.is_(True),
                                              AppRelease.status == "published"))


def latest_or_404(db: Session) -> AppRelease:
    release = latest(db)
    if release is None or not _path(release).is_file():
        raise HTTPException(status_code=404, detail="NO_APP_RELEASE")
    return release


def register_download(db: Session, release: AppRelease) -> Path:
    db.execute(update(AppRelease).where(AppRelease.id == release.id).values(download_count=AppRelease.download_count + 1))
    db.commit()
    return _path(release)


def download_filename(release: AppRelease) -> str:
    return f"VIZU-DEUTSCH-{release.version_name}.apk"


def qr_svg(url: str | None = None) -> str:
    img = qrcode.make(url or f"{settings.PUBLIC_SITE_URL.rstrip('/')}/download", image_factory=qrcode.image.svg.SvgPathImage,
                      box_size=10, border=2)
    return img.to_string(encoding="unicode")


# ── admin ────────────────────────────────────────────────────────────────────


def list_releases(db: Session) -> dict:
    rows = db.scalars(select(AppRelease).order_by(AppRelease.version_code.desc())).all()
    current = next((r for r in rows if r.is_latest), None)
    return {
        "releases": [admin_view(r) for r in rows],
        "overview": {
            "latest": admin_view(current) if current else None,
            "total_downloads": sum(r.download_count for r in rows),
            "published": sum(1 for r in rows if r.status == "published"),
            "drafts": sum(1 for r in rows if r.status == "draft"),
            "archived": sum(1 for r in rows if r.status == "archived"),
            "package": ANDROID_PACKAGE,
        },
    }


def _get(db: Session, release_id: UUID) -> AppRelease:
    release = db.get(AppRelease, release_id)
    if release is None:
        raise HTTPException(status_code=404, detail="APP_RELEASE_NOT_FOUND")
    return release


async def upload(db: Session, actor: User, file: UploadFile, release_notes: str) -> dict:
    name = (file.filename or "").strip()
    if not name.lower().endswith(".apk"):
        raise HTTPException(status_code=400, detail="APK_EXTENSION: only .apk files")
    if (file.content_type or "").lower() not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="APK_MIME_TYPE")
    storage_name = f"{uuid4().hex}.apk"
    try:
        await storage.upload(file, storage_name, max_bytes=MAX_APK_BYTES)
    except ValueError:
        raise HTTPException(status_code=413, detail=f"APK_TOO_LARGE: max {MAX_APK_BYTES // (1024 * 1024)} MB")
    path = storage._inside_root(storage_name)
    try:
        info = inspect_apk(path)
        if info.package != ANDROID_PACKAGE:
            raise ApkError("APK_WRONG_PACKAGE")
        if info.debug_signed:
            raise ApkError("APK_DEBUG_SIGNED")
        signers = set(db.scalars(select(AppRelease.signer_sha256).where(AppRelease.signer_sha256.is_not(None),
                                                                       AppRelease.status != "draft")).all())
        if signers and info.signer_sha256 not in signers:
            raise ApkError("APK_SIGNER_MISMATCH")
        if db.scalar(select(AppRelease.id).where(AppRelease.platform == "android", AppRelease.version_code == info.version_code)):
            raise ApkError("APK_VERSION_EXISTS")
    except ApkError as e:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=e.code)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    release = AppRelease(
        platform="android", version_name=info.version_name, version_code=info.version_code,
        min_android_version=android_version(info.min_sdk), release_notes=(release_notes or "").strip()[:5000],
        status="draft", is_latest=False, storage_name=storage_name, original_name=name[:255], size_bytes=info.size_bytes,
        sha256=info.sha256, signer_sha256=info.signer_sha256, created_by=actor.id,
    )
    db.add(release)
    db.flush()
    write_audit(db, str(actor.id), "APP_RELEASE_UPLOAD", details=f"android {info.version_name} ({info.version_code}) sha256={info.sha256}")
    db.commit()
    db.refresh(release)
    return admin_view(release)


def update_notes(db: Session, actor: User, release_id: UUID, release_notes: str) -> dict:
    release = _get(db, release_id)
    release.release_notes = (release_notes or "").strip()[:5000]
    write_audit(db, str(actor.id), "APP_RELEASE_NOTES", details=f"android {release.version_name}")
    db.commit()
    db.refresh(release)
    return admin_view(release)


def publish(db: Session, actor: User, release_id: UUID) -> dict:
    release = _get(db, release_id)
    if release.status == "archived":
        raise HTTPException(status_code=409, detail="APP_RELEASE_ARCHIVED")
    if not _path(release).is_file():
        raise HTTPException(status_code=409, detail="APP_RELEASE_FILE_MISSING")
    current = latest(db, release.platform)
    if current is not None and current.id != release.id and release.version_code <= current.version_code:
        raise HTTPException(status_code=409, detail="VERSION_CODE_NOT_NEWER")
    if current is not None and current.id != release.id:
        current.is_latest = False
        db.flush()
    release.status, release.is_latest = "published", True
    release.published_at = release.published_at or _now()
    write_audit(db, str(actor.id), "APP_RELEASE_PUBLISH", details=f"android {release.version_name} ({release.version_code})")
    db.commit()
    db.refresh(release)
    return admin_view(release)


def archive(db: Session, actor: User, release_id: UUID) -> dict:
    release = _get(db, release_id)
    if release.status == "draft":
        raise HTTPException(status_code=409, detail="APP_RELEASE_DRAFT: delete drafts instead")
    release.status, release.is_latest, release.archived_at = "archived", False, _now()
    write_audit(db, str(actor.id), "APP_RELEASE_ARCHIVE", details=f"android {release.version_name} ({release.version_code})")
    db.commit()
    db.refresh(release)
    return admin_view(release)


def delete_draft(db: Session, actor: User, release_id: UUID) -> None:
    release = _get(db, release_id)
    if release.status != "draft":
        raise HTTPException(status_code=409, detail="APP_RELEASE_NOT_DRAFT: archive published releases")
    path = _path(release)
    write_audit(db, str(actor.id), "APP_RELEASE_DELETE_DRAFT", details=f"android {release.version_name} ({release.version_code})")
    db.delete(release)
    db.commit()
    path.unlink(missing_ok=True)


def admin_file(db: Session, release_id: UUID) -> tuple[Path, AppRelease]:
    release = _get(db, release_id)
    path = _path(release)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="APP_RELEASE_FILE_MISSING")
    return path, release
