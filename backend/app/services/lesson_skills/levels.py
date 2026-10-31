"""CEFR level profiles A1-C1: default rubrics for Schreiben / Sprechen and the
level expectations used by the AI evaluation prompts. One place for all five
levels — the components and APIs are level-agnostic.

Every rubric totals 100 points. Admins can replace the rubric per task; these
are the defaults when a task has none."""

from uuid import UUID

from sqlalchemy.orm import Session

LEVELS = ["A1", "A2", "B1", "B2", "C1"]
DEFAULT_LEVEL = "A1"

# Uzbek names, as shown to students (feedback default language uz)
_W = {
    "task": "Topshiriqni bajarish",
    "content": "Mazmun va mavzuga moslik",
    "grammar": "Grammatika",
    "vocabulary": "Lug'at",
    "vocabulary_a": "Lug'at va mavzuga moslik",
    "coherence": "Gaplar tuzilishi va mantiqiy bog'lanish",
    "structure": "Matn tuzilishi va bog'lovchilar",
    "register": "Uslub va registr",
    "spelling": "Imlo va tinish belgilari",
}

WRITING_RUBRICS: dict[str, list[dict]] = {
    "A1": [
        {"key": "task", "name": _W["task"], "max": 25},
        {"key": "grammar", "name": _W["grammar"], "max": 25},
        {"key": "vocabulary", "name": _W["vocabulary_a"], "max": 20},
        {"key": "coherence", "name": _W["coherence"], "max": 15},
        {"key": "spelling", "name": _W["spelling"], "max": 15},
    ],
    # A2 Schreiben analysis: the seven criteria of the VIZU A2 course (2026-11-01)
    "A2": [
        {"key": "task", "name": "Aufgabenbewältigung — topshiriqni bajarish", "max": 20},
        {"key": "grammar", "name": "Grammatik — grammatik to'g'rilik", "max": 15},
        {"key": "vocabulary", "name": "Wortschatz — so'z boyligi va qo'llash", "max": 15},
        {"key": "sentence", "name": "Satzbau — gap tuzilishi", "max": 15},
        {"key": "spelling", "name": "Rechtschreibung — imlo", "max": 10},
        {"key": "coherence", "name": "Kohärenz — matn izchilligi", "max": 15},
        {"key": "structure", "name": "Textstruktur — matn tuzilishi", "max": 10},
    ],
    "B1": [
        {"key": "task", "name": _W["task"], "max": 25},
        {"key": "structure", "name": _W["structure"], "max": 20},
        {"key": "grammar", "name": _W["grammar"], "max": 25},
        {"key": "vocabulary", "name": _W["vocabulary"], "max": 20},
        {"key": "spelling", "name": _W["spelling"], "max": 10},
    ],
    "B2": [
        {"key": "task", "name": _W["task"], "max": 20},
        {"key": "structure", "name": _W["structure"], "max": 20},
        {"key": "grammar", "name": _W["grammar"], "max": 20},
        {"key": "vocabulary", "name": _W["vocabulary"], "max": 20},
        {"key": "register", "name": _W["register"], "max": 10},
        {"key": "spelling", "name": _W["spelling"], "max": 10},
    ],
    "C1": [
        {"key": "task", "name": _W["task"], "max": 20},
        {"key": "structure", "name": _W["structure"], "max": 20},
        {"key": "grammar", "name": _W["grammar"], "max": 20},
        {"key": "vocabulary", "name": _W["vocabulary"], "max": 20},
        {"key": "register", "name": _W["register"], "max": 15},
        {"key": "spelling", "name": _W["spelling"], "max": 5},
    ],
}

_S = {
    "content": "Savolga javob va mazmun",
    "structure": "Nutq tuzilishi va bog'lanish",
    "interaction": "Muloqot va javob qaytarish",
    "grammar": "Grammatika",
    "vocabulary": "Lug'at",
    "pronunciation": "Talaffuz",
    "fluency": "Ravonlik va tushunarlilik",
}

