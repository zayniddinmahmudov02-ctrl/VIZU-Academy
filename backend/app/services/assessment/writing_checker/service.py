import re

from app.services.assessment.feedback import FeedbackService
from app.services.assessment.grammar_checker import GrammarCheckerService
from app.services.assessment.cefr import (
    CEFRService,
)

class WritingCheckerService:

    @staticmethod
    def analyze(text: str):

        words = text.split()

        sentences = re.split(
            r"[.!?]+",
            text,
        )

        sentences = [
            s
            for s in sentences
            if s.strip()
        ]

        return {
            "characters": len(text),
            "words": len(words),
            "sentences": len(sentences),
        }

    @staticmethod
    def vocabulary_score(text: str):

        words = text.lower().split()

        unique = len(set(words))

        if not words:
            return 0

        return round(
            unique * 100 / len(words),
            1,
        )

    @staticmethod
    def sentence_score(text: str):

        sentences = re.split(
            r"[.!?]+",
            text,
        )

        sentences = [
            s
            for s in sentences
            if s.strip()
        ]

        if not sentences:
            return 0

        avg = (
            sum(
                len(sentence.split())
                for sentence in sentences
            )
            / len(sentences)
        )

        return round(
            min(avg * 5, 100),
            1,
        )

    @staticmethod
    def evaluate(text: str):

        info = WritingCheckerService.analyze(text)

        vocabulary = WritingCheckerService.vocabulary_score(
            text
        )

        sentence = WritingCheckerService.sentence_score(
            text
        )

        grammar = GrammarCheckerService.evaluate(
            text
        )

        overall = round(
            (
                vocabulary
                + sentence
                + grammar["grammar_score"]
            )
            / 3,
            1,
        )
        return {
    **info,
    **grammar,
    "vocabulary_score": vocabulary,
    "sentence_score": sentence,
    "overall": overall,
    "level": CEFRService.detect(
        overall,
    ),
    "feedback": FeedbackService.generate(
        overall,
    ),
}