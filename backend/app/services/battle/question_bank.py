"""VIZU Battle question bank: text rounds (vocabulary + grammar) per CEFR level, next to the picture rounds (owner, 2026-11-19).

* Formats (FORMATS): translation de→uz / uz→de, choose the German word, gap in a sentence, grammatical form, article, verb form,
  synonym, antonym, collocation. Each has a fixed German + Uzbek instruction; an article question has 3 options (der / die / das),
  every other one 4 (one `answer` + `wrong`).
* Exactly one correct answer: the options are different after normalising, the answer is never among the wrong ones.
* No duplicates: `norm_key` = format + normalised prompt is unique per level (database constraint); an import or the seed skips a
  question whose key exists already and never adds it a second time.
* Only `published` questions of the stage's own level reach a match (C1+ plays C1); a match stores its own copy of each question, so
  editing or deleting a question never changes a running or finished match.
* Picture rounds (battle_words) stay as they are; `questions.build` mixes them in where the level has its own picture words.
The pure helpers (normalise, validate, fix_uz, pick, round_entry) are unit-tested without a database."""

from __future__ import annotations

import json
import random
import re
import unicodedata
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.battle import BattleMatch, BattleQuestion
from app.services.battle import config

LEVELS = config.WORD_LEVELS
KINDS = ("vocab", "grammar")
STATUSES = ("draft", "published", "disabled")
SOURCES = ("seed", "admin", "import")
PAGE = 30
MAX_IMPORT = 2000

# format → (options, instruction de, instruction uz); the language of the answer options follows from the format
FORMATS: dict[str, dict] = {
    "de_uz": {"options": 4, "de": "Was bedeutet das?", "uz": "So‘zning o‘zbekcha tarjimasini toping"},
    "uz_de": {"options": 4, "de": "Wie heißt das auf Deutsch?", "uz": "Nemischasini toping"},
    "word_choice": {"options": 4, "de": "Welches Wort passt?", "uz": "To‘g‘ri nemischa so‘zni tanlang"},
    "gap": {"options": 4, "de": "Ergänze die Lücke.", "uz": "Gapdagi bo‘sh joyni to‘ldiring"},
    "grammar": {"options": 4, "de": "Welche Form ist richtig?", "uz": "To‘g‘ri grammatik variantni tanlang"},
    "article": {"options": 3, "de": "Welcher Artikel ist richtig?", "uz": "To‘g‘ri artiklni tanlang"},
    "verb_form": {"options": 4, "de": "Welche Verbform ist richtig?", "uz": "Fe’lning to‘g‘ri shaklini tanlang"},
    "synonym": {"options": 4, "de": "Welches Wort bedeutet dasselbe?", "uz": "Mos sinonimni toping"},
    "antonym": {"options": 4, "de": "Was ist das Gegenteil?", "uz": "Antonimini toping"},
    "collocation": {"options": 4, "de": "Was vervollständigt die Verbindung?", "uz": "So‘z birikmasini to‘g‘ri yakunlang"},
}
# formats whose answer options are Uzbek (all others are German)
UZ_OPTIONS = ("de_uz",)
# formats whose prompt is Uzbek
UZ_PROMPT = ("uz_de",)
GAP = "___"