SPEAKING_RUBRICS: dict[str, list[dict]] = {
    "A1": [
        {"key": "content", "name": _S["content"], "max": 25},
        {"key": "grammar", "name": _S["grammar"], "max": 20},
        {"key": "vocabulary", "name": _S["vocabulary"], "max": 20},
        {"key": "pronunciation", "name": _S["pronunciation"], "max": 20},
        {"key": "fluency", "name": _S["fluency"], "max": 15},
    ],
    "A2": [
        {"key": "content", "name": _S["content"], "max": 25},
        {"key": "grammar", "name": _S["grammar"], "max": 20},
        {"key": "vocabulary", "name": _S["vocabulary"], "max": 20},
        {"key": "pronunciation", "name": _S["pronunciation"], "max": 20},
        {"key": "fluency", "name": _S["fluency"], "max": 15},
    ],
    "B1": [
        {"key": "content", "name": _S["content"], "max": 25},
        {"key": "structure", "name": _S["structure"], "max": 15},
        {"key": "grammar", "name": _S["grammar"], "max": 20},
        {"key": "vocabulary", "name": _S["vocabulary"], "max": 15},
        {"key": "pronunciation", "name": _S["pronunciation"], "max": 15},
        {"key": "fluency", "name": _S["fluency"], "max": 10},
    ],
    "B2": [
        {"key": "content", "name": _S["content"], "max": 20},
        {"key": "structure", "name": _S["structure"], "max": 20},
        {"key": "grammar", "name": _S["grammar"], "max": 20},
        {"key": "vocabulary", "name": _S["vocabulary"], "max": 15},
        {"key": "pronunciation", "name": _S["pronunciation"], "max": 15},
        {"key": "fluency", "name": _S["fluency"], "max": 10},
    ],
    "C1": [
        {"key": "content", "name": _S["content"], "max": 20},
        {"key": "structure", "name": _S["structure"], "max": 20},
        {"key": "grammar", "name": _S["grammar"], "max": 15},
        {"key": "vocabulary", "name": _S["vocabulary"], "max": 20},
        {"key": "pronunciation", "name": _S["pronunciation"], "max": 10},
        {"key": "fluency", "name": _S["fluency"], "max": 15},
    ],
}

# What a learner at the level is expected to produce (used in AI prompts, Uzbek)
WRITING_EXPECTATIONS = {
    "A1": "A1 darajasi: juda qisqa, oddiy gaplar (Ich heiße…, Ich wohne in…). Kundalik so'zlar. Murakkab ergash gaplar talab qilinmaydi. Avvalo topshiriq talabi va mazmun bajarilganini bahola; B1+ talablarini qo'llama.",
    "A2": "A2 darajasi: qisqa bog'langan gaplar (und, aber, weil, dann), oddiy o'tgan zamon (Perfekt), kundalik vaziyatlar (xabar, qisqa e-mail). Fe'l ikkinchi o'rinda, weil/dass dan keyin fe'l oxirida bo'lishi kutiladi; murakkab ergash gaplar, Konjunktiv, nominal uslub va rasmiy registr TALAB QILINMAYDI. Tushunishga xalaqit bermaydigan kichik xatolarni qattiq jazolama. B1/B2/C1 talablarini qo'llama.",
    "B1": "B1 darajasi: bog'langan, mantiqiy tuzilgan matn; fikrni asoslash, ergash gaplar (weil, dass, obwohl), Präteritum/Perfekt, mos murojaat va xayrlashuv shakllari (xat, e-mail, forum). Kichik xatolar tushunishga xalaqit bermasa, qattiq jazolama.",
    "B2": "B2 darajasi: aniq va batafsil matn, argumentlar va qarama-qarshi fikrlar, turli bog'lovchilar, Konjunktiv II va Passiv, rasmiy/norasmiy registrni to'g'ri tanlash. Grammatik aniqlik va matn tuzilishi muhim.",
    "C1": "C1 darajasi: murakkab, yaxshi tuzilgan, uslubiy jihatdan mos matn; nozik ma'no farqlari, idiomatik ifodalar, nominal uslub, registrni izchil saqlash, xulosalar va yashirin ma'nolarni ifodalash. Talablar yuqori, lekin topshiriq turiga mos baholansin.",
}

SPEAKING_EXPECTATIONS = {
    "A1": "A1 darajasi: qisqa, oddiy gaplar; o'zi haqida asosiy ma'lumot. Uzilishlar va to'xtashlar normal. Yuqori daraja talablarini qo'llama.",
    "A2": "A2 darajasi: kundalik vaziyatlarda qisqa bog'langan gaplar, oddiy savol-javob, Perfekt. Sekin va to'xtab gapirish normal.",
    "B1": "B1 darajasi: tanish mavzularda bog'langan nutq, fikr va sabablarni bildirish, voqea hikoya qilish. Ba'zi xatolar va to'xtashlar mumkin, lekin fikr tushunarli bo'lishi kerak.",
    "B2": "B2 darajasi: aniq, batafsil va ravon nutq, fikrni dalillar bilan himoya qilish, afzallik/kamchiliklarni solishtirish, suhbatda faol ishtirok.",
    "C1": "C1 darajasi: ravon, spontan va yaxshi tuzilgan nutq; murakkab mavzular, nozik fikrlar, idiomatik ifodalar, registrni moslash.",
}


