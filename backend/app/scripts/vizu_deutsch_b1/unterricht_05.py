"""B1 5. Unterricht — Im Berufsleben — Grammatik: Konjunktiv II (book pp. 79-95).

Book: title p.79, Frage des Themas (Was machen Sie beruflich? Was ist Ihr
Traumberuf?) p.80, Konjunktiv II: alle Regeln auf einen Blick p.81, Grammatik
Aufgabe 1 (hätte / wäre) p.82, Aufgabe 2 (Modalverben; printed as "Aufgabe 1")
p.83, Aufgabe 3 (Aktiv -> Konjunktiv II) p.84, Lesen Aufgabe 1 (Jörgs Blog,
richtig / falsch) p.85, Lesen Aufgabe 2 (Rätsel: Fremde Länder) p.86, Lesen
Aufgabe 3 (Beruf und Gesundheit, richtig / falsch) p.87, Hören Teil 1 + 2
(Sabine und Jakob, Lückentext, one audio "5.Unterricht Hören.mp3") pp.88-89,
Schreiben Aufgabe 1-3 pp.90-92, Sprechen Teil 1 (Person A / B: Kinder oder
Karriere) p.93, Sprechen Teil 2 (Präsentation Berufstätige Eltern,
Musterstruktur) p.94, Wortschatz Im Berufsleben p.95.

Book defects: Aufgabe 1 Satz 9 "Wenn wir in einer anderen Stadt wohnen
(sein) …" cannot be completed with hätte / wäre -> shown, not graded; Satz 10
prints the infinitive (anstrengen) -> "hätte" and "angestrengt hätte" accepted.
The Rätsel grid does not match the clue words (e.g. 15 boxes for
"Herausforderungen") -> the nine clue words are asked, the solution word is not.
Hören: 20 blanks without word bank or key -> key_pending."""

from . import (
    base, example_gap, exercise, gap, intro_html, key_meta, meaning_sets, mc, summary_html, tf, transform,
)

L = 5
LESSON_TITLE = "Im Berufsleben"
LESSON_DESCRIPTION = "Thema: Im Berufsleben · Grammatik: Konjunktiv II (würde, hätte, wäre, Modalverben)"
AUDIO = {"vizu-b1-l05-hoeren-01": "5.Unterricht Hören.mp3"}

EINFUEHRUNG_HTML = intro_html(
    5, "Im Berufsleben", "Konjunktiv II",
    ["Konjunktiv II — istak, orzu, xushmuomala iltimos, real bo'lmagan holat va maslahat: würde + Infinitiv, hätte, wäre;",
     "modal fe'llar Konjunktiv II da: könnte, müsste, dürfte, sollte, wollte, möchte;",
     "kasb, ish va ishga joylashish haqida so'zlar."],
    ["kasbingiz va orzuyingizdagi kasb haqida gapirasiz;",
     "amaliyotchi blogini va kasb hamda salomatlik haqidagi matnni tushunasiz;",
     "maktab bitiruvchilarining kelajak rejalari haqidagi suhbatni tinglaysiz;",
     "taklifnoma, fikr va o'qituvchiga uzrnoma yozasiz;",
     "„Ishlaydigan ota-onalar“ mavzusida taqdimot qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(5, [
    "Konjunktiv II = Wunsch • Traum • Höflichkeit • Irrealität • Ratschlag.",
    "<strong>würde + Infinitiv</strong>: Ich würde gern nach Deutschland reisen. (Im Alltag meistens würde + Infinitiv.)",
    "<strong>sein / haben</strong>: wäre, hätte — Ich wäre gern reich. Ich hätte mehr Zeit. Wenn ich Zeit hätte, würde ich reisen.",
    "<strong>Modalverben</strong>: könnte, müsste, dürfte, sollte, wollte, möchte — Du solltest mehr schlafen.",
    "<strong>Im Berufsleben:</strong> sich bewerben, ein Vorstellungsgespräch haben, eingestellt werden, befördert werden, Überstunden machen, "
    "Beruf und Privatleben vereinbaren, unter Druck arbeiten.",
])

