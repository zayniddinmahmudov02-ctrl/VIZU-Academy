"""B1 6. Unterricht — Lernen und Weiterbildung — Grammatik: Reflexive Verben und
reflexive Pronomen (book pp. 96-110).

Book: title p.96, Frage des Themas (Wie sind die Möglichkeiten zum Studium in
Deutschland? — Einleitung / Hauptteil / Schluss) p.97, Grammatik: Reflexive
Verben und reflexive Pronomen p.98, 30 wichtigste sich-Verben (with Uzbek
translation) p.99, Grammatik Aufgaben: sich richtig einfügen (30 sentences)
p.100, Lesen Teil 1 "Meine Erlebnisse" (text p.101, Aufgaben 1-6 p.102),
Lesen Aufgabe 2 (E-Mail an Sara, Verben im Perfekt) p.103, Lesen Aufgabe 3
(Christiane Paul, Verben im Präteritum) p.104, Hören Aufgabe 1 (Interview:
Tätigkeiten im Beruf, richtig / falsch) p.105, Hören Aufgabe 2 (Nachrichten auf
der Mailbox, 10 Lücken) p.106, Schreiben Aufgabe 1 (Sätze verbinden mit damit /
deshalb / weil / um … zu) p.107, Schreiben Aufgabe 2 (E-Mail "Mein
Griechischkurs", Lösungswörter) p.108, Sprechen Aufgabe 1 (Interview: Lernen)
p.109, Wortschatz Lernen und Weiterbildung p.110.

Book defects: Lesen Teil 1 — the text is by "Marie-Charlotte Maas" (ich), the
statements name "Sven"; the statements are kept as printed. Lesen Aufgabe 2 —
the word bank prints "verbringen" twice for one gap. Lesen Aufgabe 3 — the
instruction says "auf dieser und der nächsten Seite", the book has one page; gap
10 is printed "Den Arztberuf ___ (10) sie promovieren, auf- allerdings für die
Schauspielerei ___ (11)" (stray words) -> shown as "Den Arztberuf (10) sie
allerdings für die Schauspielerei (11)." The sich-Verben page is headed "A2".
Hören: no key in the book -> keys from the audio are set in Lösung (held)."""

from . import (
    HOLD_AUDIO, base, choice_gap, exercise, example_gap, gap, intro_html, key_meta, meaning_sets, mc, numbered, summary_html, tf,
)

L = 6
LESSON_TITLE = "Lernen und Weiterbildung"
LESSON_DESCRIPTION = "Thema: Lernen und Weiterbildung · Grammatik: Reflexive Verben und reflexive Pronomen"
AUDIO = {"vizu-b1-l06-hoeren-01": "6.Unterricht Aufgabe 1.mp3", "vizu-b1-l06-hoeren-02": "6.Unterricht Aufgabe 2.mp3"}

EINFUEHRUNG_HTML = intro_html(
    6, "Lernen und Weiterbildung", "Reflexive Verben und reflexive Pronomen",
    ["refleksiv fe'llar — ega harakatni o'ziga qaratadi: Ich wasche mich.",
     "refleksiv olmoshlar Akkusativ (mich, dich, sich, uns, euch) va Dativ (mir, dir, sich, uns, euch) da;",
     "predlogli refleksiv fe'llar: sich freuen auf / über, sich interessieren für, sich erinnern an, sich vorbereiten auf;",
     "o'qish, kurslar va malaka oshirish haqida so'zlar."],
    ["Germaniyada o'qish imkoniyatlari haqida gapirasiz;",
     "sayohatdagi telefon voqeasi haqidagi matnni va qisqa tarjimai holni tushunasiz;",
     "kasb haqidagi suhbat va telefon xabarlarini tinglaysiz;",
     "gaplarni damit, deshalb, weil, um … zu bilan bog'laysiz va xat yozasiz;",
     "kurs ishtirokchilaridan o'qish haqida intervyu olasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(6, [
    "Reflexive Verben: Das Subjekt führt die Handlung an sich selbst aus — Ich wasche mich. Sie interessiert sich für Deutsch.",
    "Reflexivpronomen: ich mich/mir · du dich/dir · er/sie/es sich · wir uns · ihr euch · sie/Sie sich.",
    "Ohne Akkusativ-Objekt → Akkusativ (Ich wasche mich.) · mit Akkusativ-Objekt → Dativ (Ich wasche mir die Hände.).",
    "Mit Präposition: sich freuen auf / über, sich interessieren für, sich erinnern an, sich vorbereiten auf.",
    "Satzstrukturen: Präsens Subjekt + Verb + Pronomen · Perfekt Subjekt + haben + Pronomen + Partizip II · Modalverb + Pronomen + Infinitiv.",
    "<strong>Lernen und Weiterbildung:</strong> der Kurs, das Zertifikat, die Online-Schulung, sich weiterbilden, die Fortbildung, die Fähigkeit.",
])

