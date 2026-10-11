"""Generation instructions for Claude, one per level A1-C1, plus a checklist
and an example document. Claude is used as an AUTHORING tool here: the admin
copies the prompt into Claude, gets JSON back and imports it (validation ->
preview -> commit -> publish). Nothing in this module calls an API."""

import json

from app.services.content_import.schema import SCHEMA_VERSION
from app.services.lesson_skills import levels

_EXAMPLE = {
    "schema_version": SCHEMA_VERSION,
    "language": "de",
    "source": "claude",
    "items": [
        {
            "content_id": "{lv}-m1-l1-lesen-01",
            "level": "{LV}",
            "module": 1,
            "lesson": 1,
            "skill": "lesen",
            "title": "Lesen: Neue Nachbarn",
            "instruction": "Lies die Texte und löse die Aufgaben.",
            "max_score": 4,
            "passages": [{"title": "Text 1: Anna", "text": "Hallo! Ich heiße Anna …"}],
            "questions": [
                {"type": "multiple_choice", "passage": 1, "question": "Wie alt ist Anna?", "options": ["8 Jahre", "9 Jahre", "10 Jahre"], "correct_answer": "B", "points": 1, "explanation": "Im Text: „ich bin 9 Jahre alt“."},
                {"type": "true_false", "passage": 1, "question": "Anna wohnt in Berlin.", "correct_answer": "falsch", "points": 1},
                {"type": "matching", "passage": 1, "question": "Was passt zusammen?", "items": ["Anna", "Tom"], "targets": ["mag Musik", "mag Fußball", "mag Tennis"], "pairs": {"1": "A", "2": "B"}, "points": 1},
                {"type": "gap_fill", "passage": 1, "question": "Ergänze.", "text": "Ich [[1]] Anna und ich [[2]] aus Usbekistan.", "gaps": {"1": ["heiße"], "2": {"accepted": ["komme"], "options": ["komme", "kommst", "kommt"]}}, "points": 1},
            ],
        },
        {
            "content_id": "{lv}-m1-l1-hoeren-01", "level": "{LV}", "module": 1, "lesson": 1, "skill": "hoeren",
            "title": "Hören: Am Bahnhof", "instruction": "Hör zu und kreuze an.", "audio_file": "{lv}_m1_l1_hoeren_01.mp3",
            "transcript": "Achtung am Gleis 3 …", "max_score": 1,
            "questions": [{"type": "short_answer", "question": "Auf welchem Gleis fährt der Zug ab? (Zahl)", "accepted": ["3", "drei", "Gleis 3"], "points": 1}],
        },
        {
            "content_id": "{lv}-m1-l1-schreiben-01", "level": "{LV}", "module": 1, "lesson": 1, "skill": "schreiben",
            "title": "Schreiben: Eine Nachricht an Ihre Freundin", "prompt": "Ihre Freundin hat Geburtstag …",
            "task_type": "message", "audience": "eine Freundin", "min_words": 30, "max_words": 60, "time_limit": 15,
            "support_phrases": ["Liebe …", "Leider kann ich nicht …"], "max_score": 100,
        },
        {
            "content_id": "{lv}-m1-l1-sprechen-01", "level": "{LV}", "module": 1, "lesson": 1, "skill": "sprechen",
            "title": "Sprechen: Sich vorstellen", "prompt": "Stellen Sie sich vor.", "topic": "Ich über mich",
            "questions": ["Wie heißen Sie?", "Woher kommen Sie?", "Was machen Sie gern?"], "response_type": "monolog",
            "min_duration": 20, "max_duration": 60, "speech_goal": "Name, Herkunft, Wohnort und ein Hobby nennen", "max_score": 100,
        },
    ],
}


def example(level: str) -> dict:
    lv = levels.normalise_level(level)
    text = json.dumps(_EXAMPLE, ensure_ascii=False).replace("{lv}", lv.lower()).replace("{LV}", lv)
    return json.loads(text)


