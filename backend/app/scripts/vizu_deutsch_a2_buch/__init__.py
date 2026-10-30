"""VIZU-DEUTSCH A2 — book-faithful edition (2026-10-27).

Built on top of the first digitisation (app/scripts/vizu_deutsch_a2, now
archived on production as "[Archiv] …") and the page-by-page audit of the
book (docs/a2-book-content-audit.md, 183/183 pages). What changes:

* Only material that is in the book: VIZU-made items (Einführung /
  Zusammenfassung texts, Abschlusstest, "Zuordnung", "Der, die oder das?",
  "Nemischa qanday?" …), handout ("Unterrichtsblatt") questions and the
  translated word lists taken from handouts are dropped.
* No invented limits: word counts, minutes, speaking durations and support
  phrases stay only where the book states them. A writing task without a
  word count has min_words / max_words = None (migration a7c2e9f4b1d6).
  Speaking/Frage max_duration is the recorder's technical cap (300 s), not a
  book requirement.
* The audit's FIX items (missing book questions, wrong instructions,
  transcript wording, page panels) — see FIXES below.
* Questions the book itself leaves undecidable (NEEDS_REVIEW in the audit)
  are listed in the task instruction and are NOT auto-graded.
* New content ids "vizu-a2buch-l<NN>-…": the archived rows keep their ids,
  nothing collides, re-running the import skips what exists.

Answer keys: the book prints none. Lesen keys are taken from the text (each
question's explanation quotes it, metadata key_source "text"); the Hören keys
of lessons 1, 2, 3, 5, 8, 9 come from "Vizu-Antworten A2" (key_source
"vizu-antworten"); all other Hören tasks have no key and stay drafts;
grammar keys follow the rule taught (key_source "grammar_rule").
"""

import copy
import importlib
import re

LEVEL = "A2"
MODULE = 1
OLD_PREFIX = "vizu-a2-"
NEW_PREFIX = "vizu-a2buch-"
EDITION = "buch-2026-10-27"
RECORDER_CAP_SECONDS = 300  # technical recording limit, not from the book

TITLES = {14: "Wiederholung"}
DESCRIPTIONS = {14: "Wiederholung — im Buch (Inhaltsverzeichnis) ohne eigene Seiten."}

# Track numbers printed in the book, shown as the label of the task's audio.
AUDIO_LABELS = {
    "vizu-a2buch-l10-hoeren-03": "Track 7–11 (laut Buch)",
    "vizu-a2buch-l10-hoeren-04": "Track 7–11 (laut Buch)",
    "vizu-a2buch-l12-hoeren-01": "Track 27–31",
    "vizu-a2buch-l12-hoeren-02": "Track 32",
    "vizu-a2buch-l12-hoeren-03": "Track 33–37",
    "vizu-a2buch-l12-hoeren-04": "Track 38–39",
    "vizu-a2buch-l13-hoeren-01": "Track 40–44",
    "vizu-a2buch-l13-hoeren-02": "Track 45",
    "vizu-a2buch-l13-hoeren-03": "Track 46–50",
    "vizu-a2buch-l13-hoeren-04": "Track 51–52",
}

# Book page images attached as lesson resources (file, competency, title).
IMAGES = {1: [("p015_musik_zeit.jpg", "HOEREN", "Buch S. 15 — Musik Zeit")]}

# Writing word counts the book states: content_id (old) -> (min, max).
BOOK_WORDS = {
    "vizu-a2-l02-schreiben-01": (30, 40),
    "vizu-a2-l03-schreiben-01": (80, None),
    "vizu-a2-l05-schreiben-01": (80, None),
    "vizu-a2-l06-schreiben-01": (80, None),
    "vizu-a2-l06-schreiben-03": (80, None),
    "vizu-a2-l08-schreiben-01": (80, None),
    "vizu-a2-l08-schreiben-03": (80, None),
    "vizu-a2-l09-schreiben-01": (80, None),
    "vizu-a2-l09-schreiben-03": (80, None),
    **{f"vizu-a2-l{n}-schreiben-01": (20, 30) for n in (10, 11, 12, 13)},
    **{f"vizu-a2-l{n}-schreiben-03": (30, 40) for n in (10, 11, 12, 13)},
}

# Speaking durations the book states (seconds): content_id (old) -> (min, max).
BOOK_DURATIONS = {
    "vizu-a2-l02-sprechen-01": (60, 120),  # "ca. 1–2 Minuten"
    "vizu-a2-l05-sprechen-01": (60, RECORDER_CAP_SECONDS),  # "mindestens 1–2 Minuten"
}