GRAMMAR_HTML = (
    "<h3>Konjunktiv II: alle Regeln auf einen Blick</h3>"
    "<h4>1. Verwendung</h4><p>Konjunktiv II wird verwendet für: Wünsche · Träume · höfliche Bitten · irreale Situationen · Ratschläge</p>"
    "<h4>2. Bildung — die Hauptformen</h4>"
    "<p><strong>A) würde + Infinitiv</strong> — Subjekt + würde + Infinitiv</p>"
    "<ul><li>Ich würde gern nach Deutschland reisen.</li><li>Wir würden mehr Sport machen.</li><li>Er würde ein neues Auto kaufen.</li>"
    "<li>Sie würde das Problem lösen.</li><li>Ihr würdet viel besser werden.</li></ul>"
    "<p><strong>B) Modalverben im Konjunktiv II</strong></p>"
    "<table><thead><tr><th>Infinitiv</th><th>Konjunktiv II</th></tr></thead><tbody>"
    "<tr><td>können</td><td>könnte</td></tr><tr><td>müssen</td><td>müsste</td></tr><tr><td>dürfen</td><td>dürfte</td></tr>"
    "<tr><td>sollen</td><td>sollte</td></tr><tr><td>wollen</td><td>wollte</td></tr><tr><td>mögen</td><td>möchte</td></tr></tbody></table>"
    "<h4>3. Beispiele mit Modalverben</h4><ul><li>Ich könnte heute länger arbeiten.</li><li>Du solltest mehr schlafen.</li>"
    "<li>Wir müssten pünktlich sein.</li><li>Er dürfte das nicht wissen.</li><li>Ich möchte Arzt werden.</li><li>Sie wollte früher anfangen.</li></ul>"
    "<h4>4. sein und haben im Konjunktiv II</h4>"
    "<table><thead><tr><th>Infinitiv</th><th>Konjunktiv II</th><th>Beispiel</th></tr></thead><tbody>"
    "<tr><td>sein</td><td>wäre</td><td>Ich wäre gern reich.</td></tr><tr><td>haben</td><td>hätte</td><td>Ich hätte mehr Zeit.</td></tr>"
    "<tr><td>werden</td><td>würde</td><td>Ich würde Lehrer werden.</td></tr><tr><td>wissen</td><td>wüsste</td><td>Ich wüsste die Antwort.</td></tr>"
    "<tr><td>können</td><td>könnte</td><td>Ich könnte es schaffen.</td></tr></tbody></table>"
    "<h4>5. Weitere wichtige Strukturen</h4><ul><li>Subjekt + wäre + … → Es wäre schön, mehr Urlaub zu haben.</li>"
    "<li>Subjekt + hätte + … → Ich hätte gern ein eigenes Büro.</li><li>Wenn ich … hätte, würde ich … → Wenn ich Zeit hätte, würde ich reisen.</li>"
    "<li>Ich wünschte, … → Ich wünschte, ich könnte fliegen.</li><li>Es ist wichtig, dass … → Es ist wichtig, dass du lernst.</li></ul>"
    "<h4>6. Wichtige Hinweise</h4><ul><li>Im Alltag benutzt man meistens würde + Infinitiv.</li><li>Konjunktiv II hat keine Vergangenheitsformen.</li>"
    "<li>Aussprache ist wie im Indikativ.</li><li>Konjunktiv II ist nicht für die Realität, sondern für Möglichkeiten, Wünsche und Höflichkeit.</li></ul>"
    "<p><strong>Merke:</strong> Konjunktiv II = Wunsch • Traum • Höflichkeit • Irrealität • Ratschlag</p>"
)

_HW = ["hätte", "hättest", "hätten", "wäre", "wärst", "wären"]
HAETTE_WAERE = [
    ("Wenn ich mehr Zeit (haben) [[1]], würde ich jeden Tag Sport machen.", ["hätte"]),
    ("Wenn er reich (sein) [[1]], würde er um die Welt reisen.", ["wäre"]),
    ("Wenn wir früher losgefahren (sein) [[1]], hätten wir den Zug nicht verpasst.", ["wären"]),
    ("Wenn ich du (sein) [[1]], hätte ich das anders gemacht.", ["wäre"]),
    ("Wenn sie mehr gelernt (haben) [[1]], hätte sie die Prüfung bestanden.", ["hätte"]),
    ("Wenn das Wetter besser (sein) [[1]], wären wir an den See gefahren.", ["wäre", "gewesen wäre"]),
    ("Wenn ich genug Geld (haben) [[1]], hätte ich ein neues Auto gekauft.", ["hätte", "gehabt hätte"]),
    ("Wenn du mich gefragt (haben) [[1]], hätte ich dir geholfen.", ["hättest"]),
    ("Wenn er sich mehr anstrengen (haben) [[1]], hätte er sein Ziel erreicht.", ["hätte", "angestrengt hätte"]),
]
MODAL = [
    ("Wenn ich mehr Zeit hätte, (können) [[1]] ich jeden Tag Sport machen.", "könnte"),
    ("Wenn er krank wäre, (müssen) [[1]] er zum Arzt gehen.", "müsste"),
    ("Wenn wir mehr Geld hätten, (sollen) [[1]] wir sparen.", "sollten"),
    ("Wenn du hier wohnen würdest, (dürfen) [[1]] du ein Haustier haben.", "dürftest"),
    ("Wenn ich ihr helfen könnte, (wollen) [[1]] ich sofort kommen.", "wollte"),
    ("Wenn ihr morgen Zeit hättet, (möchten) [[1]] wir euch besuchen.", "möchten"),
    ("Wenn das Wetter besser wäre, (können) [[1]] wir wandern gehen.", "könnten"),
    ("Wenn ich das Buch verstehen würde, (müssen) [[1]] ich es nicht noch einmal lesen.", "müsste"),
    ("Wenn er mehr Erfahrung hätte, (sollen) [[1]] er die Leitung übernehmen.", "sollte"),
    ("Wenn ich frei hätte, (wollen) [[1]] ich ans Meer fahren.", "wollte"),
]
KONJ = [
    ("Ich habe viel Arbeit.", ["Ich hätte viel Arbeit."]),
    ("Er versteht die Aufgabe nicht.", ["Er würde die Aufgabe nicht verstehen.", "Er verstünde die Aufgabe nicht.", "Er verstände die Aufgabe nicht."]),
    ("Wir fahren morgen nach Berlin.", ["Wir würden morgen nach Berlin fahren.", "Wir führen morgen nach Berlin."]),
    ("Sie hat kein Geld.", ["Sie hätte kein Geld."]),
    ("Du bist sehr müde.", ["Du {wärst|wärest} sehr müde."]),
    ("Sie kann gut Deutsch sprechen.", ["Sie könnte gut Deutsch sprechen."]),
    ("Ich finde das Buch interessant.", ["Ich würde das Buch interessant finden.", "Ich fände das Buch interessant."]),
    ("Er macht jeden Tag Sport.", ["Er würde jeden Tag Sport machen."]),
    ("Wir haben ein Auto.", ["Wir hätten ein Auto."]),
    ("Du hilfst mir immer.", ["Du würdest mir immer helfen."]),
]
GRAMMATIK_SETS = [
    exercise("Aufgabe 1: Konjunktiv II mit „hätte“ oder „wäre“", [
        gap(f"{n}. Bilde den Satz im Konjunktiv II mit „hätte“ oder „wäre“.", s, {"1": acc}, explanation=" / ".join(acc))
        for n, (s, acc) in zip([1, 2, 3, 4, 5, 6, 7, 8, 10], HAETTE_WAERE)],
        "Bilde Sätze im Konjunktiv II mit „hätte“ oder „wäre“ (Buch S. 82). Satz 9 im Buch („Wenn wir in einer anderen Stadt wohnen (sein) …, "
        "wären die Mieten günstiger.“) lässt sich mit hätte / wäre nicht bilden und wird nicht bewertet; bei Satz 10 zählt „hätte“ und "
        "„angestrengt hätte“."),
    exercise("Aufgabe 2: Konjunktiv II mit Modalverben", [
        gap(f"{n}. Ergänze das Modalverb im Konjunktiv II.", s, {"1": {"accepted": [a], "options": sorted({m for _, m in MODAL} | {a})}}, explanation=a)
        for n, (s, a) in enumerate(MODAL, start=1)],
        "Bilde Sätze im Konjunktiv II mit Modalverben: können • müssen • sollen • dürfen • wollen • möchten (Buch S. 83)."),
    exercise("Aufgabe 3: Aktiv → Konjunktiv II", [transform(n, s, p, "Konjunktiv II") for n, (s, p) in enumerate(KONJ, start=1)],
             "Wandle die Sätze vom Aktiv in den Konjunktiv II um (Buch S. 84). Die würde-Form und die Konjunktiv-II-Form des Verbs zählen beide."),
]

