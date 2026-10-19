"""A1 Hören: answer keys from the VIZU answer-sheet PDF + automatic publishing.

The PDF ("Vizu-Javoblar A1") lists, per lesson ("N-Dars"), the answers of
every part; only the block "Hören – Eshitish qismi javoblari" is read here —
Grammatik / Lesen / Schreiben / Sprechen answers are never touched.

Nothing is guessed:
  * answers are assigned to the EXISTING Hören questions of A1 lesson N in
    their order (MC / Richtig-Falsch = one answer per question, Lückentext =
    one answer per gap); a lesson whose number of answers does not fit its
    questions is not assigned at all (shown for review);
  * a multiple-choice answer must be a letter of an existing option or an
    option's text; a name before "→" must appear in the question;
  * an answer that conflicts with an existing key, or a gap answer that
    already stands right next to the gap in the text (the sheet was made for
    a differently cut text), is only applied after an admin accepted it.
No question, option, task or attempt is created or deleted — only answer keys
of existing questions are filled. Re-running the import changes nothing that
already matches.

Publishing (A1 only): a Hören task is set "Veröffentlicht" when its uploaded
audio file exists on the server, it has questions and every question has a
complete answer key — after this import, after an audio upload and after the
questions were edited. Otherwise it keeps its status."""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.lesson import Lesson
from app.models.lesson_skill import QUESTION_GAP_FILL, QUESTION_MULTIPLE_CHOICE, QUESTION_TRUE_FALSE
from app.models.listening import Listening
from app.services.lesson_skills.question_types import GAP_PATTERN
from app.services.lms import structure

LEVEL = "A1"
MAX_PDF_BYTES = 20 * 1024 * 1024
LETTERS = "ABCDEF"
ARTICLES = ("der", "die", "das", "den", "dem", "des")

# slot status
NEW, MATCH, CONFLICT, SUSPICIOUS, INVALID = "new", "match", "conflict", "suspicious", "invalid"
REVIEW = (CONFLICT, SUSPICIOUS)


class PdfImportError(ValueError):
    pass


# ============================================================
# PDF -> text -> Hören blocks
# ============================================================


def pdf_text(data: bytes) -> str:
    if not data or len(data) > MAX_PDF_BYTES:
        raise PdfImportError("PDF_EMPTY_OR_TOO_LARGE: max 20 MB.")
    if not data.startswith(b"%PDF"):
        raise PdfImportError("NOT_A_PDF")
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > 200:
            raise PdfImportError("PDF_TOO_MANY_PAGES: max 200.")
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except PdfImportError:
        raise
    except Exception:
        raise PdfImportError("PDF_UNREADABLE") from None
    text = unicodedata.normalize("NFC", text)
    if not text.strip():
        raise PdfImportError("PDF_HAS_NO_TEXT: scanned images are not supported.")
    return text


LESSON_RE = re.compile(r"^\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*-\s*Dars(?:lar)?\b", re.I)
# a section heading "Hören – …" / "… va Hören – …", not a verb inside an answer
HOEREN_RE = re.compile(r"(?:^|\s)H(?:ö|oe)ren\s*[–—:-]", re.I)
STOP_RE = re.compile(r"^\s*(Schreiben|Sprechen|Lesen|Grammatik|Wortschatz|@vizu|\d{1,3}(?:\s*-\s*\d{1,3})?\s*-\s*Dars)", re.I)


@dataclass
class HoerenBlock:
    lessons: list[int]
    heading: str
    text: str  # answers only ("" = the sheet has no Hören answers for the lesson)


def hoeren_blocks(text: str) -> list[HoerenBlock]:
    """One block per lesson section that mentions Hören."""
    blocks: list[HoerenBlock] = []
    lessons: list[int] | None = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = LESSON_RE.match(line)
        if m:
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            lessons = list(range(a, b + 1)) if 0 < b - a < 10 else [a]
            i += 1
            continue
        if lessons and HOEREN_RE.search(line):
            heading = " ".join(line.split())
            if "javob" not in line.lower():  # e.g. "Lesen … va Hören … ovozli yuborasiz" — no answers
                blocks.append(HoerenBlock(lessons, heading, ""))
                i += 1
                continue
            body = [line.split(":", 1)[1] if ":" in line else ""]
            i += 1
            while i < len(lines) and not STOP_RE.match(lines[i]):
                body.append(lines[i])
                i += 1
            blocks.append(HoerenBlock(lessons, heading, "\n".join(body).strip()))
            continue
        i += 1
    return blocks


