from app.schemas.base import BaseSchema


class AIGenerateRequest(BaseSchema):
    """Admin pastes plain text/instructions (a topic, a source paragraph,
    lesson notes...) and the level to target — the only input every
    generation endpoint needs. count only matters for the endpoints that
    generate a list of questions."""

    source_text: str
    level: str = "A1"
    count: int = 5


# ============================================================
# Grammatik Quiz
# ============================================================


class AIQuizOptionPreview(BaseSchema):
    option_text: str
    is_correct: bool = False
    match_value: str | None = None


class AIQuizQuestionPreview(BaseSchema):
    question: str
    question_type: str = "MULTIPLE_CHOICE"
    points: int = 1
    options: list[AIQuizOptionPreview] = []
    correct_text_answer: str | None = None


class AIGrammarQuizPreview(BaseSchema):
    questions: list[AIQuizQuestionPreview]


# ============================================================
# Lesen / Hören — multiple-choice comprehension questions. Mapped onto
# the Assessment Engine's generic option-based question/option editor
# (the only multi-question shape it supports outside CLOZE_TEXT/
# SHORT_ANSWER/WRITING/SPEAKING), not free text — every question needs
# an explicit correct option, never an unscoreable open answer.
# ============================================================


class AIComprehensionOptionPreview(BaseSchema):
    option_text: str
    is_correct: bool = False


class AIComprehensionQuestionPreview(BaseSchema):
    prompt: str
    options: list[AIComprehensionOptionPreview]


class AILesenPreview(BaseSchema):
    reading_text: str
    questions: list[AIComprehensionQuestionPreview]


class AIHoerenPreview(BaseSchema):
    questions: list[AIComprehensionQuestionPreview]


# ============================================================
# Schreiben / Sprechen — task + rubric
# ============================================================


class AIRubricCriterionPreview(BaseSchema):
    name: str
    max_score: int = 5


class AISchreibenPreview(BaseSchema):
    task_content: str
    requirements: str
    rubric_criteria: list[AIRubricCriterionPreview]


class AISprechenPreview(BaseSchema):
    task_content: str
    preparation_instructions: str
    rubric_criteria: list[AIRubricCriterionPreview]
