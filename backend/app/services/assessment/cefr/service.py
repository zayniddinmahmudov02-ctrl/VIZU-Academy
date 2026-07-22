class CEFRService:

    @staticmethod
    def detect(score: float):

        if score >= 90:
            return "C1"

        if score >= 80:
            return "B2"

        if score >= 70:
            return "B1"

        if score >= 60:
            return "A2"

        return "A1"