GRAMMAR_HTML = (
    "<h3>Reflexive Verben und reflexive Pronomen</h3>"
    "<h4>1. Was sind reflexive Verben?</h4><p>Reflexive Verben sind Verben, bei denen das Subjekt die Handlung <strong>an sich selbst</strong> "
    "ausführt.</p><ul><li>Ich wasche <strong>mich</strong>.</li><li>Sie interessiert <strong>sich</strong> für Deutsch.</li></ul>"
    "<p><strong>Struktur:</strong> Subjekt + Verb + reflexives Pronomen + …</p>"
    "<h4>2. Reflexive Pronomen</h4>"
    "<table><thead><tr><th>Person</th><th>Akkusativ</th><th>Dativ</th></tr></thead><tbody>"
    "<tr><td>ich</td><td>mich</td><td>mir</td></tr><tr><td>du</td><td>dich</td><td>dir</td></tr><tr><td>er/sie/es</td><td>sich</td><td>sich</td></tr>"
    "<tr><td>wir</td><td>uns</td><td>uns</td></tr><tr><td>ihr</td><td>euch</td><td>euch</td></tr><tr><td>sie/Sie</td><td>sich</td><td>sich</td></tr>"
    "</tbody></table><p>Akkusativ-Objekt vorhanden → reflexives Pronomen im Dativ.</p>"
    "<h4>3. Wichtige reflexive Verben</h4><ul><li>sich waschen</li><li>sich duschen</li><li>sich anziehen</li><li>sich ausziehen</li>"
    "<li>sich treffen</li><li>sich beeilen</li><li>sich entschuldigen</li></ul>"
    "<p><strong>Beispiele:</strong> Ich dusche <strong>mich</strong> jeden Morgen. · Wir treffen <strong>uns</strong> am Wochenende. · "
    "Beeil <strong>dich</strong> bitte!</p>"
    "<h4>4. Verben mit Präpositionen</h4><ul><li><strong>sich freuen auf</strong> — Ich freue mich auf das Wochenende.</li>"
    "<li><strong>sich freuen über</strong> — Ich freue mich über das Geschenk.</li>"
    "<li><strong>sich interessieren für</strong> — Ich interessiere mich für deutsche Kultur.</li>"
    "<li><strong>sich erinnern an</strong> — Ich erinnere mich an meine Schulzeit.</li>"
    "<li><strong>sich vorbereiten auf</strong> — Ich bereite mich auf die Prüfung vor.</li></ul>"
    "<h4>5. Satzstrukturen</h4><ul><li><strong>Präsens:</strong> Subjekt + Reflexivverb + Reflexivpronomen + Ergänzung</li>"
    "<li><strong>Perfekt:</strong> Subjekt + haben + Reflexivpronomen + Partizip II</li>"
    "<li><strong>Modalverben:</strong> Subjekt + Modalverb + Reflexivpronomen + Infinitiv</li></ul>"
)

SICH_VERBEN = [
    ("sich waschen", "o'zini yuvmoq"), ("sich duschen", "dush qabul qilmoq"), ("sich kämmen", "sochini taramoq"), ("sich anziehen", "kiyinmoq"),
    ("sich ausziehen", "yechinmoq"), ("sich die Zähne putzen", "tishini tozalamoq"), ("sich das Gesicht waschen", "yuzini yuvmoq"),
    ("sich hinlegen", "yotmoq"), ("sich hinsetzen", "o'tirmoq"), ("sich verabschieden", "xayrlashmoq"), ("sich begrüßen", "salomlashmoq"),
    ("sich treffen", "uchrashmoq"), ("sich umarmen", "quchoqlashmoq"), ("sich bedanken", "rahmat aytmoq"), ("sich freuen", "quvonmoq"),
    ("sich ärgern", "g'azablanmoq"), ("sich schämen", "uyalmoq"), ("sich wundern", "hayron bo'lmoq"), ("sich entspannen", "dam olmoq, bo'shashmoq"),
    ("sich beeilen", "shoshilmoq"), ("sich verlieben", "sevib qolmoq"), ("sich erinnern", "eslamoq"), ("sich vorstellen", "o'zini tanishtirmoq"),
    ("sich melden", "xabar bermoq"), ("sich helfen", "yordam bermoq"), ("sich konzentrieren", "diqqatini jamlamoq"), ("sich sorgen", "tashvishlanmoq"),
    ("sich verletzen", "o'zini jarohatlamoq"), ("sich fühlen (krank)", "o'zini (kasal) his qilmoq"),
]
# the book lists "sich verabschieden" twice (Nr. 10 and 25) — kept once

