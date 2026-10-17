"""Modul 13 — Termine und Alltag in Deutschland — Grammatik: Modalverben im
Präteritum (book pp. 126-135).

p.130: in the six texts several modal verbs fit many gaps ("Ein Mann ___ mir
helfen" — konnte / wollte / sollte …), so a gap alone has no single answer.
Each gap now names its verb in brackets — the verb of the answer sheet — and
asks for the Präteritum form; that answer is unique. The Hören page (p.132)
has no transcript: the questions wait for the audio (key_pending), the old
answer sheet's letters are kept as a hint."""

from . import (
    article_set, base, choice_gap, exercise, gap, html_table, intro_html, match, mc, mc_pending, reverse_vocab_set, summary_html, tf,
    vocab_match_sets, words,
)

L = 13
LESSON_TITLE = "Termine und Alltag in Deutschland"
LESSON_DESCRIPTION = "Thema: Termine und Alltag in Deutschland · Grammatik: Modalverben im Präteritum"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 13 — Termine und Alltag in Deutschland (Buch, S. 126)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    13, "Termine und Alltag in Deutschland", "Modalverben im Präteritum",
    ["modal fe'llarning o'tgan zamoni: konnte, musste, wollte, durfte, sollte, mochte (umlaut tushib qoladi);",
     "shaxs qo'shimchalari: ich konnte, du konntest, er konnte, wir konnten, ihr konntet, sie konnten;",
     "uchrashuv (Termin) belgilash, ko'chirish va bekor qilish;",
     "rasmiy va norasmiy xat yozish: Sehr geehrte … / Hallo …"],
    ["„Leider konnte ich gestern nicht kommen, ich musste arbeiten.“ — nega kela olmaganingizni tushuntirasiz;",
     "uchrashuvlar haqidagi to'rtta xatni o'qib, sarlavhalarni moslaysiz;",
     "telefon xabarlarini tinglab, kim nega kela olmasligini aniqlaysiz;",
     "uzr so'rab xat yozasiz va telefonda shifokor qabuliga yozilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(13, [
    "<strong>Präteritum:</strong> können → konnte, müssen → musste, dürfen → durfte, mögen → mochte, wollen → wollte, sollen → sollte.",
    "<strong>Endungen:</strong> ich -te, du -test, er/sie/es -te, wir -ten, ihr -tet, sie/Sie -ten (ich va er shakli bir xil).",
    "<strong>Satz:</strong> modal fe'l 2-o'rinda, Infinitiv oxirida — Ich musste gestern lange arbeiten.",
    "<strong>Termine:</strong> einen Termin vereinbaren / verschieben / absagen / bestätigen · Leider konnte ich nicht kommen. · Können wir einen neuen Termin machen?",
])

_MPRAET = (
    html_table(["", "können", "müssen", "wollen"],
               [["Qoida", "Präteritumda ö → o; fe'lga -te qo'shiladi: können → konnte", "ü → u; -te: müssen → musste", "o'zak o'zgarmaydi; -te: wollen → wollte"],
                ["Gap tuzilishi", "Shaxs + konnte(n) + … + Infinitiv", "Shaxs + musste(n) + … + Infinitiv", "Shaxs + wollte(n) + … + Infinitiv"],
                ["ich", "Ich konnte kommen. (Men kela oldim.)", "Ich musste kommen. (Men kelishim kerak edi.)", "Ich wollte kommen. (Men kelmoqchi edim.)"],
                ["du", "Du konntest Deutsch sprechen.", "Du musstest Deutsch lernen.", "Du wolltest Deutsch sprechen."],
                ["er / sie / es", "Er konnte Auto fahren.", "Er musste Auto fahren.", "Er wollte Auto fahren."],
                ["wir", "Wir konnten heute lernen.", "Wir mussten heute arbeiten.", "Wir wollten heute lernen."],
                ["ihr", "Ihr konntet schnell helfen.", "Ihr musstet schnell gehen.", "Ihr wolltet helfen."],
                ["sie / Sie", "Sie konnten bleiben.", "Sie mussten bleiben.", "Sie wollten bleiben."]])
    + html_table(["", "dürfen", "sollen", "mögen"],
                 [["Qoida", "ü → u; -te: dürfen → durfte", "o'zak o'zgarmaydi; -te: sollen → sollte", "ö → o; -te: mögen → mochte"],
                  ["Gap tuzilishi", "Shaxs + durfte(n) + … + Infinitiv", "Shaxs + sollte(n) + … + Infinitiv", "Shaxs + mochte(n) + … (+ Infinitiv)"],
                  ["ich", "Ich durfte kommen. (ruxsat bor edi)", "Ich sollte kommen. (birov aytgan)", "Ich mochte Pizza essen. (yoqtirardim)"],
                  ["du", "Du durftest Deutsch sprechen.", "Du solltest Deutsch lernen.", "Du mochtest Deutsch lernen."],
                  ["er / sie / es", "Er durfte Auto fahren.", "Er sollte Auto fahren.", "Er mochte Musik hören."],
                  ["wir", "Wir durften heute gehen.", "Wir sollten heute arbeiten.", "Wir mochten heute bleiben."],
                  ["ihr", "Ihr durftet helfen.", "Ihr solltet helfen.", "Ihr mochtet helfen."],
                  ["sie / Sie", "Sie durften bleiben.", "Sie sollten bleiben.", "Sie mochten Kaffee trinken."]])
    + "<p><strong>Beispiele aus dem Alltag:</strong> Ich wollte kommen, aber … / Du wolltest mich anrufen, aber du hast nicht angerufen. / "
      "Sie mussten um 9 Uhr Tabletten einnehmen. / Sie sollten drei Tage zu Hause bleiben. / Mein Arzt hat gesagt, ich sollte … / "
      "Sie durften gestern zum Urlaub fahren.</p>"
)

