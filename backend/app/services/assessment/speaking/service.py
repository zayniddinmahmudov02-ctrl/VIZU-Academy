from app.services.assessment.feedback import FeedbackService
from app.services.assessment.cefr import CEFRService
from app.services.assessment.pronunciation import (
    PronunciationAssessmentService,
)
from app.services.assessment.fluency import (
    FluencyAssessmentService,
)


class SpeakingAssessmentService:

    @staticmethod
    def evaluate(
        pronunciation: float,
        fluency: float,
        vocabulary: float,
        grammar: float,
    ):

        pronunciation_result = (
            PronunciationAssessmentService.evaluate(
                pronunciation,
            )
        )

        fluency_result = (
            FluencyAssessmentService.evaluate(
                fluency,
            )
        )

        overall = round(
            (
                pronunciation_result["score"]
                + fluency_result["score"]
                + vocabulary
                + grammar
            )
            / 4,
            1,
        )

        return {
            "pronunciation": pronunciation_result["score"],
            "fluency": fluency_result["score"],
            "vocabulary": vocabulary,
            "grammar": grammar,
            "overall": overall,
            "level": CEFRService.detect(
                overall,
            ),
            "feedback": FeedbackService.generate(
                overall,
            ),
            "passed": overall >= 60,
        }