"""A2 13. Unterricht — Geld, Finanzen und Alltag — Grammatik: Konjunktiv II (book pp. 164-183).

Prüfungsnah. Book: Frage p.165, Konjunktiv II p.166, Aufgaben 1-4 p.167, Lesen
Teil 1-4 pp.168-174, Hören Teil 1-4 pp.175-178 (no transcript, no key),
Schreiben Teil 1 / 2 with Musterlösungen p.179, Sprechen Teil 1-3
pp.180-182, Wortschatz (Wortschatzmethode) p.183. The lesson PDF has no text
layer — everything is taken from the page images.

Keys: "Vizu-Antworten A2" has none. Corrections: the book's Konjunktiv table
gives "können → müsste" and "müssen → dürfte" (printing error) — shown as
können → könnte, müssen → müsste, dürfen → dürfte; "Ein Relativsatz II" →
"Der Konjunktiv II". Aufgaben with more than one correct form accept every
correct form (e.g. Könnten / Würden Sie …?). AUDIO: the files
"A2 13.Unterricht Teil 1-4" are byte-identical to lesson 12's (tracks 27-39),
but lesson 13 needs tracks 40-52 — the right audio is missing, nothing is
attached; the four Hören tasks stay drafts (key_pending) until an admin
uploads the right audio and sets the keys."""

from . import base, exercise, gap, intro_html, match, mc, mc_pending, summary_html, tf, ul

