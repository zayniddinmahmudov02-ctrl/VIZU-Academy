class FeedbackService:

    @staticmethod
    def generate(
        score: float,
    ):

        if score >= 90:
            return "Excellent"

        if score >= 80:
            return "Very Good"

        if score >= 70:
            return "Good"

        if score >= 60:
            return "Satisfactory"

        return "Needs Improvement"