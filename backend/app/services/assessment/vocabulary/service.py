class VocabularyAssessmentService:

    A1 = 500
    A2 = 1000
    B1 = 2000
    B2 = 4000
    C1 = 8000

    @classmethod
    def estimate_level(
        cls,
        unique_words: int,
    ):

        if unique_words >= cls.C1:
            return "C1"

        if unique_words >= cls.B2:
            return "B2"

        if unique_words >= cls.B1:
            return "B1"

        if unique_words >= cls.A2:
            return "A2"

        return "A1"