# Items dropped as a whole (handout / VIZU material labelled "book" in the first edition).
DROP = {
    "vizu-a2-l01-uebungen-01",  # Unterrichtsblatt + VIZU practice
    "vizu-a2-l05-wortschatz-01", "vizu-a2-l06-wortschatz-01",  # word lists from handouts;
    "vizu-a2-l07-wortschatz-01", "vizu-a2-l08-wortschatz-01",  # the book page is a task without translations
    # 4. Unterricht "Hören: Familie Mannsberg" replaced by the tasks Text 1 / 2 / 3 (2026-10-30),
    # managed in Media Management (services/a2_audio/lesson4_hoeren.py) — not imported again
    "vizu-a2-l04-hoeren-01",
}


def _old_module(n: int):
    return importlib.import_module(f"app.scripts.vizu_deutsch_a2.unterricht_{n:02d}")


def _new_id(cid: str) -> str:
    assert cid.startswith(OLD_PREFIX), cid
    return NEW_PREFIX + cid[len(OLD_PREFIX):]


def _replace(text: str, old: str, new: str) -> str:
    """Exact replacement that fails loudly if the source changed."""
    assert old in text, f"text to replace not found: {old[:80]!r}"
    return text.replace(old, new, 1)


def _note(item: dict, text: str) -> None:
    """A hint shown to the student in the task instruction."""
    item["instruction"] = f"{item['instruction']}\n\n{text}" if item.get("instruction") else text


def _review(item: dict, *entries: str) -> None:
    item.setdefault("metadata", {}).setdefault("needs_review", []).extend(entries)


def _key_source(item: dict, source: str) -> None:
    item.setdefault("metadata", {})["key_source"] = source


def _editorial(item: dict, book_text: str, note_html: str, rule: int = 0) -> None:
    """An editorial correction of a book error: the book's own wording stays
    in metadata.book_original, the student sees a marked note — never a
    silent change."""
    item.setdefault("metadata", {}).setdefault("book_original", []).append(book_text)
    rules = item.get("rules")
    if rules:
        rules[rule]["html"] += f"<p><em><strong>Redaktioneller Hinweis:</strong> {note_html}</em></p>"
    else:
        item["prompt"] += f"\n\nRedaktioneller Hinweis: {note_html}"


# ============================================================
# per-lesson fixes (docs/a2-book-content-audit.md)
# ============================================================

