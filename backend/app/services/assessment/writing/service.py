class WritingAssessmentService:

    @staticmethod
    def evaluate(
        grammar: float,
        vocabulary: float,
        coherence: float,
        task: float,
    ):

        score = round(
            (
                grammar
                + vocabulary
                + coherence
                + task
            )
            / 4,
            1,
        )

        return {
            "grammar": grammar,
            "vocabulary": vocabulary,
            "coherence": coherence,
            "task": task,
            "overall": score,
            "passed": score >= 60,
        }