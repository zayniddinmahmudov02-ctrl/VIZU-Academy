class PronunciationAssessmentService:

    @staticmethod
    def evaluate(
        pronunciation: float,
    ):

        pronunciation = max(
            0,
            min(
                pronunciation,
                100,
            ),
        )

        return {
            "score": pronunciation,
            "passed": pronunciation >= 60,
        }