def _fix_01(items: dict) -> None:
    frage = items["vizu-a2-l01-frage-01"]
    frage["metadata"]["book_quote"] = "Eine gute Berufswahl ist der erste Schritt zu einer erfolgreichen Zukunft!"

    gram = items["vizu-a2-l01-grammatik-01"]
    hints_1 = [("lernte", "gelernt – haben"), ("besuchten", "besucht – haben"), ("kaufte", "gekauft – haben"),
               ("fuhr", "gefahren – sein"), ("las", "gelesen – haben"), ("schrieb", "geschrieben – haben")]
    for q, (prat, perf) in zip(gram["exercises"][0]["questions"], hints_1, strict=True):
        lines = q["text"].split("\n")
        q["text"] = "\n".join([lines[0], f"{lines[1]} ({prat})", f"{lines[2]} ({perf})"])
    for q in gram["exercises"][1]["questions"]:
        m = re.search(r"Kitobda: \((.+?)\) · \((.+?)\)", q["explanation"])
        assert m, q["explanation"]
        lines = q["text"].split("\n")
        q["text"] = "\n".join([lines[0], f"{lines[1]} ({m.group(1)})", f"{lines[2]} ({m.group(2)})"])
    _key_source(gram, "grammar_rule")

    lesen = items["vizu-a2-l01-lesen-01"]
    lesen["questions"] = lesen["questions"][:18]  # the book's 3 × 6; the rest came from a handout
    lesen["max_score"] = 18
    lesen["metadata"].pop("note", None)
    _key_source(lesen, "text")

    hoeren = items["vizu-a2-l01-hoeren-01"]
    t = hoeren["transcript"]
    t = _replace(t, "weil mein Vater auch Architekt war.", "weil mein Vater auch Architekt ist.")
    t = _replace(t, "Als Kind habe ich oft mit ihm gearbeitet und Häuser gezeichnet.",
                 "Als Kind habe ich oft mit ihm gezeichnet und Häuser gezeichnet.")
    hoeren["transcript"] = t
    _review(hoeren, "Transkript S. 14 wie im Buch („mit ihm gezeichnet und Häuser gezeichnet“) — mit dem Audio abgleichen.")
    _key_source(hoeren, "vizu-antworten")

    schreiben = items["vizu-a2-l01-schreiben-01"]
    schreiben["title"] = "Schreiben: Mein Traumberuf"
    schreiben["prompt"] = (
        "Mein Traumberuf – Schritt für Schritt\n\n"
        "Schritt 1: Einleitung — Zuerst schreibst du, was dein Traumberuf ist. Antworte auf die Frage: Was ist dein Traumberuf?\n"
        "Du kannst so beginnen: • Mein Traumberuf ist … • Ich möchte … werden.\n"
        "Beispiel: Mein Traumberuf ist Architekt. Ich möchte später Ärztin werden.\n\n"
        "Schritt 2: Begründung — Danach erklärst du, warum du diesen Beruf möchtest. Benutze „weil“.\n"
        "Struktur: • Ich möchte … werden, weil … • Dieser Beruf ist interessant, weil …\n"
        "Beispiel: Ich möchte Arzt werden, weil ich Menschen helfen will. Ich möchte Fußballspieler werden, weil ich Sport liebe.\n\n"
        "Schritt 3: Vergangenheit — Jetzt schreibst du etwas über deine Kindheit oder deine Erfahrungen. Benutze Perfekt oder Präteritum.\n"
        "Mögliche Anfänge: • Als Kind habe ich … • Früher wollte ich … • Ich habe schon …\n"
        "Beispiel: Als Kind habe ich oft Fußball gespielt. Ich habe viele Bücher über Medizin gelesen.\n\n"
        "Schritt 4: Zukunft — Schreibe über deine Pläne. Benutze Futur I oder Präsens mit Zukunftsbedeutung.\n"
        "Struktur: • Ich werde … • In Zukunft werde ich …\n"
        "Beispiel: Ich werde Medizin studieren. Ich werde hart arbeiten und viel lernen.\n\n"
        "Schritt 5: Schluss — Am Ende schreibst du einen positiven Satz über deinen Traum.\n"
        "Beispiel: • Ich hoffe, dass ich erfolgreich werde. • Ich bin motiviert und glaube an meinen Traum.\n\n"
        "Kompletter Beispieltext (A2): Mein Traumberuf ist Arzt. Ich möchte Arzt werden, weil ich Menschen helfen will. "
        "Als Kind habe ich gern mit meinen Puppen gespielt und sie behandelt. In der Schule habe ich Biologie besonders gemocht. "
        "Ich habe viel über den menschlichen Körper gelernt. In Zukunft werde ich Medizin studieren und hart arbeiten. "
        "Ich hoffe, dass ich ein guter Arzt werde."
    )


def _fix_02(items: dict) -> None:
    lesen = items["vizu-a2-l02-lesen-01"]
    lesen["questions"] = [q for q in lesen["questions"] if q["type"] == "true_false"]  # the 12 MC came from a handout
    assert len(lesen["questions"]) == 12
    lesen["max_score"] = 12
    lesen["instruction"] = "Lesen Sie die Texte. Richtig oder Falsch?"
    lesen["metadata"].pop("note", None)
    _key_source(lesen, "text")
    _key_source(items["vizu-a2-l02-hoeren-01"], "vizu-antworten")


def _fix_03(items: dict) -> None:
    rule = items["vizu-a2-l03-grammatik-01"]["rules"][0]
    rule["html"] = re.sub(r"<h4>Beispiel \(Unterrichtsblatt\)</h4><ul>.*?</ul>", "", rule["html"])
    assert "Unterrichtsblatt" not in rule["html"]
    _editorial(items["vizu-a2-l03-grammatik-01"], "S. 33, du: „Verbstamm + t/Ø“",
               "Im Buch steht beim Imperativ mit „du“ „Verbstamm + t/Ø“ (Druckfehler). Richtig ist Verbstamm + e/Ø — "
               "wie die Beispiele im Buch zeigen: Lerne Deutsch! · Komm! · Mach die Hausaufgabe!")
    task = items["vizu-a2-l03-schreiben-02"]
    task["prompt"] = _replace(
        task["prompt"],
        "\n\nBeispiel: Ich habe Kopfschmerzen. → Nimm eine Tablette! · Trinkt mehr Wasser! · Schlafen Sie noch mehr!", "")
    _key_source(items["vizu-a2-l03-lesen-01"], "vizu-antworten")  # checked against the text
    _key_source(items["vizu-a2-l03-hoeren-01"], "vizu-antworten")