_REFL = ["mich", "mir", "dich", "dir", "sich", "uns", "euch"]
SICH_EINFUEGEN = [
    ("Ich wasche ___ jeden Morgen.", "mich"), ("Du solltest ___ mehr Zeit nehmen.", "dir"), ("Er rasiert ___ jeden Tag.", "sich"),
    ("Sie schminkt ___ vor dem Spiegel.", "sich"), ("Wir freuen ___ auf den Urlaub.", "uns"), ("Ihr trefft ___ heute um 18 Uhr.", "euch"),
    ("Ich muss ___ beeilen.", "mich"), ("Du erinnerst ___ an alles.", "dich"), ("Er zieht ___ schnell an.", "sich"),
    ("Sie kümmert ___ um ihre Kinder.", "sich"), ("Wir interessieren ___ für Musik.", "uns"), ("Ihr beschwert ___ immer.", "euch"),
    ("Ich lege ___ kurz hin.", "mich"), ("Du setzt ___ neben mich.", "dich"), ("Er gewöhnt ___ an die neue Arbeit.", "sich"),
    ("Sie bedankt ___ herzlich.", "sich"), ("Wir waschen ___ die Hände.", "uns"), ("Ihr erinnert ___ oft an die Termine.", "euch"),
    ("Er konzentriert ___ auf die Prüfung.", "sich"), ("Sie freut ___ über das Geschenk.", "sich"), ("Ich melde ___ krank.", "mich"),
    ("Du verletzt ___ nicht.", "dich"), ("Wir verabschieden ___ von unseren Freunden.", "uns"), ("Ihr kümmert ___ gut darum.", "euch"),
    ("Er entscheidet ___ für diesen Kurs.", "sich"), ("Sie stellt ___ eine Frage.", "sich"), ("Ich bereite ___ auf den Test vor.", "mich"),
    ("Du hilfst ___ immer.", "dir"), ("Wir sehen ___ morgen.", "uns"), ("Sie ärgert ___ über die Situation.", "sich"),
]
_WHY = {"dir": "Mit Akkusativ-Objekt → Dativ.", "uns": None, "mich": None}
GRAMMATIK_SETS = [
    exercise("Aufgabe: sich richtig einfügen (1–15)", [
        choice_gap(f"{n}. {s}", _REFL, a, question="Setzen Sie das passende reflexive Personalpronomen ein.",
                   explanation="Mit Akkusativ-Objekt → Dativ (z. B. „Du solltest dir mehr Zeit nehmen.“)." if a in ("dir", "mir") else None)
        for n, (s, a) in enumerate(SICH_EINFUEGEN[:15], start=1)],
        "Setzen Sie das passende reflexive Personalpronomen ein. Achten Sie auf Dativ (mir, dir, sich, uns, euch) und Akkusativ "
        "(mich, dich, sich, uns, euch). (Buch S. 100)"),
    exercise("Aufgabe: sich richtig einfügen (16–30)", [
        choice_gap(f"{n}. {s}", _REFL, a, question="Setzen Sie das passende reflexive Personalpronomen ein.",
                   explanation="Mit Akkusativ-Objekt → Dativ (z. B. „Du hilfst dir immer.“ — helfen + Dativ)." if a in ("dir", "mir") else None)
        for n, (s, a) in enumerate(SICH_EINFUEGEN[15:], start=16)],
        "Setzen Sie das passende reflexive Personalpronomen ein. Tipp: Ohne Objekt → Akkusativ (Ich wasche mich.), mit Akkusativ-Objekt → "
        "Dativ (Ich wasche mir die Hände.). (Buch S. 100)"),
]

# ---------- Lesen ----------
ERLEBNISSE = (
    "25. August\n\n"
    "Mein Handy-Unfall ereignete sich im Sommerurlaub in Griechenland. Ich hatte das Handy in der Tasche meiner Badehose und bin damit ins Meer "
    "gelaufen. Dort habe ich natürlich relativ schnell festgestellt, dass mein Handy noch in der Tasche ist. Leider stand ich schon hüfttief im "
    "Wasser.\n\n"
    "Ich bin sofort zurück an den Strand gelaufen und habe das Handy aus meiner Tasche geholt. Meine erste Reaktion war, das Handy mit dem Handtuch "
    "trocken zu wischen. Danach habe ich es auseinandergebaut und die einzelnen Teile ebenfalls mit dem Handtuch getrocknet.\n\n"
    "Doch bereits da wurde mir klar, dass mein Handy nur eine geringe Überlebenschance hatte. Ich habe es dann für den Rest des Strandtages in die "
    "Sonne gelegt. Im Hotel angekommen habe ich das Handy trocken geföhnt, doch auch das sollte nicht helfen. Es ging zwar an, aber der Bildschirm hat "
    "nur wirre Pixel angezeigt. Ich hatte keinen Zugriff aufs Menü und konnte weder telefonieren noch SMS schreiben. Auf einer Online-Plattform "
    "erfuhr ich, das Beste sei es, das Handy ein paar Tage ausgeschaltet zu lassen. Ein nicht ganz leicht zu befolgender Hinweis, wenn man im Urlaub "
    "ist. Schließlich wollte ich Kontakt zu meiner Familie und meinen Freunden aufnehmen.\n\n"
    "Es war der erste Urlaubstag, somit war es doppelt ärgerlich. Aber einen guten Aspekt hatte es dann doch. Ich habe Geld gespart, da teure "
    "Auslandsgespräche und SMS aus dem Ausland nicht mehr möglich waren.\n\n"
    "Zu Hause kam dann die große Erleichterung: Die SIM-Karte war glücklicherweise noch zu gebrauchen und so hatte ich weder Nummern noch Nachrichten "
    "verloren. Hätte ich ein neueres Modell gehabt, wären die wohl weg gewesen, denn da speichert sich fast alles auf dem Mobilfunkgerät selber und "
    "nicht auf der SIM-Karte. Finanziell hielt sich der Schaden in Grenzen, da es kein ganz neues Handymodell war. Leider konnte ich keine "
    "Garantieansprüche geltend machen. Ein Wasserschaden läuft nämlich nie auf Garantie. Aber ich habe das Handy meiner Oma bekommen, das war das "
    "gleiche Modell.\n\n"
    "Noch einmal wird mir so etwas nicht passieren. Ich ziehe nur noch Badehosen ohne Taschen an, damit ich gar nicht erst auf die Idee komme, mein "
    "Handy in die Hosentasche zu stecken.\n\n"
    "Marie-Charlotte Maas")