GROUP_RE = re.compile(r"((?:Text|Wetterbericht|Teil|Aufgabe|Dialog)\s*\d+|Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s*:", re.I)
NUMBERED_RE = re.compile(r"(?:(?<=^)|(?<=[\s,;]))(\d{1,2})\s*[).\-]\s*(?!\d)")


@dataclass
class Group:
    label: str | None
    answers: list[dict]  # {"text": str, "hint": str | None}
    numbered: bool = False
    problem: str | None = None


def _items(chunk: str) -> tuple[list[str], bool, str | None]:
    chunk = " ".join(chunk.split())
    marks = list(NUMBERED_RE.finditer(chunk))
    if len(marks) >= 2:
        numbers = [int(m.group(1)) for m in marks]
        if numbers != list(range(1, len(numbers) + 1)):
            return [], True, f"Nummerierung nicht fortlaufend: {numbers}"
        out = [chunk[m.end(): marks[k + 1].start() if k + 1 < len(marks) else len(chunk)] for k, m in enumerate(marks)]
        return [o.strip(" ,;") for o in out], True, None
    sep = ";" if ";" in chunk else "—" if "—" in chunk else ","
    return [p.strip() for p in chunk.split(sep)], False, None


def parse_groups(text: str) -> list[Group]:
    # drop title lines without answers ("Mein Tag in Taschkent matni javoblari:")
    lines = [ln for ln in text.splitlines() if ln.strip() and not (ln.strip().endswith(":") and not GROUP_RE.fullmatch(ln.strip()))]
    text = "\n".join(lines)
    parts = GROUP_RE.split(text)
    chunks: list[tuple[str | None, str]] = []
    if len(parts) == 1:
        chunks.append((None, parts[0]))
    else:
        if parts[0].strip():
            chunks.append((None, parts[0]))
        for k in range(1, len(parts), 2):
            chunks.append((" ".join(parts[k].split()), parts[k + 1]))
    groups = []
    for label, chunk in chunks:
        items, numbered, problem = _items(chunk)
        answers = []
        for item in items:
            item = item.strip().rstrip(".").strip()
            if not item:
                continue
            hint = None
            if "→" in item:
                hint, item = (s.strip() for s in item.split("→", 1))
            answers.append({"text": item, "hint": hint})
        groups.append(Group(label, answers, numbered, problem))
    return groups


# ============================================================
# Plan: PDF answers -> existing questions
# ============================================================


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    return " ".join(text.split()).strip().rstrip(".!?").strip().casefold()


def _bare(value: str) -> str:
    words = _norm(value).split()
    return " ".join(words[1:]) if len(words) > 1 and words[0] in ARTICLES else " ".join(words)


def _variants(answer: str) -> list[str]:
    """The PDF answer plus spellings that are the same answer: without the
    article ("das Brot" in "Ich esse [[1]]") and the time without a leading
    zero / with a dot (08:00 = 8:00 = 8.00)."""
    out = [answer.strip()]
    words = answer.split()
    if len(words) > 1 and words[0].casefold() in ARTICLES:
        out.append(" ".join(words[1:]))
    t = re.fullmatch(r"(\d{1,2})[:.](\d{2})", answer.strip())
    if t:
        h, mnt = int(t.group(1)), t.group(2)
        out += [f"{h:02d}:{mnt}", f"{h}:{mnt}", f"{h:02d}.{mnt}", f"{h}.{mnt}"]
    seen, uniq = set(), []
    for v in out:
        if v and v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


@dataclass
class Slot:
    id: str
    question_id: str
    question_no: int
    question: str
    kind: str  # MC | TF | GAP
    gap_id: str | None = None
    context: str = ""
    current: str | None = None
    answer: str | None = None
    hint: str | None = None
    status: str | None = None
    note: str | None = None
    # what is written: option index (MC/TF) or accepted list (GAP)
    value: object = None


