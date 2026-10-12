"""Modul 13 — Termine und Alltag in Deutschland — Grammatik: Modalverben im
Präteritum (book pp. 126-135).

p.130: several modal verbs fit some gaps; the answer of the book's answer
sheet is accepted together with the alternatives that are equally correct
in the context."""

from . import base, choice_gap, exercise, gap, html_table, match, mc, tf, words

L = 13

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
TEXT_EX = [gap(f"{title}: {_Q}", text, {str(i): acc for i, acc in enumerate(keys, start=1)}, points=6,
               explanation="Kitob kaliti: " + ", ".join(k[0] for k in keys)) for title, text, keys in TEXTS]

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
    mc("Warum konnte Julia Fischer nicht zum Termin kommen?", ["Sie war krank.", "Sie musste an einer wichtigen Besprechung teilnehmen.",
                                                               "Ihr Zug hatte Verspätung."], "B", passage=2),
    tf("Thomas Schneider und Frau Hoffmann haben über ein neues Projekt gesprochen.", True, passage=3),
    mc("Was hat Lukas Müller heute geschickt?", ["Einige Dokumente", "Ein Geschenk", "Eine Rechnung"], "A", passage=4),
]

HOEREN = [
    mc("Markus Klein: Warum konnte Markus nicht kommen?", ["Er war krank.", "Er konnte nicht zum Termin kommen.", "Er hatte keinen Parkplatz."], "B"),
    mc("Leon Schmidt: Wie spät kommt Leon?", ["30 Minuten später.", "20 Minuten später.", "Er kommt nicht."], "A"),
    mc("Laura Neumann: Warum musste Laura zu Hause bleiben?", ["Sie hatte viel Arbeit.", "Sie war krank.", "Sie hatte einen anderen Termin."], "B"),
    mc("Tim Wagner: Was war sein Problem?", ["Der Zug hatte Verspätung.", "Er konnte keinen Parkplatz finden.", "Er war krank."], "B"),
    mc("Jana Hoffmann: Warum konnte sie nicht pünktlich sein?", ["Sie musste arbeiten.", "Sie wollte nicht kommen.", "Der Zug hatte Verspätung."], "C"),
    mc("Daniel Fischer: Was möchte Daniel?", ["Das Treffen verschieben.", "Den Termin absagen.", "30 Minuten später kommen."], "A"),
]

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


def items() -> list[dict]:
    return [
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
             questions=LESEN, max_score=8),
        base(L, "hoeren", 1, "Hören: Termine — wer kann nicht kommen?", page=132, audio_file="A1-13.m4a",
             instruction="Hören Sie die Nachrichten und wählen Sie die richtige Antwort.",
             metadata={"book_page": 132, "note": "Javoblar kitobning javoblar varag'idan; audio yuklanganda admin tekshirsin."},
             questions=HOEREN, max_score=len(HOEREN)),
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
        base(L, "wortschatz", 1, "Wortschatz Modul 13", page=135, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 13", source="vizu",
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
    ]
