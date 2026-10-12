"""VIZU-DEUTSCH A1 course book -> lesson content (import format 1.1).

One module file per book module (modul_01.py … modul_14.py). Book "Modul N"
is LMS level A1 -> module 1 -> lesson N. Every item carries a stable
content_id (vizu-a1-l<NN>-<skill>-<nn>) so a re-import never duplicates, and
a source: "book" (taken from the book) or "vizu" (created by VIZU from the
lesson material because the book has no such task — e.g. questions for a
text without questions, the Yakuniy Test, the Wortschatz practice).

    python -m app.scripts.vizu_deutsch_a1.build      # writes app/data/vizu_deutsch_a1/*.json
    python -m app.scripts.import_vizu_deutsch_a1 --dry-run
"""

LEVEL = "A1"
MODULE = 1  # every book module is a lesson of the A1 course's module 1


def cid(lesson: int, skill: str, n: int = 1) -> str:
    return f"vizu-a1-l{lesson:02d}-{skill}-{n:02d}"


def base(lesson: int, skill: str, n: int, title: str, source: str = "book", page: int | str | None = None, **extra) -> dict:
    item = {"content_id": cid(lesson, skill, n), "level": LEVEL, "module": MODULE, "lesson": lesson, "skill": skill,
            "title": title, "source": source}
    if page is not None:
        item["metadata"] = {"book_page": page}
    item.update({k: v for k, v in extra.items() if v is not None})
    return item


# ---------- questions ----------


def mc(question: str, options: list[str], answer: str | int, explanation: str | None = None, points: int = 1, passage: int = 1) -> dict:
    """answer: letter A-F or 1-based index."""
    q = {"type": "multiple_choice", "question": question, "options": options, "correct_answer": answer, "points": points, "passage": passage}
    if explanation:
        q["explanation"] = explanation
    return q


def mc_pending(question: str, options: list[str], points: int = 1) -> dict:
    """Hören question whose answer can only be taken from the audio."""
    return {"type": "multiple_choice", "question": question, "options": options, "points": points}


def tf(statement: str, true: bool | None, explanation: str | None = None, passage: int = 1, points: int = 1) -> dict:
    q = {"type": "true_false", "question": statement, "points": points, "passage": passage}
    if true is not None:
        q["correct_answer"] = "richtig" if true else "falsch"
    if explanation:
        q["explanation"] = explanation
    return q


def gap(question: str, text: str, gaps: dict, points: int = 1, explanation: str | None = None, passage: int = 1, case_sensitive: bool = False) -> dict:
    """gaps: {"1": ["answer", "variant"]} or {"1": {"accepted": [...], "options": [...]}}."""
    q = {"type": "gap_fill", "question": question, "text": text, "gaps": gaps, "points": points, "passage": passage, "case_sensitive": case_sensitive}
    if explanation:
        q["explanation"] = explanation
    return q


def short(question: str, accepted: list[str], points: int = 1, explanation: str | None = None, max_length: int = 200, passage: int = 1) -> dict:
    q = {"type": "short_answer", "question": question, "accepted": accepted, "points": points, "max_length": max_length, "passage": passage}
    if explanation:
        q["explanation"] = explanation
    return q


def match(question: str, items: list[str], targets: list[str], pairs: dict, points: int = 1, explanation: str | None = None, passage: int = 1) -> dict:
    q = {"type": "matching", "question": question, "items": items, "targets": targets, "pairs": pairs, "points": points, "passage": passage}
    if explanation:
        q["explanation"] = explanation
    return q


def choice_gap(sentence: str, options: list[str], answer: str, question: str = "Wählen Sie das richtige Wort.", points: int = 1,
               explanation: str | None = None) -> dict:
    """A one-gap sentence ('Ich ___ müde.') as a Lückentext with a choice list."""
    text = sentence.replace("___", "[[1]]", 1)
    return gap(question, text, {"1": {"accepted": [answer], "options": options}}, points=points, explanation=explanation)


def text_gap(sentence: str, accepted: list[str], question: str = "Ergänzen Sie.", points: int = 1, explanation: str | None = None) -> dict:
    """A one-gap sentence with free input; accepted = every correct form."""
    return gap(question, sentence.replace("___", "[[1]]", 1), {"1": accepted}, points=points, explanation=explanation)


def exercise(title: str, questions: list[dict], instruction: str | None = None, source: str = "book") -> dict:
    out = {"title": title, "source": source, "questions": questions}
    if instruction:
        out["instruction"] = instruction
    return out


def words(rows: list[tuple], group: str | None = None) -> list[dict]:
    """rows: (word, translation) or (article, word, translation) or
    (article, word, plural, translation)."""
    out = []
    for row in rows:
        if len(row) == 2:
            art, w, pl, tr = None, row[0], None, row[1]
        elif len(row) == 3:
            art, w, tr = row
            pl = None
        else:
            art, w, pl, tr = row
        item = {"word": w, "translation": tr}
        if art:
            item["article"] = art
        if pl:
            item["plural"] = pl
        if group:
            item["group"] = group
        out.append(item)
    return out


def html_table(header: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def gap_paragraphs(question: str, text: str, gaps: dict) -> list[dict]:
    """A long Lückentext ([[1]] … [[n]], paragraphs separated by newlines) as
    one question per paragraph — a question holds at most 20 gaps. Gap ids
    stay the book's numbers; points = number of gaps."""
    import re

    out = []
    for n, para in enumerate([p for p in text.split("\n") if p.strip()], start=1):
        ids = re.findall(r"\[\[([0-9]+)\]\]", para)
        if not ids:
            continue
        out.append(gap(f"{question} ({n})", para, {i: gaps[i] for i in ids}, points=len(ids)))
    return out
