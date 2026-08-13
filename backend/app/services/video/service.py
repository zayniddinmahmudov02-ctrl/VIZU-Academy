import asyncio
import math
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging.logger import logger
from app.core.security.jwt import create_video_stream_token
from app.core.storage.factory import StorageFactory
from app.core.storage.protected_local import (
    ProtectedVideoStorage,
    ProtectedVideoUploadTempStorage,
)

from app.models.user import User
from app.models.video import Video
from app.models.video_upload_session import VideoUploadSession

from app.repositories.enrollment import EnrollmentRepository
from app.repositories.lesson import LessonRepository
from app.repositories.video import VideoRepository
from app.services.vizu_pay.access import has_premium_bypass, is_free_lesson, is_user_premium

# Bounds RAM while re-assembling chunks into the final file in
# complete_upload(), independent of LocalStorage.CHUNK_SIZE.
_ASSEMBLE_READ_SIZE = 1024 * 1024


class VideoService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = VideoRepository(db)
        self.lessons = LessonRepository(db)
        self.enrollments = EnrollmentRepository(db)
        # Thumbnails stay on the public storage backend (self.storage) —
        # only the video file itself needs to be unreachable by a bare URL.
        self.storage = StorageFactory.create(settings.STORAGE_PROVIDER)
        self.video_storage = ProtectedVideoStorage()
        self.upload_temp_storage = ProtectedVideoUploadTempStorage()

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
            await self.video_storage.delete(video.storage_key)

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

        return self._finalize_new_video(
            lesson_id=lesson_id,
            storage_key=storage_key,
            title=title,
            description=description,
            duration_seconds=duration_seconds,
            order_index=order_index,
            is_preview=is_preview,
            is_published=is_published,
            thumbnail_url=resolved_thumbnail_url,
            thumbnail_key=thumbnail_key,
        )

    def _finalize_new_video(
        self,
        lesson_id: UUID,
        storage_key: str,
        title: str,
        description: str | None,
        duration_seconds: int,
        order_index: int,
        is_preview: bool,
        is_published: bool,
        thumbnail_url: str | None = None,
        thumbnail_key: str | None = None,
    ) -> Video:
        """Inserts the Video row for an already-stored file. Shared by
        upload_video() (single-shot multipart) and complete_upload()
        (chunked) — everything above this point differs in how the bytes
        reached storage_key; nothing below it does."""

        # Generated up front (instead of left to the id column's default=)
        # so it's available immediately below — video_url needs it to
        # build a signed streaming URL before the row is ever inserted.
        video_id = uuid4()

        video = Video(
            id=video_id,
            lesson_id=lesson_id,
            title=title,
            description=description,
            storage_key=storage_key,
            # Cached for the admin "Preview" action only — actual student
            # playback always recomputes this from storage_key via
            # get_playable_video(), so it stays correct even if
            # STORAGE_PROVIDER changes later. A fresh signed URL, not a
            # bare storage path — the file lives in protected storage now.
            video_url=self._stream_url(video_id),
            thumbnail_url=thumbnail_url,
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

        storage_key = await self._store_video_file(
            video.lesson_id,
            file,
        )

        return await self._finalize_replace(video, storage_key, duration_seconds)

    async def _finalize_replace(
        self,
        video: Video,
        storage_key: str,
        duration_seconds: int | None,
    ) -> Video:
        """Swaps in an already-stored replacement file. Shared by
        replace_video() (single-shot) and complete_upload() (chunked,
        when the session carries a replace_video_id)."""

        old_storage_key = video.storage_key

        video.storage_key = storage_key
        video.video_url = self._stream_url(video.id)

        if duration_seconds is not None:
            video.duration_seconds = duration_seconds

        self.db.commit()
        self.db.refresh(video)

        if old_storage_key:
            await self.video_storage.delete(old_storage_key)

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

        await self.video_storage.upload(file, storage_key)

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
        self._validate_content_type(file.content_type)

        # UploadFile.size is populated by Starlette from the spooled temp
        # file once the upload completes; if a given ASGI server doesn't
        # provide it, we skip the check rather than buffer the whole file
        # into memory just to measure it.
        if file.size is not None:
            self._validate_total_size(file.size)

    def _validate_content_type(self, content_type: str | None) -> None:
        allowed_types = {
            t.strip()
            for t in settings.VIDEO_ALLOWED_CONTENT_TYPES.split(",")
            if t.strip()
        }

        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported video type '{content_type}'. "
                    f"Allowed: {', '.join(sorted(allowed_types))}"
                ),
            )

    def _validate_total_size(self, size_bytes: int) -> None:
        max_bytes = settings.VIDEO_MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if size_bytes > max_bytes:
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

        return playable, self._stream_url(playable.id)

    def generate_streaming_url(
        self,
        video_id: UUID,
        user: User,
    ) -> tuple[Video, str]:
        """The single gate a student's playback request has to pass:
        video must exist, be published, have a stored file, and the
        requesting user must either be watching a free preview, hold an
        active premium subscription, or be enrolled in the video's
        course. Returns the video plus a short-lived signed URL pointing
        at GET /videos/{id}/stream — never a bare storage path, since the
        file lives in protected storage and isn't reachable any other
        way."""

        video = self.get_playable_video(video_id, user)

        return video, self._stream_url(video.id)

    def _stream_url(self, video_id: "UUID | str") -> str:
        token = create_video_stream_token(str(video_id))
        return f"/api/v1/videos/{video_id}/stream?token={token}"

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

        if not (self.video_storage.ROOT / video.storage_key).exists():
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

    def resolve_video_path(self, video: Video) -> Path:
        """Where GET /videos/{id}/stream reads bytes from, once the
        caller's token has already proven authorization."""

        return self.video_storage.ROOT / video.storage_key

    # ==========================
    # Chunked Upload
    # ==========================
    #
    # Works around the edge proxy (Cloudflare) rejecting any single
    # request above ~50-99MB with a 413 before it ever reaches this
    # server (confirmed live) — a real lesson video averaging ~1.5GB can
    # never go through the single-shot upload_video()/replace_video()
    # path above in production. The client instead: POSTs metadata to
    # /init (returns upload_id + the chunk size to slice by), PUTs each
    # slice to /chunk, then POSTs /complete once every slice has landed.
    # Reuses _finalize_new_video/_finalize_replace above so the resulting
    # Video row is byte-for-byte the same shape either upload path
    # produces.

    def init_upload_session(
        self,
        admin: User,
        lesson_id: UUID,
        title: str,
        description: str | None,
        duration_seconds: int,
        order_index: int,
        is_preview: bool,
        is_published: bool,
        filename: str,
        content_type: str,
        total_size_bytes: int,
        replace_video_id: UUID | None = None,
    ) -> VideoUploadSession:
        self.cleanup_stale_upload_sessions()

        lesson = self.lessons.get(str(lesson_id))

        if lesson is None:
            raise NotFoundError("Lesson not found")

        self._validate_content_type(content_type)
        self._validate_total_size(total_size_bytes)

        if replace_video_id is not None and self.repository.get(replace_video_id) is None:
            raise NotFoundError("Video to replace not found")

        extension = Path(filename or "").suffix.lower() or ".mp4"
        chunk_size_bytes = settings.VIDEO_UPLOAD_CHUNK_SIZE_MB * 1024 * 1024
        total_chunks = max(1, math.ceil(total_size_bytes / chunk_size_bytes))

        session = VideoUploadSession(
            admin_id=admin.id,
            lesson_id=lesson_id,
            replace_video_id=replace_video_id,
            title=title,
            description=description,
            duration_seconds=duration_seconds,
            order_index=order_index,
            is_preview=is_preview,
            is_published=is_published,
            extension=extension,
            content_type=content_type,
            total_size_bytes=total_size_bytes,
            total_chunks=total_chunks,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_owned_upload_session(
        self,
        upload_id: UUID,
        admin: User,
    ) -> VideoUploadSession:
        session = self.db.get(VideoUploadSession, upload_id)

        if session is None:
            raise NotFoundError("Upload session not found")

        # A stray/leaked upload_id must not let a different admin resume,
        # inspect, or finalize someone else's in-progress upload.
        if session.admin_id != admin.id and admin.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This upload session belongs to a different admin",
            )

        return session

    async def save_chunk(
        self,
        session: VideoUploadSession,
        chunk_number: int,
        total_chunks: int,
        file: UploadFile,
    ) -> int:
        """Returns the number of chunks uploaded so far (including this
        one) for the caller to report in its response."""

        if total_chunks != session.total_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="total_chunks does not match this upload session",
            )

        if chunk_number < 0 or chunk_number >= session.total_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"chunk_number must be between 0 and {session.total_chunks - 1}",
            )

        chunk_size_bytes = settings.VIDEO_UPLOAD_CHUNK_SIZE_MB * 1024 * 1024

        try:
            await self.upload_temp_storage.upload(
                file,
                self._chunk_key(session.id, chunk_number),
                max_bytes=chunk_size_bytes,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return len(self._uploaded_chunk_numbers(session))

    def get_upload_status(self, session: VideoUploadSession) -> dict:
        uploaded = self._uploaded_chunk_numbers(session)

        return {
            "upload_id": session.id,
            "total_chunks": session.total_chunks,
            "uploaded_chunks": uploaded,
            "is_ready_to_complete": uploaded == list(range(session.total_chunks)),
        }

    async def complete_upload(self, session: VideoUploadSession) -> Video:
        uploaded = self._uploaded_chunk_numbers(session)
        expected = list(range(session.total_chunks))

        if uploaded != expected:
            missing = sorted(set(expected) - set(uploaded))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Missing chunks: {missing}" if missing
                    else "Uploaded chunks are duplicated or out of order"
                ),
            )

        storage_key = f"videos/{session.lesson_id}/{uuid4().hex}{session.extension}"
        destination = self.video_storage.ROOT / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)

        assembled_bytes = await self._assemble_chunks(session, destination)

        if assembled_bytes != session.total_size_bytes:
            destination.unlink(missing_ok=True)
            self._delete_upload_temp_dir(session.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Assembled file is {assembled_bytes} bytes, "
                    f"expected {session.total_size_bytes}"
                ),
            )

        if session.replace_video_id is not None:
            video = self.repository.get(session.replace_video_id)

            if video is None:
                destination.unlink(missing_ok=True)
                self._delete_upload_temp_dir(session.id)
                raise NotFoundError("Video to replace no longer exists")

            result = await self._finalize_replace(video, storage_key, session.duration_seconds)
        else:
            result = self._finalize_new_video(
                lesson_id=session.lesson_id,
                storage_key=storage_key,
                title=session.title,
                description=session.description,
                duration_seconds=session.duration_seconds,
                order_index=session.order_index,
                is_preview=session.is_preview,
                is_published=session.is_published,
            )

        self._delete_upload_temp_dir(session.id)
        self.db.delete(session)
        self.db.commit()

        return result

    async def _assemble_chunks(self, session: VideoUploadSession, destination: Path) -> int:
        """Concatenates every chunk file onto disk in order, streaming
        through a small fixed-size buffer exactly like LocalStorage.upload
        — RAM stays bounded by CHUNK_READ_SIZE regardless of how large
        the finished video is, and disk reads/writes run off the event
        loop so a big assembly never freezes other requests either."""

        assembled_bytes = 0

        with open(destination, "wb") as out:
            for chunk_number in range(session.total_chunks):
                chunk_path = self.upload_temp_storage.ROOT / self._chunk_key(session.id, chunk_number)

                with open(chunk_path, "rb") as chunk_file:
                    while data := await asyncio.to_thread(chunk_file.read, _ASSEMBLE_READ_SIZE):
                        assembled_bytes += len(data)
                        await asyncio.to_thread(out.write, data)

        return assembled_bytes

    def cleanup_stale_upload_sessions(self) -> int:
        """Deletes any upload session (and its temp chunk files) whose
        /complete never arrived within VIDEO_UPLOAD_SESSION_MAX_AGE_HOURS
        — an abandoned tab, a dead connection, an admin who gave up.
        Runs opportunistically at the start of every /init call instead
        of needing a separate cron/scheduler process."""

        cutoff = datetime.now(UTC) - timedelta(hours=settings.VIDEO_UPLOAD_SESSION_MAX_AGE_HOURS)

        stale = (
            self.db.query(VideoUploadSession)
            .filter(VideoUploadSession.created_at < cutoff)
            .all()
        )

        for session in stale:
            self._delete_upload_temp_dir(session.id)
            self.db.delete(session)

        if stale:
            self.db.commit()

        return len(stale)

    def _chunk_key(self, upload_id: UUID, chunk_number: int) -> str:
        return f"{upload_id}/chunk_{chunk_number:06d}"

    def _uploaded_chunk_numbers(self, session: VideoUploadSession) -> list[int]:
        chunk_dir = self.upload_temp_storage.ROOT / str(session.id)

        if not chunk_dir.exists():
            return []

        numbers = []

        for entry in chunk_dir.iterdir():
            if entry.is_file() and entry.name.startswith("chunk_"):
                try:
                    numbers.append(int(entry.name.removeprefix("chunk_")))
                except ValueError:
                    continue

        return sorted(numbers)

    def _delete_upload_temp_dir(self, upload_id: UUID) -> None:
        chunk_dir = self.upload_temp_storage.ROOT / str(upload_id)

        if chunk_dir.exists():
            shutil.rmtree(chunk_dir, ignore_errors=True)
