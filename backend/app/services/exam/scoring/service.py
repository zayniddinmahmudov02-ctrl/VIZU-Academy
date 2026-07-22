class ExamScoringService:

    @staticmethod
    def calculate(
        correct_answers: int,
        total_questions: int,
    ):

        if total_questions == 0:
            return 0

        return round(
            correct_answers * 100 / total_questions,
            1,
        )

    @staticmethod
    def passed(
        score: float,
        passing_score: float = 60,
    ):

        return score >= passing_score