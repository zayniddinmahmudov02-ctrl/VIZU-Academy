"""A2 11. Unterricht — Umwelt und Verantwortung — Grammatik: Passiv Präsens + man-Strukturen (book pp. 125-146).

Prüfungsnah like lesson 10. Book: Frage p.126, Grammatik pp.127-128, Lesen
Teil 1-4 pp.129-136, Hören Teil 1-4 pp.137-140 (no transcript, no key),
Schreiben Teil 1 / 2 pp.141-142, Sprechen Teil 1-3 pp.143-145,
Wortschatzmethode p.146.

Keys: "Vizu-Antworten A2" has none. Lesen: decided by the text (quoted).
Lesen Teil 1, Aufgabe 5 ("Tauchen lernen kostet … als Bungee-Jumping") is NOT
imported: the text gives no price for Bungee-Jumping. Grammar: one sentence
each (Passiv with or without "von …"; man-sentences in both word orders).
Hören waits for an admin (key_pending); Teil 2 / 3 picture tasks are
attached as book images. Audio: "A2 11.Unterricht Teil_1-4". Wortschatz:
word lists without translations — no word list is invented."""

from . import base, exercise, gap, intro_html, match, mc, mc_pending, short, summary_html, tf, ul

L = 11
LESSON_TITLE = "Umwelt und Verantwortung"
LESSON_DESCRIPTION = "Thema: Umwelt und Verantwortung · Grammatik: Passiv Präsens + man-Strukturen · Prüfungstraining A2"
AUDIO = {"vizu-a2-l11-hoeren-01": "A2 11.Unterricht Teil_1.m4a", "vizu-a2-l11-hoeren-02": "A2 11.Unterricht Teil_2.m4a",
         "vizu-a2-l11-hoeren-03": "A2 11.Unterricht Teil_3.m4a", "vizu-a2-l11-hoeren-04": "A2 11.Unterricht Teil_4.m4a"}