_Q = "Ergänzen Sie das passende Modalverb im Präteritum."
TEXTS = [
    ("Text 1 — Reise nach Berlin", "Letzten Monat [[1]] ich nach Berlin fahren. Ich [[2]] sehr früh aufstehen. Am Bahnhof [[3]] ich mein Ticket nicht "
     "finden. Ein Mann [[4]] mir helfen. Im Hotel [[5]] ich länger bleiben, aber es war teuer. Am Abend [[6]] ich die Stadt besichtigen.",
     [["wollte"], ["musste"], ["konnte"], ["konnte", "wollte"], ["wollte"], ["wollte"]]),
    ("Text 2 — Schulzeit", "In der Schule [[1]] wir jeden Tag viele Aufgaben machen. Ich [[2]] Mathe nicht verstehen. Mein Freund [[3]] mir alles "
     "erklären. Wir [[4]] in der Pause nicht laut sein. Unsere Lehrerin sagte, wir [[5]] mehr lernen. Nach der Schule [[6]] ich nach Hause gehen.",
     [["mussten"], ["konnte"], ["konnte", "wollte"], ["durften"], ["sollten"], ["konnte", "durfte", "musste"]]),
    ("Text 3 — Familienabend", "Gestern [[1]] wir zusammen kochen. Meine Mutter [[2]] eine Suppe machen. Ich [[3]] den Tisch decken. Mein Bruder "
     "[[4]] nicht helfen, weil er krank war. Wir [[5]] lange fernsehen. Am Ende [[6]] ich noch Musik hören.",
     [["wollten"], ["wollte"], ["musste", "sollte"], ["konnte"], ["durften"], ["wollte"]]),
    ("Text 4 — Sporttag", "Am Samstag [[1]] wir am Sportfest teilnehmen. Ich [[2]] sehr schnell laufen. Mein Freund [[3]] leider nicht kommen. Wir "
     "[[4]] lange trainieren. Der Trainer sagte, wir [[5]] mehr üben. Am Ende [[6]] wir früher nach Hause gehen.",
     [["wollten", "durften", "mussten"], ["konnte"], ["konnte"], ["mussten"], ["sollten"], ["durften", "konnten"]]),
    ("Text 5 — Krankenhaus", "Letzte Woche [[1]] ich ins Krankenhaus gehen. Ich [[2]] nicht arbeiten. Der Arzt sagte, ich [[3]] viel Wasser "
     "trinken. Ich [[4]] im Bett bleiben. Meine Schwester [[5]] mich besuchen. Zum Glück [[6]] ich bald nach Hause gehen.",
     [["musste"], ["konnte", "durfte"], ["sollte"], ["musste"], ["wollte", "konnte", "durfte"], ["konnte", "durfte"]]),
    ("Text 6 — Kindheit", "Als Kind [[1]] ich nicht schwimmen. Meine Eltern [[2]] mir helfen. Ich [[3]] jeden Tag üben. Wir [[4]] abends nicht "
     "lange draußen bleiben. In der Schule [[5]] ich viele Bücher lesen. Am Wochenende [[6]] ich mit Freunden spielen.",
     [["konnte"], ["wollten"], ["musste"], ["durften"], ["musste", "sollte"], ["wollte", "durfte", "konnte"]]),
]
_INF = {"konnte": "können", "musste": "müssen", "wollte": "wollen", "durfte": "dürfen", "sollte": "sollen", "mochte": "mögen"}


