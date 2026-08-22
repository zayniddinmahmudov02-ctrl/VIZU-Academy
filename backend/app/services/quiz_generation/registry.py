"""Extensible template registry for the deterministic (non-AI) quiz
generator. A topic (e.g. "alphabet") is a set of QuestionTemplates, each
scoped to one or more CEFR levels and producing MULTIPLE_CHOICE
candidates for one narrow question pattern (e.g. "Buchstabe nach X").
Adding a new topic (Artikel, Personalpronomen, sein/haben, ...) later is
just a new module that registers its own templates here — nothing in
quiz_generation_service.py or the API needs to change."""

from dataclasses import dataclass
from random import Random
from typing import Callable


@dataclass(frozen=True)
class Candidate:
    """One fully-formed, self-contained question candidate — everything
    needed to insert a QuizQuestion + 4 QuizOptions, plus the two dedup
    signals (see quiz_generation_service.py's dedup logic)."""

    template_type: str
    source_value: str
    question_text: str
    correct_text: str
    distractor_texts: tuple[str, str, str]


@dataclass(frozen=True)
class QuestionTemplate:
    template_type: str
    topic: str
    label: str
    level_range: tuple[str, ...]
    difficulty: str
    question_type: str
    generate: Callable[[Random], list[Candidate]]


_REGISTRY: list[QuestionTemplate] = []


def register_template(template: QuestionTemplate) -> None:
    _REGISTRY.append(template)


def get_templates(topic: str, level: str, question_types: list[str] | None = None) -> list[QuestionTemplate]:
    types_filter = set(question_types) if question_types else None
    return [
        t
        for t in _REGISTRY
        if t.topic == topic and level in t.level_range and (types_filter is None or t.template_type in types_filter)
    ]


def get_topics_for_level(level: str) -> list[dict]:
    """Groups registered templates by topic for the admin UI's Thema
    dropdown + Fragetypen checkboxes — driven entirely by what's actually
    registered, so a new topic module shows up here automatically."""
    topics: dict[str, list[QuestionTemplate]] = {}
    for t in _REGISTRY:
        if level in t.level_range:
            topics.setdefault(t.topic, []).append(t)

    return [
        {
            "topic": topic,
            "label": templates[0].topic.capitalize(),
            "question_types": [
                {"template_type": t.template_type, "label": t.label, "difficulty": t.difficulty} for t in templates
            ],
        }
        for topic, templates in topics.items()
    ]