# ---------- Lesen ----------
BLOG = (
    "Ich bin Journalist und habe in den Niederlanden ein dreimonatiges Praktikum gemacht. Ich wollte wissen, wie die Medien in unserem Nachbarland. "
    "Ich habe mich bei mehreren niederländischen Zeitungen um einen Praktikumsplatz beworben, schließlich hat mich eine Zeitung in der Provinz "
    "Süd-Holland genommen. Ich habe dann noch einen Niederländischkurs für Fortgeschrittene gemacht, um meine Kenntnisse aufzufrischen und zu "
    "erweitern. Das hat mir großen Spaß gemacht, denn ich lerne gerne Fremdsprachen.\n\n"
    "Ich wusste schon, dass man in den Niederlanden miteinander nicht so formell umgeht wie in Deutschland. Es hat mich trotzdem überrascht, dass mich "
    "gleich am ersten Tag alle Leute in der Redaktion geduzt haben. Daran musste ich mich erst einmal gewöhnen.\n\n"
    "Außerdem haben niederländische Firmen eine flache Hierarchie. Deshalb wusste ich am Anfang nicht so genau, wer eigentlich der Chef ist, wer die "
    "Mitarbeiter und wer die Praktikanten sind. Einmal habe ich einen älteren Herrn um Rat gebeten, weil ich dachte, er ist ein erfahrener Kollege. "
    "Aber es stellte sich heraus, dass er „nur“ Praktikant war.\n\n"
    "Ich habe in der Redaktion gearbeitet, an Sitzungen teilgenommen und Interviews geführt. Besonders gut hat mir gefallen, dass ich von Anfang an "
    "selbstständig arbeiten musste. Meine Kollegen haben mir natürlich geholfen, wenn ich Fragen hatte, aber die meisten Lösungen musste ich alleine "
    "finden. Ich habe auch ein paar Fehler gemacht, aber niemand fand das schlimm und auf diese Weise konnte ich viel lernen.\n\n"
    "Ich habe vor, eine Artikelreihe über meine Erfahrungen in den Niederlanden zu schreiben, die ich in diesem Blog veröffentlichen werde.")
