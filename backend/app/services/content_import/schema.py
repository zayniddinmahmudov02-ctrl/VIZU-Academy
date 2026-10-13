"""Standard content format for Claude-generated lesson content (A1-C1).

A document holds a list of items; each item is one task of one skill of one
lesson. The JSON Schema served to admins (GET /admin/content-import/schema)
is generated from these models, so the documentation can never drift from
the validation.

Answer keys (correct_answer, pairs, gaps, accepted) arrive here and are
stored server-side only — students receive questions without them."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.2"
# 1.1 = 1.0 + grammatik / wortschatz / frage / yakuniy items
# 1.2 = 1.1 + uebungen / schreiben_uebungen (exercise sets) and kompetenz (VIZU LMS competency text)
SCHEMA_VERSIONS = ("1.0", "1.1", "1.2")
Source = Literal["book", "vizu"]

Level = Literal["A1", "A2", "B1", "B2", "C1"]
ContentId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{2,119}$", description="Stable unique id, e.g. 'a1-m1-l1-lesen-01'")]
TextType = Literal["message", "email", "letter", "description", "opinion", "essay", "report", "other"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Question(_Strict):
    """One auto-graded question (Lesen / Hören)."""

    type: Literal["multiple_choice", "true_false", "matching", "gap_fill", "short_answer"]
    question: str = Field(min_length=1, max_length=2000, description="Question / instruction text")
    passage: int = Field(default=1, ge=1, le=10, description="Lesen: 1-based number of the passage the question belongs to")
    points: int = Field(default=1, ge=1, le=100)
    explanation: str | None = Field(default=None, max_length=2000, description="Shown after submission")
    # multiple_choice / true_false
    options: list[str] | None = Field(default=None, max_length=6, description="multiple_choice: 2-6 options; true_false: optional, default ['Richtig','Falsch']")
    correct_answer: str | int | bool | None = Field(
        default=None, description="multiple_choice: letter 'A'-'F', 1-based number or the exact option text; true_false: 'richtig'/'falsch' (or true/false)"
    )
    # matching (Zuordnung)
    items: list[str] | None = Field(default=None, max_length=12, description="matching: left side, numbered 1..n")
    targets: list[str] | None = Field(default=None, max_length=15, description="matching: right side, lettered A..; may contain distractors")
    pairs: dict[str, str] | None = Field(default=None, description="matching: {'1': 'C', '2': 'A'} item number -> target letter")
    # gap_fill (Lückentext)
    text: str | None = Field(default=None, max_length=5000, description="gap_fill: text with [[1]], [[2]] … placeholders")
    gaps: dict[str, list[str] | dict] | None = Field(
        default=None, description="gap_fill: {'1': ['heiße']} accepted answers, or {'1': {'accepted': [...], 'options': [...]}} for a choice gap"
    )
    case_sensitive: bool = False
    # short_answer
    accepted: list[str] | None = Field(default=None, max_length=20, description="short_answer: all accepted answers (only for answers a key can decide)")
    max_length: int | None = Field(default=None, ge=1, le=300)


class Passage(_Strict):
    title: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=20000, description="Plain text; blank line = new paragraph")
    image_url: str | None = Field(default=None, max_length=500)


class Rubric(_Strict):
    key: str = Field(pattern=r"^[a-z0-9_]{1,40}$")
    name: str = Field(min_length=1, max_length=120)
    max: int = Field(ge=1, le=100)


class _ItemBase(_Strict):
    content_id: ContentId
    level: Level
    module: int = Field(ge=1, le=100)
    lesson: int = Field(ge=1, le=500)
    title: str = Field(min_length=1, max_length=255)
    instruction: str | None = Field(default=None, max_length=5000)
    task_type: str | None = Field(default=None, max_length=40)
    max_score: int | None = Field(default=None, ge=1, le=1000, description="Lesen/Hören: must equal the sum of question points; Schreiben/Sprechen: must equal the rubric total")
    status: Literal["draft", "review"] = Field(default="draft", description="Imported content is ALWAYS created unpublished; an admin publishes it after preview")
    order: int | None = Field(default=None, ge=1, le=100)
    source: Source = Field(default="book", description="book = taken from the course book; vizu = created by VIZU from the lesson material")
    metadata: dict | None = Field(default=None, description="Free-form (topic, grammar, can-do statements, page …)")


class LesenItem(_ItemBase):
    skill: Literal["lesen"]
    passages: list[Passage] = Field(min_length=1, max_length=10)
    questions: list[Question] = Field(min_length=1, max_length=60)


class HoerenItem(_ItemBase):
    skill: Literal["hoeren"]
    audio_asset_id: str | None = Field(default=None, max_length=120, description="Hint only — the audio file is uploaded by an admin after the import")
    audio_file: str | None = Field(default=None, max_length=255, description="Hint only (expected file name)")
    transcript: str | None = Field(default=None, max_length=20000, description="Script / transcript; shown to students only after their first attempt")
    questions: list[Question] = Field(min_length=1, max_length=40)
    key_pending: bool = Field(
        default=False,
        description="True when the answer key can only be set after listening to the audio: questions may omit correct_answer; "
        "the task stays unpublished until an admin has uploaded the audio and set every key",
    )


class SchreibenItem(_ItemBase):
    skill: Literal["schreiben"]
    prompt: str = Field(min_length=1, max_length=5000, description="Task text shown to the student")
    task_type: TextType = "other"
    audience: str | None = Field(default=None, max_length=1000, description="Addressee / communicative situation")
    min_words: int = Field(ge=1, le=2000)
    max_words: int = Field(ge=1, le=3000)
    time_limit: int | None = Field(default=None, ge=1, le=240, description="Recommended time in minutes")
    support_phrases: list[str] | None = Field(default=None, max_length=40)
    image_url: str | None = Field(default=None, max_length=500)
    rubric: list[Rubric] | None = Field(default=None, max_length=10, description="Default: the level's rubric (100 points)")
    ai_instructions: str | None = Field(default=None, max_length=5000, description="Server-side only")
    feedback_language: str = Field(default="uz", pattern=r"^[a-z]{2}$")
    max_attempts: int = Field(default=3, ge=1, le=20)


class SprechenItem(_ItemBase):
    skill: Literal["sprechen"]
    prompt: str = Field(min_length=1, max_length=5000, description="Instruction shown to the student")
    topic: str | None = Field(default=None, max_length=255)
    questions: list[str] | None = Field(default=None, max_length=20, description="Guiding questions / dialogue cues")
    response_type: Literal["monolog", "dialog"] = "monolog"
    min_duration: int = Field(default=0, ge=0, le=3600, description="Seconds")
    max_duration: int = Field(ge=10, le=3600, description="Seconds")
    preparation_time: int = Field(default=0, ge=0, le=600, description="Seconds")
    speech_goal: str | None = Field(default=None, max_length=2000, description="Expected communicative goal (AI evaluation only)")
    keywords: list[str] | None = Field(default=None, max_length=40)
    sample_answer: str | None = Field(default=None, max_length=5000)
    rubric: list[Rubric] | None = Field(default=None, max_length=10)
    ai_instructions: str | None = Field(default=None, max_length=5000)
    feedback_language: str = Field(default="uz", pattern=r"^[a-z]{2}$")
    max_attempts: int = Field(default=3, ge=1, le=20)


class ExerciseSet(_Strict):
    """One auto-graded exercise set (Grammatik / Wortschatz practice, Yakuniy Test)."""

    title: str = Field(min_length=1, max_length=255)
    instruction: str | None = Field(default=None, max_length=5000)
    source: Source = "book"
    questions: list[Question] = Field(min_length=1, max_length=100)


class GrammarRule(_Strict):
    title: str = Field(min_length=1, max_length=255)
    html: str = Field(min_length=1, max_length=100_000, description="Rule, explanations, examples and tables as simple HTML (sanitized)")


class GrammatikItem(_ItemBase):
    skill: Literal["grammatik"]
    rules: list[GrammarRule] = Field(default_factory=list, max_length=20)
    exercises: list[ExerciseSet] = Field(default_factory=list, max_length=20)


class Word(_Strict):
    word: str = Field(min_length=1, max_length=255, description="German word or phrase without the article")
    article: Literal["der", "die", "das"] | None = None
    plural: str | None = Field(default=None, max_length=255)
    translation: str = Field(min_length=1, max_length=255)
    example: str | None = Field(default=None, max_length=1000)
    example_translation: str | None = Field(default=None, max_length=1000)
    group: str | None = Field(default=None, max_length=120, description="Topic group as in the book")


class WortschatzItem(_ItemBase):
    skill: Literal["wortschatz"]
    words: list[Word] = Field(min_length=1, max_length=300)
    exercises: list[ExerciseSet] = Field(default_factory=list, max_length=10)
    auto_practice: bool = Field(default=True, description="Generate a translation practice set (multiple choice) from the words")


class FrageItem(_ItemBase):
    skill: Literal["frage"]
    prompt: str = Field(min_length=1, max_length=5000, description="The topic question / instruction shown to the student")
    questions: list[str] | None = Field(default=None, max_length=20)
    min_duration: int = Field(default=0, ge=0, le=3600)
    max_duration: int = Field(default=120, ge=10, le=3600)


class YakuniyItem(_ItemBase):
    skill: Literal["yakuniy"]
    questions: list[Question] = Field(min_length=1, max_length=100)


class ExercisesItem(_ItemBase):
    """Auto-graded practice sets of the VIZU LMS Übungen competency
    (skill 'uebungen') or of Schreiben (skill 'schreiben_uebungen': word bank,
    gap texts, sentence building — free writing stays a 'schreiben' item)."""

    skill: Literal["uebungen", "schreiben_uebungen"]
    exercises: list[ExerciseSet] = Field(min_length=1, max_length=20)


Competency = Literal["EINFUEHRUNG", "WORTSCHATZ", "GRAMMATIK", "LESEN", "HOEREN", "SPRECHEN", "SCHREIBEN", "UEBUNGEN", "ABSCHLUSSTEST", "ZUSAMMENFASSUNG"]


class KompetenzItem(_ItemBase):
    """The explanatory text of one VIZU LMS competency (topic, goals, summary).
    Written only into an empty competency text — an admin's text is never
    overwritten."""

    skill: Literal["kompetenz"]
    competency: Competency
    html: str = Field(min_length=1, max_length=100_000, description="Simple HTML (sanitized)")


ContentItem = Annotated[
    LesenItem | HoerenItem | SchreibenItem | SprechenItem | GrammatikItem | WortschatzItem | FrageItem | YakuniyItem | ExercisesItem | KompetenzItem,
    Field(discriminator="skill"),
]


class ContentDocument(_Strict):
    schema_version: Literal["1.0", "1.1", "1.2"]
    language: str = Field(default="de", pattern=r"^[a-z]{2}$")
    source: str | None = Field(default=None, max_length=100, description="e.g. 'claude'")
    items: list[ContentItem] = Field(min_length=1, max_length=200)


def json_schema() -> dict:
    schema = ContentDocument.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://vizu.academy/schemas/lesson-content-1.2.json"
    schema["title"] = "VIZU Academy lesson content (A1-C1)"
    return schema