def _slots(listening: Listening) -> tuple[list[Slot], str | None]:
    slots: list[Slot] = []
    for n, q in enumerate(sorted(listening.questions, key=lambda q: (q.order_index, q.created_at)), start=1):
        if q.question_type in (QUESTION_MULTIPLE_CHOICE, QUESTION_TRUE_FALSE):
            options = sorted(q.options, key=lambda o: o.order_index)
            correct = [o.option_text for o in options if o.is_correct]
            slots.append(Slot(f"{q.id}:-", str(q.id), n, q.question, "TF" if q.question_type == QUESTION_TRUE_FALSE else "MC",
                              context=" | ".join(f"{LETTERS[i] if i < len(LETTERS) else i + 1}) {o.option_text}" for i, o in enumerate(options)),
                              current=correct[0] if len(correct) == 1 else None))
        elif q.question_type == QUESTION_GAP_FILL:
            config = q.config or {}
            text = config.get("text") or ""
            for gid in GAP_PATTERN.findall(text):
                g = (config.get("gaps") or {}).get(gid)
                accepted = (g.get("accepted") if isinstance(g, dict) else g) or []
                accepted = [str(a) for a in (accepted if isinstance(accepted, list) else [accepted]) if str(a).strip()]
                slots.append(Slot(f"{q.id}:{gid}", str(q.id), n, q.question, "GAP", gap_id=gid, context=_gap_context(text, gid),
                                  current=", ".join(accepted) or None))
        else:
            return [], f"Frage {n}: Typ {q.question_type} wird vom PDF-Import nicht unterstützt"
    return slots, None


def _gap_context(text: str, gid: str, width: int = 40) -> str:
    marker = f"[[{gid}]]"
    i = text.find(marker)
    before = GAP_PATTERN.sub("___", text[max(0, i - width): i])
    after = GAP_PATTERN.sub("___", text[i + len(marker): i + len(marker) + width])
    return " ".join(f"…{before}[{gid}]{after}…".split())


def _neighbour_words(text: str, gid: str, n: int = 2) -> set[str]:
    marker = f"[[{gid}]]"
    i = text.find(marker)
    # "(fliegen)" after a gap is the verb hint of the exercise, not text
    clean = lambda s: [w.strip(".,;:!?()„“\"'").casefold() for w in GAP_PATTERN.sub(" ", re.sub(r"\([^)]*\)", " ", s)).split()]  # noqa: E731
    before, after = clean(text[:i])[-n:], clean(text[i + len(marker):])[:n]
    return {w for w in before + after if w}


def _resolve(slot: Slot, answer: dict, listening: Listening) -> None:
    slot.answer, slot.hint = answer["text"], answer.get("hint")
    q = next(q for q in listening.questions if str(q.id) == slot.question_id)
    if slot.kind in ("MC", "TF"):
        options = sorted(q.options, key=lambda o: o.order_index)
        a = answer["text"].strip()
        index = None
        if len(a) == 1 and a.upper() in LETTERS[: len(options)]:
            index = LETTERS.index(a.upper())
        else:
            words = {"r": "richtig", "f": "falsch", "true": "richtig", "false": "falsch", "wahr": "richtig"}
            key = words.get(a.casefold(), a.casefold())
            hits = [i for i, o in enumerate(options) if _norm(o.option_text) == _norm(key)]
            index = hits[0] if len(hits) == 1 else None
        if index is None:
            slot.status, slot.note = INVALID, f"„{a}“ passt zu keiner Antwortoption"
            return
        slot.value = index
        chosen = options[index].option_text
        if slot.hint and not all(w.casefold() in _norm(q.question) for w in slot.hint.split()):
            slot.status, slot.note = SUSPICIOUS, f"PDF nennt „{slot.hint}“, die Frage nicht"
        elif slot.current is None:
            slot.status = NEW
        elif _norm(slot.current) == _norm(chosen):
            slot.status = MATCH
        else:
            slot.status, slot.note = CONFLICT, f"bisher „{slot.current}“, PDF: „{chosen}“"
        slot.answer = f"{a} → {chosen}" if a.upper() in LETTERS and len(a) == 1 else chosen
        return
    # gap
    config = q.config or {}
    g = (config.get("gaps") or {}).get(slot.gap_id)
    options = g.get("options") if isinstance(g, dict) else None
    variants = _variants(answer["text"])
    slot.value = variants
    if options and not any(_bare(v) == _bare(o) for v in variants for o in options):
        slot.status, slot.note = INVALID, "nicht unter den Auswahlwörtern der Lücke"
        return
    current = [s.strip() for s in (slot.current or "").split(",") if s.strip()]
    neighbours = _neighbour_words(config.get("text") or "", slot.gap_id)
    if current and any(_bare(v) == _bare(c) for v in variants for c in current):
        slot.status = MATCH
    elif _bare(answer["text"]) in neighbours or _norm(answer["text"]) in neighbours:
        slot.status, slot.note = SUSPICIOUS, "das Wort steht schon direkt neben der Lücke — passt das PDF zu diesem Text?"
    elif not current:
        slot.status = NEW
    else:
        slot.status, slot.note = CONFLICT, f"bisher „{', '.join(current)}“"