def _fix_04(items: dict) -> None:
    frage = items["vizu-a2-l04-frage-01"]
    frage["prompt"] = _replace(frage["prompt"], "Wie planen Sie Ihren Tag? Erzählen Sie über Ihren Tagesablauf.", "Wie planen Sie Ihren Tag?")
    frage["prompt"] += ("\n\nBeispiel-Tagesablauf: 07:00 Aufstehen · 07:30 Frühstück machen · 09:00–17:00 Arbeiten · "
                        "13:00–14:00 Mittagspause · 18:00 Sport machen · 20:00 Deutsch lernen · 21:00 Zeit mit der Familie · 23:00 Schlafen gehen")

    gram = items["vizu-a2-l04-grammatik-01"]
    gram["rules"] = gram["rules"][:1]  # "Infinitivgruppe um / ohne / anstatt" came from a handout
    gram["exercises"] = []  # 60 + 30 handout gap exercises

    task = items["vizu-a2-l04-schreiben-02"]
    task["prompt"] = _replace(task["prompt"], "Verbinden Sie die zwei Sätze mit „zu“ + Infinitiv (Aufgabe 1) bzw. mit „um … zu“ (Aufgabe 2).",
                              "Verbinden Sie die zwei Sätze mit „zu“ + Infinitiv (Aufgabe 1 und Aufgabe 2).")

    lesen = items["vizu-a2-l04-lesen-01"]
    template = lesen["questions"][0]
    book_19_24 = [
        ("19. Martin steht jeden Morgen um 7 Uhr auf.", "B", "„Martin steht jeden Morgen um 6:30 Uhr auf.“"),
        ("20. Martin fährt mit dem Fahrrad zur Arbeit.", "C", "Der Text sagt nur: „Um 7:30 Uhr fährt er ins Büro.“ — womit, steht nicht im Text."),
        ("21. Martin arbeitet nur am Computer.", "B", "„Er zeichnet Pläne, arbeitet am Computer und spricht mit seinen Kollegen.“"),
        ("23. Martin geht zum Mittagessen nach Hause.", "B", "„Oft geht er mit seinen Kollegen in ein kleines Restaurant in der Nähe.“"),
        ("24. Martin treibt am Abend oft Sport.", "A", "„Am Abend macht er oft Sport oder geht spazieren.“"),
    ]
    martin = []
    for text, key, quote in book_19_24:
        q = copy.deepcopy(template)
        q.update(question=text, correct_answer=key, explanation=quote, passage=3)
        martin.append(q)
    lesen["questions"] = [q for q in lesen["questions"] if q.get("passage") != 3] + martin
    lesen["max_score"] = sum(q.get("points", 1) for q in lesen["questions"])
    lesen["metadata"].pop("note", None)
    _note(lesen, "Hinweis: Aufgabe 22 „Martin hat oft Meetings mit Kunden.“ wird nicht automatisch bewertet "
                 "(im Text steht „Manchmal …“ — im Buch keine eindeutige Lösung). Die Nummern 13–18 fehlen im Buch.")
    _review(lesen, "S. 48 Aufgabe 22: „oft“ vs. „manchmal“ — Lösung festlegen.")
    _key_source(lesen, "text")


def _fix_05(items: dict) -> None:
    rule = items["vizu-a2-l05-grammatik-01"]["rules"][0]
    rule["html"] = _replace(rule["html"], "Ich bleibe zu Hause, weil ich krank bin.<br>",
                            "Ich bleibe zu Hause, weil ich krank bin. <em>(I stay at home because I am sick.)</em><br>")
    rule["html"] = _replace(rule["html"], "Da ich krank bin, bleibe ich zu Hause.<br>",
                            "Da ich krank bin, bleibe ich zu Hause. <em>(Since I am sick, I stay at home.)</em><br>")
    _key_source(items["vizu-a2-l05-grammatik-01"], "grammar_rule")

    lesen = items["vizu-a2-l05-lesen-01"]
    open_questions = lesen["metadata"].pop("open_questions")
    lesen["metadata"].pop("note", None)
    _key_source(lesen, "text")
    items["vizu-a2-l05-schreiben-05"] = {
        "content_id": "vizu-a2-l05-schreiben-05", "level": LEVEL, "module": MODULE, "lesson": 5, "skill": "schreiben",
        "title": "Lesen: Fragen zum Text (Aufgabe)", "source": "book", "metadata": {"book_page": 57},
        "task_type": "other",
        "prompt": "Lesen Sie den Text „Wie ist der Lebensstil der Deutschen?“ und beantworten Sie die Fragen.\n\n"
                  + "\n".join(f"{i}. {q}" for i, q in enumerate(open_questions, 1)),
    }

    hoeren = items["vizu-a2-l05-hoeren-01"]
    _key_source(hoeren, "vizu-antworten")
    _review(hoeren, "S. 59 Frage 4: Vizu-Antworten „B“, Audioanalyse „C“ (1500–2100 Euro) — prüfen.",
            "S. 59 Frage 5: Schlüssel aus Vizu-Antworten passt nicht zum Inhalt — prüfen.")


