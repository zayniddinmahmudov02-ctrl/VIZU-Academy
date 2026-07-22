from sqlalchemy.orm import Session

from app.repositories.student_progress import (
    StudentProgressRepository,
)

from app.schemas.student_progress import (
    StudentProgressCreate,
    StudentProgressUpdate,
)

from app.services.learning.experience import (
    ExperienceService,
)

from app.services.learning.streak import (
    DailyStreakService,
)

from app.services.learning.achievement import (
    AchievementService,
)
from app.services.learning.module_completion import (
    ModuleCompletionService,
)
from app.services.learning.course_completion import (
    CourseCompletionService,
)
class StudentProgressService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = StudentProgressRepository(db)
        self.experience = ExperienceService(db)
        self.streak = DailyStreakService(db)
        self.achievement = AchievementService()
        self.module_completion = ModuleCompletionService(db)
        self.course_completion = CourseCompletionService(db)
    # ==========================
    # CRUD
    # ==========================

    def get_all(self):
        return self.repository.get_all()

    def get(
        self,
        item_id: str,
    ):
        return self.repository.get(item_id)

    def create(
        self,
        data: StudentProgressCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: StudentProgressUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        item_id: str,
    ):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True

    # ==========================
    # Experience
    # ==========================

    def add_experience(
        self,
        progress_id: str,
        activity: str,
    ):
        progress = self.repository.get(progress_id)

        if not progress:
            return None

        return self.experience.add(
            progress,
            activity,
        )

    def current_score(
        self,
        progress_id: str,
    ):
        progress = self.repository.get(progress_id)

        if not progress:
            return 0

        return self.experience.current(
            progress,
        )

    # ==========================
    # Daily Streak
    # ==========================

    def update_streak(
        self,
        progress_id: str,
    ):
        progress = self.repository.get(progress_id)

        if not progress:
            return None

        return self.streak.update(
            progress,
        )

    def current_streak(
        self,
        progress_id: str,
    ):
        progress = self.repository.get(progress_id)

        if not progress:
            return 0

        return self.streak.current(
            progress,
        )

    # ==========================
    # Achievements
    # ==========================

    def achievements(
        self,
        progress_id: str,
    ):
        progress = self.repository.get(progress_id)

        if not progress:
            return []

        return self.achievement.evaluate(
            progress,
        )
    # ==========================
    # Module Completion
    # ==========================

    def complete_module(
        self,
        module_id: str,
        user_id: str,
    ):
        return self.module_completion.complete(
            module_id,
            user_id,
        )
    # ==========================
    # Course Completion
    # ==========================

    def complete_course(
        self,
        course_id: str,
        user_id: str,
    ):
        return self.course_completion.complete(
            course_id,
            user_id,
        )