LESEN_1 = [
    tf("Jörg war drei Monate lang im Ausland.", True, "„… in den Niederlanden ein dreimonatiges Praktikum gemacht.“"),
    tf("Er hat bei einer niederländischen Zeitung gearbeitet.", True, "„… schließlich hat mich eine Zeitung in der Provinz Süd-Holland genommen.“"),
    tf("Am Anfang des Praktikums konnte er kein Niederländisch.", False, "„… einen Niederländischkurs für Fortgeschrittene gemacht, um meine Kenntnisse aufzufrischen …“"),
    tf("Er hat in der Redaktion einige Missverständnisse erlebt.", True,
       "„Einmal habe ich einen älteren Herrn um Rat gebeten, weil ich dachte, er ist ein erfahrener Kollege. Aber … er „nur“ Praktikant war.“"),
    tf("Das Verhältnis zwischen den Kollegen ist formeller als in Deutschland.", False,
       "„… dass man in den Niederlanden miteinander nicht so formell umgeht wie in Deutschland.“"),
    tf("Seine Kollegen wollten ihm nicht helfen.", False, "„Meine Kollegen haben mir natürlich geholfen, wenn ich Fragen hatte …“"),
    tf("Er will Texte über seine Erfahrungen publizieren.", True, "„Ich habe vor, eine Artikelreihe über meine Erfahrungen … zu schreiben, die ich in diesem Blog veröffentlichen werde.“"),
]
RAETSEL = [
    ("Viele junge Leute gehen zum [[1]] in ein fremdes Land.", ["Studium"]),
    ("Das bringt große [[1]] mit sich.", ["Herausforderungen"]),
    ("Man sollte auf die kulturellen Gepflogenheiten im [[1]] achten.", ["Gastland"]),
    ("Es ist auch wichtig, sich über kulturelle [[1]] zu informieren.", ["Unterschiede"]),
    ("In vielen Ländern legt man auf [[1]] großen Wert.", ["Pünktlichkeit", "Puenktlichkeit"]),
    ("Mit Respekt und [[1]] kann man nicht viel falsch machen.", ["Höflichkeit", "Hoeflichkeit"]),
    ("Man darf nicht überall seine eigenen [[1]] loben.", ["Leistungen"]),
    ("Themen wie Politik oder [[1]] sollte man vermeiden.", ["Religion"]),
    ("In Japan gilt enger Körperkontakt bei der [[1]] als unangenehm.", ["Begrüßung", "Begrüssung", "Begruessung"]),
]
LESEN_2 = [gap(f"{n}. Ergänzen Sie das Nomen.", s, {"1": acc}, explanation=f"Lösung (VIZU): {acc[0]}") for n, (s, acc) in enumerate(RAETSEL, start=1)]
GESUNDHEIT = (
    "Thomas steht jeden Morgen um 6.23 Uhr auf und arbeitet in einem Büro (wie 33 Prozent der Deutschen). Im Büro erscheint er pünktlich und erledigt "
    "seine Arbeit korrekt und zuverlässig. Allerdings ist Thomas nicht immer motiviert und macht oft Dienst nach Vorschrift. Ursprünglich wollte er "
    "etwas ganz anderes werden, sein Kindheitstraum war Fußballprofi. Als moderner Büromensch bewegt sich Thomas zu wenig. Er leidet unter "
    "Rückenschmerzen. Außerdem hat er Probleme mit den Gelenken und dem Herz-Kreislauf-System.")
LESEN_3 = [
    tf("Thomas arbeitet zu Hause.", False, "„… und arbeitet in einem Büro …“"),
    tf("Thomas ist immer motiviert.", False, "„Allerdings ist Thomas nicht immer motiviert …“"),
    tf("Thomas hat gesundheitliche Probleme.", True, "„Er leidet unter Rückenschmerzen. Außerdem hat er Probleme mit den Gelenken …“"),
    tf("Thomas wollte als Kind Fußballprofi werden.", True, "„… sein Kindheitstraum war Fußballprofi.“"),
]

# ---------- Hören (key only from the audio) ----------
H1 = (
    "Sabine: Und Jakob, wie geht's dir mit deinen [[1]]?\n"
    "Jakob: Es läuft eigentlich ganz gut. Nächste Woche noch zwei, dann habe ich es geschafft. Hoffentlich bekomme ich den [[2]], den ich für die "
    "Fachoberschule brauche!\n"
    "Sabine: Das heißt, du willst jetzt wirklich weitermachen nach der Mittleren Reife?\n"
    "Jakob: Ja, auf jeden Fall. Ich weiß einfach noch nicht, was für ein [[3]] der richtige für mich ist. Außerdem sind meine Chancen mit Abitur noch "
    "besser.\n"
    "Sabine: Ja, das haben meine Eltern auch immer gesagt, wenn ich mit der Schule aufhören wollte. Wahrscheinlich haben sie ja recht. So kurz vor dem "
    "Ziel aufzugeben, wäre wirklich verrückt. In zwei Jahren habe ich's ja auch geschafft! Aber es ist schon [[4]].\n"
    "Jakob: Das glaube ich dir. Was willst du denn nach dem Abitur machen?\n"
    "Sabine: Am liebsten würde ich erst einmal ein Jahr ins [[5]] gehen, entweder als Au-pair-Mädchen oder mit dem Programm „Work And Travel“. [[6]] "
    "wäre toll, oder Australien …\n"
    "Jakob: Du hast doch auch Spanisch in der Schule, oder?\n"
    "Sabine: Ja, letztes Jahr konnte ich endlich [[7]] ablegen und Spanisch nehmen. Eine Freundin meiner Schwester hat in Chile in einem Kinderheim "
    "gearbeitet, das war eine tolle [[8]] für sie. Und wenn ich keinen Studienplatz für Medizin bekomme, überlege ich mir, vielleicht [[9]] zu "
    "studieren.\n"
    "Jakob: Das könnte ich mir auch gut für dich vorstellen. Medizin dauert so unglaublich lang! Erst wartest du, wenn du Pech hast, ein paar Jahre auf "
    "deinen Studienplatz, dann studierst du fünf oder sechs Jahre, dann die Doktorarbeit und die [[10]] – du bist uralt, bis du fertig bist!")