LESEN_1 = [
    tf("Svens Handy ging kaputt, als er es mit dem Handtuch zu trocknen versuchte.", False,
       "Das Handy war schon im Meer nass geworden: „… und bin damit ins Meer gelaufen … Leider stand ich schon hüfttief im Wasser.“"),
    tf("Den Rest des Tages verbrachte Sven am Strand in der Sonne.", False,
       "Nicht die Person, sondern das Handy lag in der Sonne: „Ich habe es dann für den Rest des Strandtages in die Sonne gelegt.“"),
    tf("Sven informierte sich im Internet darüber, was er tun sollte.", True,
       "„Auf einer Online-Plattform erfuhr ich, das Beste sei es, das Handy ein paar Tage ausgeschaltet zu lassen.“"),
    tf("Sven ärgerte sich zwar sehr, doch er konnte Geld sparen.", True,
       "„… somit war es doppelt ärgerlich. Aber einen guten Aspekt hatte es dann doch. Ich habe Geld gespart …“"),
    tf("Weil die SIM-Karte in Ordnung war, blieben sowohl Nummern als auch Nachrichten gespeichert.", True,
       "„Die SIM-Karte war glücklicherweise noch zu gebrauchen und so hatte ich weder Nummern noch Nachrichten verloren.“"),
    tf("Sven hat sich das gleiche Modell wie seine Oma angeschafft.", False,
       "Er hat das Handy der Oma bekommen, nicht gekauft: „Aber ich habe das Handy meiner Oma bekommen, das war das gleiche Modell.“"),
]
SARA = (
    "Liebe Sara,\n"
    "ich muss dir unbedingt berichten, was in den letzten Wochen [[1]] ist. Du weißt ja, dass ich meine Abschlussprüfung [[2]] habe. Und dann haben "
    "Dani und ich eine große Reise [[3]].\n"
    "Zuerst sind wir mit dem Zug nach Kroatien [[4]] und dort sind wir zwei Wochen lang vor der Küste mit einem Schiff [[5]]. Das war wirklich "
    "traumhaft! Dann haben wir zwei Wochen auf einer griechischen Insel [[6]]. Wir haben uns so richtig [[7]] und viele Bücher [[8]].\n"
    "Danach hatten wir wieder genug Energie für Istanbul! Eine Woche nur Kultur und gutes Essen! Ich glaube, wir haben alle Sehenswürdigkeiten [[9]], "
    "die es in Istanbul gibt. Als wir dann nach Hause [[10]] sind, waren wir müde, aber glücklich.\n"
    "Ein richtiger Traumurlaub! Und wie war dein Sommer? Melde dich bald und erzähl mir alles!\nLiebe Grüße\nAnna")
SARA_KEY = {"1": ["passiert"], "2": ["bestanden"], "3": ["gemacht"], "4": ["gefahren"], "5": ["gesegelt"], "6": ["verbracht"], "7": ["erholt"],
            "8": ["gelesen"], "9": ["besichtigt"], "10": ["geflogen"]}
PAUL = (
    "Christiane Paul [[1]] 1974 in Ost-Berlin zur Welt. Ihre Eltern [[2]] beide Ärzte. Mit 16 Jahren [[3]] sie an einem Modelwettbewerb [[4]] und "
    "[[5]] in der Folgezeit als Model für Teenie-Zeitschriften. 1991 [[6]] ihre Schauspielkarriere mit dem Film „Deutschfieber“. Seitdem [[7]] sie in "
    "zahlreichen Filmen. Außerdem [[8]] Christiane Medizin und [[9]] 2002. Den Arztberuf [[10]] sie allerdings für die Schauspielerei [[11]]. "
    "Christiane Paul engagiert sich für viele soziale Projekte und lebt mit ihren Kindern in Berlin.")
PAUL_KEY = {"1": ["kam"], "2": ["waren"], "3": ["nahm"], "4": ["teil"], "5": ["jobbte"], "6": ["begann"], "7": ["spielte"], "8": ["studierte"],
            "9": ["promovierte"], "10": ["gab"], "11": ["auf"]}

# ---------- Hören (keys only from the audio) ----------
HOEREN_1 = [tf(s, None) for s in [
    "Ute macht die neue Arbeit Spaß.", "Bei ihrer alten Stelle hat sie mehr verdient.", "Ute hat schon oft Produkte auf Englisch präsentiert.",
    "Conrad findet, dass Geschäftsreisen nichts mit Urlaub zu tun haben.", "Ute muss für ihren Englischkurs nicht bezahlen.",
    "Conrad muss in Besprechungen mehrere Sprachen sprechen."]]
