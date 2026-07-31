from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError

from app.models.user import User
from app.models.video_progress import VideoProgress

from app.repositories.student_progress import StudentProgressRepository
from app.repositories.video import VideoRepository
from app.repositories.video_progress import VideoProgressRepository

from app.services.video.service import VideoService

# A forward jump is only ever accepted up to this many seconds beyond
# what real elapsed wall-clock time since the last update would allow —
# the margin that absorbs normal player/network jitter without opening a
# meaningful skip window.
GRACE_SECONDS = 5

# Matches the spec: watching >=95% of the video (or reaching its end)
# is what "completed" means.
COMPLETION_THRESHOLD_PERCENT = 95

# A user is considered to have reached the end if they're within this
# many seconds of the video's reported duration.
END_TOLERANCE_SECONDS = 2


class VideoProgressService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = VideoProgressRepository(db)
        self.videos = VideoRepository(db)
        self.student_progress = StudentProgressRepository(db)
        self.video_service = VideoService(db)

    # ==========================
    # Read
    # ==========================

    def get_for_lesson(
        self,
        user: User,
        lesson_id: UUID,
    ) -> VideoProgress:
        video = self.videos.get_primary_for_lesson(lesson_id)

        if video is None:
            raise NotFoundError("Video not found")

        # Same access gate as playback — no peeking at progress for a
        # video you're not allowed to watch.
        self.video_service.get_playable_video(video.id, user)

        progress = self.repository.get_by_user_and_video(
            user.id,
            video.id,
        )

        if progress is not None:
            return progress

        return VideoProgress(
            user_id=user.id,
            video_id=video.id,
            lesson_id=lesson_id,
            last_position=0,
            watch_percent=0,
            completed=False,
        )

    # ==========================
    # Update (server-validated)
    # ==========================

    def update_progress(
        self,
        user: User,
        video_id: UUID,
        position: int,
        ended: bool = False,
    ) -> VideoProgress:
        video = self.videos.get(video_id)

        if video is None:
            raise NotFoundError("Video not found")

        self.video_service.get_playable_video(video_id, user)

        position = max(0, position)

        progress = self.repository.get_by_user_and_video(
            user.id,
            video_id,
        )

        if progress is None:
            # First-ever report for this user/video: nothing to compare
            # against yet, so a huge initial position is still clamped
            # to a small grace window rather than trusted outright.
            allowed_position = min(position, GRACE_SECONDS)

            allowed_position = self._clamp_to_duration(
                allowed_position,
                video.duration_seconds,
            )

            progress = self.repository.create(
                user_id=user.id,
                video_id=video_id,
                lesson_id=video.lesson_id,
                last_position=allowed_position,
                watch_percent=self._watch_percent(
                    allowed_position,
                    video.duration_seconds,
                ),
                completed=False,
            )

            return progress

        allowed_position = self._clamp_forward_jump(
            progress,
            position,
        )

        allowed_position = self._clamp_to_duration(
            allowed_position,
            video.duration_seconds,
        )

        watch_percent = self._watch_percent(
            allowed_position,
            video.duration_seconds,
        )

        return self.repository.update(
            progress,
            last_position=allowed_position,
            watch_percent=max(progress.watch_percent, watch_percent),
        )

    def _clamp_forward_jump(
        self,
        progress: VideoProgress,
        requested_position: int,
    ) -> int:
        """The anti-skip guarantee, enforced server-side so it can't be
        bypassed by manipulating the client: rewinding is always free,
        but advancing past `last_position` is capped at how much real
        wall-clock time has actually elapsed since the last report (plus
        a small grace window) — never at whatever the client claims."""

        if requested_position <= progress.last_position:
            return requested_position

        now = datetime.now(UTC)
        last_update = progress.updated_at

        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=UTC)

        elapsed = max((now - last_update).total_seconds(), 0)
        max_allowed = progress.last_position + elapsed + GRACE_SECONDS

        return int(min(requested_position, max_allowed))

    @staticmethod
    def _clamp_to_duration(
        position: int,
        duration_seconds: int,
    ) -> int:
        if duration_seconds > 0:
            return min(position, duration_seconds)

        return position

    @staticmethod
    def _watch_percent(
        position: int,
        duration_seconds: int,
    ) -> int:
        if duration_seconds <= 0:
            return 0

        return max(
            0,
            min(100, round((position / duration_seconds) * 100)),
        )

    # ==========================
    # Complete
    # ==========================

    def complete_progress(
        self,
        user: User,
        video_id: UUID,
        ended: bool = False,
    ) -> VideoProgress:
        video = self.videos.get(video_id)

        if video is None:
            raise NotFoundError("Video not found")

        self.video_service.get_playable_video(video_id, user)

        progress = self.repository.get_by_user_and_video(
            user.id,
            video_id,
        )

        if progress is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No watch progress recorded for this video yet",
            )

        reached_end = (
            video.duration_seconds > 0
            and progress.last_position
            >= video.duration_seconds - END_TOLERANCE_SECONDS
        )

        eligible = (
            progress.watch_percent >= COMPLETION_THRESHOLD_PERCENT
            or ended
            or reached_end
        )

        if not eligible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Video must be watched to at least "
                    f"{COMPLETION_THRESHOLD_PERCENT}% before it can be "
                    "marked complete"
                ),
            )

        progress = self.repository.update(
            progress,
            completed=True,
        )

        student_progress = self.student_progress.get_or_create(
            str(user.id),
            str(video.lesson_id),
        )

        if not student_progress.video_completed:
            self.student_progress.mark_video_completed(student_progress)

        return progress