H2 = (
    "Sabine: Das stimmt schon, aber das ist mein Traum seit meiner Kindheit! Mal sehen … Und du? Was kommt für dich in Frage? Du musst dich doch auf "
    "der Fachoberschule auch schon für einen [[1]] entscheiden?\n"
    "Jakob: Ja, ich überlege noch, ob ich den [[2]] nehmen soll oder den Wirtschaftszweig – beides würde mich interessieren. Mit dem Fachabitur in "
    "Wirtschaft könnte ich sicher eine kaufmännische Ausbildung in einer Firma machen und dann vielleicht noch [[3]] studieren, also "
    "Betriebswirtschaft.\n"
    "Sabine: Puh, das klingt verdammt trocken!\n"
    "Jakob: Ja, aber mir macht es Spaß! Auf der anderen Seite weiß ich, dass ich auch nicht schlecht bin in [[4]] und Design. Das könnte ich mir auch "
    "gut vorstellen.\n"
    "Sabine: Und wenn du erst mal nach der Mittleren Reife ein [[5]] machst?\n"
    "Jakob: Das hatte ich mir sowieso schon überlegt. Ein Jahr Auszeit mit Praktika oder auch ein [[6]] Soziales Jahr – vielleicht weiß ich danach, "
    "was ich will!\n"
    "Sabine: Warst du schon bei der [[7]]?\n"
    "Jakob: Noch nicht. Jetzt muss ich erst einmal die [[8]] gut schaffen, dann sehe ich weiter.\n"
    "Sabine: Also, lern schön – ich drücke dir die [[9]]!\n"
    "Jakob: Danke! Und nächste Woche, wenn's vorbei ist, gehen wir [[10]], ja?\n"
    "Sabine: Klar!")
HOEREN = [
    gap("Teil 1 – Hören (Lückentext): Ergänzen Sie die Lücken 1–10.", H1, {str(i): [] for i in range(1, 11)}, points=10),
    gap("Teil 2 – Hören (Lückentext): Ergänzen Sie die Lücken 1–10.", H2, {str(i): [] for i in range(1, 11)}, points=10),
]

# ---------- Sprechen ----------
PERSON_A = (
    "PERSON A — Erfahrung: Ich habe selbst noch keine Kinder. Aber meine ältere Schwester hat eine kleine Tochter und arbeitet trotzdem in Teilzeit. "
    "Sie sagt, dass es nicht einfach ist, Familie und Beruf zu verbinden.\nSituation: In meinem Land entscheiden sich viele Frauen zuerst für die "
    "Familie. Trotzdem möchten heute immer mehr Frauen auch eine gute Karriere machen. Deshalb ist dieses Thema sehr aktuell.\nVorteile — Kinder: "
    "Kinder bringen Freude und Glück in die Familie. Man fühlt sich nicht allein und hat später Unterstützung von den Kindern. Karriere: Mit einer "
    "guten Karriere kann man finanziell unabhängig sein. Man kann seine Träume verwirklichen und mehr Erfahrungen sammeln.\nNachteile — Kinder: "
    "Kinder kosten viel Zeit und Geld. Man hat oft weniger Freizeit. Karriere: Man hat manchmal viel Stress und wenig Zeit für die Familie. Oft muss "
    "man Überstunden machen.\nMeinung: Meiner Meinung nach sollte man zuerst eine stabile Ausbildung oder Karriere aufbauen. Danach kann man leichter "
    "eine Familie gründen und den Kindern ein gutes Leben bieten.")
PERSON_B = (
    "PERSON B — Erfahrung: Ich habe keine eigenen Kinder, aber mein Cousin ist Vater von zwei Kindern. Er sagt, dass Kinder zwar viel Verantwortung "
    "bedeuten, aber auch das Schönste im Leben sind.\nSituation: In vielen Familien arbeiten heute beide Eltern. Das ist oft notwendig, weil die "
    "Lebenshaltungskosten sehr hoch sind. Deshalb müssen Familie und Beruf gut organisiert werden.\nVorteile — Kinder: Kinder machen das Leben "
    "interessanter und glücklicher. Sie stärken den Zusammenhalt in der Familie. Karriere: Mit einer guten Arbeit verdient man mehr Geld. Man kann "
    "sich ein besseres Leben leisten und seine Familie unterstützen.\nNachteile — Kinder: Kleine Kinder brauchen viel Aufmerksamkeit. Man muss auf "
    "viele persönliche Wünsche verzichten. Karriere: Eine Karriere kann sehr anstrengend sein. Manche Menschen haben dadurch weniger Zeit für ihre "
    "Kinder.\nMeinung: Ich finde, dass weder Kinder noch Karriere wichtiger sind. Das Wichtigste ist ein gutes Gleichgewicht. Wenn man Familie und "
    "Beruf gut plant, kann man beides erfolgreich schaffen.")