def _fix_06(items: dict) -> None:
    _key_source(items["vizu-a2-l06-grammatik-01"], "grammar_rule")
    lesen = items["vizu-a2-l06-lesen-01"]
    not_in_book = {"Lukas möchte Jonas bald wiedersehen.", "Jonas glaubt, dass ihre Freundschaft schwach ist.",
                   "Paul denkt, dass Leon mutig ist.", "Leon sagt, dass Paul ihm nicht wichtig ist."}
    before = len(lesen["questions"])
    lesen["questions"] = [q for q in lesen["questions"] if q["question"] not in not_in_book]
    assert before - len(lesen["questions"]) == 4
    lesen["max_score"] = len(lesen["questions"])
    lesen["metadata"].pop("note", None)
    _note(lesen, "Hinweis: Paul und Leon, Aussage 9 „Paul bekommt gute Noten in der Schule.“ wird nicht automatisch bewertet "
                 "(im Text steht nur, dass in der Schule „alles gut läuft“).")
    _review(lesen, "S. 68 Aussage 9 (Noten) — Lösung festlegen.")
    _key_source(lesen, "text")


def _fix_07(items: dict) -> None:
    gram = items["vizu-a2-l07-grammatik-01"]
    html = gram["rules"][0]["html"]
    for prep in ("zu (…ga, oldiga)", "außer (…dan tashqari)", "gegenüber (ro‘parasida)", "entgegen (qarshi tomonga)", "ab (…dan boshlab)"):
        html, n = re.subn(rf"<tr><td>{re.escape(prep)}</td><td>[^<]*</td></tr>", "", html)
        assert n == 1, prep
    gram["rules"][0]["html"] = html
    ex = gram["exercises"][0]
    not_graded = gram["metadata"].pop("not_graded")
    ex["instruction"] = ("Wähle die richtige Präposition: A, B oder C.\n\nNicht automatisch bewertet "
                         "(im Buch keine eindeutige Lösung): " + " · ".join(f"{k}. {v}" for k, v in not_graded.items()))
    _review(gram, "S. 77 Aufgaben 2, 9, 18, 25, 26 — Lösung bzw. Optionen festlegen.")
    _key_source(gram, "grammar_rule")
    for cid in ("vizu-a2-l07-schreiben-01", "vizu-a2-l07-schreiben-03"):
        items[cid]["prompt"] = "Hinweis (Buch S. 81): Wählen Sie eine der beiden Aufgaben.\n\n" + items[cid]["prompt"]
    _key_source(items["vizu-a2-l07-lesen-01"], "text")