# topic → (kind, German label, Uzbek label)
TOPICS: dict[str, tuple[str, str, str]] = {
    # A1 vocabulary by theme
    "alltag": ("vocab", "Alltag", "Kundalik so‘zlar"),
    "familie": ("vocab", "Familie & Menschen", "Oila va insonlar"),
    "wohnen": ("vocab", "Haus & Wohnung", "Uy va jihozlar"),
    "essen": ("vocab", "Essen & Trinken", "Oziq-ovqat"),
    "farben_zahlen": ("vocab", "Farben & Zahlen", "Ranglar va raqamlar"),
    "berufe": ("vocab", "Berufe", "Kasblar"),
    "tiere": ("vocab", "Tiere", "Hayvonlar"),
    "zeit": ("vocab", "Zeit & Tagesablauf", "Vaqt va kun tartibi"),
    "verkehr": ("vocab", "Verkehr", "Transport"),
    "orte": ("vocab", "Orte & Wege", "Joylar va yo‘nalishlar"),
    "koerper": ("vocab", "Körper & Gesundheit", "Tana va salomatlik"),
    "kleidung": ("vocab", "Kleidung", "Kiyim-kechak"),
    "freizeit": ("vocab", "Freizeit & Hobby", "Bo‘sh vaqt"),
    "natur": ("vocab", "Wetter & Natur", "Ob-havo va tabiat"),
    "lernen_arbeit": ("vocab", "Schule & Arbeit", "O‘qish va ish"),
    # vocabulary by word type (A2–C1)
    "nomen": ("vocab", "Nomen", "Otlar"),
    "verben": ("vocab", "Verben", "Fe’llar"),
    "adjektive": ("vocab", "Adjektive", "Sifatlar"),
    "adverbien": ("vocab", "Adverbien", "Ravishlar"),
    "wendungen": ("vocab", "Wendungen", "Iboralar"),
    "konjunktionen": ("vocab", "Konjunktionen", "Bog‘lovchilar"),
    # vocabulary in use
    "synonyme_antonyme": ("vocab", "Synonyme & Antonyme", "Sinonim va antonimlar"),
    "kollokationen": ("vocab", "Kollokationen", "So‘z birikmalari"),
    "redemittel": ("vocab", "Redemittel", "Nutq iboralari"),
    "idiome": ("vocab", "Idiomatische Wendungen", "Frazeologizmlar"),
    "nomen_verb": ("vocab", "Nomen-Verb-Verbindungen", "Ot va fe’l birikmalari"),
    "funktionsverbgefuege": ("vocab", "Funktionsverbgefüge", "Funksional fe’l birikmalari"),
    "akademisch": ("vocab", "Akademische Lexik", "Akademik leksika"),
    "abstrakt": ("vocab", "Abstrakte Begriffe", "Mavhum tushunchalar"),
    "bedeutung": ("vocab", "Bedeutungsnuancen", "Ma’no nozikliklari"),
    "praezise_synonyme": ("vocab", "Präzise Synonyme", "Aniq sinonimlar"),
    # grammar
    "sein_haben": ("grammar", "sein & haben", "sein va haben fe’llari"),
    "praesens": ("grammar", "Präsens", "Hozirgi zamon"),
    "pronomen": ("grammar", "Personalpronomen", "Kishilik olmoshlari"),
    "w_fragen": ("grammar", "W-Fragen", "So‘roq so‘zlari"),
    "negation": ("grammar", "nicht & kein", "Inkor: nicht va kein"),
    "possessiv": ("grammar", "Possessivartikel", "Egalik artikllari"),
    "modalverben": ("grammar", "Modalverben", "Modal fe’llar"),
    "praep_zeit": ("grammar", "Präpositionen der Zeit", "Vaqt predloglari"),
    "akkusativ": ("grammar", "Akkusativ", "Akkusativ kelishigi"),
    "imperativ": ("grammar", "Imperativ", "Buyruq mayli"),
    "artikel": ("grammar", "Artikel", "Artikllar"),
    "akk_dat": ("grammar", "Akkusativ & Dativ", "Akkusativ va Dativ"),
    "perfekt": ("grammar", "Perfekt", "Perfekt (o‘tgan zamon)"),
    "trennbare_verben": ("grammar", "Trennbare Verben", "Ajraluvchi fe’llar"),
    "wechselpraep": ("grammar", "Wechselpräpositionen", "Ikki kelishikli predloglar"),
    "komparativ": ("grammar", "Komparativ & Superlativ", "Qiyosiy va orttirma daraja"),
    "praeteritum": ("grammar", "Präteritum", "Präteritum (o‘tgan zamon)"),
    "nebensaetze": ("grammar", "Nebensätze: weil, dass, wenn", "Ergash gaplar: weil, dass, wenn"),
    "adjektiv_verb": ("grammar", "Adjektive & Verben im Satz", "Sifat va fe’llarning qo‘llanishi"),
    "konnektoren": ("grammar", "Konnektoren", "Bog‘lovchi so‘zlar"),
    "relativsaetze": ("grammar", "Relativsätze", "Nisbiy ergash gaplar"),
    "passiv": ("grammar", "Passiv", "Majhul nisbat"),
    "infinitiv_zu": ("grammar", "Infinitiv mit zu", "zu bilan infinitiv"),
    "konjunktiv2": ("grammar", "Konjunktiv II", "Konjunktiv II (shart mayli)"),
    "plusquamperfekt": ("grammar", "Plusquamperfekt", "Plusquamperfekt (uzoq o‘tgan zamon)"),
    "praepositionen": ("grammar", "Präpositionen", "Predloglar"),
    "verben_praep": ("grammar", "Verben mit Präpositionen", "Predlogli fe’llar"),
    "adjektivdeklination": ("grammar", "Adjektivdeklination", "Sifatlarning turlanishi"),
    "wortbildung": ("grammar", "Wortbildung", "So‘z yasalishi"),
    "passiv_ersatz": ("grammar", "Passiv & Passiversatz", "Majhul nisbat va uning muqobillari"),
    "konjunktiv": ("grammar", "Konjunktiv I & II", "Konjunktiv I va II"),
    "nominalisierung": ("grammar", "Nominalisierung & Verbalisierung", "Otlashtirish va fe’llashtirish"),
    "partizipien": ("grammar", "Partizipialkonstruktionen", "Sifatdosh konstruksiyalari"),
    "nebensaetze_komplex": ("grammar", "Komplexe Nebensätze", "Murakkab ergash gaplar"),
    "praep_genitiv": ("grammar", "Präpositionen mit Genitiv", "Genitiv bilan predloglar"),
    "konnektoren_c1": ("grammar", "Anspruchsvolle Konnektoren", "Murakkab bog‘lovchilar"),
    "satzstrukturen": ("grammar", "Komplexe Satzstrukturen", "Murakkab gap tuzilmalari"),
    "nominalstil": ("grammar", "Nominalstil", "Nominal uslub"),
    "stilistik": ("grammar", "Stilistik & Wortbildung", "Uslubiyat va so‘z yasalishi"),
    "praep_komplex": ("grammar", "Komplexe Präpositionen", "Murakkab predloglar"),
    "grammatik_c1": ("grammar", "Anspruchsvolle Grammatik", "Murakkab grammatik tuzilmalar"),
}

