from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging.logger import logger
from app.core.storage.factory import StorageFactory

from app.models.user import User
from app.models.video import Video

from app.repositories.enrollment import EnrollmentRepository
from app.repositories.lesson import LessonRepository
from app.repositories.video import VideoRepository
from app.services.vizu_pay.access import has_premium_bypass, is_free_lesson, is_user_premium


class VideoService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = VideoRepository(db)
        self.lessons = LessonRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.storage = StorageFactory.create(settings.STORAGE_PROVIDER)

    # ==========================
    # CRUD
    # ==========================

    def get_all(
        self,
    ) -> list[Video]:
        return self.repository.get_all()

    def get(
        self,
        video_id: UUID,
    ) -> Video | None:
        return self.repository.get(video_id)

    def get_by_lesson(
        self,
        lesson_id: UUID,
    ) -> list[Video]:
        return self.repository.get_by_lesson(lesson_id)

    def create(
        self,
        data,
    ) -> Video:
        return self.repository.create(data)

    def update(
        self,
        video: Video,
        data,
    ) -> Video:
        return self.repository.update(
            video,
            data,
        )

    def publish(
        self,
        video: Video,
    ) -> Video:
        return self.repository.publish(video)

    def unpublish(
        self,
        video: Video,
    ) -> Video:
        return self.repository.unpublish(video)

    async def delete(
        self,
        video: Video,
    ) -> None:
        """Deletes the video row and, if it has one, its backing storage
        object. Storage deletion happens first — if it fails we'd rather
        keep the (now possibly orphaned-file) DB row than lose the
        metadata needed to retry, than delete the row and leak storage
        forever."""

        if video.storage_key:
            await self.storage.delete(video.storage_key)

        if video.thumbnail_key:
            await self.storage.delete(video.thumbnail_key)

        self.repository.delete(video)

    # ==========================
    # Upload
    # ==========================

    async def upload_video(
        self,
        lesson_id: UUID,
        file: UploadFile,
        title: str,
        description: str | None,
        order_index: int,
        is_preview: bool,
        is_published: bool,
        thumbnail_url: str | None = None,
        thumbnail_file: UploadFile | None = None,
        duration_seconds: int = 0,
    ) -> Video:
        """Validates the lesson and the file, saves it via the configured
        storage backend, and persists the resulting storage_key. Raises
        NotFoundError if the lesson doesn't exist, HTTPException(400) for
        an invalid file."""

        lesson = self.lessons.get(str(lesson_id))

        if lesson is None:
            raise NotFoundError("Lesson not found")

        self._validate_upload(file)

        storage_key = await self._store_video_file(lesson_id, file)

        resolved_thumbnail_url = thumbnail_url
        thumbnail_key = None

        if thumbnail_file is not None:
            thumbnail_key = await self._store_thumbnail_file(
                lesson_id,
                thumbnail_file,
            )
            resolved_thumbnail_url = self.storage.url(thumbnail_key)

        video = Video(
            lesson_id=lesson_id,
            title=title,
            description=description,
            storage_key=storage_key,
            # Cached for the admin "Preview" action only — actual student
            # playback always recomputes this from storage_key via
            # get_playable_video(), so it stays correct even if
            # STORAGE_PROVIDER changes later.
            video_url=self.storage.url(storage_key),
            thumbnail_url=resolved_thumbnail_url,
            thumbnail_key=thumbnail_key,
            duration_seconds=duration_seconds,
            order_index=order_index,
            is_preview=is_preview,
            is_published=is_published,
        )

        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)

        return video

    async def replace_video(
        self,
        video: Video,
        file: UploadFile,
        duration_seconds: int | None = None,
    ) -> Video:
        """Swaps the backing file for an existing video row, keeping the
        same id/metadata. The old file is deleted after the new one is
        stored, so a failed upload never leaves the video without a
        playable file."""

        self._validate_upload(file)

        old_storage_key = video.storage_key

        video.storage_key = await self._store_video_file(
            video.lesson_id,
            file,
        )
        video.video_url = self.storage.url(video.storage_key)

        if duration_seconds is not None:
            video.duration_seconds = duration_seconds

        self.db.commit()
        self.db.refresh(video)

        if old_storage_key:
            await self.storage.delete(old_storage_key)

        return video

    async def _store_video_file(
        self,
        lesson_id: UUID,
        file: UploadFile,
    ) -> str:
        extension = Path(file.filename or "").suffix.lower() or ".mp4"
        storage_key = f"videos/{lesson_id}/{uuid4().hex}{extension}"

        logger.info(
            "Storing video: lesson_id=%s key=%s content_type=%s",
            lesson_id,
            storage_key,
            file.content_type,
        )

        await self.storage.upload(file, storage_key)

        return storage_key

    async def _store_thumbnail_file(
        self,
        lesson_id: UUID,
        file: UploadFile,
    ) -> str:
        extension = Path(file.filename or "").suffix.lower() or ".jpg"
        thumbnail_key = f"videos/thumbnails/{lesson_id}/{uuid4().hex}{extension}"

        await self.storage.upload(file, thumbnail_key)

        return thumbnail_key

    def _validate_upload(
        self,
        file: UploadFile,
    ) -> None:
        allowed_types = {
            content_type.strip()
            for content_type in settings.VIDEO_ALLOWED_CONTENT_TYPES.split(",")
            if content_type.strip()
        }

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported video type '{file.content_type}'. "
                    f"Allowed: {', '.join(sorted(allowed_types))}"
                ),
            )

        max_bytes = settings.VIDEO_MAX_UPLOAD_SIZE_MB * 1024 * 1024

        # UploadFile.size is populated by Starlette from the spooled temp
        # file once the upload completes; if a given ASGI server doesn't
        # provide it, we skip the check rather than buffer the whole file
        # into memory just to measure it.
        if file.size is not None and file.size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Video exceeds the maximum upload size of "
                    f"{settings.VIDEO_MAX_UPLOAD_SIZE_MB}MB"
                ),
            )

    # ==========================
    # Secure Streaming
    # ==========================

    def get_lesson_playback(
        self,
        lesson_id: UUID,
        user: User,
    ) -> tuple[Video, str]:
        """The lesson's primary (first, published) video plus a playable
        URL — what the student-facing "video for this lesson" endpoint
        returns."""

        video = self.repository.get_primary_for_lesson(lesson_id)

        if video is None:
            raise NotFoundError("Video not found")

        playable = self.get_playable_video(video.id, user)

        return playable, self.storage.url(playable.storage_key)

    def generate_streaming_url(
        self,
        video_id: UUID,
        user: User,
    ) -> tuple[Video, str]:
        """The single gate a student's playback request has to pass:
        video must exist, be published, have a stored file, and the
        requesting user must either be watching a free preview, hold an
        active premium subscription, or be enrolled in the video's
        course. Returns the video plus a URL served by the configured
        storage backend (a local /uploads/... path today; swapping
        STORAGE_PROVIDER to a remote backend later changes nothing
        here)."""

        video = self.get_playable_video(video_id, user)

        return video, self.storage.url(video.storage_key)

    def get_playable_video(
        self,
        video_id: UUID,
        user: User,
    ) -> Video:
        video = self.repository.get(video_id)

        if video is None or not video.is_published:
            raise NotFoundError("Video not found")

        if not video.storage_key:
            raise NotFoundError("Video not found")

        if not video.is_preview:
            self._require_access(video, user)

        if not (Path("uploads") / video.storage_key).exists():
            logger.error(
                "Stored file missing for published video: video_id=%s key=%s",
                video_id,
                video.storage_key,
            )
            raise NotFoundError("Video not found")

        return video

    def _require_access(
        self,
        video: Video,
        user: User,
    ) -> None:
        if has_premium_bypass(user) or is_user_premium(user):
            return

        # The level's first 3 lessons are free regardless of premium
        # status — same rule as every other lesson-content endpoint (see
        # app.services.vizu_pay.access.can_access_lesson).
        lesson = self.lessons.get(str(video.lesson_id))

        if lesson is not None and is_free_lesson(lesson):
            return

        course_id = self.repository.get_course_id(video.id)

        if course_id and self.enrollments.has_active_enrollment(
            str(user.id),
            str(course_id),
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PREMIUM_REQUIRED",
        )