def _fix_08(items: dict) -> None:
    gram = items["vizu-a2-l08-grammatik-01"]
    html = gram["rules"][0]["html"]
    html = re.sub(r"<p>Nach „trotzdem“ \(Position 1\).*?</p>$", "", html)
    assert "Position 1" not in html
    html += ("<h4>Vergleich: aber + mehr Beispiele</h4><ul><li>Ich bin müde, <strong>aber</strong> ich lerne Deutsch.</li>"
             "<li>Es ist kalt. <strong>Trotzdem</strong> ziehe ich keine Jacke an.</li><li>Sie hat Angst. <strong>Trotzdem</strong> fährt sie allein wieder.</li>"
             "<li>Ich habe Hunger, <strong>aber</strong> sie fährt nicht allein.</li><li>Ich habe Kopfschmerzen, <strong>aber</strong> ich bleibe zuhause.</li>"
             "<li>Ich bin müde. <strong>Trotzdem</strong> lerne ich Deutsch.</li></ul>"
             "<h4>Mini-Übungen</h4><ul><li>Ich bin krank, <strong>aber</strong> ich gehe zur Schule.</li><li>Es ist kalt, <strong>Trotzdem</strong> gehe ich zur Schule.</li>"
             "<li>Sie hat Angst, <strong>aber</strong> sie fährt allein.</li><li>Er hat wenig Erfahrung. <strong>Trotzdem</strong> bekommt er den Job.</li>"
             "<li>Ich bin krank, <strong>aber</strong> ich gehe zur Schule.</li><li>Er hat wenig Erfahrung. <strong>Trotzdem</strong> bekommt er den Job.</li></ul>")
    gram["rules"][0]["html"] = html
    _editorial(gram, "S. 86: „Ich habe Hunger, aber sie fährt nicht allein.“ · „Es ist kalt, Trotzdem gehe ich zur Schule.“",
               "„Ich habe Hunger, aber sie fährt nicht allein.“ zeigt keinen Gegensatz (zwei verschiedene Personen, kein Zusammenhang). "
               "„Es ist kalt, Trotzdem gehe ich zur Schule.“ — nach einem Komma klein: „Es ist kalt, trotzdem gehe ich zur Schule.“ "
               "(oder mit Punkt: „Es ist kalt. Trotzdem gehe ich zur Schule.“).")

    task = items["vizu-a2-l08-schreiben-02"]
    task["title"] = "Grammatik-Aufgaben: A, B, C (trotzdem)"
    task["prompt"] = (
        "A2 8. Unterricht — Üben · Verstehen · Besser sprechen!\n\n"
        "A) Wort in der richtigen Form — Setze das passende Wort in der richtigen Form ein.\n"
        "1. Ich bin müde, ___ (trotzdem) gehe ich zur Arbeit.\n2. Es regnet, ___ (trotzdem) gehe ich spazieren.\n"
        "3. Ich habe wenig Zeit, ___ (mache) ich meine Hausaufgaben.\n4. Er ist krank, ___ (trotzdem) kommt er zur Schule.\n"
        "5. Wir haben kein Geld, ___ (trotzdem) kaufen wir das Buch.\n6. Sie hat viel Stress, ___ (trotzdem) hilft sie mir.\n"
        "7. Ich habe Angst, ___ (trotzdem) gehe ich ins Kino.\n8. Es ist sehr kalt, ___ (trotzdem) mache ich Sport.\n"
        "9. Ich habe keine Lust, ___ (trotzdem) arbeite ich.\n10. Wir sind spät, ___ (trotzdem) nehmen wir den Bus.\n\n"
        + _replace(task["prompt"].split("\n\n", 1)[1].split("\n\nUnterrichtsblatt", 1)[0],
                   "C) Fehler finden und korrigieren — schreibe die Sätze mit „trotzdem“:",
                   "C) Fehler finden und korrigieren — Finde die Fehler im Satz und korrigiere sie.")
    )
    assert "Unterrichtsblatt" not in task["prompt"] and task["prompt"].count("\n10.") == 3
    task["metadata"].pop("note", None)

    lesen = items["vizu-a2-l08-lesen-01"]
    lesen["passages"][0]["text"] += (
        "\n\nMüll: Ø 552 kg Müll pro Person pro Jahr · Plastikmüll: Ø 36 kg Plastikmüll pro Person pro Jahr · "
        "Elektroschrott: 62 Millionen Tonnen weltweit im Jahr 2022 · Lebensmittelverschwendung: Ø 931 Millionen Tonnen pro Jahr\n"
        "Unser Ziel: Bewusst konsumieren · Weniger verschwenden · Recyceln · Nachhaltig handeln")
    _key_source(lesen, "vizu-antworten")  # checked against the text
    _key_source(items["vizu-a2-l08-hoeren-01"], "vizu-antworten")


def _fix_09(items: dict) -> None:
    _key_source(items["vizu-a2-l09-grammatik-01"], "grammar_rule")
    lesen = items["vizu-a2-l09-lesen-01"]
    _key_source(lesen, "vizu-antworten")  # checked against the text
    # "fast 30 %" means just under 30 % — the key "richtig" follows from the text
    lesen["metadata"]["key_decision"] = "S. 99 Aussage 6 „Weniger als 30 %“: Text „fast 30 %“ → richtig."
    _editorial(items["vizu-a2-l09-schreiben-02"], "S. 97 Beispiel: „…, damit ich in Deutschland studieren will.“",
               "Im Beispiel des Buches richtig: „…, damit ich in Deutschland studieren kann.“ (nach „damit“ kein „wollen“ — "
               "der Wunsch steckt schon in „damit“).")
    _key_source(items["vizu-a2-l09-hoeren-01"], "vizu-antworten")


