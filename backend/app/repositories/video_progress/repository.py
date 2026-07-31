from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.video_progress import VideoProgress


class VideoProgressRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_by_user_and_video(
        self,
        user_id: UUID,
        video_id: UUID,
    ) -> VideoProgress | None:

        result = self.db.execute(
            select(VideoProgress).where(
                VideoProgress.user_id == user_id,
                VideoProgress.video_id == video_id,
            )
        )

        return result.scalars().first()

    def get_by_user_and_lesson(
        self,
        user_id: UUID,
        lesson_id: UUID,
    ) -> VideoProgress | None:

        result = self.db.execute(
            select(VideoProgress).where(
                VideoProgress.user_id == user_id,
                VideoProgress.lesson_id == lesson_id,
            )
        )

        return result.scalars().first()

    def create(
        self,
        user_id: UUID,
        video_id: UUID,
        lesson_id: UUID,
        last_position: int,
        watch_percent: int,
        completed: bool = False,
    ) -> VideoProgress:

        progress = VideoProgress(
            user_id=user_id,
            video_id=video_id,
            lesson_id=lesson_id,
            last_position=last_position,
            watch_percent=watch_percent,
            completed=completed,
        )

        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)

        return progress

    def update(
        self,
        progress: VideoProgress,
        **fields,
    ) -> VideoProgress:

        for key, value in fields.items():
            setattr(progress, key, value)

        self.db.commit()
        self.db.refresh(progress)

        return progress
