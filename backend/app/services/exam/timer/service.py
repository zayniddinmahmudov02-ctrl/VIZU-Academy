from datetime import datetime, timedelta


class ExamTimerService:

    @staticmethod
    def end_time(duration_minutes: int):

        return (
            datetime.utcnow()
            + timedelta(
                minutes=duration_minutes
            )
        )

    @staticmethod
    def expired(end_time):

        return datetime.utcnow() >= end_time