def checklist(level: str) -> list[str]:
    g = levels.guide(level)
    return [
        f"Lesetexte {g['reading_words'][0]}-{g['reading_words'][1]} Wörter pro Text.",
        f"Schreiben: Wortgrenze im Bereich {g['writing_words'][0]}-{g['writing_words'][1]}; Textsorte aus: {', '.join(g['text_types'])}.",
        f"Sprechen: max_duration im Bereich {g['speaking_seconds'][0]}-{g['speaking_seconds'][1]} Sekunden.",
        "Jede Frage ist nur aus dem Text / Transkript beantwortbar — keine Fakten von außen.",
        "Jede auto-bewertete Frage hat genau eine eindeutig richtige Lösung (short_answer: alle akzeptierten Varianten).",
        "max_score = Summe der Fragenpunkte (Lesen/Hören) bzw. Summe der Rubrik (Schreiben/Sprechen).",
        "content_id ist eindeutig und stabil (z. B. b1-m3-l2-lesen-01).",
        "Hören: Transkript liefern; die Audiodatei wird vom Admin hochgeladen.",
    ]


def prompt(level: str) -> str:
    lv = levels.normalise_level(level)
    g = levels.guide(lv)
    w_rubric = ", ".join(f"{c['key']} ({c['name']}) {c['max']}" for c in levels.writing_rubric(lv))
    s_rubric = ", ".join(f"{c['key']} ({c['name']}) {c['max']}" for c in levels.speaking_rubric(lv))
    return f"""Du bist Autor:in für Deutsch-als-Fremdsprache-Material auf Niveau {lv} (GER/CEFR) für VIZU Academy.
Erstelle Lerninhalte für: Niveau {lv}, Modul <MODUL>, Lektion <LEKTION>, Thema: <THEMA>.

Gib AUSSCHLIESSLICH gültiges JSON zurück (kein Markdown, keine Kommentare), genau im Format
schema_version "{SCHEMA_VERSION}" (siehe Beispiel und JSON-Schema). Ein Eintrag in "items" = eine Aufgabe einer Fertigkeit.

NIVEAU {lv} — Vorgaben
- Lesen: {g['lesen']} Textlänge {g['reading_words'][0]}-{g['reading_words'][1]} Wörter.
- Hören: {g['hoeren']} Liefere das Transkript (die Audiodatei wird separat produziert und hochgeladen).
- Schreiben: {g['schreiben']} Wortgrenze im Bereich {g['writing_words'][0]}-{g['writing_words'][1]}. Erlaubte task_type: {', '.join(g['text_types'])}.
- Sprechen: {g['sprechen']} Dauer {g['speaking_seconds'][0]}-{g['speaking_seconds'][1]} Sekunden (min_duration/max_duration in Sekunden).

Fragetypen (Lesen/Hören): multiple_choice (options + correct_answer als Buchstabe), true_false (correct_answer "richtig"/"falsch"),
matching (items, targets, pairs {{"1": "B"}}), gap_fill (text mit [[1]] … und gaps), short_answer (accepted = ALLE akzeptierten Varianten;
nur für Antworten, die sich eindeutig prüfen lassen). Jede Frage muss allein aus Text/Transkript lösbar sein; keine Fakten von außen.
Gib zu jeder Frage eine kurze explanation (auf Deutsch, einfach) an.

Bewertung
- Lesen/Hören: points pro Frage (Standard 1); max_score = Summe der points.
- Schreiben (Standardrubrik {lv}, 100 Punkte): {w_rubric}. Eigene "rubric" nur wenn nötig; max_score = Summe der Rubrik.
- Sprechen (Standardrubrik {lv}, 100 Punkte): {s_rubric}. speech_goal = was die Antwort inhaltlich leisten soll.

Regeln
- content_id eindeutig: "{lv.lower()}-m<MODUL>-l<LEKTION>-<skill>-<nn>".
- status immer "draft" (Veröffentlichung erfolgt nach Prüfung durch einen Admin).
- Sprache der Aufgaben: Deutsch. Keine personenbezogenen echten Daten.

Prüfe vor der Ausgabe: {' / '.join(checklist(lv))}
"""


def guide(level: str) -> dict:
    lv = levels.normalise_level(level)
    return {
        "level": lv,
        "prompt": prompt(lv),
        "checklist": checklist(lv),
        "ranges": {k: v for k, v in levels.guide(lv).items() if k.endswith(("_words", "_seconds"))},
        "text_types": levels.guide(lv)["text_types"],
        "default_rubrics": {"writing": levels.writing_rubric(lv), "speaking": levels.speaking_rubric(lv)},
        "example": example(lv),
    }