@dataclass
class TaskPlan:
    listening_id: str
    title: str
    lesson_number: int
    slots: list[Slot] = field(default_factory=list)
    problem: str | None = None
    pdf_answers: list[str] = field(default_factory=list)


@dataclass
class LessonPlan:
    lesson_number: int
    lesson_id: str | None
    lesson_title: str | None
    heading: str
    status: str  # ok | no_answers | no_tasks | not_assigned | lesson_missing
    note: str | None = None
    tasks: list[TaskPlan] = field(default_factory=list)


def a1_lessons(db: Session) -> dict[int, Lesson]:
    course = structure.level_course(db, LEVEL)
    module = structure.main_module(db, course) if course else None
    return {lesson.number: lesson for lesson in structure.level_lessons(db, module)}


def lesson_listenings(db: Session, lesson_id) -> list[Listening]:
    rows = db.scalars(select(Listening).where(Listening.lesson_id == lesson_id)).all()
    # archived copies of rebuilt lessons ("[Archiv] …") are never targets
    rows = [r for r in rows if not (r.title or "").startswith("[Archiv]")]
    return sorted(rows, key=lambda r: (r.order_index or 0, r.content_id or "", r.created_at))


def build_plan(db: Session, text: str) -> list[LessonPlan]:
    lessons = a1_lessons(db)
    plans: list[LessonPlan] = []
    for block in hoeren_blocks(text):
        if len(block.lessons) > 1:
            numbers = "–".join(map(str, (block.lessons[0], block.lessons[-1])))
            status = "no_answers" if not block.text else "not_assigned"
            note = "keine Hören-Antworten im PDF" if not block.text else f"Abschnitt gilt für die Lektionen {numbers} — Zuordnung nicht eindeutig"
            for n in block.lessons:
                lesson = lessons.get(n)
                plans.append(LessonPlan(n, str(lesson.id) if lesson else None, lesson.title if lesson else None, block.heading, status, note))
            continue
        n = block.lessons[0]
        lesson = lessons.get(n)
        plan = LessonPlan(n, str(lesson.id) if lesson else None, lesson.title if lesson else None, block.heading, "ok")
        plans.append(plan)
        if lesson is None:
            plan.status, plan.note = "lesson_missing", f"A1 Lektion {n} existiert nicht"
            continue
        if not block.text:
            plan.status, plan.note = "no_answers", "keine Hören-Antworten im PDF (z. B. „ovozli yuborasiz“)"
            continue
        listenings = lesson_listenings(db, lesson.id)
        if not listenings:
            plan.status, plan.note = "no_tasks", "die Lektion hat keine Hören-Aufgabe"
            continue
        groups = parse_groups(block.text)
        broken = next((g.problem for g in groups if g.problem), None)
        tasks = [TaskPlan(str(lst.id), lst.title, n) for lst in listenings]
        task_slots = []
        for lst, tp in zip(listenings, tasks):
            slots, problem = _slots(lst)
            tp.slots, tp.problem = slots, problem
            task_slots.append(slots)
        if broken or any(tp.problem for tp in tasks):
            plan.status, plan.note = "not_assigned", broken or next(tp.problem for tp in tasks if tp.problem)
            continue
        # which answers belong to which task
        if len(groups) == len(tasks) > 1:
            by_label = []
            for g in groups:
                hits = [k for k, lst in enumerate(listenings) if g.label and _norm(g.label) in _norm(lst.title)]
                by_label.append(hits[0] if len(hits) == 1 else None)
            order = by_label if None not in by_label and len(set(by_label)) == len(tasks) else list(range(len(tasks)))
            assignment = {order[k]: groups[k].answers for k in range(len(groups))}
            per_task = [assignment[k] for k in range(len(tasks))]
        else:
            flat = [a for g in groups for a in g.answers]
            per_task, start = [], 0
            total = sum(len(s) for s in task_slots)
            if len(flat) != total:
                # "bin geflogen" = two gaps (helper verb + participle)
                tokens = [{"text": w, "hint": None} for a in flat for w in a["text"].split()]
                if len(tokens) == total and all(s.kind == "GAP" for slots in task_slots for s in slots):
                    flat = tokens
                    plan.note = "mehrteilige Antworten wurden auf einzelne Lücken verteilt (z. B. „bin geflogen“ → 2 Lücken)"
            for slots in task_slots:
                per_task.append(flat[start: start + len(slots)])
                start += len(slots)
            if start != len(flat):
                per_task = None
        if per_task is None or any(len(ans) != len(slots) for ans, slots in zip(per_task, task_slots)):
            got = sum(len(g.answers) for g in groups)
            want = sum(len(s) for s in task_slots)
            plan.status, plan.note = "not_assigned", f"PDF: {got} Antworten, Aufgaben: {want} Fragen/Lücken — keine Zuordnung"
            for g, tp in zip(groups, tasks):
                tp.pdf_answers = [a["text"] for a in g.answers]
            if len(groups) != len(tasks):
                tasks[0].pdf_answers = [a["text"] for g in groups for a in g.answers]
            plan.tasks = tasks
            continue
        for lst, tp, answers in zip(listenings, tasks, per_task):
            tp.pdf_answers = [a["text"] for a in answers]
            for slot, answer in zip(tp.slots, answers):
                _resolve(slot, answer, lst)
            # one doubtful gap means the sheet may be cut differently for the
            # whole sentence group — the other new answers of it wait as well
            doubtful = {s.question_id for s in tp.slots if s.kind == "GAP" and s.status == SUSPICIOUS}
            for s in tp.slots:
                if s.question_id in doubtful and s.status == NEW:
                    s.status, s.note = SUSPICIOUS, "eine andere Lücke dieser Frage passt nicht zum PDF — bitte prüfen"
        plan.tasks = tasks
    seen = {p.lesson_number for p in plans}
    for n, lesson in sorted(lessons.items()):
        if n not in seen:
            plans.append(LessonPlan(n, str(lesson.id), lesson.title, "", "no_answers", "kein Hören-Abschnitt im PDF"))
    return sorted(plans, key=lambda p: p.lesson_number)