MAILBOX = [
    ("Nachricht 1", "Hallo Herr Neumann, hier ist Petra Bleibtreu von der Firma BNO. Wir haben Ihre [[1]] bekommen, aber es fehlt eine offizielle "
                    "[[2]] Ihrer Englischkenntnisse. Könnten Sie uns das Dokument so schnell wie möglich [[3]] zuschicken? Vielen Dank. Auf Wiederhören."),
    ("Nachricht 2", "Salü Jens, hier ist Barbara. Du, [[1]] geht wieder nicht. Könntest du mal vorbeikommen und den reparieren? Ich warte auf dich in "
                    "[[2]]. Vielen Dank! Adieu!"),
    ("Nachricht 3", "Guten Tag, Frau Heinrich, hier ist Nina Esser von der Firma Braun & Co. Ich habe gerade festgestellt, dass Ihre Firma [[1]] von "
                    "uns noch nicht bezahlt hat. Die [[2]] lautet 3545, das [[3]] ist der 14. März. Könnten Sie das bitte kontrollieren und mich "
                    "zurückrufen? Vielen Dank. Auf Wiederhören."),
    ("Nachricht 4", "Servus Thomas, hier Niko. Ich habe mehrmals versucht, dich [[1]], aber es hat nicht geklappt. Wo bist du denn? Könntest du mich "
                    "zurückrufen, wenn du wieder da bist? Ich muss [[2]]. Danke."),
]
HOEREN_2 = [gap(f"{title}: Ergänzen Sie die Informationen.", text, {str(i): [] for i in range(1, text.count("[[") + 1)}, points=text.count("[["))
            for title, text in MAILBOX]

# ---------- Schreiben ----------
VERBINDEN = [
    "Ich besuche einen Sprachkurs. Ich kann die Sprache zusammen mit anderen Menschen üben.",
    "Ich lerne Deutsch. Ich kann mich an einer deutschen Universität bewerben.",
    "Ich will die Krimis von Agatha Christie in der Originalsprache lesen. Ich lerne Englisch.",
    "Ich wiederhole die Wörter regelmäßig. Ich vergesse sie nicht.",
    "Ich habe mich zu einem Italienischkurs angemeldet. Ich möchte mit meinen italienischen Kollegen kurze Gespräche führen.",
    "Ich nehme Privatstunden. Ich kann mehr in der Fremdsprache kommunizieren.",
    "Margit besucht einen Englischkurs in London. Sie kann auch außerhalb des Kurses Englisch sprechen.",
    "Ich habe einen Online-Kurs gebucht. Ich kann meine Lernzeit selbst einteilen.",
    "Ich habe von dem guten Preis-Leistungs-Verhältnis gehört. Ich lerne an der Volkshochschule kochen.",
]
GRIECHISCH = (
    "Ich lerne jetzt Griechisch\n\nLiebe Laura,\nich habe mich bei dir lange nicht gemeldet. Ich [[1]] in den letzten Wochen sehr wenig Zeit. Im "
    "Auftrag meines Chefs lerne ich nun Griechisch, [[2]] wir neue Geschäftspartner aus Griechenland haben.\n"
    "Ich habe mich für einen Kurs an der Volkshochschule [[3]]. [[4]] ich bezahle hier für 50 Unterrichtsstunden nur 250 Euro. Die Hälfte der "
    "Kursgebühr [[5]] ich selbst zahlen, die andere Hälfte zahlt mein [[6]].\n"
    "Der Kurs findet zweimal in der Woche statt, von 19.00 bis 21.00 Uhr. Danach bin ich immer sehr müde. Wir mussten in den ersten Stunden erst mal "
    "das griechische [[7]] lernen, [[8]] fand ich den Anfang sehr schwer. Jetzt geht es besser, ich [[9]] schon einige Sätze sprechen.\n"
    "Ich hoffe, dass es [[10]] gut geht. Hast du auch eine neue Fremdsprache gelernt? Wenn du mal Griechisch lernen willst, kann ich dir vielleicht "
    "helfen.\nLiebe Grüße und bis bald\nAnita")
GRIECHISCH_KEY = {
    "1": ("hatte", ["hatte", "habe"], "Präteritum: „Ich hatte … sehr wenig Zeit.“ (Ich habe … Zeit = Präsens passt nicht zu „in den letzten Wochen“.)"),
    "2": ("weil", ["weil", "denn"], "Verb am Ende („… haben“) → weil."),
    "3": ("entschieden", ["gewählt", "entschieden"], "sich für etwas entscheiden."),
    "4": ("Denn", ["Denn", "Deshalb"], "Grund: Der Kurs ist billig → denn (Verb an Position 2 nach „denn“ + Subjekt: „Denn ich bezahle …“)."),
    "5": ("muss", ["muss", "darf"], "Pflicht: Die Hälfte muss ich selbst zahlen."),
    "6": ("Arbeitgeber", ["Arbeitgeber", "Arbeitnehmer"], "Der Chef / die Firma = Arbeitgeber."),
    "7": ("Alphabet", ["Alphabet", "Schrift"], "„das griechische Alphabet“ (die Schrift = feminin)."),
    "8": ("deshalb", ["deshalb", "denn"], "Folge + Verb an Position 2 („deshalb fand ich …“)."),
    "9": ("kann", ["kann", "will"], "Fähigkeit: Ich kann schon einige Sätze sprechen."),
    "10": ("dir", ["dich", "dir"], "es geht + Dativ: Wie geht es dir?"),
}