def _inf(form: str) -> str:
    return _INF[form[:-1] if form.endswith("en") else form]


def _with_verbs(text: str, keys: list[list[str]]) -> str:
    for i, k in enumerate(keys, start=1):
        text = text.replace(f"[[{i}]]", f"[[{i}]] ({_inf(k[0])})", 1)
    return text


_Q = "Setzen Sie das Modalverb in Klammern ins Präteritum."
TEXT_EX = [gap(f"{title}: {_Q}", _with_verbs(text, keys), {str(i): [k[0]] for i, k in enumerate(keys, start=1)}, points=6,
               explanation="Javob: " + ", ".join(k[0] for k in keys)) for title, text, keys in TEXTS]

TEXT_A = ("Sehr geehrter Herr Becker,\n\nich hatte gestern einen Termin in Ihrer Praxis. Leider konnte ich nicht kommen, weil ich krank war. Ich musste "
          "zu Hause bleiben und mich ausruhen. Könnten Sie mir bitte einen neuen Termin geben?\n\nMit freundlichen Grüßen\nAnna Weber")
TEXT_B = ("Sehr geehrter Herr Wagner,\n\nleider konnte ich gestern nicht zu unserem Termin kommen. Ich musste kurzfristig an einer wichtigen Besprechung "
          "teilnehmen. Könnten wir bitte einen neuen Termin vereinbaren? Vielen Dank für Ihr Verständnis.\n\nMit freundlichen Grüßen\nJulia Fischer")
TEXT_C = ("Sehr geehrte Frau Hoffmann,\n\nvielen Dank für unser Treffen letzte Woche. Wir wollten über das neue Projekt sprechen und konnten gute Ideen "
          "sammeln. Am Ende mussten wir einen klaren Plan machen. Ich freue mich auf die weitere Zusammenarbeit.\n\nMit freundlichen Grüßen\nThomas Schneider")
TEXT_D = ("Sehr geehrte Frau Schneider,\n\nvielen Dank für das Gespräch am Montag. Ich konnte viele Informationen über die Stelle bekommen. Ich musste noch "
          "einige Dokumente vorbereiten und habe sie heute geschickt. Ich freue mich sehr auf Ihre Antwort.\n\nMit freundlichen Grüßen\nLukas Müller")
LESEN = [
    match("Ordnen Sie die passenden Überschriften zu.", ["Text A", "Text B", "Text C", "Text D"],
          ["Bewerbungsgespräch — Dank für das Gespräch", "Verpasster Arzttermin — Bitte um neuen Termin",
           "Geschäftstreffen — Erfolgreiche Zusammenarbeit", "Termin verschoben — Neuer Termin gewünscht"],
          {"1": "B", "2": "D", "3": "C", "4": "A"}, points=4),
    mc("Warum konnte Anna Weber nicht in die Praxis kommen?", ["Sie war krank.", "Sie hatte eine Besprechung.", "Sie war im Urlaub."], "A", passage=1),
    tf("Anna Weber hatte gestern einen Termin in der Praxis von Herrn Becker.", True, "„ich hatte gestern einen Termin in Ihrer Praxis.“", passage=1),
    mc("Worum bittet Anna Weber?", ["Um einen neuen Termin", "Um ein Rezept", "Um eine Rechnung"], "A", "„Könnten Sie mir bitte einen neuen Termin geben?“", passage=1),
    mc("Warum konnte Julia Fischer nicht zum Termin kommen?", ["Sie war krank.", "Sie musste an einer wichtigen Besprechung teilnehmen.",
                                                               "Ihr Zug hatte Verspätung."], "B", passage=2),
    mc("Was möchte Julia Fischer?", ["Einen neuen Termin vereinbaren", "Den Termin absagen", "Herrn Wagner im Büro besuchen"], "A",
       "„Könnten wir bitte einen neuen Termin vereinbaren?“", passage=2),
    tf("Julia Fischer dankt Herrn Wagner für sein Verständnis.", True, "„Vielen Dank für Ihr Verständnis.“", passage=2),
    tf("Thomas Schneider und Frau Hoffmann haben über ein neues Projekt gesprochen.", True, passage=3),
    mc("Wann war das Treffen mit Frau Hoffmann?", ["Letzte Woche", "Gestern", "Am Montag"], "A", "„vielen Dank für unser Treffen letzte Woche.“", passage=3),
    mc("Was mussten sie am Ende des Treffens machen?", ["Einen klaren Plan", "Einen neuen Termin", "Eine Pause"], "A",
       "„Am Ende mussten wir einen klaren Plan machen.“", passage=3),
    mc("Was hat Lukas Müller heute geschickt?", ["Einige Dokumente", "Ein Geschenk", "Eine Rechnung"], "A", passage=4),
    mc("Wann war das Gespräch von Lukas Müller und Frau Schneider?", ["Am Montag", "Letzte Woche", "Gestern"], "A",
       "„vielen Dank für das Gespräch am Montag.“", passage=4),
    tf("Lukas Müller hat viele Informationen über die Stelle bekommen.", True, "„Ich konnte viele Informationen über die Stelle bekommen.“", passage=4),
]

