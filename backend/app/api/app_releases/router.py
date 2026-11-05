"""VIZU DEUTSCH mobile app API (Android APK releases; iOS is a PWA).

Public, no login (the download page is public and carries no user data):
* GET /app/releases/latest        metadata of the latest published Android release (404 NO_APP_RELEASE if none)
* GET /app/android/latest.apk     the APK itself (attachment, application/vnd.android.package-archive, no-cache)
* GET /app/download-qr.svg        QR code of the public /download page

Admin (/admin/app-releases): Super Admin only, read and write (require_super_admin)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.services.app_releases import service

router = APIRouter(prefix="/app", tags=["Mobile App"])
admin_router = APIRouter(prefix="/admin/app-releases", tags=["Admin App Management"])


class NotesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    release_notes: str = Field(default="", max_length=5000)


@router.get("/releases/latest")
def latest_release(db: Session = Depends(get_db)):
    return service.public_view(service.latest_or_404(db))


@router.get("/android/latest.apk")
def latest_apk(db: Session = Depends(get_db)):
    release = service.latest_or_404(db)
    path = service.register_download(db, release)
    return FileResponse(path, media_type=service.APK_MEDIA_TYPE, filename=service.download_filename(release),
                        headers={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff",
                                 "X-APK-SHA256": release.sha256, "X-APK-Version": release.version_name})


@router.get("/download-qr.svg")
def download_qr():
    return Response(service.qr_svg(), media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


# ── admin ────────────────────────────────────────────────────────────────────


@admin_router.get("")
def list_releases(db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    return service.list_releases(db)


@admin_router.post("", status_code=201)
async def upload_release(file: UploadFile = File(...), release_notes: str = Form(default="", max_length=5000),
                         db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    return await service.upload(db, user, file, release_notes)


@admin_router.patch("/{release_id}")
def update_release(release_id: UUID, body: NotesIn, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    return service.update_notes(db, user, release_id, body.release_notes)


@admin_router.post("/{release_id}/publish")
def publish_release(release_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    return service.publish(db, user, release_id)


@admin_router.post("/{release_id}/archive")
def archive_release(release_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    return service.archive(db, user, release_id)


@admin_router.delete("/{release_id}", status_code=204)
def delete_release(release_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    service.delete_draft(db, user, release_id)
    return Response(status_code=204)


@admin_router.get("/{release_id}/file")
def release_file(release_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    path, release = service.admin_file(db, release_id)
    return FileResponse(path, media_type=service.APK_MEDIA_TYPE, filename=service.download_filename(release),
                        headers={"Cache-Control": "private, no-store"})
