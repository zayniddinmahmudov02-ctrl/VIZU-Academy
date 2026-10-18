"""VIZU-DEUTSCH A2 course book -> lesson content (import format 1.1).

Same pipeline and helpers as the A1 book (app/scripts/vizu_deutsch_a1): one
file per book lesson ("A2 N.Unterricht", unterricht_01.py … unterricht_14.py),
built into app/data/vizu_deutsch_a2/*.json and imported into the EXISTING
lessons A2 -> module 1 -> lesson N. Content ids are vizu-a2-l<NN>-<skill>-<nn>
(never the A1 ids), source "book" (taken from the book) or "vizu" (made by
VIZU from the book material — Wortschatz practice, Abschlusstest).

Sources: "VIZU-Deutsch A2.pdf" (183 pages, lessons 1-13; page numbers in the
metadata refer to it), the per-lesson PDFs (text layer of lessons 1-12),
"A2 14.Unterricht.pdf" (lesson 14 is not in the book) and
"Vizu-Antworten A2" (answer keys of lessons 1, 2, 3, 5, 8 and 9).

    python -m app.scripts.vizu_deutsch_a2.build
    python -m app.scripts.import_vizu_deutsch_a1 --level A2 --dry-run
"""

from app.scripts.vizu_deutsch_a1 import (  # noqa: F401 — re-exported helpers
    _unique_words,
    article_set,
    choice_gap,
    exercise,
    forward_vocab_set,
    gap,
    gap_paragraphs,
    html_table,
    match,
    mc,
    mc_pending,
    pairs,
    reverse_vocab_set,
    short,
    text_gap,
    tf,
    ul,
    vocab_match_sets,
    word_order_mc,
    words,
)

LEVEL = "A2"
MODULE = 1  # every book lesson is a lesson of the A2 course's module 1


def cid(lesson: int, skill: str, n: int = 1) -> str:
    return f"vizu-a2-l{lesson:02d}-{skill}-{n:02d}"


def base(lesson: int, skill: str, n: int, title: str, source: str = "book", page: int | str | None = None, **extra) -> dict:
    item = {"content_id": cid(lesson, skill, n), "level": LEVEL, "module": MODULE, "lesson": lesson, "skill": skill,
            "title": title, "source": source}
    if page is not None:
        item["metadata"] = {"book_page": page}
    if extra.get("metadata"):
        item["metadata"] = {**item.get("metadata", {}), **extra.pop("metadata")}
    item.update({k: v for k, v in extra.items() if v is not None})
    return item


STRUCTURE = "Einführung → Wortschatz → Grammatik → Lesen → Hören → Sprechen → Schreiben → Übungen → Abschlusstest → Zusammenfassung"


def intro_html(n: int, topic: str, grammar: str, goals: list[str], can_do: list[str]) -> str:
    return (
        f"<h3>A2 {n}. Unterricht — {topic}</h3>"
        f"<p><strong>Mavzu:</strong> {topic} · <strong>Grammatik:</strong> {grammar}</p>"
        "<h4>Dars maqsadlari</h4>" + ul(goals)
        + "<h4>Dars oxirida siz quyidagilarni bajara olasiz</h4>" + ul(can_do)
        + f"<h4>Darsning tuzilishi</h4><p>{STRUCTURE}</p>"
    )


def summary_html(n: int, points: list[str]) -> str:
    return (f"<h3>A2 {n}. Unterricht — qisqacha</h3>" + ul(points)
            + "<p>Natijalaringiz pastda — tugallanmagan bo'limlarni yakunlang, so'ng keyingi darsga o'ting.</p>")


def numbered_words(rows: list[tuple], group: str | None = None) -> list[dict]:
    """The book's word tables: (word with article, translation) — the article
    is split off ("der Architekt" -> article der, word Architekt)."""
    out = []
    for word, translation in rows:
        parts = word.split(" ", 1)
        if len(parts) == 2 and parts[0] in ("der", "die", "das"):
            out.extend(words([(parts[0], parts[1], translation)], group))
        else:
            out.extend(words([(word, translation)], group))
    return out
