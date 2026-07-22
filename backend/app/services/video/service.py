from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging.logger import logger
from app.core.storage.r2 import get_r2_client

from app.models.user import User
from app.models.video import Video

from app.repositories.enrollment import EnrollmentRepository
from app.repositories.lesson import LessonRepository
from app.repositories.video import VideoRepository


class VideoService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = VideoRepository(db)
        self.lessons = LessonRepository(db)
        self.enrollments = EnrollmentRepository(db)
        self.r2 = get_r2_client()

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

    def delete(
        self,
        video: Video,
    ) -> None:
        """Deletes the video row and, if it has one, its backing R2
        object. R2 deletion happens first — if it fails we'd rather keep
        the (now possibly orphaned-file) DB row than lose the metadata
        needed to retry, than delete the row and leak storage forever."""

        if video.storage_key:
            self.r2.delete_file(video.storage_key)

        self.repository.delete(video)

    # ==========================
    # R2 Upload
    # ==========================

    def upload_video(
        self,
        lesson_id: UUID,
        file: UploadFile,
        title: str,
        description: str | None,
        order_index: int,
        is_preview: bool,
        is_published: bool,
        thumbnail_url: str | None = None,
    ) -> Video:
        """Validates the lesson and the file, streams it to R2, and
        persists the resulting storage_key. Raises NotFoundError if the
        lesson doesn't exist, HTTPException(400) for an invalid file."""

        lesson = self.lessons.get(str(lesson_id))

        if lesson is None:
            raise NotFoundError("Lesson not found")

        self._validate_upload(file)

        extension = Path(file.filename or "").suffix.lower() or ".mp4"
        storage_key = f"videos/{lesson_id}/{uuid4().hex}{extension}"

        logger.info(
            "Uploading video to R2: lesson_id=%s key=%s content_type=%s",
            lesson_id,
            storage_key,
            file.content_type,
        )

        self.r2.upload_file(
            file.file,
            storage_key,
            content_type=file.content_type,
        )

        video = Video(
            lesson_id=lesson_id,
            title=title,
            description=description,
            storage_key=storage_key,
            thumbnail_url=thumbnail_url,
            order_index=order_index,
            is_preview=is_preview,
            is_published=is_published,
        )

        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)

        return video

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

    def generate_streaming_url(
        self,
        video_id: UUID,
        user: User,
    ) -> str:
        """The single gate a student's playback request has to pass:
        video must exist, be published, have a stored file, and the
        requesting user must either be watching a free preview, hold an
        active premium subscription, or be enrolled in the video's
        course. Returns a presigned R2 URL, valid for
        settings.R2_SIGNED_URL_EXPIRE_SECONDS."""

        video = self.repository.get(video_id)

        if video is None or not video.is_published:
            raise NotFoundError("Video not found")

        if not video.storage_key:
            raise NotFoundError("Video not found")

        if not video.is_preview:
            self._require_access(video, user)

        if not self.r2.object_exists(video.storage_key):
            logger.error(
                "R2 object missing for published video: video_id=%s key=%s",
                video_id,
                video.storage_key,
            )
            raise NotFoundError("Video not found")

        return self.r2.generate_signed_url(video.storage_key)

    def _require_access(
        self,
        video: Video,
        user: User,
    ) -> None:
        now = datetime.now(UTC)

        is_premium = bool(
            user.premium_until and user.premium_until > now
        )

        if is_premium:
            return

        course_id = self.repository.get_course_id(video.id)

        if course_id and self.enrollments.has_active_enrollment(
            str(user.id),
            str(course_id),
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An active enrollment or premium subscription is required to watch this video",
        )