MUSTER_ELTERN = (
    "1. Begrüßung & Thema: Guten Abend an alle. Jetzt spreche ich zum Thema „Berufstätige Eltern“. Dieses Thema ist heute sehr aktuell und betrifft "
    "viele Familien.\n2. Eigene Erfahrung: Zuerst möchte ich über meine eigenen Erfahrungen sprechen. Ich habe selbst wenig Erfahrung mit diesem Thema, "
    "aber ich kenne Familien, in denen beide Eltern arbeiten.\n3. Situation im Heimatland: Nun möchte ich die Situation in meinem Heimatland "
    "beschreiben. Bei uns sind nicht alle Eltern berufstätig. Wenn beide Eltern arbeiten, kümmern sich oft Großeltern oder Kindergärten um die "
    "Kinder.\n4. Vorteile: Ein wichtiger Vorteil ist, dass die Eltern mehr Geld verdienen können. Außerdem können beide Eltern beruflich erfolgreich "
    "sein und ihre Karriere entwickeln.\n5. Nachteile: Natürlich gibt es auch einige Nachteile. Die Eltern haben weniger Zeit für ihre Kinder und "
    "müssen Beruf und Familie gleichzeitig organisieren. Außerdem können Kindergärten sehr teuer sein.\n6. Meine Meinung: Meiner Meinung nach ist es "
    "wichtig, dass Familie und Beruf im Gleichgewicht sind. Ich finde, dass es gut wäre, wenn sich beide Eltern die Verantwortung für die Kinder "
    "teilen könnten.\n7. Schluss: Damit bin ich am Ende meiner Präsentation. Vielen Dank für Ihre Aufmerksamkeit. Wenn Sie Fragen haben, beantworte "
    "ich sie gerne.")

BERUF = [
    ("einen Job finden", "eine Arbeitsstelle bekommen", "ish topmoq"),
    ("sich bewerben", "eine Bewerbung schicken, um eine Stelle zu bekommen", "ishga ariza topshirmoq"),
    ("ein Vorstellungsgespräch haben", "mit dem Arbeitgeber sprechen, um den Job zu bekommen", "suhbatdan o'tmoq"),
    ("eingestellt werden", "den Job bekommen und offiziell anfangen", "ishga qabul qilinmoq"),
    ("befördert werden", "eine höhere Position oder mehr Verantwortung bekommen", "lavozimga ko'tarilmoq"),
    ("Überstunden machen", "länger arbeiten als normal", "qo'shimcha ishlamoq"),
    ("Erfahrungen sammeln", "durch Arbeit neues Wissen und Fähigkeiten bekommen", "tajriba to'plamoq"),
    ("Ziele im Beruf haben", "klare Pläne für die Karriere haben", "kasbiy maqsadlar qo'ymoq"),
    ("Beruf und Privatleben vereinbaren", "Arbeit und Freizeit gut miteinander verbinden", "ish va shaxsiy hayotni muvofiqlashtirmoq"),
    ("unter Druck arbeiten", "wegen Stress und Verantwortung anstrengend arbeiten", "bosim ostida ishlamoq"),
]
WORDS = [{"word": w, "translation": uz, "example": f"Bedeutung: {de}", "group": "Im Berufsleben"} for w, de, uz in BERUF]