L = 13
LESSON_TITLE = "Geld, Finanzen und Alltag"
LESSON_DESCRIPTION = "Thema: Geld, Finanzen und Alltag · Grammatik: Konjunktiv II · Prüfungstraining A2"
AUDIO: dict = {}  # the delivered files are lesson 12's audio — see module docstring
IMAGES = [("p176_hoeren_teil2.jpg", "HOEREN", "Hören Teil 2 — Wie war Carmens Geburtstag? Bilder a bis i (Buch, S. 176)"),
          ("p177_hoeren_teil3.jpg", "HOEREN", "Hören Teil 3 — Bilder (Buch, S. 177)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    13, "Geld, Finanzen und Alltag", "Konjunktiv II",
    ["Konjunktiv II bilan istak, real bo'lmagan holat, xushmuomala iltimos va maslahat aytish;",
     "würde + Infinitiv va wäre / hätte / könnte / müsste / sollte shakllari;",
     "Wenn-Sätze: Wenn ich reich wäre, würde ich reisen."],
    ["kundalik hayotda qanday pul tejash mumkinligini aytasiz;",
     "kasbiy ta'lim, yoshlar dasturi, e-mail va to'garak e'lonlarini tushunasiz;",
     "SMS va o'qituvchingizga e-mail yozasiz;",
     "savol berasiz, o'zingiz haqida gapirasiz va dars uchun uchrashuv vaqtini kelishasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(13, [
    "<strong>Wunsch:</strong> Ich hätte gern mehr Zeit. · Ich würde gern in Deutschland leben.",
    "<strong>Irreale Situation:</strong> Wenn ich reich wäre, würde ich ein Haus kaufen. · Wenn ich Zeit hätte, käme ich mit.",
    "<strong>Höfliche Bitte:</strong> Könnten Sie mir helfen? · Würden Sie bitte langsamer sprechen?",
    "<strong>Ratschlag:</strong> Du solltest mehr lernen. · Du könntest früher schlafen.",
    "<strong>Geld sparen:</strong> Einkaufsliste, Preise vergleichen, Licht ausschalten, Budget planen.",
])

GRAMMAR_HTML = (
    "<h3>Konjunktiv II (A2–B1)</h3>"
    "<h4>1. Was ist Konjunktiv II?</h4><p>Der Konjunktiv II beschreibt: <strong>irreale Situationen</strong> (nicht real), <strong>Wünsche</strong>, "
    "<strong>Höflichkeit</strong>.</p>"
    "<h4>2. Verwendung</h4><ul><li><strong>Wunsch:</strong> Ich hätte gern mehr Zeit. · Ich würde gern in Deutschland leben.</li>"
    "<li><strong>Irreale Situationen:</strong> Wenn ich reich wäre, würde ich ein Haus kaufen. · Wenn ich Zeit hätte, käme ich mit.</li>"
    "<li><strong>Höfliche Bitten:</strong> Könnten Sie mir helfen? · Würden Sie bitte langsamer sprechen?</li>"
    "<li><strong>Ratschläge:</strong> Du solltest mehr lernen. · Du könntest früher schlafen.</li></ul>"
    "<h4>3. Bildung (Struktur)</h4><p><strong>a) Mit „würde“ + Infinitiv</strong> (am häufigsten): Subjekt + würde + Infinitiv — Ich würde Deutsch lernen. · "
    "Wir würden nach Berlin fahren.</p>"
    "<p><strong>b) Mit starken Verben:</strong> sein → wäre · haben → hätte · können → könnte · müssen → müsste · dürfen → dürfte · sollen → sollte · "
    "wollen → wollte</p>"
    "<p><em>Hinweis: Im Buch steht „können → müsste“ und „müssen → dürfte“ (Druckfehler) — hier die richtigen Formen.</em></p>"
    "<h4>4. Wenn-Sätze (sehr wichtig)</h4><p>Wenn + Subjekt + Verb (am Ende), würde + Infinitiv — Wenn ich reich wäre, würde ich reisen. · Wenn ich Zeit "
    "hätte, würde ich dir helfen.</p>"
    "<h4>Unterschied: Realität vs. Irrealität</h4><ul><li>Ich habe Zeit → Realität</li><li>Ich hätte Zeit → nicht real / Wunsch</li></ul>"
    "<h4>5. Mini-Übung</h4><ul><li>✗ Ich würde kann gehen → ✓ Ich könnte gehen</li><li>✗ Wenn ich würde Zeit haben → ✓ wenn ich Zeit hätte</li></ul>"
)

A1 = [
    gap("Ergänzen Sie mit hätte / wäre / würde.", "1. Ich [[1]] gern mehr Zeit.", {"1": ["hätte"]}),
    gap("Ergänzen Sie mit hätte / wäre / würde.", "2. Ich [[1]] nach Deutschland reisen.", {"1": ["würde", "würde gern"]}),
    gap("Ergänzen Sie mit hätte / wäre / würde.", "3. Wenn ich reich [[1]], [[2]] ich ein großes Haus kaufen.", {"1": ["wäre"], "2": ["würde"]}, points=2),
    gap("Ergänzen Sie mit hätte / wäre / würde.", "4. Ich [[1]] gern besser Deutsch sprechen.", {"1": ["würde"]}),
    gap("Ergänzen Sie mit hätte / wäre / würde.", "5. Wenn ich frei [[1]], [[2]] ich dich besuchen.", {"1": ["hätte", "wäre"], "2": ["würde"]}, points=2),
]
A2 = [
    gap("Ergänzen Sie die Wenn-Sätze.", "1. Wenn ich mehr Geld [[1]], [[2]] ich ein Auto kaufen.", {"1": ["hätte"], "2": ["würde"]}, points=2),
    gap("Ergänzen Sie die Wenn-Sätze.", "2. Wenn ich in Berlin [[1]], [[2]] ich jeden Tag Deutsch sprechen.",
        {"1": ["wäre", "wohnte", "lebte", "wohnen würde", "leben würde"], "2": ["würde"]}, points=2),
    gap("Ergänzen Sie die Wenn-Sätze.", "3. Wenn ich Zeit [[1]], [[2]] ich dir helfen.", {"1": ["hätte"], "2": ["würde"]}, points=2),
    gap("Ergänzen Sie die Wenn-Sätze.", "4. Wenn ich ein Lehrer [[1]], [[2]] ich weniger Hausaufgaben geben.", {"1": ["wäre"], "2": ["würde"]}, points=2),
    gap("Ergänzen Sie die Wenn-Sätze.", "5. Wenn ich fliegen [[1]], [[2]] ich um die Welt reisen.", {"1": ["könnte"], "2": ["würde"]}, points=2),
]
A3 = [
    gap("Ergänzen Sie mit könnte / würde.", "1. [[1]] Sie mir bitte helfen?", {"1": ["Könnten", "Würden"]}),
    gap("Ergänzen Sie mit könnte / würde.", "2. [[1]] Sie langsamer sprechen?", {"1": ["Könnten", "Würden"]}),
    gap("Ergänzen Sie mit könnte / würde.", "3. [[1]] ich bitte ein Glas Wasser bekommen?", {"1": ["Könnte"]}),
    gap("Ergänzen Sie mit könnte / würde.", "4. [[1]] Sie das Fenster öffnen?", {"1": ["Könnten", "Würden"]}),
    gap("Ergänzen Sie mit könnte / würde.", "5. [[1]] du mir dein Buch geben?", {"1": ["Könntest", "Würdest"]}),
]
A4 = [gap("Ergänzen Sie mit sollte / könnte.", f"{i}. Du [[1]] {s}", {"1": ["solltest", "könntest"]}) for i, s in enumerate(
    ["mehr lernen.", "früher schlafen.", "mehr Sport machen.", "weniger am Handy sein.", "mehr Deutsch sprechen."], start=1)]

TEXT_T1 = (
    "„Berufsausbildung in Deutschland“\n\nDie Wahl des passenden Berufs beschäftigt Kinder und Jugendliche, solange sie noch zur Schule gehen. Familie, Lehrer, "
    "Freunde und Bekannte können da sicher helfen, aber die Entscheidung muss von dem Jugendlichen getroffen werden. In Deutschland wollen viele Schüler nach "
    "ihrem Schulabschluss nicht auf die Uni gehen, sondern einen Beruf lernen. Wer will, kann daher nach Abschluss der Hauptschule, Realschule oder des "
    "Gymnasiums eine Berufsausbildung beginnen. Dazu besucht man eine Berufsschule.\n\nIn den Berufsschulen haben die Jugendlichen zwei- oder dreimal in "
    "der Woche Unterricht und an den anderen Tagen arbeiten sie, zum Beispiel bei einem Friseur, bei einer Firma, in einem Büro oder woanders. So können "
    "die Jugendlichen den Beruf besser lernen und dabei auch etwas Geld verdienen.\n\nDie Schüler in den Berufsschulen heißen „Azubis“. Das kommt von "
    "„Auszubildende“ und bedeutet „Leute, die ausgebildet werden müssen“. Die Azubis besuchen die Berufsschule zwei bis dreieinhalb Jahre lang und "
    "bekommen jeden Monat etwa 380 Euro.\n\nDiese Art der Berufsausbildung heißt „duale Ausbildung“, das heißt Ausbildung auf zwei Wegen, denn "
    "Jugendliche haben Unterricht und arbeiten, sie machen also beides, eine Kombination von Theorie und Praxis, die für den späteren Beruf sehr nützlich "
    "ist.\n\nDie duale Berufsausbildung ist in Deutschland bei den Jugendlichen, die nicht studieren wollen, sehr beliebt. Auf die Frage „Wie findet ihr "
    "die duale Ausbildung?“ antworten die meisten: „Ganz toll!“ Es ist aber für die Jugendlichen nicht immer leicht, einen Ausbildungsplatz in ihrem "
    "Traumberuf zu finden.")
LESEN_T1 = [
    mc("1 In Deutschland …", ["wollen alle Schüler nach der Schule studieren.", "wollen die meisten Schüler keinen Beruf lernen.",
                              "kann man nach Abschluss der Schule einen Beruf lernen."], "C",
       "„Wer will, kann daher nach Abschluss der Hauptschule, Realschule oder des Gymnasiums eine Berufsausbildung beginnen.“"),
    mc("2 In der Berufsschule …", ["muss man jeden Tag arbeiten.", "hat man nicht jeden Tag Unterricht.", "muss man für die Teilnahme am Unterricht zahlen."], "B",
       "„… zwei- oder dreimal in der Woche Unterricht und an den anderen Tagen arbeiten sie …“"),
    mc("3 Die Schüler …", ["in der Berufsschule nennt man „Azubis“.", "müssen die Berufsschule mindestens drei Jahre lang besuchen.",
                           "bekommen alle zwei Monate etwa 400 Euro."], "A", "„Die Schüler in den Berufsschulen heißen „Azubis“.“"),
    mc("4 „Duale Berufsausbildung“ bedeutet:", ["Zwei Berufe zur gleichen Zeit lernen.", "Eine Berufsausbildung gleichzeitig in zwei Firmen machen.",
                                               "Unterricht haben und arbeiten."], "C", "„… denn Jugendliche haben Unterricht und arbeiten …“"),
    mc("5 Die meisten Jugendlichen …", ["finden die duale Ausbildung leicht, aber langweilig.", "sind mit der dualen Ausbildung sehr zufrieden.",
                                        "können problemlos einen Ausbildungsplatz finden."], "B", "„… antworten die meisten: „Ganz toll!“"),
]
TEXT_T2 = (
    "Sommerprogramm des Jugendtreffs Stuttgart vom 6. bis 11. August\n\nMontag, 6. August: Wir wollen an diesem Tag das Schloss Neuschwanstein besuchen. Es "
    "ist nicht sehr weit weg, nur 2 Stunden mit dem Bus. Dieser Ausflug lohnt sich!\nDienstag, 7. August: Wer Lust hat, kann mit anderen Jungen oder Mädchen "
    "Fußball spielen. Von 15 Uhr bis 18 Uhr ist das Fußballstadion frei. Meldet euch an!\nMittwoch, 8. August: Da es an diesem Tag sehr warm werden soll, "
    "organisieren wir einen Ausflug ins Freibad. Wem es zu warm ist, kann mitkommen!\nDonnerstag, 9. August: Am Abend haben wir vor, einen spannenden Krimi zu "
    "zeigen. Es ist der neue James-Bond-Film. Den solltet ihr euch unbedingt ansehen!\nFreitag, 10. August: Wer gern Rad fährt, sollte an dieser Veranstaltung "
    "teilnehmen. Wir fahren diesmal ungefähr 10 Kilometer.\nSamstag, 11. August: Party, Beginn 20 Uhr. Ihr seid alle herzlich eingeladen. Es wird etwas zu "
    "essen und zu trinken geben. Der Eintritt kostet nur 3 Euro.")
LESEN_T2 = [
    mc("6 Du möchtest eine Fahrradtour machen.", ["Dienstag, 7. August", "Donnerstag, 9. August", "anderer Tag"], "C", "Radfahren: Freitag, 10. August → anderer Tag."),
    mc("7 Du möchtest Sport treiben.", ["Montag, 6. August", "Dienstag, 7. August", "anderer Tag"], "B", "Dienstag: Fußball spielen."),
    mc("8 Du gehst gern schwimmen.", ["Mittwoch, 8. August", "Freitag, 10. August", "anderer Tag"], "A", "Mittwoch: Ausflug ins Freibad."),
    mc("9 Du möchtest gern einen Film sehen.", ["Montag, 6. August", "Dienstag, 7. August", "anderer Tag"], "C", "Film: Donnerstag, 9. August → anderer Tag."),
    mc("10 Du möchtest einen Ausflug zu einer Sehenswürdigkeit machen.", ["Montag, 6. August", "Mittwoch, 8. August", "anderer Tag"], "A",
       "Montag: Schloss Neuschwanstein."),
]
TEXT_T3 = (
    "Von: Petra · An: Annette · Betreff: Prüfungsstress\n\nLiebe Annette,\nich kann deinen Prüfungsstress gut verstehen, denn mir ging es früher auch so. Am "
    "Tag vor einer Prüfung konnte ich nicht richtig lernen, und gut geschlafen habe ich da auch nicht. Aber du bist nicht die Einzige, die dieses Problem "
    "hat.\n\nIn meiner E-Mail möchte ich dir darum ein paar Tipps geben, die gegen diesen Stress helfen. Die Tipps habe ich von meinem Vater bekommen, der, "
    "wie du ja weißt, Lehrer ist. In solchen Situationen kann dir ein Lehrer, glaube ich, besser als ein Arzt helfen.\n\nNun zu den Tipps: Du solltest am "
    "Abend vor der Prüfung den Stoff noch einmal durchgehen und früh schlafen gehen. Lerne nicht allein, sondern mit deinen Freunden zusammen. Trefft euch "
    "regelmäßig vor der Prüfung, denn zusammen macht das Lernen mehr Spaß.\n\nBesonders wichtig ist nicht, wie viele Stunden du lernst, sondern wie du "
    "lernst. Warte nicht bis zum letzten Tag vor der Prüfung! Mach dir einen genauen Lernplan und lerne jeden Tag ein bisschen! Unterstreiche mit einem "
    "Textmarker, was du dir merken musst.\n\nVergiss außerdem die gesunde Ernährung nicht, iss nicht zu viel Süßes, stattdessen lieber viel Obst und viel "
    "Gemüse. Und mach beim Lernen kleine Pausen, fünf Minuten sind meistens genug. Pausen sind wichtig und helfen dir, dich zu konzentrieren.\n\nHoffentlich "
    "habe ich dir ein wenig geholfen. Viel Erfolg bei der nächsten Prüfung!\n\nAlles Liebe\ndeine Petra")
LESEN_T3 = [
    mc("11 Was sagt Petra zu Beginn?", ["Dass sie gestern gut geschlafen hat.", "Dass sie früher auch Angst vor Prüfungen hatte.",
                                        "Dass sie Annettes Ruhe vor Prüfungen toll findet."], "B", "„… denn mir ging es früher auch so.“"),
    mc("12 Wer hat Petra die Tipps gegen Stress gegeben?", ["Ihr Lehrer.", "Ihr Arzt.", "Ihr Vater."], "C", "„Die Tipps habe ich von meinem Vater bekommen …“"),
    mc("13 Was hilft nach Ansicht von Petra beim Lernen vor einer Prüfung?", ["Immer allein lernen.", "Eine Wiederholung am Abend vor der Prüfung.",
                                                                              "Sich am Tag der Prüfung mit Freunden treffen."], "B",
       "„Du solltest am Abend vor der Prüfung den Stoff noch einmal durchgehen …“"),
    mc("14 Was ist beim Lernen wichtig?", ["Am Tag vor der Prüfung nicht mehr lernen.", "Möglichst viele Stunden lernen.", "Genau planen, wann man was lernt."], "C",
       "„Mach dir einen genauen Lernplan …“"),
    mc("15 Was soll Annette beim Lernen nicht vergessen?", ["Sich zu konzentrieren.", "Kleine Pausen zu machen.", "Jeden Tag etwas Schokolade zu essen."], "B",
       "„Und mach beim Lernen kleine Pausen …“"),
]
TEXT_T4 = (
    "Am schwarzen Brett der Schule: Freizeit-AGs\n\na Alles über Haustiere: Bist du tierlieb? Hättest du auch gern ein Haustier? In dieser AG lernt man, wie man "
    "sich richtig um sein Haustier kümmern sollte. Man lernt, was ein Haustier frisst und wann man es zum Tierarzt bringen muss.\n\nb Musik, Musik, Musik!: "
    "Wer schon immer Musik machen wollte, ist in dieser AG am richtigen Platz. Hier könnt ihr schnell ein Instrument spielen lernen. Wählen könnt ihr "
    "zwischen Schlagzeug, Gitarre oder Flöte. Das Tolle dabei: Am Schuljahresende nehmt ihr an einem Konzert teil!\n\nc Fit durch Tanz: Hier könnt ihr zwei "
    "Aktivitäten miteinander kombinieren, nämlich Gymnastik und Tanzen. In dieser AG lernt ihr Tänze aus der ganzen Welt, von Tango bis Breakdance. Es gibt "
    "eine Gruppe für Anfänger und eine für Fortgeschrittene.\n\nd AG „Botanik“: Wie wäre es mit einem eigenen Apfelbaum im Garten? Oder magst du lieber "
    "Tulpen? Egal! Wenn ihr euch für Bäume, Pflanzen und die verschiedenen Blumenarten interessiert, dann warten in der AG „Botanik“ viele interessante "
    "Projekte auf euch.\n\ne PC-Freunde: Computer haben zwei Seiten, eine gute und eine gefährliche. Hier lernt ihr, welche Vor- und Nachteile das Surfen "
    "im Internet hat. Ihr lernt, wie man das Internet für die Schule nutzen kann und was man auf keinen Fall tun sollte.\n\nf AG „Sport“ – der Klassiker: "
    "Sport macht immer Spaß, Sport ist gut für die Gesundheit. In dieser AG können alle mitmachen. Es werden Fußball, Basketball, Handball, Volleyball und "
    "auch Tennis angeboten. Neu in diesem Jahr: Fußball für Mädchen. Meldet euch rechtzeitig an!")
LESEN_T4 = [match(
    "Welche Anzeige passt zu welcher Person? (Für eine Aufgabe gibt es keine Lösung: X)",
    ["16 Inge hat zum Geburtstag eine Katze geschenkt bekommen.", "17 Rainer möchte Klavier spielen lernen.", "18 Peter arbeitet gern im Garten.",
     "19 Renate tanzt in ihrer Freizeit sehr gern.", "20 Markus sitzt lange am Computer und surft."],
    ["Anzeige a) Alles über Haustiere", "Anzeige c) Fit durch Tanz", "Anzeige d) AG „Botanik“", "Anzeige e) PC-Freunde", "X – keine passende Anzeige"],
    {"1": "A", "2": "E", "3": "C", "4": "B", "5": "D"}, points=5,
    explanation="16 → a, 17 → X (die Musik-AG bietet Schlagzeug, Gitarre oder Flöte — kein Klavier), 18 → d, 19 → c, 20 → e. Anzeige b und f bleiben übrig.")]

_X = "X – keine Lösung"
HOEREN_T1 = [mc_pending(q, o + [_X]) for q, o in [
    ("1 Was macht Anne?", ["Sie geht gleich zum Obsthändler.", "Sie macht gerade ihre Hausaufgaben.", "Sie hilft Stefanie in Mathe."]),
    ("2 Warum können die Schüler nach Hause gehen?", ["Weil sie morgen einen Ausflug machen.", "Weil es sehr warm ist.", "Weil auf der Straße zu viel Lärm ist."]),
    ("3 Wer gewinnt einen Media-Player?", ["Die ersten zehn Personen mit einem lustigen Sport-Foto.", "Wer zehn lustige Sport-Fotos schickt.",
                                           "Gruppen von zehn Freunden, die am Wettbewerb teilnehmen."]),
    ("4 Bärbel ruft an, …", ["weil sie nicht mit Marianne ins Kino gehen möchte.", "weil sie für ihre Oma einkaufen muss.", "weil sie zum Treffen kommen kann."]),
    ("5 Was sagt der Moderator?", ["Es ist genau zwei Uhr.", "Am Freitag gibt es immer eine Diskussion.", "In der heutigen Sendung geht es um E-Mails."])]]
_BILDER = ["a) Fahrrad", "b) Buch lesen", "c) Thermometer (Fieber)", "d) Musik (5 Seconds of Summer)", "e) Tee", "f) tanzen", "g) Getränke", "h) Pizza",
           "i) Geburtstagstorte"]
HOEREN_T2 = [gap("Wie war Carmens Geburtstag? Wähle das passende Bild.", f"{name}: [[1]]", {"1": {"accepted": [], "options": _BILDER}})
             for name in ("6 Carmen", "7 Paul", "8 Luisa", "9 Nadine", "10 Eltern")]
HOEREN_T3 = [mc_pending(q, o) for q, o in [
    ("11 Was isst das Mädchen zuerst?", ["a) Schnitzel mit Pommes", "b) Eis", "c) Salat"]),
    ("12 Was für ein Geschenk kaufen die Mädchen?", ["a) eine Tasche", "b) eine Kette", "c) ein Buch"]),
    ("13 Mit welchem Verkehrsmittel reisen die Jugendlichen?", ["a) mit dem Zug", "b) mit dem Flugzeug", "c) mit dem Bus"]),
    ("14 Wann kommt Tante Anna zu Besuch?", ["a) Sonntag, 5.", "b) Donnerstag, 9.", "c) Freitag, 7."]),
    ("15 Welches Kleidungsstück kauft das Mädchen?", ["a) einen Pullover", "b) ein T-Shirt", "c) ein Kleid"])]]
HOEREN_T4 = [{"type": "true_false", "question": q, "options": ["Ja", "Nein"], "points": 1, "passage": 1} for q in [
    "16 Die Abschlussprüfung war schwierig.", "17 Sebastian wollte von Anfang an Medizin studieren.", "18 Nach dem Studium will Sebastian freiwillig in Afrika arbeiten.",
    "19 Sebastian möchte in der Nähe seines Hauses arbeiten.", "20 Sebastian wartet, bis er eine Stelle im Katharina-Hospital findet."]]

VARIANTEN = {
    "Variante 1": ["das Geld", "der Preis", "der Einkauf", "der Supermarkt", "die Rechnung", "das Angebot"],
    "Variante 2": ["bezahlen", "sparen", "kaufen", "verkaufen", "kosten", "verdienen"],
    "Variante 3": ["das Konto", "die Bank", "die Karte", "das Bargeld", "die Überweisung", "der Automat"],
    "Variante 4": ["das Budget", "die Ausgaben", "die Einnahmen", "die Miete", "die Rechnung", "die Kosten"],
    "Variante 5": ["das Einkommen", "der Job", "das Taschengeld", "die Zukunft", "die Planung", "die Sicherheit"],
}
WORTSCHATZ_HTML = ("<h3>Wortschatz A2 — Geld, Finanzen und Alltag</h3>" + "".join(f"<h4>{k}</h4>" + ul(v) for k, v in VARIANTEN.items())
                   + "<p>Formulieren Sie einen Text mit den Wörtern einer Variante (Aufgabe im Bereich Schreiben).</p>")


def _hoeren(n: int, title: str, page: int, instruction: str, questions: list[dict]) -> dict:
    return base(L, "hoeren", n, title, page=page, key_pending=True, instruction=instruction, questions=questions,
                metadata={"note": "AUDIO YO'Q: yetkazilgan „A2 13.Unterricht Teil 1-4“ fayllari 12-darsnikiga aynan bir xil (kitobda 40-52-treklar kerak). "
                                  "To'g'ri audio va kalit admin tomonidan kiritilguncha qoralama."})


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 13. Unterricht", source="vizu", page=164, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie kann man im Alltag Geld sparen?", page=165, prompt="Wie kann man im Alltag Geld sparen? Sprecht darüber!",
             questions=["1 Bewusst einkaufen", "2 Energie sparen", "3 Geld planen"], min_duration=20, max_duration=120,
             metadata={"book_answers": {
                 "Bewusst einkaufen": "Ich mache immer eine Einkaufsliste und kaufe nur das, was ich wirklich brauche. Ich vergleiche Preise und achte auf "
                                      "Angebote. So gebe ich weniger aus und spare Geld.",
                 "Energie sparen": "Ich schalte das Licht aus, wenn ich es nicht brauche. Ich dusche statt zu baden und nutze Energiesparlampen. Das spart nicht "
                                   "nur Geld, sondern schützt auch die Umwelt.",
                 "Geld planen": "Ich plane mein Budget und schreibe meine Ausgaben auf. Ich setze mir Sparziele, z. B. für Reisen oder neue Dinge. So habe ich "
                                "mehr Kontrolle über mein Geld."}}),
        base(L, "grammatik", 1, "Grammatik: Konjunktiv II", page="166-167", rules=[{"title": "Konjunktiv II (A2–B1)", "html": GRAMMAR_HTML}],
             exercises=[exercise("1 Wünsche (Lückentext)", A1, "Ergänzen Sie mit hätte / wäre / würde + Infinitiv."),
                        exercise("2 Irreale Situationen (Wenn-Sätze)", A2, "Ergänzen Sie die Sätze."),
                        exercise("3 Höfliche Bitten (Lückentext)", A3, "Ergänzen Sie mit könnte / würde (in der richtigen Form)."),
                        exercise("4 Ratschläge (Tipps geben)", A4, "Ergänzen Sie mit sollte / könnte (in der richtigen Form).")],
             metadata={"book_page": "166-167", "corrections": ["können → könnte, müssen → müsste (Buch: müsste / dürfte — Druckfehler).",
                                                               "„Ein Relativsatz II“ → „Der Konjunktiv II“."]}),
        base(L, "lesen", 1, "Lesen Teil 1: Berufsausbildung in Deutschland", page="168-169", instruction="Du liest einen Zeitungstext. Wähle a, b oder c.",
             passages=[{"title": "Berufsausbildung in Deutschland", "text": TEXT_T1}], questions=LESEN_T1, max_score=5),
        base(L, "lesen", 2, "Lesen Teil 2: Sommerprogramm des Jugendtreffs Stuttgart", page="170-171",
             instruction="Du liest am Jugendtreff das Veranstaltungsprogramm. Welcher Tag ist richtig? Wähle a, b oder c.",
             passages=[{"title": "Sommerprogramm des Jugendtreffs Stuttgart", "text": TEXT_T2}], questions=LESEN_T2, max_score=5),
        base(L, "lesen", 3, "Lesen Teil 3: E-Mail von Petra — Prüfungsstress", page="172-173",
             instruction="Du liest eine E-Mail. Wähle für die Aufgaben 11 bis 15 a, b oder c.",
             passages=[{"title": "E-Mail: Prüfungsstress", "text": TEXT_T3}], questions=LESEN_T3, max_score=5),
        base(L, "lesen", 4, "Lesen Teil 4: Freizeit-AGs am schwarzen Brett", page=174,
             instruction="Sechs Jugendliche suchen eine passende Freizeit-AG. Welche Anzeige passt zu welcher Person? Für eine Aufgabe gibt es keine Lösung.",
             passages=[{"title": "Freizeit-AGs", "text": TEXT_T4}], questions=LESEN_T4, max_score=5),
        _hoeren(1, "Hören Teil 1: Fünf kurze Texte", 175, "Du hörst fünf kurze Texte zweimal. Wähle a, b oder c. Für eine Aufgabe gibt es keine Lösung: X.", HOEREN_T1),
        _hoeren(2, "Hören Teil 2: Wie war Carmens Geburtstag?", 176, "Du hörst ein Gespräch einmal. Wähle für die Aufgaben 6 bis 10 ein passendes Bild "
                                                                     "(Bild im Abschnitt). Wähle jeden Buchstaben nur einmal.", HOEREN_T2),
        _hoeren(3, "Hören Teil 3: Fünf kurze Gespräche", 177, "Du hörst fünf kurze Gespräche einmal. Wähle a, b oder c (Bilder im Abschnitt).", HOEREN_T3),
        _hoeren(4, "Hören Teil 4: Interview mit Sebastian", 178, "Du hörst ein Interview zweimal. Wähle „Ja“ oder „Nein“. (Beispiel: 0 Sebastian ist Student. → Ja)",
                HOEREN_T4),
        base(L, "schreiben", 1, "Schreiben Teil 1: SMS an Susanne", page=179, task_type="message",
             prompt="Deine Freundin Susanne schickt dir eine SMS mit einer Einladung zu einer Gartenparty. Antworte Susanne mit einer SMS.\n"
                    "• Schreib, ob du kommst.\n• Frage, wann die Party stattfindet und wie lange sie dauert.\n• Frage, was du mitbringen sollst.\n\n"
                    "Schreib 20–30 Wörter. Schreib zu allen drei Punkten.\n\nBeispiel (Buch): Hallo Susanne, vielen Dank für deine Einladung. Ich gehe "
                    "natürlich zu deiner Party. Aber habe eine Frage. Wann findet die Party statt? Und kannst du noch sagen, wie lange sie dauert? Was kann ich "
                    "noch für die Party mitbringen? Wenn du möchtest, kann ich einige Getränke mitbringen. Schreib mir bitte deine Antwort. Dein Alex",
             audience="Freundin Susanne (informell)", min_words=20, max_words=40, time_limit=10),
        base(L, "schreiben", 3, "Schreiben Teil 2: E-Mail an Herrn Häfner", page=179, task_type="email",
             prompt="Dein Klassenlehrer Herr Häfner hat sein Bein gebrochen und liegt im Krankenhaus. Du und zwei andere Mitschüler wollt ihn besuchen. Schreib "
                    "Herrn Häfner eine E-Mail:\n• Frage, wie es ihm geht, und wünsch ihm gute Besserung.\n• Informiere ihn über den geplanten Besuch.\n"
                    "• Frage nach dem passenden Termin (Tag und Uhrzeit).\n\nSchreib 30–40 Wörter. Schreib zu allen drei Punkten.",
             audience="Klassenlehrer Herr Häfner (formell)", min_words=30, max_words=50, time_limit=15,
             support_phrases=["Sehr geehrter Herr Häfner,", "wie geht es Ihnen?", "Wir wünschen Ihnen gute Besserung.", "Wir möchten Sie besuchen.",
                              "Wann passt es Ihnen?", "Mit freundlichen Grüßen"],
             metadata={"book_sample": "Sehr geehrter Herr Häfner, hoffentlich geht Ihnen gut. Und wünschen wir Ihnen lebenslange Gesundheit. Wir haben mit "
                                      "unseren Mitschülern vor, Sie zu besuchen. Können Sie sagen, wann wir besuchen können? Wir warten auf Ihre Antwort. "
                                      "Mit freundlichen Grüßen Alex, Anna, Markus"}),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Geld, Finanzen und Alltag", page=183, task_type="description",
             prompt="Formulieren Sie mit den Wörtern einer Variante einen Text.\n\n" + "\n".join(f"{k}: {', '.join(v)}" for k, v in VARIANTEN.items()),
             min_words=40, max_words=200, time_limit=25),
        base(L, "sprechen", 1, "Sprechen Teil 1: Fragen zur Person", page=180, topic="Fragen zur Person", response_type="dialog",
             prompt="Du nimmst vier Karten und stellst mit diesen Karten vier Fragen. Dein Partner / deine Partnerin antwortet.",
             questions=["Kandidat 1: Sport?", "Kandidat 1: Wohnort?", "Kandidat 1: Lieblingsmusik?", "Kandidat 1: Computerspiele?", "Kandidat 2: Kino?",
                        "Kandidat 2: Lesen?", "Kandidat 2: Haustier?", "Kandidat 2: Theater?"],
             min_duration=30, max_duration=150, speech_goal="Zu jedem Stichwort eine korrekte Frage stellen und beantworten.",
             keywords=["Machst du", "Wo wohnst du", "Was hörst du", "Hast du"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Von sich erzählen", page=181, topic="Von sich erzählen",
             prompt="Du bekommst eine Karte und erzählst etwas über dein Leben. Karte A: Wie findest du deine Schule? Karte B: Was machst du nach der Schule?",
             questions=["Karte A: Klassenzimmer?", "Karte A: Computerraum?", "Karte A: Lehrer?", "Karte A: Kantine?", "Karte B: Computer?",
                        "Karte B: draußen spielen?", "Karte B: Fremdsprachen?", "Karte B: Hausaufgaben?"],
             response_type="monolog", min_duration=45, max_duration=150, speech_goal="Zu einer Aufgabenkarte zusammenhängend von sich erzählen.",
             keywords=["meine Schule", "nach der Schule", "gern", "weil"]),
        base(L, "sprechen", 3, "Sprechen Teil 3: Für den Englischtest lernen — wann treffen wir uns?", page=182, topic="Einen Termin finden",
             response_type="dialog",
             prompt="Ihr wollt am Samstag zusammen für den Englischtest am Montag lernen. Wann könnt ihr euch treffen? (Samstag, 08.12.)\n\n"
                    "Aufgabenblatt A: 09.00–10.00 Einkaufen · 11.00 Zimmer aufräumen · 13.00 Mittagessen · 16.00 im Garten arbeiten · 18.00 am Computer spielen\n"
                    "Aufgabenblatt B: 09.00–10.00 Fußball-Training · 11.00–12.00 Zahnarzt · 14.00 in die Stadt gehen · 16.00 Hausaufgaben · 18.00 Paul treffen · "
                    "20.00 ins Kino gehen",
             questions=["Hast du um … Uhr Zeit?", "Um … Uhr kann ich nicht, ich muss …", "Wie wäre es um …?", "Gut, dann treffen wir uns um …"],
             min_duration=45, max_duration=180, speech_goal="Gemeinsam einen freien Termin aushandeln (Konjunktiv: Wie wäre es …? Könntest du …?).",
             keywords=["Hast du Zeit", "Wie wäre es", "leider", "treffen"]),
        base(L, "kompetenz", 3, "Wortschatz: Geld, Finanzen und Alltag", page=183, competency="WORTSCHATZ", html=WORTSCHATZ_HTML,
             metadata={"note": "Kitobda tarjima berilmagan — so'z ro'yxati to'qib chiqarilmadi."}),
        base(L, "yakuniy", 1, "Abschlusstest: A2 13. Unterricht", source="vizu",
             instruction="Konjunktiv II va dars matnlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Wenn ich reich ___, würde ich reisen.", ["wäre", "bin", "würde"], "A"),
                 mc("Ich ___ gern mehr Zeit.", ["hätte", "habe", "würde"], "A"),
                 mc("___ Sie mir bitte helfen?", ["Könnten", "Können", "Konnten"], "A", "Höfliche Bitte: Konjunktiv II."),
                 mc("Du ___ mehr lernen. (Ratschlag)", ["solltest", "sollst", "sollen"], "A"),
                 mc("Welcher Satz ist richtig?", ["Ich könnte gehen.", "Ich würde kann gehen.", "Ich würde könnte gehen."], "A", "Mini-Übung im Buch."),
                 mc("Wie viel Geld bekommen Azubis jeden Monat?", ["etwa 380 Euro", "etwa 400 Euro", "etwa 800 Euro"], "A", "Lesen Teil 1."),
                 mc("Was ist die „duale Ausbildung“?", ["Unterricht haben und arbeiten", "zwei Berufe lernen", "in zwei Firmen arbeiten"], "A", "Lesen Teil 1."),
                 tf("Petra hat die Tipps von ihrem Vater bekommen.", True, "Lesen Teil 3."),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 13. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
