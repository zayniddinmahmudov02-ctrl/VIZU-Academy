"""A1 "Alphabet" topic — first (and, at import time, only) topic
registered with the deterministic quiz generator (see registry.py).
Self-contained: uses only a fixed 26-letter alphabet, a small fixed list
of common A1 nouns, and randomness — no lesson content, no Vocabulary
table, no other lesson's topic is ever referenced, keeping this strictly
scoped to "Alphabet" per the content-safety requirement.

Every template produces MULTIPLE_CHOICE candidates with exactly 4
options (1 correct + 3 distractors). Each generate() enumerates its full,
deterministic candidate space up front (bounded — dozens to ~100 per
template) rather than sampling exactly `count` — quiz_generation_service
is the one place that pools everything, dedups, shuffles and truncates,
so no template needs to know the requested count."""

import random

from app.services.quiz_generation.registry import Candidate, QuestionTemplate, register_template

TOPIC = "alphabet"
LEVELS = ("A1",)

LETTERS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
VOWELS = tuple("AEIOU")
CONSONANTS = tuple(l for l in LETTERS if l not in VOWELS)

# Common, simple A1 nouns — used only for the two word-based templates
# below, not pulled from the Vocabulary table (that would cross into
# other lessons' content, which this topic must not do).
WORDS = (
    "HAUS", "NAME", "BUCH", "TISCH", "STUHL", "LAMPE", "APFEL", "WASSER",
    "BROT", "MILCH", "KATZE", "HUND", "AUTO", "SCHULE", "LEHRER", "ARBEIT",
    "ZEIT", "JAHR", "BALL", "STADT",
)


def _distractors_from(rng: random.Random, pool: tuple[str, ...], exclude: set[str], n: int = 3) -> list[str]:
    choices = [x for x in pool if x not in exclude]
    return rng.sample(choices, n)


def _gen_buchstabe_nach(rng: random.Random) -> list[Candidate]:
    candidates = []
    for i, letter in enumerate(LETTERS[:-1]):
        correct = LETTERS[i + 1]
        distractors = _distractors_from(rng, LETTERS, {letter, correct})
        candidates.append(
            Candidate(
                template_type="buchstabe_nach",
                source_value=letter,
                question_text=f"Welcher Buchstabe kommt nach {letter}?",
                correct_text=correct,
                distractor_texts=tuple(distractors),
            )
        )
    return candidates


def _gen_buchstabe_vor(rng: random.Random) -> list[Candidate]:
    candidates = []
    for i, letter in enumerate(LETTERS[1:], start=1):
        correct = LETTERS[i - 1]
        distractors = _distractors_from(rng, LETTERS, {letter, correct})
        candidates.append(
            Candidate(
                template_type="buchstabe_vor",
                source_value=letter,
                question_text=f"Welcher Buchstabe kommt vor {letter}?",
                correct_text=correct,
                distractor_texts=tuple(distractors),
            )
        )
    return candidates


def _gen_vokal_erkennen(rng: random.Random) -> list[Candidate]:
    candidates = []
    seen: set[tuple[str, ...]] = set()
    for vowel in VOWELS:
        for _ in range(12):
            distractors = _distractors_from(rng, CONSONANTS, {vowel})
            key = tuple(sorted([vowel, *distractors]))
            if key in seen:
                continue
            seen.add(key)
            options = [vowel, *distractors]
            rng.shuffle(options)
            candidates.append(
                Candidate(
                    template_type="vokal_erkennen",
                    source_value="|".join(key),
                    question_text=f"Welcher dieser Buchstaben ist ein Vokal: {', '.join(options)}?",
                    correct_text=vowel,
                    distractor_texts=tuple(distractors),
                )
            )
    return candidates


def _gen_konsonant_erkennen(rng: random.Random) -> list[Candidate]:
    candidates = []
    seen: set[tuple[str, ...]] = set()
    for consonant in CONSONANTS:
        for _ in range(3):
            distractors = _distractors_from(rng, VOWELS, set(), n=3)
            key = tuple(sorted([consonant, *distractors]))
            if key in seen:
                continue
            seen.add(key)
            options = [consonant, *distractors]
            rng.shuffle(options)
            candidates.append(
                Candidate(
                    template_type="konsonant_erkennen",
                    source_value="|".join(key),
                    question_text=f"Welcher dieser Buchstaben ist ein Konsonant: {', '.join(options)}?",
                    correct_text=consonant,
                    distractor_texts=tuple(distractors),
                )
            )
    return candidates


def _gen_grossbuchstabe_erkennen(rng: random.Random) -> list[Candidate]:
    candidates = []
    seen: set[tuple[str, ...]] = set()
    for correct in LETTERS:
        for _ in range(3):
            distractors = _distractors_from(rng, LETTERS, {correct})
            key = (correct, *sorted(distractors))
            if key in seen:
                continue
            seen.add(key)
            lower_distractors = [d.lower() for d in distractors]
            options = [correct, *lower_distractors]
            rng.shuffle(options)
            candidates.append(
                Candidate(
                    template_type="grossbuchstabe_erkennen",
                    source_value="|".join(key),
                    question_text=f"Welcher dieser Buchstaben ist ein Großbuchstabe: {', '.join(options)}?",
                    correct_text=correct,
                    distractor_texts=tuple(lower_distractors),
                )
            )
    return candidates


