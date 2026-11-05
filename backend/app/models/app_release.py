"""VIZU DEUTSCH app releases (Android APK; the iOS app is a PWA and has no release file).

* One row per uploaded APK. The file lives in app/protected_storage/app-releases under a random name and is
  only ever streamed by the API (public download of the LATEST published release, admin download of any).
* status: draft (uploaded, not downloadable) → published → archived. Exactly one published row per platform
  may be `is_latest` (partial unique index); /downloads/android/latest.apk serves that row.
* version_code is Android's integer versionCode (also the build number); unique per platform and it must grow
  with every publish, otherwise installed apps refuse the update.
* download_count is a plain counter (no device or user data is stored)."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AppRelease(BaseModel):
    __tablename__ = "app_releases"
    __table_args__ = (
        UniqueConstraint("platform", "version_code", name="uq_app_releases_platform_version_code"),
        UniqueConstraint("storage_name", name="uq_app_releases_storage_name"),
        Index("uq_app_releases_latest_per_platform", "platform", unique=True, postgresql_where=text("is_latest")),
    )

    platform: Mapped[str] = mapped_column(String(20), nullable=False, default="android", server_default="android")
    version_name: Mapped[str] = mapped_column(String(40), nullable=False)
    version_code: Mapped[int] = mapped_column(Integer, nullable=False)
    min_android_version: Mapped[str] = mapped_column(String(20), nullable=False, default="7.0", server_default="7.0")
    release_notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    storage_name: Mapped[str] = mapped_column(String(80), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    signer_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