def _fix_10(items: dict) -> None:
    _key_source(items["vizu-a2-l10-grammatik-01"], "grammar_rule")
    _editorial(items["vizu-a2-l10-grammatik-01"], "S. 106, Spalte Futur I: „Lisa wird wohl schon geschlafen haben.“",
               "„Lisa wird wohl schon geschlafen haben.“ steht im Buch unter Futur I, ist aber Futur II (werden + Partizip II + haben).")
    kadewe = items["vizu-a2-l10-lesen-02"]["passages"][0]
    kadewe["text"] = re.sub(r"\nErdgeschoss: [^\n]*", "", kadewe["text"])
    assert "Erdgeschoss:" not in kadewe["text"]
    for n in (1, 2, 3, 4):
        _key_source(items[f"vizu-a2-l10-lesen-0{n}"], "text")
    for n in (3, 4):
        _review(items[f"vizu-a2-l10-hoeren-0{n}"], "S. 118/119: Teil 3 und Teil 4 tragen beide „Track 7–11“ — Trackangabe prüfen.")


def _fix_11(items: dict) -> None:
    _key_source(items["vizu-a2-l11-grammatik-01"], "grammar_rule")
    lesen = items["vizu-a2-l11-lesen-01"]
    lesen["metadata"].pop("note", None)
    _note(lesen, "Hinweis: Aufgabe 5 „Tauchen lernen … a) kostet genauso viel wie Bungee-Jumping. b) ist billiger als Bungee-Jumping. "
                 "c) kostet mehr als Bungee-Jumping.“ wird nicht automatisch bewertet (der Text nennt keinen Preis für Bungee-Jumping).")
    _review(lesen, "S. 130 Aufgabe 5 — Text enthält keinen Bungee-Preis.")
    for n in (1, 2, 3, 4):
        _key_source(items[f"vizu-a2-l11-lesen-0{n}"], "text")
    email = items["vizu-a2-l11-schreiben-03"]
    email["prompt"] = ("Format & Tipps: 1. Lies zuerst die Aufgabe, d.h. die Situation und die drei Leitpunkte. 2. Überlege: "
                       "a) An wen schreibst du? b) Aus welchem Anlass schreibst du? c) Was willst du erreichen? "
                       "3. Schreibe die E-Mail. 4. Kontrolliere schnell, was du geschrieben hast.\n\n" + email["prompt"])
    sprechen = items["vizu-a2-l11-sprechen-01"]
    sprechen["questions"] = [q for q in sprechen["questions"] if q.startswith("Kandidat 1")] + [
        "Kandidat 2: Schule?", "Kandidat 2: Freizeit?", "Kandidat 2: Schule?", "Kandidat 2: Butter, Essen?"]
    _review(sprechen, "S. 143 Kandidat 2: Karte „Schule?“ steht im Buch zweimal.")
    _review(items["vizu-a2-l11-sprechen-03"], "S. 145 Format & Tipps von Teil 3 ist eine Kopie aus Teil 2.")


def _fix_12(items: dict) -> None:
    gram = items["vizu-a2-l12-grammatik-01"]
    ex = gram["exercises"][0]
    ex["title"] = "Grammatik Aufgaben: Relativpronomen"
    ex["instruction"] = ("Wähle das richtige Relativpronomen.\n\nNicht automatisch bewertet: Aufgabe 20 „Das Kind, ___ Ball verloren hat, "
                         "weint. (dessen / dem / den)“ — keine der Optionen ist richtig.")
    # the corrected table carries a visible "Hinweis" (first edition); the
    # book's wording is kept here, the correction is standard grammar
    gram["metadata"]["book_original"] = ["S. 149 Relativpronomen-Tabelle: Spalten vertauscht (z. B. Dativ feminin „die“, "
                                         "Genitiv Plural „denen“; Nominativ/Akkusativ fehlen)."]
    _review(gram, "S. 150 Aufgabe 20 ohne richtige Option (nicht automatisch bewertet).")
    _key_source(gram, "grammar_rule")

    teil1 = items["vizu-a2-l12-lesen-01"]
    teil1["metadata"].pop("note", None)
    _note(teil1, "Hinweis: Im Buch ist der Text zwischen den Spalten unterbrochen. Nicht automatisch bewertet: "
                 "Aufgabe 3 „Peter spielt am Computer, … a) bevor er seine Hausaufgaben macht. b) wenn er keine Hausaufgaben hat. "
                 "c) wenn er mit den Hausaufgaben fertig ist.“ · Aufgabe 4 „Peter … a) macht es keinen Spaß, im Internet zu surfen. "
                 "b) muss viel Geld für Online-Spiele ausgeben. c) spielt gern im Internet.“")
    _review(teil1, "S. 151 Text unterbrochen — Aufgaben 3 und 4.")
    teil4 = items["vizu-a2-l12-lesen-04"]
    teil4["metadata"].pop("note", None)
    _note(teil4, "Hinweis: Birgit „Birgit möchte in ihrem Urlaub auch Sport treiben.“ wird nicht automatisch bewertet "
                 "(Anzeige a und f passen beide).")
    _review(teil4, "S. 154: 6 Personen bei 5 Aufgabennummern; Birgit mehrdeutig.")
    for n in (1, 2, 3, 4):
        _key_source(items[f"vizu-a2-l12-lesen-0{n}"], "text")