def _gen_kleinbuchstabe_erkennen(rng: random.Random) -> list[Candidate]:
    candidates = []
    seen: set[tuple[str, ...]] = set()
    for correct in LETTERS:
        for _ in range(3):
            distractors = _distractors_from(rng, LETTERS, {correct})
            key = (correct, *sorted(distractors))
            if key in seen:
                continue
            seen.add(key)
            correct_lower = correct.lower()
            options = [correct_lower, *distractors]
            rng.shuffle(options)
            candidates.append(
                Candidate(
                    template_type="kleinbuchstabe_erkennen",
                    source_value="|".join(key),
                    question_text=f"Welcher dieser Buchstaben ist ein Kleinbuchstabe: {', '.join(options)}?",
                    correct_text=correct_lower,
                    distractor_texts=tuple(distractors),
                )
            )
    return candidates


def _gen_alphabet_reihenfolge(rng: random.Random) -> list[Candidate]:
    candidates = []
    for i in range(len(LETTERS) - 2):
        a, b, c = LETTERS[i], LETTERS[i + 1], LETTERS[i + 2]
        correct_order = f"{a}, {b}, {c}"
        wrong_permutations = [
            f"{b}, {a}, {c}",
            f"{c}, {b}, {a}",
            f"{a}, {c}, {b}",
            f"{b}, {c}, {a}",
            f"{c}, {a}, {b}",
        ]
        distractors = rng.sample(wrong_permutations, 3)
        shown_order = rng.choice(distractors)
        candidates.append(
            Candidate(
                template_type="alphabet_reihenfolge",
                source_value=a,
                question_text=f"Welche ist die richtige alphabetische Reihenfolge für {shown_order}?",
                correct_text=correct_order,
                distractor_texts=tuple(distractors),
            )
        )
    return candidates


def _gen_buchstaben_zuordnung(rng: random.Random) -> list[Candidate]:
    candidates = []
    for i, letter in enumerate(LETTERS, start=1):
        correct = str(i)
        pool = [str(n) for n in range(1, 27) if n != i]
        distractors = rng.sample(pool, 3)
        candidates.append(
            Candidate(
                template_type="buchstaben_zuordnung",
                source_value=letter,
                question_text=f"Der wievielte Buchstabe im Alphabet ist {letter}?",
                correct_text=correct,
                distractor_texts=tuple(distractors),
            )
        )
    return candidates


def _gen_einfaches_buchstabieren(rng: random.Random) -> list[Candidate]:
    candidates = []
    for word in WORDS:
        correct_len = len(word)
        pool = sorted({n for n in range(max(2, correct_len - 3), correct_len + 4) if n != correct_len})
        distractors = rng.sample(pool, 3)
        candidates.append(
            Candidate(
                template_type="einfaches_buchstabieren",
                source_value=word,
                question_text=f"Wie viele Buchstaben hat das Wort {word}?",
                correct_text=str(correct_len),
                distractor_texts=tuple(str(d) for d in distractors),
            )
        )
    return candidates


def _gen_buchstabe_im_wort_erkennen(rng: random.Random) -> list[Candidate]:
    candidates = []
    for word in WORDS:
        letters_in_word = sorted(set(word) & set(LETTERS))
        letters_not_in_word = [l for l in LETTERS if l not in letters_in_word]
        correct = rng.choice(letters_in_word)
        distractors = rng.sample(letters_not_in_word, 3)
        candidates.append(
            Candidate(
                template_type="buchstabe_im_wort_erkennen",
                source_value=word,
                question_text=f"Welcher Buchstabe kommt in dem Wort {word} vor?",
                correct_text=correct,
                distractor_texts=tuple(distractors),
            )
        )
    return candidates


for _template_type, _label, _difficulty, _generate_fn in [
    ("buchstabe_nach", "Buchstabe nach X", "easy", _gen_buchstabe_nach),
    ("buchstabe_vor", "Buchstabe vor X", "easy", _gen_buchstabe_vor),
    ("vokal_erkennen", "Vokal erkennen", "easy", _gen_vokal_erkennen),
    ("konsonant_erkennen", "Konsonant erkennen", "easy", _gen_konsonant_erkennen),
    ("grossbuchstabe_erkennen", "Großbuchstabe erkennen", "easy", _gen_grossbuchstabe_erkennen),
    ("kleinbuchstabe_erkennen", "Kleinbuchstabe erkennen", "easy", _gen_kleinbuchstabe_erkennen),
    ("alphabet_reihenfolge", "Alphabet-Reihenfolge", "medium", _gen_alphabet_reihenfolge),
    ("buchstaben_zuordnung", "Einfache Buchstaben-Zuordnung", "medium", _gen_buchstaben_zuordnung),
    ("einfaches_buchstabieren", "Einfaches Buchstabieren", "medium", _gen_einfaches_buchstabieren),
    ("buchstabe_im_wort_erkennen", "Buchstaben in einem einfachen Wort erkennen", "medium", _gen_buchstabe_im_wort_erkennen),
]:
    register_template(
        QuestionTemplate(
            template_type=_template_type,
            topic=TOPIC,
            label=_label,
            level_range=LEVELS,
            difficulty=_difficulty,
            question_type="MULTIPLE_CHOICE",
            generate=_generate_fn,
        )
    )