UEBUNGEN = [
    exercise("Konjunktiv II — welche Form passt? (Beispiele aus dem Buch)", [
        example_gap("Ich ___ gern nach Deutschland reisen.", "würde", ["würde", "wäre", "hätte"], "würde + Infinitiv."),
        example_gap("Ich ___ gern reich.", "wäre", ["wäre", "hätte", "würde"], "sein → wäre."),
        example_gap("Ich ___ mehr Zeit.", "hätte", ["hätte", "wäre", "würde"], "haben → hätte."),
        example_gap("Du ___ mehr schlafen.", "solltest", ["solltest", "sollst", "solltet"], "Ratschlag: sollte."),
        example_gap("Wenn ich Zeit hätte, ___ ich reisen.", "würde", ["würde", "werde", "wäre"]),
        example_gap("Ich wünschte, ich ___ fliegen.", "könnte", ["könnte", "kann", "konnte nicht"]),
        example_gap("Ich ___ die Antwort.", "wüsste", ["wüsste", "weiß", "würde"], "wissen → wüsste."),
    ], "Wählen Sie die richtige Form (Buch S. 81).", source="vizu"),
]
ABSCHLUSSTEST = [
    mc("Wofür verwendet man den Konjunktiv II nicht?", ["Für reale Tatsachen", "Für höfliche Bitten", "Für Wünsche"], "A",
       "Buch S. 81: Konjunktiv II ist nicht für die Realität, sondern für Möglichkeiten, Wünsche und Höflichkeit."),
    example_gap("Wir ___ pünktlich sein.", "müssten", ["müssten", "mussten", "müssen"], "müssen → müsste."),
    example_gap("Er ___ das nicht wissen.", "dürfte", ["dürfte", "durfte", "darf"]),
    example_gap("Es ___ schön, mehr Urlaub zu haben.", "wäre", ["wäre", "hätte", "würde"]),
    example_gap("Wenn ich du wäre, ___ ich das anders gemacht.", "hätte", ["hätte", "wäre", "würde"]),
    example_gap("Wenn ich frei hätte, ___ ich ans Meer fahren.", "wollte", ["wollte", "will", "wollen"]),
    mc("Wie lange war Jörg im Ausland?", ["Drei Monate", "Ein Jahr", "Drei Wochen"], "A", "Lesen Aufgabe 1: dreimonatiges Praktikum."),
    mc("„befördert werden“ bedeutet …", ["eine höhere Position oder mehr Verantwortung bekommen", "länger arbeiten als normal",
                                          "eine Bewerbung schicken"], "A", "Wortschatz Im Berufsleben."),
    mc("„Überstunden machen“ — o'zbekchasi?", ["qo'shimcha ishlamoq", "ish topmoq", "tajriba to'plamoq"], "A"),
    mc("„sich bewerben“ — o'zbekchasi?", ["ishga ariza topshirmoq", "ishga qabul qilinmoq", "lavozimga ko'tarilmoq"], "A"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 5. Unterricht", source="vizu", page=79, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Was machen Sie beruflich? Was ist Ihr Traumberuf?", page=80,
             prompt="01 Was machen Sie beruflich? 02 Was ist Ihr Traumberuf?", questions=["Was machen Sie beruflich?", "Was ist Ihr Traumberuf?"],
             min_duration=30, max_duration=150,
             metadata={"book_samples": [
                 "Ich arbeite als Softwareentwickler in einem IT-Unternehmen. Ich entwickle Anwendungen und löse technische Probleme. Mein Job macht mir "
                 "Spaß, weil ich kreativ und herausfordernd ist. Ich arbeite in einem tollen Team und habe flexible Arbeitszeiten. In meiner Freizeit "
                 "lerne ich neue Technologien und treibe Sport. Ich bin zufrieden mit meinem Beruf und sehe gute Zukunftschancen.",
                 "Mein Traumberuf ist es, als Übersetzerin zu arbeiten. Ich liebe Sprachen und möchte Menschen verbinden. Ich würde gerne für "
                 "internationale Organisationen arbeiten. Mein Beruf soll sinnvoll sein und mir ermöglichen, zu reisen. Ich möchte jeden Tag dazulernen "
                 "und neue Kulturen entdecken. Ich bin motiviert und arbeite jeden Tag an meinem Ziel."]}),
        base(L, "grammatik", 1, "Grammatik: Konjunktiv II", page="81-84", rules=[{"title": "Konjunktiv II: alle Regeln auf einen Blick", "html": GRAMMAR_HTML}],
             exercises=GRAMMATIK_SETS, metadata={"note": "Lösungen von VIZU nach der Grammatik; Buchfehler Aufgabe 1 Satz 9/10 im Hinweis."}),
        base(L, "lesen", 1, "Lesen Aufgabe 1: Jörgs Blog — Bericht eines Praktikanten", page=85,
             instruction="a) Lesen Sie den folgenden Blogeintrag. b) Was steht im Text? Ist die Aussage richtig oder falsch? Kreuzen Sie an.",
             passages=[{"title": "Jörgs Blog: Bericht eines Praktikanten", "text": BLOG}], questions=LESEN_1, max_score=len(LESEN_1), metadata=key_meta("vizu")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: Rätsel — Fremde Länder", page=86,
             instruction="Rätsel: Fremde Länder. Ergänzen Sie die Nomen. (Im Buch als Kreuzworträtsel mit Lösungswort.)",
             passages=[{"title": "Rätsel: Fremde Länder", "text": "\n".join(f"{n}. {s.replace('[[1]]', '……')}" for n, (s, _) in enumerate(RAETSEL, start=1))}],
             questions=LESEN_2, max_score=len(LESEN_2),
             metadata=key_meta("vizu", "Das Gitter im Buch passt nicht zu den Wörtern (z. B. 15 Kästchen für „Herausforderungen“, 11 für „Pünktlichkeit“); "
                                       "deshalb werden die 9 Nomen abgefragt, das Lösungswort nicht. Lösung von VIZU — bitte prüfen.")),
        base(L, "lesen", 3, "Lesen Aufgabe 3: Beruf und Gesundheit", page=87, instruction="Lesen Sie den Text und entscheiden Sie: richtig oder falsch?",
             passages=[{"title": "Beruf und Gesundheit", "text": GESUNDHEIT}], questions=LESEN_3, max_score=len(LESEN_3), metadata=key_meta("vizu")),
        base(L, "hoeren", 1, "Hören Teil 1 + 2: Sabine und Jakob — nach der Schule", page="88-89", audio_file=AUDIO["vizu-b1-l05-hoeren-01"], key_pending=True,
             instruction="Hören (Lückentext): Hören Sie das Gespräch und ergänzen Sie die Lücken. (Eine Audiodatei für Teil 1 und Teil 2.)",
             questions=HOEREN, max_score=20,
             metadata=key_meta("pending", "Lückentext ohne Wörterliste und ohne Lösung im Buch — alle 20 Lücken nach dem Anhören in Lösung festlegen.")),
        base(L, "schreiben", 1, "Schreiben Aufgabe 1: Einladung zu einem Ausflug", page=90, task_type="message",
             prompt="Arbeitszeit: 20 Minuten. Sie möchten einen Freund / eine Freundin, der/die Ihnen in einer schwierigen Situation geholfen hat, zu "
                    "einem Ausflug einladen.\n• Begründen Sie: Warum war seine/ihre Hilfe so wichtig?\n• Beschreiben Sie: Wohin geht der Ausflug und was "
                    "haben Sie geplant?\n• Erklären Sie, warum er/sie auf keinen Fall ablehnen kann.\n\nSchreiben Sie eine persönliche Nachricht (circa 80 "
                    "Wörter). Schreiben Sie etwas zu allen drei Punkten. Achten Sie auf den Textaufbau (Anrede, Einleitung, Reihenfolge der "
                    "Inhaltspunkte, Schluss).",
             audience="Ein Freund / eine Freundin (informell)", min_words=70, max_words=120, time_limit=20),
        base(L, "schreiben", 2, "Schreiben Aufgabe 2: Meinung — Vegetarische Ernährung", page=91, task_type="opinion",
             prompt="Sie haben im Internet einen Artikel zum Thema „Vegetarische Ernährung“ gelesen. Im Gästebuch der Internetseite "
                    "(www.meinungsaustausch.de) finden Sie folgende Meinung:\n\nSonntag, 2. Oktober, 19:16 — Lina: Ich habe mich für eine vegetarische "
                    "Ernährung entschieden, weil mir die Tiere leidtun. Meine Mutter behauptet zwar, dass es ungesund ist, kein Fleisch zu essen. Aber "
                    "Tiere haben auch das Recht auf Leben.\n\nSchreiben Sie nun Ihre Meinung (circa 80 Wörter).\n• Stimmen Sie Lina zu oder nicht?\n"
                    "• Begründen Sie Ihre Meinung.\n• Geben Sie Beispiele aus Ihrem Alltag.\n• Schreiben Sie einen gut strukturierten Text.\n\nTipp: Achten "
                    "Sie auf den Textaufbau: Anrede – Einleitung – Hauptteil – Schluss. Schreiben Sie klar und verständlich.",
             audience="Gästebuch einer Internetseite", min_words=70, max_words=120, time_limit=25),
        base(L, "schreiben", 3, "Schreiben Aufgabe 3: E-Mail an Herrn Hackl — Entschuldigung", page=92, task_type="email",
             prompt="Ihr Sohn ist krank und die Kinderärztin hat empfohlen, dass er eine Woche zu Hause bleibt. Sie möchten seinem Klassenlehrer, Herrn "
                    "Hackl, Bescheid geben.\n\nIhre Aufgabe: Schreiben Sie an Herrn Hackl.\n• Entschuldigen Sie höflich das Fehlen Ihres Sohnes.\n"
                    "• Informieren Sie ihn, wann er wieder zum Unterricht kommen kann.\n• Schreiben Sie eine E-Mail (circa 40 Wörter).\n• Vergessen Sie "
                    "nicht die Anrede und den Gruß am Schluss.\n\nTipp: Seien Sie höflich und klar. Geben Sie den Grund an. Nennen Sie den Zeitraum. "
                    "Schließen Sie freundlich ab. Textaufbau einer E-Mail: Anrede → Einleitung (Grund) → Hauptteil (Information) → Schluss (Gruß).",
             audience="Herr Hackl, Klassenlehrer (formell)", min_words=35, max_words=70, time_limit=15),
        base(L, "sprechen", 1, "Sprechen Teil 1: Kinder oder Karriere — Person A und Person B", page=93, topic="Kinder oder Karriere",
             prompt="Sprechen Sie mit Ihrem Partner / Ihrer Partnerin über das Thema „Kinder oder Karriere“. Person A und Person B sprechen nacheinander "
                    "über die Punkte: Erfahrung, Situation, Vorteile (Kinder / Karriere), Nachteile (Kinder / Karriere), Meinung.",
             questions=["Erfahrung", "Situation", "Vorteile — Kinder und Karriere", "Nachteile — Kinder und Karriere", "Meinung"],
             response_type="dialog", min_duration=90, max_duration=240, sample_answer=PERSON_A + "\n\n" + PERSON_B,
             speech_goal="Erfahrung, Situation, Vor- und Nachteile von Kindern und Karriere nennen und die eigene Meinung begründen.",
             keywords=["Erfahrung", "Situation", "Vorteile", "Nachteile", "Meiner Meinung nach", "Ich finde"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Präsentation — Berufstätige Eltern", page=94, topic="Berufstätige Eltern",
             prompt="Halten Sie eine Präsentation zum Thema „Berufstätige Eltern“. Folgen Sie der Musterstruktur: Begrüßung & Thema, eigene Erfahrung, "
                    "Situation im Heimatland, Vorteile, Nachteile, meine Meinung, Schluss.",
             questions=["Begrüßung & Thema", "Eigene Erfahrung", "Situation im Heimatland", "Vorteile", "Nachteile", "Meine Meinung", "Schluss"],
             response_type="monolog", preparation_time=300, min_duration=120, max_duration=180, sample_answer=MUSTER_ELTERN,
             speech_goal="Strukturierte Präsentation in 7 Schritten (Musterstruktur des Buches).",
             keywords=["Jetzt spreche ich zum Thema", "Zuerst", "Nun möchte ich", "Ein wichtiger Vorteil", "Natürlich gibt es auch", "Damit bin ich am Ende"]),
        base(L, "wortschatz", 1, "Wortschatz: Im Berufsleben", page=95, words=WORDS, exercises=meaning_sets(WORDS), auto_practice=False,
             metadata={"note": "Buch: Redewendung, Bedeutung (Deutsch) und Übersetzung (usbekisch)."}),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Im Berufsleben — eigene Sätze", page=95, task_type="other",
             prompt="Hier sind 10 wichtige Redewendungen zum Thema „Im Berufsleben“. Lesen Sie die Redewendungen, ihre Bedeutungen und schreiben Sie "
                    "eigene Sätze.\n\n" + "\n".join(f"{i}. {w} — {de}" for i, (w, de, _) in enumerate(BERUF, start=1)),
             min_words=40, max_words=300, time_limit=20, metadata={"note": "Ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "uebungen", 1, "Übungen: B1 5. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 5. Unterricht", source="vizu",
             instruction="Abschlusstest zu Konjunktiv II und Berufsleben (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 5. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
