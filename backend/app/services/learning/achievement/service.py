from app.models.student_progress import StudentProgress


class AchievementService:

    ACHIEVEMENTS = {

        "first_lesson": {
            "title": "First Lesson",
            "condition": lambda p: p.lesson_completed,
        },

        "xp_100": {
            "title": "100 XP",
            "condition": lambda p: p.total_score >= 100,
        },

        "xp_500": {
            "title": "500 XP",
            "condition": lambda p: p.total_score >= 500,
        },

        "streak_7": {
            "title": "7 Day Streak",
            "condition": lambda p: p.streak >= 7,
        },

        "streak_30": {
            "title": "30 Day Streak",
            "condition": lambda p: p.streak >= 30,
        },
    }

    @classmethod
    def evaluate(
        cls,
        progress: StudentProgress,
    ):

        unlocked = []

        for key, achievement in cls.ACHIEVEMENTS.items():

            if achievement["condition"](progress):

                unlocked.append(
                    {
                        "key": key,
                        "title": achievement["title"],
                    }
                )

        return unlocked