def _fix_13(items: dict) -> None:
    gram = items["vizu-a2-l13-grammatik-01"]
    gram["metadata"]["book_original"] = ["S. 166: „können → müsste, müssen → dürfte“", "S. 166: „Ein Relativsatz II. beschreibt …“"]
    gram["rules"][0]["html"] = _replace(
        gram["rules"][0]["html"], "(Druckfehler) — hier die richtigen Formen.",
        "(Druckfehler) — hier die richtigen Formen. Ebenso steht im Buch „Ein Relativsatz II“ statt „Der Konjunktiv II“.")
    _key_source(gram, "grammar_rule")
    for n in (1, 2, 3, 4):
        _key_source(items[f"vizu-a2-l13-lesen-0{n}"], "text")
    email = items["vizu-a2-l13-schreiben-03"]
    sample = email["metadata"].pop("book_sample")
    email["prompt"] += f"\n\nBeispiel (Buch): {sample}"
    _editorial(email, "S. 179 Beispiel: „hoffentlich geht Ihnen gut. Und wünschen wir Ihnen …“ · „wann wir besuchen können?“",
               "Im Beispiel des Buches richtig: „hoffentlich geht es Ihnen gut. Wir wünschen Ihnen …“ und "
               "„Können Sie sagen, wann wir Sie besuchen können?“")
    _editorial(items["vizu-a2-l13-schreiben-01"], "S. 179 Beispiel: „Aber habe eine Frage.“",
               "Im Beispiel des Buches richtig: „Aber ich habe eine Frage.“")


FIXES = {1: _fix_01, 2: _fix_02, 3: _fix_03, 4: _fix_04, 5: _fix_05, 6: _fix_06, 7: _fix_07, 8: _fix_08, 9: _fix_09,
         10: _fix_10, 11: _fix_11, 12: _fix_12, 13: _fix_13}


# ============================================================
# the edition
# ============================================================

def _is_vizu(item: dict) -> bool:
    if item.get("source") == "vizu" or item["skill"] == "yakuniy":
        return True
    return item["skill"] == "kompetenz" and item.get("competency") in ("EINFUEHRUNG", "ZUSAMMENFASSUNG")


def _normalise(item: dict, old_id: str) -> dict:
    skill = item["skill"]
    if skill == "schreiben":
        item.pop("time_limit", None)
        item.pop("support_phrases", None)
        lo, hi = BOOK_WORDS.get(old_id, (None, None))
        item["min_words"], item["max_words"] = lo, hi
    elif skill in ("sprechen", "frage"):
        lo, hi = BOOK_DURATIONS.get(old_id, (0, RECORDER_CAP_SECONDS))
        item["min_duration"], item["max_duration"] = lo, hi
    if "exercises" in item:
        item["exercises"] = [e for e in item["exercises"] if e.get("source") != "vizu"]
    if skill == "wortschatz":
        item["auto_practice"] = False
    item["content_id"] = _new_id(item["content_id"])
    item.setdefault("metadata", {})["edition"] = EDITION
    return item


def items(n: int) -> list[dict]:
    """The lesson's book items, in the first edition's order."""
    if n == 14:
        return []
    old = [copy.deepcopy(i) for i in _old_module(n).items()]
    by_id = {i["content_id"]: i for i in old if not _is_vizu(i) and i["content_id"] not in DROP}
    FIXES[n](by_id)
    out = []
    for old_id, item in by_id.items():
        item = _normalise(item, old_id)
        if item["skill"] in ("uebungen", "schreiben_uebungen", "grammatik") and not item.get("exercises") and not item.get("rules"):
            continue
        if item["skill"] in ("uebungen", "schreiben_uebungen") and not item.get("exercises"):
            continue
        out.append(item)
    return out


def lesson_title(n: int) -> str:
    return TITLES.get(n) or _old_module(n).LESSON_TITLE


def lesson_description(n: int) -> str:
    return DESCRIPTIONS.get(n) or _old_module(n).LESSON_DESCRIPTION
