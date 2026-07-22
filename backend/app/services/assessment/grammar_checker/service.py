import re


class GrammarCheckerService:

    COMMON_ERRORS = {
        "ich bin gehen": "ich gehe",
        "ich haben": "ich habe",
        "du haben": "du hast",
        "er haben": "er hat",
        "wir hat": "wir haben",
        "sie haten": "sie hatten",
        "ein Auto": "ein Auto",
        "eine Mann": "ein Mann",
        "der Frau": "die Frau",
    }

    @classmethod
    def check(cls, text: str):

        errors = []

        lower = text.lower()

        for wrong, correct in cls.COMMON_ERRORS.items():

            if wrong in lower:

                errors.append(
                    {
                        "wrong": wrong,
                        "correct": correct,
                    }
                )

        return errors
class GrammarCheckerService:

    @classmethod
    def grammar_score(
        cls,
        text: str,
    ):

        errors = cls.check(text)

        words = len(
            text.split()
        )

        if words == 0:
            return 0

        score = max(
            0,
            100 - len(errors) * 10,
        )

        return score
class GrammarCheckerService:

    @classmethod
    def evaluate(
        cls,
        text: str,
    ):

        errors = cls.check(text)

        score = cls.grammar_score(text)

        return {
            "grammar_score": score,
            "errors": errors,
            "error_count": len(errors),
        }