# Written tasks that are NOT Schreiben (writings.competency): what they check.
# Their own rubric — a Wortschatz worksheet is never scored with Schreiben criteria.
COMPETENCY_RUBRICS: dict[str, list[dict]] = {
    "WORTSCHATZ": [
        {"key": "meaning", "name": "So'z ma'nosi va tarjima", "max": 40},
        {"key": "usage", "name": "So'zni gapda to'g'ri qo'llash", "max": 40},
        {"key": "form", "name": "Shakl: artikl, ko'plik, imlo", "max": 20},
    ],
    "GRAMMATIK": [
        {"key": "target", "name": "Mavzudagi grammatik struktura", "max": 60},
        {"key": "accuracy", "name": "Umumiy grammatik to'g'rilik", "max": 25},
        {"key": "spelling", "name": "Imlo", "max": 15},
    ],
    "LESEN": [
        {"key": "comprehension", "name": "Matnni tushunish: javoblar to'g'riligi", "max": 80},
        {"key": "answer", "name": "Javobning aniqligi va tili", "max": 20},
    ],
}

COMPETENCY_TASKS = {
    "WORTSCHATZ": "Bu Schreiben (yozma ish) EMAS, balki Wortschatz (lug'at) topshirig'i: so'zlarning ma'nosi, tarjimasi va gapda to'g'ri qo'llanishini tekshir. Matn tuzilishi, uslub yoki izchillikni baholama.",
    "GRAMMATIK": "Bu Schreiben (yozma ish) EMAS, balki Grammatik mashqi: avvalo topshiriqdagi grammatik struktura to'g'ri qo'llanganini tekshir. Mazmun, uslub va matn tuzilishini baholama.",
    "LESEN": "Bu Schreiben (yozma ish) EMAS, balki Lesen (o'qish) topshirig'ining ochiq savollari: javob quyidagi matnga muvofiqmi — faqat shuni tekshir. Til xatolari javob ma'nosini buzmasa, kam ball ayirma. Matnda yo'q ma'lumotni to'g'ri javob deb hisoblama.",
}


def competency_rubric(competency: str | None, level: str | None) -> list[dict]:
    """The default rubric of a written task: the level's Schreiben rubric, or
    the rubric of the competency the task belongs to."""
    if competency in COMPETENCY_RUBRICS:
        return [dict(c) for c in COMPETENCY_RUBRICS[competency]]
    return writing_rubric(level)


def normalise_level(level: str | None) -> str:
    value = (level or "").strip().upper()
    return value if value in LEVELS else DEFAULT_LEVEL


def writing_rubric(level: str | None) -> list[dict]:
    return [dict(c) for c in WRITING_RUBRICS[normalise_level(level)]]


def speaking_rubric(level: str | None) -> list[dict]:
    return [dict(c) for c in SPEAKING_RUBRICS[normalise_level(level)]]


def lesson_level(db: Session, lesson_id: UUID | str | None) -> str:
    """CEFR level of a lesson via Lesson -> Module -> Course.level."""
    from app.models.course import Course
    from app.models.lesson import Lesson
    from app.models.module import Module

    if lesson_id is None:
        return DEFAULT_LEVEL
    lesson = db.get(Lesson, lesson_id)
    module = db.get(Module, lesson.module_id) if lesson else None
    course = db.get(Course, module.course_id) if module else None
    return normalise_level(course.level if course else None)


def all_default_rubrics() -> dict:
    return {lv: {"writing": writing_rubric(lv), "speaking": speaking_rubric(lv)} for lv in LEVELS}