# ============================================================
# Apply + publish
# ============================================================


def apply_plan(db: Session, plans: list[LessonPlan], accepted: set[str]) -> dict:
    """Writes NEW slots and the review slots (conflict / suspicious) the admin
    accepted. Returns counts; publishing is done by publish_ready()."""
    written = skipped_review = 0
    touched: set[str] = set()
    for plan in plans:
        for tp in plan.tasks:
            listening = db.get(Listening, tp.listening_id)
            if listening is None:
                continue
            questions = {str(q.id): q for q in listening.questions}
            for slot in tp.slots:
                if slot.status == NEW or (slot.status in REVIEW and slot.id in accepted):
                    q = questions.get(slot.question_id)
                    if q is None:
                        continue
                    if slot.kind in ("MC", "TF"):
                        for i, o in enumerate(sorted(q.options, key=lambda o: o.order_index)):
                            o.is_correct = i == slot.value
                    else:
                        config = dict(q.config or {})
                        gaps = dict(config.get("gaps") or {})
                        g = gaps.get(slot.gap_id)
                        g = dict(g) if isinstance(g, dict) else {}
                        g["accepted"] = list(slot.value)
                        gaps[slot.gap_id] = g
                        config["gaps"] = gaps
                        if all(_gap_filled(gaps.get(gid)) for gid in GAP_PATTERN.findall(config.get("text") or "")):
                            config.pop("pending", None)
                        q.config = config
                        flag_modified(q, "config")
                    written += 1
                    touched.add(tp.listening_id)
                elif slot.status in REVIEW:
                    skipped_review += 1
    db.commit()
    return {"written": written, "review_skipped": skipped_review, "listening_ids": sorted(touched)}


def _gap_filled(g) -> bool:
    accepted = g.get("accepted") if isinstance(g, dict) else g
    return bool(accepted) and any(str(a).strip() for a in (accepted if isinstance(accepted, list) else [accepted]))


