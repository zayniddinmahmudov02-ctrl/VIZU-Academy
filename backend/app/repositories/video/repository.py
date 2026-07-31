from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.module import Module
from app.models.video import Video
from app.repositories.base import BaseRepository


class VideoRepository(BaseRepository[Video]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            Video,
            db,
        )

    def get_by_lesson(
        self,
        lesson_id: UUID,
    ) -> list[Video]:

        result = self.db.execute(
            select(Video)
            .where(
                Video.lesson_id == lesson_id,
            )
            .order_by(
                Video.order_index,
            )
        )

        return list(
            result.scalars().all()
        )

    def get_primary_for_lesson(
        self,
        lesson_id: UUID,
    ) -> Video | None:
        """The video a student sees first for this lesson — lowest
        order_index among published videos."""

        result = self.db.execute(
            select(Video)
            .where(
                Video.lesson_id == lesson_id,
                Video.is_published.is_(True),
            )
            .order_by(
                Video.order_index,
            )
            .limit(1)
        )

        return result.scalars().first()

    def publish(
        self,
        video: Video,
    ) -> Video:

        video.is_published = True

        self.db.commit()
        self.db.refresh(video)

        return video

    def unpublish(
        self,
        video: Video,
    ) -> Video:

        video.is_published = False

        self.db.commit()
        self.db.refresh(video)

        return video

    def get_course_id(
        self,
        video_id: UUID,
    ) -> UUID | None:
        """Resolves the course a video belongs to via
        Video -> Lesson -> Module -> Course, for enrollment checks. Returns
        None if the video (or its lesson/module chain) doesn't exist."""

        result = self.db.execute(
            select(Module.course_id)
            .join(
                Lesson,
                Lesson.module_id == Module.id,
            )
            .join(
                Video,
                Video.lesson_id == Lesson.id,
            )
            .where(
                Video.id == video_id,
            )
        )

        return result.scalar_one_or_none()