INTERVIEW = ["Sind Sie gern zur Schule gegangen? Welche Fächer mochten Sie besonders?", "Was war früher Ihr Traumberuf?",
             "Lernen Sie gern? Was lernen Sie gerade und was möchten Sie später noch lernen?",
             "Welche Sprachen haben Sie in der Schule / an der Universität gelernt? Hat Ihnen der Sprachunterricht Spaß gemacht?",
             "Bis zu welchem Alter kann ein Mensch etwas lernen? Was meinen Sie?"]

LERNEN = [
    ("lernen", "Wissen oder Fähigkeiten durch Übung oder Unterricht erwerben"), ("studieren", "an einer Hochschule lernen, ein Fach wissenschaftlich bearbeiten"),
    ("der Kurs", "Unterrichtseinheit zu einem bestimmten Thema"), ("das Zertifikat", "offizieller Nachweis über den erfolgreichen Abschluss eines Kurses"),
    ("die Online-Schulung", "Lernen über das Internet, meist flexibel und ortsunabhängig"),
    ("sich weiterbilden", "neue Kenntnisse erwerben, um beruflich besser zu werden"), ("die Fähigkeit", "etwas gut können; eine Kompetenz"),
    ("das Ziel", "etwas, das man erreichen möchte"), ("die Fortbildung", "zusätzliche Weiterbildung nach einer Ausbildung oder im Beruf"),
    ("üben", "etwas regelmäßig machen, um besser darin zu werden"),
]


def _word(w: str, meaning: str) -> dict:
    parts = w.split(" ", 1)
    if len(parts) == 2 and parts[0] in ("der", "die", "das"):
        return {"word": parts[1], "article": parts[0], "translation": meaning, "group": "Lernen und Weiterbildung"}
    return {"word": w, "translation": meaning, "group": "Lernen und Weiterbildung"}


WORDS = [_word(w, m) for w, m in LERNEN]
SICH_WORDS = [{"word": w, "translation": uz, "group": "30 wichtigste sich-Verben"} for w, uz in SICH_VERBEN]