HOEREN = [
    mc_pending("Markus Klein: Warum konnte Markus nicht kommen?", ["Er war krank.", "Er konnte nicht zum Termin kommen.", "Er hatte keinen Parkplatz."]),
    mc_pending("Leon Schmidt: Wie spät kommt Leon?", ["30 Minuten später.", "20 Minuten später.", "Er kommt nicht."]),
    mc_pending("Laura Neumann: Warum musste Laura zu Hause bleiben?", ["Sie hatte viel Arbeit.", "Sie war krank.", "Sie hatte einen anderen Termin."]),
    mc_pending("Tim Wagner: Was war sein Problem?", ["Der Zug hatte Verspätung.", "Er konnte keinen Parkplatz finden.", "Er war krank."]),
    mc_pending("Jana Hoffmann: Warum konnte sie nicht pünktlich sein?", ["Sie musste arbeiten.", "Sie wollte nicht kommen.", "Der Zug hatte Verspätung."]),
    mc_pending("Daniel Fischer: Was möchte Daniel?", ["Das Treffen verschieben.", "Den Termin absagen.", "30 Minuten später kommen."]),
]
OLD_SHEET_HINT = "Eski javoblar varag'i (tekshirilmagan): 1-B, 2-A, 3-B, 4-B, 5-C, 6-A"

_W = [("der", "Termin", "uchrashuv, termin"), ("das", "Büro", "ofis"), ("der", "Chef", "boshliq"), ("der", "Mitarbeiter", "xodim"), ("die", "Firma", "firma"),
      ("die", "Besprechung", "yig'ilish"), ("das", "Projekt", "loyiha"), ("die", "Zusammenarbeit", "hamkorlik"), ("der", "Arzt", "shifokor"),
      ("die", "Praxis", "klinika"), ("das", "Krankenhaus", "kasalxona"), ("krank", "kasal"), ("das", "Fieber", "isitma"), ("die", "Kopfschmerzen", "bosh og'rig'i"),
      ("der", "Anruf", "qo'ng'iroq"), ("vereinbaren", "kelishmoq"), ("verschieben", "ko'chirmoq"), ("absagen", "bekor qilmoq"), ("pünktlich", "vaqtida"),
      ("spät", "kech"), ("die", "Arbeit", "ish"), ("arbeiten", "ishlamoq"), ("helfen", "yordam bermoq"), ("bleiben", "qolmoq"), ("kommen", "kelmoq"),
      ("gehen", "bormoq"), ("sprechen", "gaplashmoq"), ("warten", "kutmoq"), ("planen", "rejalashtirmoq"), ("teilnehmen", "qatnashmoq"),
      ("informieren", "xabardor qilmoq"), ("entschuldigen", "uzr so'ramoq"), ("der", "Kalender", "taqvim"), ("der", "Kunde", "mijoz"),
      ("die", "Einladung", "taklif"), ("bestätigen", "tasdiqlamoq"), ("ändern", "o'zgartirmoq"), ("wichtig", "muhim"), ("dringend", "shoshilinch"),
      ("frei", "bo'sh")]