_QUOTES = str.maketrans({"„": '"', "“": '"', "”": '"', "‚": "'", "‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "´": "'", "–": "-", "—": "-"})
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize(text: str | None) -> str:
    """Comparison form: NFC, lower case, typographic quotes / dashes unified, gaps as ___, spaces collapsed, end punctuation dropped."""
    t = unicodedata.normalize("NFC", text or "").translate(_QUOTES).lower()
    t = re.sub(r"_{2,}|…{1,}|\.{3,}", GAP, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t.rstrip(" .!?;:")


def norm_key(fmt: str, prompt: str) -> str:
    return f"{fmt}|{normalize(prompt)}"[:400]


def fix_uz(text: str | None) -> str | None:
    """Uzbek Latin apostrophes as the Wörterbuch writes them: o‘ / g‘ with U+2018, the tutuq belgisi with U+2019."""
    if text is None:
        return None
    t = unicodedata.normalize("NFC", text)
    t = re.sub(r"([oOgG])['`ʻʼ‘’´]", lambda m: m.group(1) + "‘", t)
    return re.sub(r"(?<=\w)['`ʻʼ´](?=\w)", "’", t)


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip()


def option_count(fmt: str) -> int:
    return FORMATS[fmt]["options"]


def validate(item: dict) -> list[str]:
    """Problems of one question (empty = fine). Keys: level, kind, format, topic, prompt, answer, wrong, hint, explanation."""
    problems = []
    level, kind, fmt, topic = item.get("level"), item.get("kind"), item.get("format"), item.get("topic")
    if level not in LEVELS:
        problems.append("LEVEL")
    if kind not in KINDS:
        problems.append("KIND")
    if fmt not in FORMATS:
        problems.append("FORMAT")
        return problems
    if topic not in TOPICS:
        problems.append("TOPIC")
    elif kind in KINDS and TOPICS[topic][0] != kind:
        problems.append("TOPIC_KIND")
    prompt, answer = clean(item.get("prompt")), clean(item.get("answer"))
    wrong = item.get("wrong")
    if not prompt or len(prompt) > 300:
        problems.append("PROMPT")
    if not answer or len(answer) > 160:
        problems.append("ANSWER")
    if not isinstance(wrong, list) or not all(isinstance(w, str) and clean(w) for w in wrong):
        problems.append("WRONG")
        return problems
    if len(wrong) != option_count(fmt) - 1:
        problems.append("OPTION_COUNT")
    opts = [normalize(answer), *(normalize(w) for w in wrong)]
    if len(set(opts)) != len(opts):
        problems.append("OPTIONS_NOT_UNIQUE")  # also: the answer repeated among the wrong options
    if any(len(clean(w)) > 160 for w in wrong):
        problems.append("WRONG")
    if fmt == "gap" and GAP not in normalize(prompt):
        problems.append("GAP_MISSING")
    if fmt == "article" and not {normalize(answer), *map(normalize, wrong)} <= {"der", "die", "das"}:
        problems.append("ARTICLE_OPTIONS")
    german = [prompt] if fmt not in UZ_PROMPT else []
    german += [answer, *wrong] if fmt not in UZ_OPTIONS else []
    uzbek = ([prompt] if fmt in UZ_PROMPT else []) + ([answer, *wrong] if fmt in UZ_OPTIONS else [])
    if any(_CYRILLIC.search(t) for t in german + uzbek + [item.get("hint") or "", item.get("explanation") or ""]):
        problems.append("CYRILLIC")
    if any(re.search(r"[oOgG]['`´]", t) for t in uzbek + [item.get("hint") or ""]):
        problems.append("UZ_APOSTROPHE")
    if any("  " in t or t != t.strip() for t in [item.get("prompt") or "", item.get("answer") or "", *wrong]):
        problems.append("SPACES")
    return problems


# ── pool and choice for a match ──────────────────────────────────────────────


def text_level(stage: str) -> str:
    """The question level of an arena stage: C1+ (Legende) plays the C1 questions."""
    return stage if stage in LEVELS else LEVELS[-1]


def pool(db: Session, level: str) -> list[BattleQuestion]:
    return list(db.execute(select(BattleQuestion).where(BattleQuestion.level == level, BattleQuestion.status == "published")).scalars())


def pool_size(db: Session, level: str) -> int:
    return db.execute(select(func.count()).select_from(BattleQuestion)
                      .where(BattleQuestion.level == level, BattleQuestion.status == "published")).scalar_one()


def recent_ids(db: Session, user_ids: list, matches: int = 3) -> set[str]:
    """Question ids of the players' last finished matches: a new match avoids them while the pool is big enough."""
    ids: set[str] = set()
    for uid in [u for u in user_ids if u]:
        rows = db.execute(select(BattleMatch.questions).where(or_(BattleMatch.player1_id == uid, BattleMatch.player2_id == uid),
                                                              BattleMatch.status == "finished")
                          .order_by(BattleMatch.finished_at.desc().nullslast()).limit(matches)).scalars()
        for qs in rows:
            ids.update(q["q"] for q in qs or [] if isinstance(q, dict) and q.get("t") == "q")
    return ids


def pick(candidates: list, n: int, rng: random.Random, avoid_ids: set[str] = frozenset(), avoid_refs: set[str] = frozenset(),
         topic_cap: int = 2, min_grammar: int = 0) -> list:
    """n different questions: never the same id or the same word (`ref`) twice, at most `topic_cap` per topic, at least `min_grammar`
    grammar questions when the pool has them; the players' recent questions only when nothing else is left."""
    fresh = [q for q in candidates if str(q.id) not in avoid_ids]
    stale = [q for q in candidates if str(q.id) in avoid_ids]
    rng.shuffle(fresh)
    rng.shuffle(stale)
    ordered = fresh + stale
    chosen, refs, per_topic = [], {r.lower() for r in avoid_refs if r}, {}

    def take(q, cap: int) -> bool:
        ref = (q.ref or "").lower()
        if q in chosen or (ref and ref in refs) or per_topic.get(q.topic, 0) >= cap:
            return False
        chosen.append(q)
        per_topic[q.topic] = per_topic.get(q.topic, 0) + 1
        if ref:
            refs.add(ref)
        return True

    for q in ordered:  # the grammar share first
        if sum(c.kind == "grammar" for c in chosen) >= min_grammar:
            break
        if q.kind == "grammar":
            take(q, topic_cap)
    for cap in (topic_cap, n):  # then everything; the topic cap is relaxed only for a small pool
        for q in ordered:
            if len(chosen) >= n:
                break
            take(q, cap)
    rng.shuffle(chosen)
    return chosen[:n]


def round_entry(q: BattleQuestion, pos: int, rng: random.Random) -> dict:
    """The match's own copy of a question: options in random order with the answer at `pos` (folded into the option count)."""
    wrong = list(q.wrong or [])
    rng.shuffle(wrong)
    count = len(wrong) + 1
    pos = pos if pos < count else rng.randrange(count)
    opts = wrong[:]
    opts.insert(pos, q.answer)
    return {"t": "q", "q": str(q.id), "fmt": q.format, "kind": q.kind, "topic": q.topic, "p": q.prompt, "h": q.hint, "opts": opts, "c": pos,
            "x": q.explanation, "ref": q.ref}


def topic_label(topic: str | None) -> dict | None:
    if topic not in TOPICS:
        return None
    _, de, uz = TOPICS[topic]
    return {"de": de, "uz": uz}


def instruction(fmt: str | None) -> dict | None:
    f = FORMATS.get(fmt or "")
    return {"de": f["de"], "uz": f["uz"]} if f else None


# ── admin: statistics, list, create / edit / delete, import ─────────────────


def view(q: BattleQuestion) -> dict:
    return {
        "id": str(q.id), "seed_id": q.seed_id, "level": q.level, "kind": q.kind, "format": q.format, "topic": q.topic, "prompt": q.prompt,
        "hint": q.hint, "answer": q.answer, "wrong": list(q.wrong or []), "explanation": q.explanation, "status": q.status, "source": q.source,
        "ref": q.ref, "problems": validate(_as_item(q)), "updated_at": q.updated_at.isoformat() if q.updated_at else None,
    }


def _as_item(q: BattleQuestion) -> dict:
    return {"level": q.level, "kind": q.kind, "format": q.format, "topic": q.topic, "prompt": q.prompt, "answer": q.answer,
            "wrong": list(q.wrong or []), "hint": q.hint, "explanation": q.explanation}


def stats(db: Session) -> dict:
    """Per level: total, vocabulary / grammar, by status, possible duplicates, questions with problems — and per topic / format."""
    rows = db.execute(select(BattleQuestion)).scalars().all()
    levels = {lv: {"total": 0, "vocab": 0, "grammar": 0, "published": 0, "draft": 0, "disabled": 0, "duplicates": 0, "problems": 0,
                   "active_vocab": 0, "active_grammar": 0} for lv in LEVELS}
    topics: dict[str, dict] = {}
    formats: dict[str, dict] = {}
    same_prompt: dict[tuple, int] = {}
    for q in rows:
        r = levels.setdefault(q.level, {k: 0 for k in levels[LEVELS[0]]})
        r["total"] += 1
        r[q.kind] = r.get(q.kind, 0) + 1
        r[q.status] = r.get(q.status, 0) + 1
        if q.status == "published":
            r[f"active_{q.kind}"] = r.get(f"active_{q.kind}", 0) + 1
        if validate(_as_item(q)):
            r["problems"] += 1
        key = (q.level, normalize(q.prompt), normalize(q.answer))
        same_prompt[key] = same_prompt.get(key, 0) + 1
        t = topics.setdefault(f"{q.level}|{q.topic}", {"level": q.level, "topic": q.topic, "label": (topic_label(q.topic) or {}).get("de", q.topic),
                                                       "kind": q.kind, "total": 0, "published": 0})
        t["total"] += 1
        t["published"] += q.status == "published"
        f = formats.setdefault(q.format, {"format": q.format, "total": 0})
        f["total"] += 1
    for (lv, _, _), n in same_prompt.items():
        if n > 1 and lv in levels:
            levels[lv]["duplicates"] += n - 1  # the same prompt + answer in another format
    return {"levels": levels, "topics": sorted(topics.values(), key=lambda t: (t["level"], t["kind"], t["label"])),
            "formats": sorted(formats.values(), key=lambda f: f["format"]), "min_per_level": 500,
            "topic_labels": {k: {"kind": v[0], "de": v[1], "uz": v[2]} for k, v in TOPICS.items()},
            "format_labels": {k: {"de": v["de"], "uz": v["uz"], "options": v["options"]} for k, v in FORMATS.items()}}


def list_questions(db: Session, level: str | None, kind: str | None, topic: str | None, status: str | None, fmt: str | None, q: str,
                   problems_only: bool, page: int) -> dict:
    query = select(BattleQuestion)
    for col, val in ((BattleQuestion.level, level), (BattleQuestion.kind, kind), (BattleQuestion.topic, topic), (BattleQuestion.status, status),
                     (BattleQuestion.format, fmt)):
        if val:
            query = query.where(col == val)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(BattleQuestion.prompt).like(like), func.lower(BattleQuestion.answer).like(like)))
    query = query.order_by(BattleQuestion.level, BattleQuestion.topic, BattleQuestion.prompt)
    if problems_only:
        items = [view(x) for x in db.execute(query).scalars() if validate(_as_item(x))]
        total = len(items)
        items = items[(page - 1) * PAGE: page * PAGE]
    else:
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
        items = [view(x) for x in db.execute(query.offset((page - 1) * PAGE).limit(PAGE)).scalars()]
    return {"items": items, "total": total, "page": page, "page_size": PAGE}


def _prepare(data: dict) -> dict:
    """Cleans an admin / import item; the kind follows from the topic when it is missing; Uzbek apostrophes are unified."""
    fmt = data.get("format")
    item = {
        "level": data.get("level"), "format": fmt, "topic": data.get("topic"),
        "kind": data.get("kind") or (TOPICS[data["topic"]][0] if data.get("topic") in TOPICS else None),
        "prompt": clean(data.get("prompt")), "answer": clean(data.get("answer")),
        "wrong": [clean(w) for w in data.get("wrong") or [] if isinstance(w, str)],
        "hint": clean(data.get("hint")) or None, "explanation": clean(data.get("explanation")) or None,
        "status": data.get("status") or "draft", "ref": clean(data.get("ref")) or None,
    }
    if fmt in UZ_PROMPT:
        item["prompt"] = fix_uz(item["prompt"])
    if fmt in UZ_OPTIONS:
        item["answer"], item["wrong"] = fix_uz(item["answer"]), [fix_uz(w) for w in item["wrong"]]
    item["hint"] = fix_uz(item["hint"])
    return item


def _check(item: dict) -> None:
    problems = validate(item)
    if item["status"] not in STATUSES:
        problems.append("STATUS")
    if problems:
        raise HTTPException(422, f"BATTLE_QUESTION_INVALID: {', '.join(problems)}")


def _duplicate(db: Session, level: str, key: str, exclude=None):
    query = select(BattleQuestion.id).where(BattleQuestion.level == level, BattleQuestion.norm_key == key)
    if exclude is not None:
        query = query.where(BattleQuestion.id != exclude)
    return db.execute(query.limit(1)).scalar_one_or_none()


def _get(db: Session, question_id) -> BattleQuestion:
    q = db.get(BattleQuestion, question_id)
    if q is None:
        raise HTTPException(404, "BATTLE_QUESTION_NOT_FOUND")
    return q


def create(db: Session, user, data: dict) -> dict:
    item = _prepare(data)
    _check(item)
    key = norm_key(item["format"], item["prompt"])
    if _duplicate(db, item["level"], key):
        raise HTTPException(409, "BATTLE_QUESTION_DUPLICATE: Bu savol shu darajada allaqachon bor")
    q = BattleQuestion(**{k: item[k] for k in ("level", "kind", "format", "topic", "prompt", "answer", "wrong", "hint", "explanation", "status", "ref")},
                       norm_key=key, source="admin", created_by=user.id, updated_by=user.id)
    db.add(q)
    db.flush()
    write_audit(db, actor_id=str(user.id), action="battle_question_created", details=f"{q.id} {q.level} {q.format} {q.topic}")
    db.commit()
    return view(q)


def update(db: Session, user, question_id, data: dict) -> dict:
    q = _get(db, question_id)
    clearable = ("hint", "explanation", "ref")  # an explicit null empties these; for every other field null = unchanged
    merged = {**_as_item(q), "status": q.status, "ref": q.ref, **{k: v for k, v in data.items() if v is not None or k in clearable}}
    item = _prepare(merged)
    _check(item)
    key = norm_key(item["format"], item["prompt"])
    if _duplicate(db, item["level"], key, exclude=q.id):
        raise HTTPException(409, "BATTLE_QUESTION_DUPLICATE: Bu savol shu darajada allaqachon bor")
    before = json.dumps(_as_item(q), ensure_ascii=False)
    for k in ("level", "kind", "format", "topic", "prompt", "answer", "wrong", "hint", "explanation", "status", "ref"):
        setattr(q, k, item[k])
    q.norm_key, q.updated_by = key, user.id
    write_audit(db, actor_id=str(user.id), action="battle_question_updated", details=f"{q.id} before={before}"[:4000])
    db.commit()
    return view(q)


def delete(db: Session, user, question_id) -> dict:
    """Removes a question for good (matches keep their own copy, no learner history points at it); the audit entry keeps its content."""
    q = _get(db, question_id)
    snapshot = json.dumps({**_as_item(q), "seed_id": q.seed_id, "status": q.status, "source": q.source}, ensure_ascii=False)
    db.delete(q)
    write_audit(db, actor_id=str(user.id), action="battle_question_deleted", details=f"{question_id} {snapshot}"[:4000])
    db.commit()
    return {"deleted": str(question_id)}


def import_questions(db: Session, user, items: list[dict], apply: bool, publish: bool) -> dict:
    """Checks a list of questions (JSON) — valid / duplicate (in the list or already in the bank) / invalid with reasons — and, with
    `apply`, adds the valid new ones (source `import`, published or draft). Nothing existing is changed."""
    if len(items) > MAX_IMPORT:
        raise HTTPException(422, f"BATTLE_IMPORT_TOO_LARGE: at most {MAX_IMPORT} questions per import")
    seen: set[tuple] = set()
    report = {"total": len(items), "valid": 0, "duplicates": 0, "invalid": 0, "added": 0, "errors": []}
    ready = []
    for i, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            report["invalid"] += 1
            report["errors"].append({"row": i, "problems": ["NOT_AN_OBJECT"]})
            continue
        item = _prepare({**raw, "status": "published" if publish else "draft"})
        problems = validate(item)
        if problems:
            report["invalid"] += 1
            report["errors"].append({"row": i, "problems": problems, "prompt": item["prompt"][:80]})
            continue
        key = norm_key(item["format"], item["prompt"])
        if (item["level"], key) in seen or _duplicate(db, item["level"], key):
            report["duplicates"] += 1
            continue
        seen.add((item["level"], key))
        report["valid"] += 1
        ready.append((item, key))
    report["errors"] = report["errors"][:200]
    if apply and ready:
        for item, key in ready:
            db.add(BattleQuestion(**{k: item[k] for k in ("level", "kind", "format", "topic", "prompt", "answer", "wrong", "hint", "explanation", "status", "ref")},
                                  norm_key=key, source="import", created_by=user.id, updated_by=user.id))
        db.flush()
        report["added"] = len(ready)
        write_audit(db, actor_id=str(user.id), action="battle_questions_imported",
                    details=f"{len(ready)} added, {report['duplicates']} duplicates, {report['invalid']} invalid ({'published' if publish else 'draft'})")
        db.commit()
    return report