UEBUNGEN = [
    exercise("Reflexive Verben — Regeln und Beispiele aus dem Buch", [
        example_gap("Ich dusche ___ jeden Morgen.", "mich", ["mich", "mir", "sich"], "Ohne Objekt → Akkusativ."),
        example_gap("Ich wasche ___ die Hände.", "mir", ["mir", "mich", "sich"], "Mit Akkusativ-Objekt (die Hände) → Dativ."),
        example_gap("Wir treffen ___ am Wochenende.", "uns", ["uns", "euch", "sich"]),
        example_gap("Beeil ___ bitte!", "dich", ["dich", "dir", "sich"]),
        example_gap("Ich freue mich ___ das Wochenende.", "auf", ["auf", "über", "für"], "sich freuen auf = etwas kommt noch."),
        example_gap("Ich freue mich ___ das Geschenk.", "über", ["über", "auf", "an"], "sich freuen über = etwas ist schon da."),
        example_gap("Ich interessiere mich ___ deutsche Kultur.", "für", ["für", "an", "auf"]),
        example_gap("Ich erinnere mich ___ meine Schulzeit.", "an", ["an", "für", "über"]),
        example_gap("Ich bereite mich ___ die Prüfung vor.", "auf", ["auf", "an", "für"]),
    ], "Wählen Sie die richtige Form (Buch S. 98).", source="vizu"),
]
ABSCHLUSSTEST = [
    mc("Was sind reflexive Verben?", ["Verben, bei denen das Subjekt die Handlung an sich selbst ausführt", "Verben ohne Subjekt",
                                      "Verben, die nur im Perfekt stehen"], "A", "Buch S. 98."),
    mc("Welche Form steht mit Akkusativ-Objekt?", ["Dativ (mir, dir …)", "Akkusativ (mich, dich …)", "Nominativ"], "A",
       "Buch S. 98/100: Mit Akkusativ-Objekt → reflexives Pronomen im Dativ."),
    example_gap("Du solltest ___ mehr Zeit nehmen.", "dir", ["dir", "dich", "sich"]),
    example_gap("Ihr trefft ___ heute um 18 Uhr.", "euch", ["euch", "uns", "sich"]),
    example_gap("Er konzentriert sich ___ die Prüfung.", "auf", ["auf", "an", "für"]),
    example_gap("Christiane Paul ___ 1974 in Ost-Berlin zur Welt.", "kam", ["kam", "kommt", "ist gekommen"], "Lesen Aufgabe 3: Präteritum."),
    mc("„sich weiterbilden“ bedeutet …", ["neue Kenntnisse erwerben, um beruflich besser zu werden", "an einer Hochschule lernen",
                                          "etwas regelmäßig machen"], "A", "Wortschatz S. 110."),
    mc("„das Zertifikat“ ist …", ["ein offizieller Nachweis über den erfolgreichen Abschluss eines Kurses", "eine Unterrichtseinheit",
                                  "etwas, das man erreichen möchte"], "A", "Wortschatz S. 110."),
    mc("„sich beeilen“ — o'zbekchasi?", ["shoshilmoq", "uyalmoq", "eslamoq"], "A", "Buch S. 99."),
    mc("Warum hatte die Autorin von „Meine Erlebnisse“ am Ende kein neues Handy gekauft?", ["Sie hat das Handy ihrer Oma bekommen",
       "Die Garantie hat alles bezahlt", "Das Handy ging wieder"], "A", "Lesen Teil 1: „… ich habe das Handy meiner Oma bekommen …“"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 6. Unterricht", source="vizu", page=96, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie sind die Möglichkeiten zum Studium in Deutschland?", page=97,
             prompt="Wie sind die Möglichkeiten zum Studium in Deutschland? Sprechen Sie mit Einleitung, Hauptteil und Schluss.",
             questions=["Einleitung", "Hauptteil", "Schluss"], min_duration=30, max_duration=150,
             metadata={"book_sample": {
                 "Einleitung": "Deutschland ist ein beliebtes Land für Studierende aus der ganzen Welt. Viele junge Menschen möchten hier studieren, weil "
                               "die Bildung sehr gut ist und es viele Möglichkeiten gibt. In meinem Beitrag spreche ich darüber, wie die Möglichkeiten "
                               "zum Studium in Deutschland sind.",
                 "Hauptteil": "Es gibt viele Universitäten, Fachhochschulen und private Hochschulen. Die meisten öffentlichen Universitäten sind kostenlos "
                              "oder haben nur einen geringen Semesterbeitrag. Studierende können aus vielen Fachrichtungen wählen, zum Beispiel "
                              "Ingenieurwissenschaften, Wirtschaft, Medizin oder Sprachen. Außerdem gibt es verschiedene Studiengänge auf Deutsch und "
                              "Englisch. Es gibt auch Stipendien und Austauschprogramme für internationale Studierende.",
                 "Schluss": "Zusammenfassend kann man sagen, dass Deutschland sehr gute Möglichkeiten zum Studium bietet. Wichtig sind gute "
                            "Sprachkenntnisse und eine gute Vorbereitung. Ich finde, dass ein Studium in Deutschland eine gute Investition in die "
                            "Zukunft ist."}}),
        base(L, "grammatik", 1, "Grammatik: Reflexive Verben und reflexive Pronomen", page="98-100",
             rules=[{"title": "Reflexive Verben und reflexive Pronomen", "html": GRAMMAR_HTML}], exercises=GRAMMATIK_SETS,
             metadata={"note": "Lösungen von VIZU nach der Regel (Tabelle S. 98 / Tipp S. 100)."}),
        base(L, "wortschatz", 1, "Wortschatz: 30 wichtigste sich-Verben", page=99, words=SICH_WORDS, auto_practice=True,
             metadata={"note": "Buch S. 99 (Überschrift „A2 – Die häufigsten Verben mit „sich““); „sich verabschieden“ steht zweimal (Nr. 10 und 25)."}),
        base(L, "lesen", 1, "Lesen Teil 1: Meine Erlebnisse", page="101-102",
             instruction="Lesen Sie den Text und die Aufgaben 1 bis 6 dazu. Wählen Sie: Sind die Aussagen richtig oder falsch? (Arbeitszeit: 10 Minuten)",
             passages=[{"title": "Meine Erlebnisse", "text": ERLEBNISSE}], questions=LESEN_1, max_score=len(LESEN_1),
             metadata=key_meta("vizu", "Lösung von VIZU aus dem Text (Zitat in der Erklärung). Im Buch heißt die Person in den Aufgaben „Sven“, "
                                       "der Text ist von „Marie-Charlotte Maas“ (ich) — Aufgaben wie gedruckt. Bitte prüfen.")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: E-Mail an Sara — Verben im Perfekt", page=103,
             instruction="Setzen Sie die passenden Verben in die richtige Form ein. Verben: verbringen • fahren • erholen • passieren • lesen • fliegen • "
                         "verbringen • bestehen • machen • besichtigen • segeln",
             passages=[{"title": "E-Mail von Anna", "text": SARA.replace("[[", "(").replace("]]", ") ……")}],
             questions=[gap("Setzen Sie die passenden Verben in die richtige Form ein.", SARA, SARA_KEY, points=10,
                            explanation="1 passiert · 2 bestanden · 3 gemacht · 4 gefahren · 5 gesegelt · 6 verbracht · 7 erholt · 8 gelesen · "
                                        "9 besichtigt · 10 geflogen")],
             max_score=10, metadata=key_meta("vizu", "Partizip II nach Wörterliste und Kontext (jedes Verb einmal; „verbringen“ steht im Buch zweimal, "
                                                     "„fahren“ ist schon bei Lücke 4) — bitte prüfen.")),
        base(L, "lesen", 3, "Lesen Aufgabe 3: Traumberuf Schauspieler/in — Christiane Paul", page=104,
             instruction="Traumberuf Schauspieler/in. Ergänzen Sie in der Kurzbiografie die Verben im Präteritum. Verben: kommen • sein • teilnehmen • "
                         "jobben • beginnen • spielen • studieren • promovieren • aufgeben • geben • engagieren • leben",
             passages=[{"title": "Christiane Paul", "text": PAUL.replace("[[", "(").replace("]]", ") ……")}],
             questions=[gap("Ergänzen Sie die Verben im Präteritum.", PAUL, PAUL_KEY, points=11,
                            explanation="1 kam · 2 waren · 3 nahm · 4 teil · 5 jobbte · 6 begann · 7 spielte · 8 studierte · 9 promovierte · 10 gab · 11 auf")],
             max_score=11,
             metadata=key_meta("vizu", "Präteritum nach Wörterliste; trennbare Verben stehen in zwei Lücken (nahm … teil, gab … auf). Im Buch steht bei "
                                       "Lücke 10 zusätzlich „sie promovieren, auf-“ (Druckfehler) — bereinigt. Bitte prüfen.")),
        base(L, "hoeren", 1, "Hören Aufgabe 1: Interview — Tätigkeiten im Beruf", page=105, audio_file=AUDIO["vizu-b1-l06-hoeren-01"], key_pending=True,
             instruction="Hören Sie ein Gespräch auf der Straße. Sind die Aussagen richtig oder falsch? Kreuzen Sie an.",
             questions=HOEREN_1, max_score=6, metadata=key_meta("pending", "Keine Lösung im Buch — nach dem Anhören in Lösung festlegen.")),
        base(L, "hoeren", 2, "Hören Aufgabe 2: Nachrichten auf der Mailbox", page=106, audio_file=AUDIO["vizu-b1-l06-hoeren-02"], key_pending=True,
             instruction="Hören Sie die Nachrichten und ergänzen Sie die Informationen.", questions=HOEREN_2, max_score=10,
             metadata=key_meta("pending", "4 Nachrichten, 10 Lücken, keine Lösung im Buch — nach dem Anhören in Lösung festlegen.")),
        base(L, "schreiben", 1, "Schreiben Aufgabe 1: So lerne ich eine Fremdsprache — Sätze verbinden", page=107, task_type="other",
             prompt="Verbinden Sie die Sätze mit damit, deshalb, weil und um … zu. Achten Sie auf die richtige Bedeutung.\n\n" + numbered(VERBINDEN),
             min_words=60, max_words=250, time_limit=20,
             metadata={"note": "Kitobdagi ochiq topshiriq — har bir juft gapni bir nechta bog'lovchi bilan to'g'ri bog'lash mumkin, o'qituvchi tekshiradi."}),
        base(L, "uebungen", 2, "Schreiben Aufgabe 2: Mein Griechischkurs — Lösungswörter", page=108, source="book",
             exercises=[exercise("Schreiben Aufgabe 2: Mein Griechischkurs", [
                 gap("Lesen Sie die E-Mail von Anita und ergänzen Sie die richtige Lösung.", GRIECHISCH,
                     {k: {"accepted": [a], "options": opts} for k, (a, opts, _) in GRIECHISCH_KEY.items()}, points=10,
                     explanation=" · ".join(f"{k} {a} ({why})" for k, (a, _, why) in GRIECHISCH_KEY.items()))],
                 "Lesen Sie die E-Mail von Anita und ergänzen Sie die richtige Lösung (Buch S. 108, Lösungswörter: hatte/habe, weil/denn, "
                 "gewählt/entschieden, denn/deshalb, muss/darf, Arbeitgeber/Arbeitnehmer, Alphabet/Schrift, deshalb/denn, kann/will, dich/dir).")],
             metadata={"note": "Im Buch eine Schreiben-Seite mit Auswahl je Lücke — als automatisch bewertete Übung; Lösung von VIZU nach der Grammatik."}),
        base(L, "sprechen", 1, "Sprechen Aufgabe 1: Interview — Lernen", page=109, topic="Lernen",
             prompt="Fragen Sie zwei Kursteilnehmer und notieren Sie die Antworten. Fassen Sie die interessantesten Informationen zusammen und berichten Sie.",
             questions=INTERVIEW, response_type="dialog", min_duration=60, max_duration=240,
             speech_goal="Interview führen, Antworten notieren und die interessantesten Informationen zusammenfassen.",
             keywords=["Sind Sie gern …?", "Was war früher …?", "Er / Sie hat gesagt, dass …", "Am interessantesten fand ich …"]),
        base(L, "wortschatz", 2, "Wortschatz: Lernen und Weiterbildung", page=110, words=WORDS, exercises=meaning_sets(WORDS), auto_practice=False,
             metadata={"note": "Das Buch erklärt die Wörter auf Deutsch (keine Übersetzung)."}),
        base(L, "schreiben", 2, "Wortschatz-Aufgabe: Lernen und Weiterbildung — eigene Beispielsätze", page=110, task_type="other",
             prompt="Hier sind 10 wichtige Wörter und Ausdrücke zum Thema „Lernen und Weiterbildung“. Lesen Sie die Wörter, ihre Bedeutungen und "
                    "schreiben Sie eigene Beispielsätze.\n\n" + "\n".join(f"{i}. {w} — {m}" for i, (w, m) in enumerate(LERNEN, start=1)),
             min_words=40, max_words=300, time_limit=20, metadata={"note": "Ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "uebungen", 1, "Übungen: B1 6. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 6. Unterricht", source="vizu",
             instruction="Abschlusstest zu reflexiven Verben, Lesen und Wortschatz (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 6. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
