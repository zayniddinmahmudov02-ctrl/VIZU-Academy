class FluencyAssessmentService:

    @staticmethod
    def evaluate(
        fluency: float,
    ):

        fluency = max(
            0,
            min(
                fluency,
                100,
            ),
        )

        return {
            "score": fluency,
            "passed": fluency >= 60,
        }