WORDS = words(_W, "Termine und Alltag")


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS, per_set=4), article_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("Modalverben in den Briefen", [
        choice_gap("Anna Weber ___ zu Hause bleiben und sich ausruhen. (müssen)", ["musste", "mussten", "muss"], "musste",
                   explanation="Text A: „Ich musste zu Hause bleiben und mich ausruhen.“"),
        choice_gap("Julia Fischer ___ an einer wichtigen Besprechung teilnehmen. (müssen)", ["musste", "müsste", "muss"], "musste"),
        choice_gap("Thomas Schneider und Frau Hoffmann ___ über das neue Projekt sprechen. (wollen)", ["wollten", "wollte", "wollen"], "wollten"),
        choice_gap("Bei dem Treffen ___ Thomas und Frau Hoffmann gute Ideen sammeln. (können)", ["konnten", "konnte", "können"], "konnten"),
        choice_gap("Lukas Müller ___ viele Informationen über die Stelle bekommen. (können)", ["konnte", "konnten", "kann"], "konnte"),
    ], "Xatlardagi gaplarni modal fe'lning Präteritum shakli bilan to'ldiring.", source="vizu"),
    exercise("Präteritum: die richtige Form", [
        mc("du + dürfen:", ["du durftest", "du durfest", "du dürftest"], "A"),
        mc("ihr + können:", ["ihr konntet", "ihr konntest", "ihr könntet"], "A"),
        mc("wir + sollen:", ["wir sollten", "wir sollen", "wir solltet"], "A"),
        mc("er + mögen:", ["er mochte", "er mögte", "er möchte"], "A", "„möchte“ — hozirgi zamon (xohlardi emas, xohlaydi)."),
    ], "To'g'ri Präteritum shaklini tanlang.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 13", source="vizu", page=126, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage: Wie ist die Situation im Büro?", page=127,
             prompt="Wie ist die Situation im Büro? (Teamarbeit, Zeitmanagement, Aufgaben, Herausforderungen, Erfolg) Erzählen Sie: Wie sieht ein "
                    "Arbeitstag oder ein Schultag bei Ihnen aus?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Modalverben im Präteritum", page="128-130",
             rules=[{"title": "Modalverben im Präteritum", "html": _MPRAET}],
             exercises=[exercise("Grammatik-Aufgaben: sechs Texte (Modalverben im Präteritum)", TEXT_EX, _Q)]),
        base(L, "lesen", 1, "Lesen: Überschriften — Briefe zu Terminen", page=131,
             instruction="Lesen Sie die Briefe. Ordnen Sie die passenden Überschriften zu und beantworten Sie die Fragen.",
             metadata={"book_page": 131, "note": "1-topshiriq (Überschriften) kitobdan; 2-5 savollar VIZU tomonidan."},
             passages=[{"title": "Text A", "text": TEXT_A}, {"title": "Text B", "text": TEXT_B}, {"title": "Text C", "text": TEXT_C},
                       {"title": "Text D", "text": TEXT_D}],
             questions=LESEN, max_score=sum(q["points"] for q in LESEN)),
        base(L, "hoeren", 1, "Hören: Termine — wer kann nicht kommen?", page=132, audio_file="A1-13.m4a", key_pending=True,
             instruction="Hören Sie die Nachrichten und wählen Sie die richtige Antwort.",
             metadata={"book_page": 132, "note": "Kitobda transkript yo'q — javoblarni audio yuklangandan keyin admin kiritadi.",
                       "old_sheet_hint": OLD_SHEET_HINT},
             questions=HOEREN),
        base(L, "schreiben", 1, "Schreiben: Norasmiy xat — Hallo Max", page=133,
             prompt="Schreiben Sie einen informellen Brief an Ihren Freund Max. Sie konnten nicht zu seinem Geburtstag kommen.\n"
                    "1. Salomlashish: Hallo Max,\n2. Sabab: Es tut mir leid. Ich konnte nicht kommen. Ich hatte viel Arbeit.\n"
                    "3. Tabrik: Alles Gute zum Geburtstag! Ich wünsche dir viel Glück und Gesundheit.\n"
                    "4. Kelajak rejasi: Am Wochenende komme ich zu dir. Ich bringe dein Geschenk mit.\n5. Yakun: Bis bald! Dein Freund (Name)",
             task_type="letter", audience="Freund Max", min_words=40, max_words=100, time_limit=20,
             support_phrases=["Es tut mir leid.", "Ich konnte nicht kommen, weil …", "Alles Gute zum Geburtstag!", "Bis bald!"]),
        base(L, "schreiben", 2, "Schreiben: Rasmiy xat — Termin", page=133,
             prompt="Schreiben Sie einen formellen Brief an Frau Schneider. Sie konnten gestern nicht zum Termin kommen.\n"
                    "1. Rasmiy salom: Sehr geehrte Frau Schneider,\n2. Muammo: Leider konnte ich nicht kommen. Ich war krank.\n"
                    "3. Uzr: Ich bitte um Entschuldigung.\n4. Iltimos: Können wir einen neuen Termin machen?\n"
                    "5. Yakun: Mit freundlichen Grüßen, Vor- und Nachname",
             task_type="letter", audience="Frau Schneider (formell)", min_words=40, max_words=100, time_limit=20,
             support_phrases=["Sehr geehrte Frau …,", "Leider konnte ich …", "Ich bitte um Entschuldigung.", "Können wir einen neuen Termin machen?",
                              "Mit freundlichen Grüßen"]),
        base(L, "sprechen", 1, "Gespräch zwischen Chef und Mitarbeiter", page=134, topic="Im Büro",
             prompt="Sie sind Herr / Frau Meier. Antworten Sie Ihrem Chef (Modalverben im Präteritum).",
             questions=["Warum konnten Sie gestern nicht zum Termin kommen?", "Waren Sie krank?", "Geht es Ihnen heute besser?",
                        "Können Sie den Termin morgen um 11 Uhr nachholen?"],
             response_type="dialog", min_duration=20, max_duration=120,
             speech_goal="Sich entschuldigen, einen Grund im Präteritum nennen (musste, konnte nicht …) und einen neuen Termin annehmen.",
             keywords=["Es tut mir leid", "Ich musste", "Ich konnte nicht", "kein Problem"]),
        base(L, "sprechen", 2, "Telefonat mit der Arztpraxis — Termin vereinbaren", page=134, topic="Beim Arzt",
             prompt="Sie sind die Patientin / der Patient (Julia Becker). Rufen Sie die Praxis Dr. Weber an und vereinbaren Sie einen Termin.",
             questions=["Guten Tag, Praxis Dr. Weber. Wie kann ich Ihnen helfen?", "Was ist Ihr Problem?", "Haben Sie morgen Zeit?",
                        "Gut, dann haben Sie morgen um 10 Uhr einen Termin. Bitte bringen Sie Ihre Versicherungskarte mit."],
             response_type="dialog", min_duration=20, max_duration=120,
             speech_goal="Am Telefon einen Arzttermin vereinbaren: Namen nennen, Beschwerden beschreiben, Zeit vereinbaren, sich verabschieden.",
             keywords=["Ich möchte einen Termin", "Ich habe Fieber", "am Vormittag", "Auf Wiederhören"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 13", page=135, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 13", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 13", source="vizu",
             instruction="Modal fe'llarning Präteritum shakllari va darsdagi so'zlar bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Gestern ___ ich nicht kommen. (können)", ["konnte", "kann", "könnte"], "konnte"),
                 choice_gap("Wir ___ lange warten. (müssen)", ["mussten", "müssen", "musste"], "mussten"),
                 choice_gap("Du ___ mich anrufen. (wollen)", ["wolltest", "willst", "wollte"], "wolltest"),
                 choice_gap("Der Arzt sagte, ich ___ viel trinken. (sollen)", ["sollte", "soll", "sollten"], "sollte"),
                 choice_gap("Als Kind ___ ich nicht lange fernsehen. (dürfen)", ["durfte", "darf", "dürfte"], "durfte"),
                 mc("Präteritum von „mögen“ (ich):", ["mochte", "mögte", "magte"], "A"),
                 mc("„einen Termin verschieben“ — o'zbekchasi qaysi?", ["uchrashuvni ko'chirmoq", "uchrashuvni bekor qilmoq", "uchrashuvni tasdiqlamoq"], "A"),
                 mc("„dringend“ — o'zbekchasi qaysi?", ["shoshilinch", "muhim", "bo'sh"], "A"),
                 tf("„absagen“ bedeutet „bekor qilmoq“.", True),
                 match("Was passt zusammen?", ["der Chef", "die Besprechung", "pünktlich", "die Einladung"], ["boshliq", "yig'ilish", "vaqtida", "taklif", "mijoz"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 13", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