def readiness(db: Session, listening: Listening) -> dict:
    """Why an A1 Hören task is (not) publishable — the same rules as the
    manual publish (audio + complete answer keys), plus: the audio FILE must
    really exist on the server, and every key must be verified in Lösung
    (an uploaded audio or a filled key alone never publishes)."""
    from app.services.lesson_skills import loesung
    from app.services.lesson_skills.admin import listening_audio_path
    from app.services.lesson_skills.exercises import has_key

    lesson = db.get(Lesson, listening.lesson_id)
    course, _ = structure.lesson_level(db, lesson) if lesson else (None, None)
    questions = list(listening.questions)
    missing = sum(1 for q in questions if not has_key(q))
    reviews = loesung._reviews(db, "hoeren", [q.id for q in questions])
    states = [loesung.question_state(q, reviews.get(q.id)) for q in questions if has_key(q)]
    unverified = sum(1 for s in states if not s["verified"] or s["needs_review"])
    if not listening.audio_storage_path:
        audio = "none"
    elif listening_audio_path(listening) is None:
        audio = "file_missing"
    else:
        audio = "ok"
    reasons = []
    if audio == "none":
        reasons.append("kein Audio hochgeladen")
    elif audio == "file_missing":
        reasons.append("Audiodatei fehlt auf dem Server")
    if not questions:
        reasons.append("keine Fragen")
    if missing:
        reasons.append(f"{missing} Frage(n) ohne Lösung")
    if unverified:
        reasons.append(f"{unverified} Lösung(en) noch nicht geprüft (Lösung-Seite)")
    return {
        "level": course.level if course else None,
        "audio": audio,
        "questions": len(questions),
        "key_missing": missing,
        "key_unverified": unverified,
        "ready": not reasons,
        "reasons": reasons,
    }


def auto_publish(db: Session, listening: Listening, *, commit: bool = True) -> str:
    """A1 only. Returns published | already | not_ready | not_a1."""
    state = readiness(db, listening)
    if state["level"] != LEVEL:
        return "not_a1"
    if not state["ready"]:
        return "not_ready"
    if listening.is_published:
        return "already"
    listening.is_published = True
    if commit:
        db.commit()
    return "published"


def publish_ready(db: Session, listening_ids: list[str] | None = None) -> list[dict]:
    """Auto-publishes the given (or all) A1 Hören tasks that are ready."""
    out = []
    lessons = a1_lessons(db)
    for n, lesson in sorted(lessons.items()):
        for lst in lesson_listenings(db, lesson.id):
            if listening_ids is not None and str(lst.id) not in listening_ids:
                continue
            result = auto_publish(db, lst, commit=False)
            out.append({"listening_id": str(lst.id), "lesson_number": n, "title": lst.title, "result": result, **readiness(db, lst),
                        "is_published": lst.is_published})
    db.commit()
    return out


def a1_status(db: Session) -> list[dict]:
    out = []
    for n, lesson in sorted(a1_lessons(db).items()):
        for lst in lesson_listenings(db, lesson.id):
            out.append({"listening_id": str(lst.id), "lesson_id": str(lesson.id), "lesson_number": n, "lesson_title": lesson.title,
                        "title": lst.title, "is_published": lst.is_published, "audio_name": lst.audio_original_name, **readiness(db, lst)})
    return out


def plan_json(plans: list[LessonPlan]) -> list[dict]:
    def slot(s: Slot) -> dict:
        return {k: getattr(s, k) for k in ("id", "question_no", "question", "kind", "gap_id", "context", "current", "answer", "hint", "status", "note")}

    return [
        {
            "lesson_number": p.lesson_number, "lesson_id": p.lesson_id, "lesson_title": p.lesson_title, "heading": p.heading,
            "status": p.status, "note": p.note,
            "tasks": [{"listening_id": t.listening_id, "title": t.title, "problem": t.problem, "pdf_answers": t.pdf_answers,
                       "slots": [slot(s) for s in t.slots] if p.status == "ok" else []} for t in p.tasks],
        }
        for p in plans
    ]


def summary(plans: list[LessonPlan]) -> dict:
    counts = {NEW: 0, MATCH: 0, CONFLICT: 0, SUSPICIOUS: 0, INVALID: 0}
    for p in plans:
        if p.status != "ok":
            continue
        for t in p.tasks:
            for s in t.slots:
                counts[s.status] = counts.get(s.status, 0) + 1
    return {"lessons": len(plans), "lessons_assigned": sum(1 for p in plans if p.status == "ok"), **counts}