# Authoring guide per level — used by the content import (warnings when a
# Claude-generated item is far outside the usual range) and by the Claude
# generation instructions (app/services/content_import/guide.py).
LEVEL_GUIDE = {
    "A1": {
        "reading_words": (30, 150), "writing_words": (20, 80), "speaking_seconds": (20, 90),
        "lesen": "Sehr kurze Texte (Steckbrief, Nachricht, Schild, einfache E-Mail). Bekannte Wörter, Präsens, Hauptsätze. Fragen nach expliziten Einzelinformationen (Name, Alter, Ort, Uhrzeit, Preis).",
        "hoeren": "Kurze, langsam gesprochene Alltagsdialoge und Ansagen (30-60 s). Einzelinformationen: Zahlen, Uhrzeiten, Orte, Namen.",
        "schreiben": "Kurze Mitteilung, Formular, einfache Nachricht/E-Mail an Freunde (sich vorstellen, Termin, Einladung). 3-5 einfache Sätze.",
        "sprechen": "Sich vorstellen, einfache Fragen stellen und beantworten, Bitten formulieren. Monolog 20-60 s.",
        "text_types": ["message", "email", "description", "other"],
    },
    "A2": {
        "reading_words": (80, 250), "writing_words": (30, 100), "speaking_seconds": (30, 120),
        "lesen": "Kurze Alltagstexte (Anzeige, E-Mail, Programm, Speisekarte, kurzer Bericht). Hauptinformation und Details, einfache Verbindungen (weil, dann, aber). Perfekt.",
        "hoeren": "Alltagsgespräche, Durchsagen, Telefonnachrichten (45-90 s) in normalem, deutlichem Tempo.",
        "schreiben": "Persönliche Nachricht oder E-Mail (Einladung, Absage, Bitte, kurzer Bericht über ein Erlebnis), 30-80 Wörter mit allen Inhaltspunkten.",
        "sprechen": "Über Alltag, Familie, Freizeit, Erlebnisse sprechen; einfache Gespräche planen (Monolog oder Dialog).",
        "text_types": ["message", "email", "letter", "description", "other"],
    },
    "B1": {
        "reading_words": (200, 450), "writing_words": (80, 150), "speaking_seconds": (60, 180),
        "lesen": "Zusammenhängende Sachtexte, Blog- und Forumsbeiträge, Zeitungsmeldungen, Anzeigen. Hauptaussagen, Meinungen, Zuordnung von Texten zu Situationen.",
        "hoeren": "Radiobeiträge, Interviews, Gespräche über bekannte Themen (1-3 min). Hauptaussagen und wichtige Details.",
        "schreiben": "Persönlicher oder halbformeller Brief / E-Mail, Forumsbeitrag mit Meinung und Begründung, 80-150 Wörter.",
        "sprechen": "Ein Thema präsentieren, Erfahrungen und Meinungen begründen, gemeinsam etwas planen (Dialog).",
        "text_types": ["email", "letter", "opinion", "description", "report", "other"],
    },
    "B2": {
        "reading_words": (350, 700), "writing_words": (150, 250), "speaking_seconds": (90, 240),
        "lesen": "Längere argumentative und informative Texte (Kommentar, Reportage, Fachartikel populär). Detailverstehen, Haltung des Autors, Argumentationsstruktur.",
        "hoeren": "Vorträge, Diskussionen, Radiosendungen (2-5 min) in natürlichem Tempo. Standpunkte, Details, Schlussfolgerungen.",
        "schreiben": "Formeller Brief (Beschwerde, Anfrage), Stellungnahme / Forumsbeitrag mit Pro und Contra, 150-250 Wörter, passendes Register.",
        "sprechen": "Vortrag zu einem Thema, Diskussion mit Argumenten, Vor- und Nachteile abwägen, Kompromiss aushandeln.",
        "text_types": ["letter", "email", "opinion", "essay", "report", "other"],
    },
    "C1": {
        "reading_words": (500, 1000), "writing_words": (200, 350), "speaking_seconds": (120, 300),
        "lesen": "Komplexe Texte (Essays, wissenschaftsnahe Artikel, Literaturausschnitte). Implizite Aussagen, Schlussfolgerungen, Stil und Ton, Textabsicht.",
        "hoeren": "Anspruchsvolle Vorträge, Debatten, Interviews (3-6 min) mit Fachwortschatz. Implizite Haltungen, Argumentationsgang.",
        "schreiben": "Erörterung, Kommentar, formelle Stellungnahme, Zusammenfassung mit Bewertung, 200-350 Wörter, kohärent und stilistisch angemessen.",
        "sprechen": "Strukturierter Vortrag, differenzierte Argumentation, spontane Reaktion auf Gegenargumente, Register anpassen.",
        "text_types": ["essay", "opinion", "letter", "report", "other"],
    },
}


def guide(level: str | None) -> dict:
    return LEVEL_GUIDE[normalise_level(level)]