IMAGES = [("p138_hoeren_teil2.jpg", "HOEREN", "Hören Teil 2 — Bilder a bis i (Buch, S. 138)"),
          ("p139_hoeren_teil3.jpg", "HOEREN", "Hören Teil 3 — Bilder (Buch, S. 139)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    11, "Umwelt und Verantwortung", "Passiv Präsens + man-Strukturen",
    ["Passiv Präsens: werden + Partizip II — Der Brief wird geschrieben.;",
     "„man“ bilan shaxssiz gap: Man schreibt einen Brief.;",
     "A2 imtihon formatida to'rtta ko'nikma bo'yicha mashq qilish."],
    ["atrof-muhit uchun nima qila olishingizni aytasiz;",
     "gazeta matni, festival dasturi, e-mail va kurs e'lonlarini tushunasiz;",
     "qisqa matnlar, suhbat va intervyuni tinglab tushunasiz;",
     "SMS va o'qituvchiga e-mail yozasiz, savol berasiz va uchrashuvni kelishasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(11, [
    "<strong>Passiv Präsens:</strong> werden + Partizip II (+ von + Person) — Der Brief wird geschrieben.",
    "<strong>man:</strong> man + Verb (aktiv), wenn nicht wichtig ist, wer etwas tut — Man schreibt einen Brief.",
    "<strong>Merke:</strong> Passiv verwendet man, wenn die Handlung wichtiger ist als der Täter; man-Strukturen für allgemeine Aussagen.",
    "<strong>Kleine Handlungen, große Wirkung:</strong> Strom sparen, Müll trennen, Fahrrad fahren, Wasser sparen.",
])

GRAMMAR_HTML = (
    "<h3>Passiv Präsens + man-Strukturen</h3>"
    "<table><thead><tr><th>Passiv Präsens</th><th>Passiv: man</th></tr></thead><tbody>"
    "<tr><td>Das Passiv benutzt man, wenn die <strong>Handlung</strong> im Fokus steht und <strong>nicht</strong> die Person, die etwas tut.</td>"
    "<td>Das unpersönliche Pronomen „man“ benutzt man, wenn nicht wichtig ist, von wem etwas getan wird (subjektloser Satz).</td></tr>"
    "<tr><td><strong>Struktur:</strong> werden + Partizip II (+ von + Person)</td><td><strong>Struktur:</strong> man + Verb (aktiv)</td></tr>"
    "<tr><td>Der Brief wird geschrieben.<br>Die Küche wird sauber gemacht.<br>Ein Film wird oft gesehen.</td>"
    "<td>Man schreibt einen Brief.<br>Man macht die Küche sauber.<br>Man sieht oft Filme.</td></tr></tbody></table>"
    "<p><strong>Vergleich:</strong> Der Brief wird geschrieben. (werden + Partizip II) → Man schreibt einen Brief. (man + Verb)</p>"
    "<h4>Merke dir</h4><ul><li>Passiv verwendet man, wenn die Handlung wichtiger ist als der Täter.</li>"
    "<li>Man-Strukturen sind nützlich für allgemeine Aussagen ohne konkrete Person.</li><li>Beide Formen sind im Alltag und in Texten sehr häufig.</li></ul>"
)

_PASSIV = [  # (n, aktiv, passiv without agent, agent phrase)
    (2, "Die Schüler machen die Hausaufgaben.", "Die Hausaufgaben werden gemacht.", "von den Schülern"),
    (3, "Man baut ein neues Haus.", "Ein neues Haus wird gebaut.", None),
    (4, "Die Firma produziert Autos.", "Autos werden produziert.", "von der Firma"),
    (5, "Der Koch kocht das Essen.", "Das Essen wird gekocht.", "vom Koch"),
    (6, "Die Polizei kontrolliert die Autos.", "Die Autos werden kontrolliert.", "von der Polizei"),
    (7, "Die Mutter wäscht die Kleidung.", "Die Kleidung wird gewaschen.", "von der Mutter"),
    (8, "Die Kinder spielen Fußball.", "Fußball wird gespielt.", "von den Kindern"),
    (9, "Der Arzt untersucht den Patienten.", "Der Patient wird untersucht.", "vom Arzt"),
    (10, "Die Verkäuferin verkauft Brot.", "Brot wird verkauft.", "von der Verkäuferin"),
    (11, "Die Studenten schreiben einen Test.", "Ein Test wird geschrieben.", "von den Studenten"),
    (12, "Der Mechaniker repariert das Auto.", "Das Auto wird repariert.", "vom Mechaniker"),
    (13, "Die Lehrer korrigieren die Aufgaben.", "Die Aufgaben werden korrigiert.", "von den Lehrern"),
    (14, "Die Firma liefert die Pakete.", "Die Pakete werden geliefert.", "von der Firma"),
    (15, "Die Schüler lesen das Buch.", "Das Buch wird gelesen.", "von den Schülern"),
]


def _passiv(n: int, aktiv: str, passiv: str, agent: str | None) -> dict:
    accepted = [passiv, passiv.rstrip(".")]
    if agent:
        words = passiv.rstrip(".").split()
        with_agent = " ".join(words[:-1] + [agent, words[-1]]) + "."
        accepted += [with_agent, with_agent.rstrip(".")]
    return short(f"{n}. {aktiv}", accepted, explanation=passiv + (f" (oder: … {agent} …)" if agent else ""), max_length=150)


PASSIV = [_passiv(*row) for row in _PASSIV]

_MAN = [  # (n, cue, adverbial-first sentence, man-first sentence)
    (17, "am Abend / fernsehen", "Am Abend sieht man fern.", "Man sieht am Abend fern."),
    (18, "in Deutschland / Deutsch / sprechen", "In Deutschland spricht man Deutsch.", "Man spricht in Deutschland Deutsch."),
    (19, "im Restaurant / bezahlen / müssen", "Im Restaurant muss man bezahlen.", "Man muss im Restaurant bezahlen."),
    (20, "im Park / spazieren gehen", "Im Park geht man spazieren.", "Man geht im Park spazieren."),
    (21, "im Winter / Tee / trinken", "Im Winter trinkt man Tee.", "Man trinkt im Winter Tee."),
    (22, "im Sommer / schwimmen", "Im Sommer schwimmt man.", "Man schwimmt im Sommer."),
    (23, "in der Stadt / viele Menschen / sehen", "In der Stadt sieht man viele Menschen.", "Man sieht in der Stadt viele Menschen."),
    (24, "am Morgen / früh / aufstehen", "Am Morgen steht man früh auf.", "Man steht am Morgen früh auf."),
    (25, "im Büro / arbeiten", "Im Büro arbeitet man.", "Man arbeitet im Büro."),
    (26, "im Supermarkt / Obst / kaufen", "Im Supermarkt kauft man Obst.", "Man kauft im Supermarkt Obst."),
    (27, "im Unterricht / gut / zuhören", "Im Unterricht hört man gut zu.", "Man hört im Unterricht gut zu."),
    (28, "am Wochenende / Freunde / treffen", "Am Wochenende trifft man Freunde.", "Man trifft am Wochenende Freunde."),
    (29, "in der Bibliothek / ruhig / sein", "In der Bibliothek ist man ruhig.", "Man ist in der Bibliothek ruhig."),
    (30, "im Internet / viele Informationen / finden", "Im Internet findet man viele Informationen.", "Man findet im Internet viele Informationen."),
]
MAN = [short(f"{n}. ({cue})", [a, a.rstrip("."), b, b.rstrip(".")], explanation=a, max_length=150) for n, cue, a, b in _MAN]

TEXT_T1 = (
    "Zurzeit ist Extremsport sehr beliebt, und nicht nur unter Erwachsenen, denn auch Jugendliche, die noch keine 18 Jahre alt sind, haben die "
    "Möglichkeit, Extremsport zu machen. Man sollte aber in diesem Fall auf einige Dinge achten. Wenn man noch nicht erwachsen ist, ist es wichtig, dass "
    "die Eltern zustimmen, dass man von einem Arzt untersucht wird und dass man sich darüber informiert, wie viel man für jede Sportart bezahlen muss.\n\n"
    "Drei sehr beliebte Arten des Extremsports sind Fallschirmspringen, Tiefseetauchen und Bungee-Jumping. Möchtest du mal in 400 m Höhe aus dem Flugzeug "
    "springen und 60 Sekunden frei fliegen? Dann ist Fallschirmspringen genau das Richtige für dich. Mit 14 Jahren kannst du diese Erfahrung schon machen. "
    "Aber Vorsicht! Billig ist so ein Sprung nicht! Die Kosten für einen solchen Spaß liegen bei etwa 200 Euro.\n\nOder tauchst du lieber? In den "
    "Tauchschulen kannst du das lernen. Du übst zuerst 6–8 Wochen im Schwimmbad und danach kannst du in freien Gewässern in einer Tiefe von 15 m tauchen, "
    "natürlich zusammen mit einem Profi. Diese Erfahrung ist nicht billiger. Zwar kostet ein Spaziergang in der Tiefe etwa 150 Euro, Taucherbrille, "
    "Schwimmflossen und Schnorchel musst du allerdings extra bezahlen, diese Dinge kosten nochmal 150 Euro. Also dann, viel Spaß!")
LESEN_T1 = [
    mc("1 Damit Jugendliche eine Extremsportart ausüben, …", ["müssen sie in einem Sportverein sein.", "brauchen sie die Erlaubnis ihrer Eltern nicht.",
                                                              "brauchen sie eine Bestätigung von einem Arzt."], "C",
       "„… dass man von einem Arzt untersucht wird …“"),
    mc("2 Jugendliche …", ["mögen Bungee-Jumping am liebsten.", "mögen drei Extremsportarten ganz besonders.", "mögen Fallschirmspringen nicht."], "B",
       "„Drei sehr beliebte Arten des Extremsports sind …“"),
    mc("3 Beim Fallschirmspringen …", ["erlebt man eine Minute lang freies Fliegen.", "zahlt man weniger als 20 Euro für einen Sprung.",
                                       "verlässt man das Flugzeug auf viertausend Meter Höhe."], "A", "„… und 60 Sekunden frei fliegen?“"),
    mc("4 Tauchen lernt man zuerst …", ["im Schwimmbad.", "in 15 m Tiefe.", "in freien Gewässern."], "A", "„Du übst zuerst 6–8 Wochen im Schwimmbad …“"),
]
TEXT_T2 = (
    "Internationales Straßenfest „Sindelfingen“, 22. Juni\n\nBühne 1 – Marktplatz: 12:00 Uhr Spanische Folkloretänze · 12:30 Uhr Hip-Gruppe „JdP-Crew“ · "
    "13:00 Uhr Slowenische Volkstänze\nBühne 3 – Martinskirche: ganztägig Sindelfingens beste Bratwurstkantine · 12:40 Uhr Showtanz-Salsa · 13:15 Uhr "
    "BMX-Technik beim Radfahren\nBühne 4 – Schaffhauser Platz: ganztägig Italienische Küchenkultur zum Probieren · 14:30 Uhr Treffen der Bücherfreunde · "
    "15:00 Uhr Kochaktion für Jugendliche\nBühne 5 – Grabenstraße: 16:00 Uhr Spanische Spezialitäten kennenlernen · 16:30 Uhr Sprachschule „London“ · "
    "17:00 Uhr Griechischer Kulturverein Sindelfingen e.V.\nBühne 7 – Rathausvorplatz: 15:00 Uhr Kinderspielecke (ab 3 Jahren) · 16:00 Uhr Kinder-Karaoke "
    "(bis 15 Jahre) · 16:45 Uhr Kindertänze einstudieren und vorführen\nBühne 8 – Lange Straße: ganztägig Schokoladenecke · 17:30 Uhr Verband der "
    "Tierfreunde „Katz und Hund“ · 18:00 Uhr Europäischer Kulturverein\n\nBeispiel: 0 Du möchtest mit deiner Freundin aus Slowenien Hip-Hop-Musik hören. "
    "→ a) Bühne 1 – Marktplatz")
LESEN_T2 = [
    mc("1 Du kochst sehr gut.", ["Bühne 4 – Schaffhauser Platz", "Bühne 8 – Lange Straße", "anderer Ort"], "A", "Bühne 4: 15:00 Uhr Kochaktion für Jugendliche."),
    mc("2 Du möchtest Radtricks sehen.", ["Bühne 7 – Rathausvorplatz", "Bühne 4 – Schaffhauser Platz", "anderer Ort"], "C",
       "BMX-Technik beim Radfahren ist auf Bühne 3 → anderer Ort."),
    mc("3 Du interessierst dich für griechische Geschichte.", ["Bühne 8 – Lange Straße", "Bühne 5 – Grabenstraße", "anderer Ort"], "B",
       "Bühne 5: Griechischer Kulturverein."),
    mc("4 Du möchtest typisch Deutsch essen.", ["Bühne 4 – Schaffhauser Platz", "Bühne 3 – Martinskirche", "anderer Ort"], "B", "Bühne 3: Bratwurstkantine."),
    mc("5 Deine jüngere Schwester singt sehr gern.", ["Bühne 1 – Marktplatz", "Bühne 3 – Martinskirche", "anderer Ort"], "C",
       "Kinder-Karaoke ist auf Bühne 7 → anderer Ort."),
]
TEXT_T3 = (
    "Von: Steffi · An: Leo · Betreff: Alles war so schön – damals!\n\nHallo Leo,\nwir haben uns lange nicht mehr gesehen, aber ich weiß, wie es dir geht. "
    "Auf Facebook schreibst du ja immer alles! Wenn du gerade eine neue Freundin hast, sehe ich dein aktuelles Profilbild, wo ihr zusammen drauf seid. "
    "Manchmal sehe ich auch dein WhatsApp-Bild an und freue mich, wenn du darauf blöd aussiehst. Ich weiß, du denkst jetzt, wie böse ich bin. Das bin ich "
    "aber gar nicht.\n\nKannst du dich noch an die Zeit unserer Freundschaft erinnern? Das war so schön! Oft frage ich mich, ob du manchmal an unsere "
    "gemeinsame Zeit denkst, als wir uns so toll verstanden haben. Wir haben damals so viele Sachen gemeinsam unternommen. Wenn wir uns auf eine "
    "Klassenarbeit vorbereiten mussten, dann haben wir stundenlang zusammen gelernt. In unserer Freizeit sind wir Rad gefahren und waren gemeinsam auf "
    "Partys.\n\nDann hat sich alles plötzlich geändert! Du hast mir auf einmal erzählt, dass du in Maria verliebt bist. Das konnte ich nicht glauben. Ich "
    "wollte, dass wir Freunde bleiben. Du hast mir aber gesagt, du willst das nicht. Ich finde es schade, dass du mich seitdem nie wieder angerufen oder "
    "getroffen hast. Ich habe immer geglaubt, dass wir echte Freunde sind. Ich finde es wirklich schade, dass du nicht mehr mit mir über deine Probleme "
    "sprechen willst.\n\nRuf doch mal an! Wir sprechen einfach miteinander und es wäre schön, wenn wir wieder Freunde sein könnten.\nBis bald!\n"
    "Liebe Grüße\nSteffi")
LESEN_T3 = [
    mc("11 Was macht Leo auf Facebook?", ["Er ändert nie sein Profilbild.", "Er schreibt alles über sich.", "Er zeigt Fotos von seinen früheren Freundinnen."], "B",
       "„Auf Facebook schreibst du ja immer alles!“"),
    mc("12 Wann freut sich Steffi?", ["Wenn Leo auf Fotos nicht gut aussieht.", "Wenn sie ihn mit seiner Freundin auf einem Foto sieht.",
                                      "Wenn Leo sein WhatsApp-Bild nicht ändert."], "A", "„… und freue mich, wenn du darauf blöd aussiehst.“"),
    mc("13 Was möchte Steffi von Leo wissen?", ["Ob er mit ihr zusammen für die nächste Klassenarbeit lernen möchte.",
                                                "Ob er an die Zeit zurückdenkt, als sie gute Freunde waren.", "Ob er mit ihr Rad fahren möchte."], "B",
       "„Oft frage ich mich, ob du manchmal an unsere gemeinsame Zeit denkst …“"),
    mc("14 Was passiert in letzter Zeit?", ["Maria hat sich in Leo verliebt.", "Steffi hat Leo nie wieder angerufen.",
                                            "Leo wollte sich nicht mehr mit Steffi treffen."], "C",
       "„… dass du mich seitdem nie wieder angerufen oder getroffen hast.“"),
    mc("15 Steffi …", ["möchte Leo anrufen, wenn sie ein Problem hat.", "findet es nicht gut, dass Leo nicht mehr mit ihr spricht.",
                       "möchte Leo nicht mehr zum Freund haben."], "B", "„Ich finde es wirklich schade, dass du nicht mehr mit mir … sprechen willst.“"),
]
TEXT_T4 = (
    "Kurse aller Art für alle!\n\na „Lingua-Power“: Unsere Sprachschule im Stadtzentrum (Rheinstraße 8, Ecke Gerberstraße) besteht seit 2012 und "
    "beschäftigt internationale Sprachlehrer mit langjähriger Erfahrung. Neben Englisch, Französisch und Italienisch können Sie auch die Kultur jedes "
    "Landes kennenlernen.\n\nb Musikschule „Musika“: Bei „Musika“ am Hauptbahnhof können Kinder, Jugendliche und Erwachsene verschiedene "
    "Musikinstrumente lernen – in Gruppen oder in einem Einzelkurs. Schneller Erfolg zu sehr niedrigen Preisen. Sonderpreise für Familien! Wir beraten "
    "Sie gern beim Kauf Ihres Instruments.\n\nc Nachhilfe: Für alle Klassen und in allen Fächern bieten wir Hilfe an. Der Unterricht findet bei dir zu "
    "Hause statt, zu jeder passenden Zeit. Unsere Lehrer sind immer pünktlich, haben viel Erfahrung und garantieren gute Noten. Mit uns macht Schule keine "
    "Probleme mehr.\n\nd Fitnessstudio „Total fit“: Bei uns können Sie in kurzer Zeit fit werden. Wenn Sie ein paar Kilos verlieren möchten, geht das mit "
    "unseren neuen Methoden ganz schnell. Keine Hungerdiät! Wir verhelfen Ihnen zu einer neuen Figur, die sich lange hält. Tun Sie also etwas für Ihre "
    "Gesundheit!\n\ne Informatikkurs: Ohne Computer geht gar nichts, lernen Sie also den richtigen Umgang damit. Unser Angebot ist groß. Bei uns können Sie "
    "folgende Kurse besuchen: ECDL, Microsoft Office und ICT-Kurse. Kursbeginn jeden zweiten Montag, Kursdauer zwei bis vier Wochen.\n\nf Karate-Kurs: "
    "Das haben Sie wahrscheinlich noch nie erlebt: In unseren Kursen lernt man Karate mit Musik. So ist es einfacher und macht auch viel mehr Spaß. Ideal "
    "für Mädchen. Probieren Sie es aus! Sonderangebot bis Ende der Woche: Geschwister und Ehepaare zahlen die Hälfte!\n\nBeispiel: 0 Marlene möchte "
    "Englisch lernen, denn sie möchte später in England studieren. → a")
LESEN_T4 = [match(
    "Welche Anzeige passt zu welcher Person? (Für eine Aufgabe gibt es keine Lösung: X)",
    ["16 Simon möchte im Internet surfen lernen.", "17 Greta findet sich zu dick.", "18 Sarah möchte in ihrer Freizeit Latein-Tänze lernen.",
     "19 Erik ist nicht gut in der Schule.", "20 Paula möchte Klavier spielen lernen."],
    ["Anzeige b) Musikschule „Musika“", "Anzeige c) Nachhilfe", "Anzeige d) Fitnessstudio „Total fit“", "Anzeige e) Informatikkurs", "Anzeige f) Karate-Kurs",
     "X – keine passende Anzeige"],
    {"1": "D", "2": "C", "3": "F", "4": "B", "5": "A"}, points=5,
    explanation="16 → e (Umgang mit dem Computer), 17 → d (Kilos verlieren), 18 → X (Karate mit Musik ist kein Latein-Tanz), 19 → c (Nachhilfe), "
                "20 → b (Musikinstrumente). Anzeige f bleibt übrig.")]

HOEREN_T1 = [mc_pending(q, o) for q, o in [
    ("1 Warum muss Lisa aufs Land umziehen?", ["Weil ihr Vater ein neues Haus gekauft hat.", "Weil ihr Vater dort arbeiten wird.", "Weil man auf dem Land gesünder lebt."]),
    ("2 Welche Sehenswürdigkeit möchte Sascha in Berlin besuchen?", ["Er möchte das Brandenburger Tor besuchen.", "Er möchte viele Museen besuchen.",
                                                                     "Er möchte das Olympiastadion besuchen."]),
    ("3 Welche Hausarbeit findet Sabine am langweiligsten?", ["Ihr Zimmer aufräumen.", "Den Müll rausbringen.", "Das Geschirr spülen."]),
    ("4 Warum möchte Sebastian anfangen Sport zu treiben?", ["Weil er fit werden möchte.", "Weil er in einem Verein spielen möchte.", "Weil er stark sein möchte."]),
    ("5 Wie wird das Wetter am Wochenende?", ["Es wird regnen.", "Es wird kalt sein.", "Die Sonne wird scheinen."])]]
_BILDER = ["a) aufwachen / ausschlafen", "b) Party", "d) Hamburger", "e) weinender Junge", "f) Waffeln", "g) Fahrrad fahren", "h) Brettspiel", "i) Frühstück"]
HOEREN_T2 = [gap("Wie war Alisas Tag gestern? Wähle das passende Bild (Beispiel: 0 Alisas Eltern → c Kino).", f"{name}: [[1]]",
                 {"1": {"accepted": [], "options": _BILDER}}) for name in ("6 Alisa", "7 Fabian", "8 Viola", "9 Marie", "10 Jakob")]
HOEREN_T3 = [mc_pending(q, o) for q, o in [
    ("11 Welche Fremdsprache möchte Ilona noch lernen?", ["a) Spanisch", "b) Französisch", "c) Chinesisch"]),
    ("12 Was kocht Janine heute Abend?", ["a) Schnitzel", "b) Hähnchen", "c) Fisch"]),
    ("13 Warum möchte Emma in den Sommerferien jobben?", ["a) für einen Laptop", "b) für Kleidung", "c) für ein Fahrrad"]),
    ("14 Wohin möchten die Jugendlichen nach der Schule gehen?", ["a) ins Schwimmbad", "b) Eis essen", "c) ins Fußballstadion"]),
    ("15 Womit wollen die beiden Mädchen auf dem Flohmarkt viel Geld verdienen?", ["a) mit Spielzeug", "b) mit Jeans", "c) mit Büchern"])]]
HOEREN_T4 = [{"type": "true_false", "question": q, "options": ["Ja", "Nein"], "points": 1, "passage": 1} for q in [
    "16 Schüler zwischen 11 und 16 Jahren haben an diesem Wettbewerb teilgenommen.",
    "17 Den Geldpreis bekam nicht der Gewinner des Wettbewerbs, sondern er ging an Kinder in Not.", "18 Sonjas Plakat zeigt Kinder im Meer.",
    "19 Die Idee hat Sonja aus dem Internet.", "20 Sonja möchte später in Afrika studieren."]]

VARIANTEN = {
    "Variante 1": ["die Umwelt", "schützen", "die Natur", "die Erde", "der Müll"],
    "Variante 2": ["recyceln", "trennen", "der Müllberg", "der Müllcontainer", "der Abfall"],
    "Variante 3": ["das Klima", "das Wetter", "sich verändern", "die Klimakatastrophe", "die Erderwärmung"],
    "Variante 4": ["Energiesparen", "die Fahrt", "zu Fuß", "das Fahrrad", "die öffentlichen Verkehrsmittel"],
    "Variante 5": ["erneuerbar", "stoßen", "der Strom", "die Energie", "das Wasser"],
}
WORTSCHATZ_HTML = ("<h3>Wort zu Wort Wortschatzmethode — Umweltschutz A2</h3>" + "".join(f"<h4>{k}</h4>" + ul(v) for k, v in VARIANTEN.items())
                   + "<p>Formulieren Sie einen Text mit den Wörtern einer Variante (Aufgabe im Bereich Schreiben).</p>")


def _hoeren(n: int, title: str, page: int, instruction: str, questions: list[dict]) -> dict:
    return base(L, "hoeren", n, title, page=page, audio_file=AUDIO[f"vizu-a2-l11-hoeren-{n:02d}"], key_pending=True, instruction=instruction,
                questions=questions, metadata={"note": "Kitobda kalit va transkript yo'q — admin audioni tinglab javoblarni belgilaydi."})


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 11. Unterricht", source="vizu", page=125, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Was kann Einzelne für die Umwelt tun?", page=126,
             prompt="Was kann Einzelne für die Umwelt tun? Sprechen Sie über das Thema in 2–3 Sätzen.", min_duration=20, max_duration=90,
             metadata={"book_samples": [
                 "Ich kann Strom sparen, indem ich das Licht ausschalte, wenn ich es nicht brauche. Außerdem trenne ich Müll und benutze wiederverwendbare "
                 "Taschen beim Einkaufen. Jede kleine Handlung hilft unserer Umwelt.",
                 "Ich fahre mit dem Fahrrad oder gehe zu Fuß, statt das Auto zu benutzen. Das ist gut für die Umwelt und auch für meine Gesundheit. Ich "
                 "achte auch darauf, weniger Plastik zu verwenden. So kann ich die Natur schützen.",
                 "Ich kann Wasser sparen, indem ich kurz dusche und den Wasserhahn zudrehe. Ich kaufe regionale Produkte und unterstütze umweltfreundliche "
                 "Unternehmen. Gemeinsam können wir eine bessere Zukunft schaffen."]}),
        base(L, "grammatik", 1, "Grammatik: Passiv Präsens + man-Strukturen", page="127-128",
             rules=[{"title": "Passiv Präsens + man-Strukturen", "html": GRAMMAR_HTML}],
             exercises=[exercise("1. Bilden Sie Sätze im Passiv Präsens (2–15)", PASSIV, "Beispiel: Der Lehrer erklärt die Grammatik. → Die Grammatik wird erklärt."),
                        exercise("2. Bilden Sie vollständige Sätze mit „man“ (17–30)", MAN, "Beispiel: (in der Schule / viel / lernen) → In der Schule lernt man viel.")]),
        base(L, "lesen", 1, "Lesen Teil 1: Extremsport für Jugendliche", page="129-130", instruction="Du liest in einer Zeitung diesen Text. Wähle a, b oder c.",
             passages=[{"title": "Extremsport für Jugendliche", "text": TEXT_T1}], questions=LESEN_T1, max_score=len(LESEN_T1),
             metadata={"note": "5-savol olinmadi: matnda Bungee-Jumping narxi berilmagan, javobni aniqlab bo'lmaydi."}),
        base(L, "lesen", 2, "Lesen Teil 2: Finde den besten Ort! (Straßenfest)", page="131-133",
             instruction="Du liest 5 Situationen. Wähle für jede Aufgabe die richtige Lösung a, b oder c.",
             passages=[{"title": "Internationales Straßenfest „Sindelfingen“", "text": TEXT_T2}], questions=LESEN_T2, max_score=5),
        base(L, "lesen", 3, "Lesen Teil 3: E-Mail von Steffi", page="134-135", instruction="Du liest eine E-Mail. Wähle für die Aufgaben 11 bis 15 a, b oder c.",
             passages=[{"title": "E-Mail: Alles war so schön – damals!", "text": TEXT_T3}], questions=LESEN_T3, max_score=5),
        base(L, "lesen", 4, "Lesen Teil 4: Kurse aller Art für alle!", page=136,
             instruction="Sechs Jugendliche suchen im Internet nach Kursen. Welche Anzeige passt zu welcher Person? Für eine Aufgabe gibt es keine Lösung.",
             passages=[{"title": "Kurse aller Art für alle!", "text": TEXT_T4}], questions=LESEN_T4, max_score=5),
        _hoeren(1, "Hören Teil 1: Fünf kurze Texte", 137, "Du hörst fünf kurze Texte. Du hörst jeden Text zweimal. Wähle a, b oder c.", HOEREN_T1),
        _hoeren(2, "Hören Teil 2: Wie war Alisas Tag gestern?", 138, "Du hörst ein Gespräch einmal. Wähle für die Aufgaben 6 bis 10 ein passendes Bild "
                                                                     "(Bild im Abschnitt). Wähle jeden Buchstaben nur einmal.", HOEREN_T2),
        _hoeren(3, "Hören Teil 3: Fünf kurze Gespräche", 139, "Du hörst fünf kurze Gespräche einmal. Wähle a, b oder c (Bilder im Abschnitt).", HOEREN_T3),
        _hoeren(4, "Hören Teil 4: Interview mit Sonja", 140, "Du hörst ein Interview zweimal. Wähle „Ja“ oder „Nein“. (Beispiel: 0 Sonja hat ein schönes Plakat "
                                                             "gemalt. → Ja)", HOEREN_T4),
        base(L, "schreiben", 1, "Schreiben Teil 1: SMS an Sarah", page=141, task_type="message",
             prompt="Du möchtest mit deiner Freundin Sarah Kleidung kaufen gehen und schreibst ihr eine SMS.\n• Schreib, was du einkaufen möchtest.\n"
                    "• Sag, wie viel Geld du ausgeben kannst.\n• Nenne einen Treffpunkt.\n\nSchreib 20–30 Wörter. Schreib zu allen drei Punkten.\n\n"
                    "Tipps: Lies zuerst die Situation und die drei Leitpunkte. Überlege: An wen schreibst du? Aus welchem Anlass? Was willst du erreichen? "
                    "Kontrolliere am Ende, was du geschrieben hast.",
             audience="Freundin Sarah (informell)", min_words=20, max_words=40, time_limit=10),
        base(L, "schreiben", 3, "Schreiben Teil 2: E-Mail an Herrn Stark", page=142, task_type="email",
             prompt="Du kannst morgen nicht zur Schule gehen. Schreib deinem Klassenlehrer, Herrn Stark, eine E-Mail:\n• Entschuldige dich.\n"
                    "• Schreib, warum du fehlen wirst.\n• Frag nach den Hausaufgaben.\n\nSchreib 30–40 Wörter. Schreib zu allen drei Punkten.",
             audience="Klassenlehrer Herr Stark (formell)", min_words=30, max_words=50, time_limit=15,
             support_phrases=["Sehr geehrter Herr Stark,", "leider kann ich morgen nicht …, weil …", "Können Sie mir bitte sagen, …?", "Mit freundlichen Grüßen"]),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Wort zu Wort Wortschatzmethode (Umweltschutz)", page=146, task_type="description",
             prompt="Formulieren Sie mit den Wörtern einer Variante einen Text.\n\n" + "\n".join(f"{k}: {', '.join(v)}" for k, v in VARIANTEN.items()),
             min_words=40, max_words=200, time_limit=25),
        base(L, "sprechen", 1, "Sprechen Teil 1: Fragen zur Person", page=143, topic="Fragen zur Person", response_type="dialog",
             prompt="Du nimmst vier Karten und stellst mit diesen Karten vier Fragen. Dein Partner / deine Partnerin antwortet. (ca. 20 Sekunden Vorbereitung)",
             questions=["Kandidat 1: Wohnort?", "Kandidat 1: Frühstück?", "Kandidat 1: Adresse?", "Kandidat 1: Tee?", "Kandidat 2: Schule?", "Kandidat 2: Freizeit?",
                        "Kandidat 2: Butter, Essen?"],
             min_duration=30, max_duration=150, speech_goal="Zu jedem Stichwort eine korrekte Frage stellen und beantworten.",
             keywords=["Wo wohnst du", "Was isst du", "Trinkst du", "Was machst du"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Von sich erzählen", page=144, topic="Von sich erzählen",
             prompt="Du bekommst eine Karte und erzählst etwas über dein Leben. Karte A: Wie verbringst du gern deine Freizeit? Karte B: Würdest du gern ins "
                    "Ausland reisen?",
             questions=["Karte A: Hobby?", "Karte A: zu Hause?", "Karte A: Freunde?", "Karte A: Musik?", "Karte B: Land?", "Karte B: Warum?",
                        "Karte B: Verkehrsmittel?", "Karte B: Mit wem zusammen?"],
             response_type="monolog", min_duration=45, max_duration=150, speech_goal="Zu einer Aufgabenkarte zusammenhängend von sich erzählen.",
             keywords=["Freizeit", "gern", "reisen", "weil", "mit"]),
        base(L, "sprechen", 3, "Sprechen Teil 3: Wann können wir uns treffen?", page=145, topic="Einen Termin finden", response_type="dialog",
             prompt="Jeder Kandidat bekommt ein Blatt mit Vorgaben (Kalender für Freitag, 01.11.). Findet zusammen einen Termin, an dem ihr euch treffen könnt.\n\n"
                    "Aufgabenblatt A: 08.00–09.00 länger schlafen · 12.00 mit Mario skaten · 15.00 einkaufen gehen · 18.00 E-Mail an Luise schreiben\n"
                    "Aufgabenblatt B: 10.00 gemütlich frühstücken · 14.00 Bücher in der Bibliothek abgeben · 18.00–19.00 mit Mama das Abendessen kochen · "
                    "20.00 mit Freunden ins Kino",
             questions=["Wann hast du Zeit?", "Um … Uhr kann ich nicht, da …", "Geht es um … Uhr?", "Gut, dann treffen wir uns um …"],
             min_duration=45, max_duration=180, speech_goal="Mit dem Partner einen gemeinsamen freien Termin aushandeln (Vorschlag, Ablehnung mit Grund, Zustimmung).",
             keywords=["Hast du Zeit", "um … Uhr", "leider", "geht es", "treffen"]),
        base(L, "kompetenz", 3, "Wortschatz: Umweltschutz (Wortschatzmethode)", page=146, competency="WORTSCHATZ", html=WORTSCHATZ_HTML,
             metadata={"note": "Kitobda tarjima berilmagan — so'z ro'yxati to'qib chiqarilmadi."}),
        base(L, "yakuniy", 1, "Abschlusstest: A2 11. Unterricht", source="vizu",
             instruction="Passiv Präsens, man va dars matnlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Passiv: Der Lehrer erklärt die Grammatik. → Die Grammatik ___ erklärt.", ["wird", "werden", "ist"], "A"),
                 mc("Passiv: Die Firma liefert die Pakete. → Die Pakete ___ geliefert.", ["werden", "wird", "sind"], "A"),
                 mc("man: (im Supermarkt / Obst / kaufen) → Im Supermarkt ___ man Obst.", ["kauft", "kaufen", "gekauft"], "A"),
                 mc("Wann benutzt man das Passiv?", ["wenn die Handlung im Fokus steht", "wenn die Person wichtig ist", "nur in der Vergangenheit"], "A"),
                 mc("Wie lange fliegt man beim Fallschirmspringen frei?", ["60 Sekunden", "10 Sekunden", "10 Minuten"], "A", "Lesen Teil 1."),
                 mc("Wo übt man Tauchen zuerst?", ["im Schwimmbad", "im Meer", "in 15 m Tiefe"], "A", "Lesen Teil 1."),
                 tf("Steffi möchte wieder mit Leo befreundet sein.", True, "Lesen Teil 3."),
                 mc("Der Brief ___ geschrieben.", ["wird", "werden", "wirst"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 11. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
