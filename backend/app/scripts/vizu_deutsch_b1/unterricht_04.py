"""B1 4. Unterricht — Entwicklung der Länder — Grammatik: Passiv-Strukturen (book pp. 61-78).

Book: title p.61, Frage des Themas (In welcher bekannten Stadt würden Sie
wohnen?, Beispiel-Präsentation) p.62, Passiv-Strukturen (6 Zeitformen) p.63,
Grammatik Aufgabe 1-4 (Aktiv -> Passiv Präsens / Präteritum / Perfekt /
Plusquamperfekt) pp.64-67, Aufgabe 5-6 (Wortstellung Passiv Futur I / II)
pp.68-69, Lesen Aufgabe 1 (Hamburg-Blog, Verben im Präteritum / Partizip
Perfekt; page header says "B2") p.70, Lesen Aufgabe 2 (Grüne Großstädte,
richtig / falsch) p.71, Hören Aufgabe 1 + 2 (Karla und Kurt: Stadt oder Land,
word banks, one audio file "4.Unterricht Aufgabe 1-2.mp3") pp.72-73, Schreiben
Aufgabe 1 (Antwort-E-Mail an Haytam) p.74, Schreiben Teil 2 (Forumsbeitrag,
Musterbeitrag) p.75, Sprechen Teil 1 (Konzertbesuch, Musterdialog) p.76,
Sprechen Teil 2 (Land oder Stadt, Musterpräsentation) p.77, Wortschatz
Stadtleben (10 Redewendungen with Uzbek translation) p.78.

Keys: no key is printed. Grammar transformations have one grammatical
answer (variants with / without the agent accepted). Lesen and Hören keys by
VIZU (verb forms by grammar, R/F by the quoted sentence, word banks by
context) — held for verification in Lösung. Futur II p.69 Satz 3 prints
"werden" (plural: die Hausaufgaben) — correct, kept."""

from . import (
    base, example_gap, exercise, gap, intro_html, key_meta, meaning_sets, mc, summary_html, tf, transform,
)

L = 4
LESSON_TITLE = "Entwicklung der Länder"
LESSON_DESCRIPTION = "Thema: Entwicklung der Länder · Grammatik: Passiv-Strukturen (Präsens bis Futur II)"
AUDIO = {"vizu-b1-l04-hoeren-01": "4.Unterricht Aufgabe 1-2.mp3"}

EINFUEHRUNG_HTML = intro_html(
    4, "Entwicklung der Länder", "Passiv-Strukturen (Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I, Futur II)",
    ["Passivni barcha zamonlarda tuzish: werden / wurde / ist … worden / war … worden / wird … werden / wird … worden sein;",
     "Aktiv gapni Passivga o'girish;",
     "shahar hayoti, shaharlar rivoji va ekologiya haqida so'zlar."],
    ["qaysi mashhur shaharda yashashni xohlashingizni aytasiz;",
     "Gamburg haqidagi blog va Germaniyaning yashil shaharlari haqidagi matnni tushunasiz;",
     "shahar va qishloq hayoti haqidagi dialogni tinglab tushunasiz;",
     "do'stingizning e-mailiga javob va internet haqida forumga maqola yozasiz;",
     "konsertga borishni rejalashtirasiz va „Qishloqda yoki shaharda hayot“ mavzusida taqdimot qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(4, [
    "<strong>Präsens:</strong> werden + Partizip II — Die Texte werden jeden Tag korrigiert.",
    "<strong>Präteritum:</strong> wurde + Partizip II — Die Wohnung wurde gestern gereinigt.",
    "<strong>Perfekt:</strong> ist + Partizip II + worden — Die Aufgaben sind schon erledigt worden.",
    "<strong>Plusquamperfekt:</strong> war + Partizip II + worden — Die Bücher waren bereits gelesen worden.",
    "<strong>Futur I:</strong> wird + Partizip II + werden — Das Projekt wird nächste Woche beendet werden.",
    "<strong>Futur II:</strong> wird + Partizip II + worden sein — Bis 2030 wird die Brücke gebaut worden sein.",
    "<strong>Stadtleben:</strong> im Stau stehen, Kontakte knüpfen, öffentliche Verkehrsmittel nutzen, zur Miete wohnen, in der Menge untergehen.",
])

GRAMMAR_HTML = (
    "<h3>Passiv-Strukturen</h3>"
    "<table><thead><tr><th>Zeitform</th><th>Struktur</th><th>Beispiel</th></tr></thead><tbody>"
    "<tr><td>Präsens</td><td>werden + Partizip II</td><td>Die Texte werden jeden Tag korrigiert.<br>(Die Texte korrigieren jeden Tag.)</td></tr>"
    "<tr><td>Präteritum</td><td>wurde + Partizip II</td><td>Die Wohnung wurde gestern gereinigt.<br>(Jemand reinigte gestern die Wohnung.)</td></tr>"
    "<tr><td>Perfekt</td><td>ist/hat + Partizip II worden</td><td>Die Aufgaben sind schon erledigt worden.<br>(Jemand hat die Aufgaben schon erledigt.)</td></tr>"
    "<tr><td>Plusquamperfekt</td><td>war/hatte + Partizip II worden</td><td>Die Bücher waren bereits gelesen worden.<br>"
    "(Jemand hatte die Bücher bereits gelesen.)</td></tr>"
    "<tr><td>Futur I</td><td>wird + Partizip II werden</td><td>Das Projekt wird nächste Woche beendet werden.<br>"
    "(Jemand wird das Projekt nächste Woche beenden.)</td></tr>"
    "<tr><td>Futur II</td><td>wird + Partizip II worden sein</td><td>Bis 2030 wird die Brücke gebaut worden sein.<br>"
    "(Jemand wird die Brücke bis 2030 gebaut haben.)</td></tr></tbody></table>"
    "<p><em>Hinweis:</em> Das Passiv-Perfekt und -Plusquamperfekt bildet man mit <strong>sein</strong> (ist / war … worden).</p>"
)

# ---------- Grammatik Aufgaben (unique answers; agent optional) ----------
PRAESENS = [
    ("Der Lehrer erklärt die Grammatik.", ["Die Grammatik wird {vom Lehrer |von dem Lehrer |}erklärt."]),
    ("Die Firma produziert neue Autos.", ["Neue Autos werden {von der Firma |}produziert."]),
    ("Sie schreibt einen Brief an ihre Freundin.", ["Ein Brief wird {von ihr |}an ihre Freundin geschrieben.",
                                                     "Ein Brief an ihre Freundin wird {von ihr |}geschrieben."]),
    ("Die Schüler beantworten die Fragen.", ["Die Fragen werden {von den Schülern |}beantwortet."]),
    ("Mein Vater repariert das Fahrrad.", ["Das Fahrrad wird {von meinem Vater |}repariert."]),
    ("Der Chef bespricht das Projekt mit dem Team.", ["Das Projekt wird {vom Chef |von dem Chef |}mit dem Team besprochen."]),
    ("Wir reinigen das Zimmer jeden Tag.", ["Das Zimmer wird jeden Tag {von uns |}gereinigt.", "Das Zimmer wird {von uns |}jeden Tag gereinigt."]),
    ("Die Bäckerei verkauft frisches Brot.", ["Frisches Brot wird {von der Bäckerei |}verkauft."]),
]
PRAETERITUM = [
    ("Der Lehrer erklärte die Regeln.", ["Die Regeln wurden {vom Lehrer |von dem Lehrer |}erklärt."]),
    ("Die Firma produzierte neue Produkte.", ["Neue Produkte wurden {von der Firma |}produziert."]),
    ("Sie schrieb einen langen Brief.", ["Ein langer Brief wurde {von ihr |}geschrieben."]),
    ("Die Kinder malten schöne Bilder.", ["Schöne Bilder wurden {von den Kindern |}gemalt."]),
    ("Mein Bruder reparierte das Auto.", ["Das Auto wurde {von meinem Bruder |}repariert."]),
    ("Der Koch bereitete ein leckeres Essen zu.", ["Ein leckeres Essen wurde {vom Koch |von dem Koch |}zubereitet."]),
    ("Wir besuchten das Museum.", ["Das Museum wurde {von uns |}besucht."]),
    ("Die Bäckerei verkaufte frische Brötchen.", ["Frische Brötchen wurden {von der Bäckerei |}verkauft."]),
]
PERFEKT = [
    ("Der Lehrer hat die Hausaufgaben korrigiert.", ["Die Hausaufgaben sind {vom Lehrer |von dem Lehrer |}korrigiert worden."]),
    ("Die Firma hat neue Maschinen gekauft.", ["Neue Maschinen sind {von der Firma |}gekauft worden."]),
    ("Sie hat den Brief an ihre Freundin geschickt.", ["Der Brief ist {von ihr |}an ihre Freundin geschickt worden.",
                                                       "Der Brief an ihre Freundin ist {von ihr |}geschickt worden."]),
    ("Die Kinder haben die Fenster geputzt.", ["Die Fenster sind {von den Kindern |}geputzt worden."]),
    ("Mein Vater hat das Fahrrad repariert.", ["Das Fahrrad ist {von meinem Vater |}repariert worden."]),
    ("Der Chef hat das Projekt genehmigt.", ["Das Projekt ist {vom Chef |von dem Chef |}genehmigt worden."]),
    ("Wir haben das Museum besucht.", ["Das Museum ist {von uns |}besucht worden."]),
    ("Die Bäckerei hat frisches Brot verkauft.", ["Frisches Brot ist {von der Bäckerei |}verkauft worden."]),
]
PLUSQUAM = [
    ("Der Lehrer hatte die Hausaufgaben korrigiert.", ["Die Hausaufgaben waren {vom Lehrer |von dem Lehrer |}korrigiert worden."]),
    ("Die Firma hatte neue Produkte entwickelt.", ["Neue Produkte waren {von der Firma |}entwickelt worden."]),
    ("Sie hatte den Brief an ihre Freundin geschickt.", ["Der Brief war {von ihr |}an ihre Freundin geschickt worden.",
                                                         "Der Brief an ihre Freundin war {von ihr |}geschickt worden."]),
    ("Die Kinder hatten die Fenster geputzt.", ["Die Fenster waren {von den Kindern |}geputzt worden."]),
    ("Mein Vater hatte das Fahrrad repariert.", ["Das Fahrrad war {von meinem Vater |}repariert worden."]),
    ("Der Chef hatte das Projekt genehmigt.", ["Das Projekt war {vom Chef |von dem Chef |}genehmigt worden."]),
    ("Wir hatten das Museum besucht.", ["Das Museum war {von uns |}besucht worden."]),
    ("Die Bäckerei hatte frisches Brot verkauft.", ["Frisches Brot war {von der Bäckerei |}verkauft worden."]),
]
FUTUR1 = [
    ("fertiggestellt / Das neue Stadion / nächstes Jahr / werden / .", ["Das neue Stadion wird nächstes Jahr fertiggestellt werden."]),
    ("in unserer Stadt / gebaut / Ein neues Einkaufszentrum / werden / .", ["Ein neues Einkaufszentrum wird in unserer Stadt gebaut werden."]),
    ("von einem bekannten Künstler / Das Bild / ausgestellt / wird / .", ["Das Bild wird von einem bekannten Künstler ausgestellt werden."]),
    ("die Hausaufgaben / bis morgen / erledigt / werden / .", ["Die Hausaufgaben werden bis morgen erledigt werden."]),
    ("nächstes Semester / angeboten / Ein neuer Kurs / wird / .", ["Ein neuer Kurs wird nächstes Semester angeboten werden."]),
    ("von vielen Touristen / besucht / Die Altstadt / werden / .", ["Die Altstadt wird von vielen Touristen besucht werden."]),
    ("am Montag / repariert / Mein Fahrrad / wird / .", ["Mein Fahrrad wird am Montag repariert werden."]),
    ("im Internet / veröffentlicht / Der Artikel / wird / .", ["Der Artikel wird im Internet veröffentlicht werden."]),
]
FUTUR2 = [
    ("bis nächstes Jahr / fertiggestellt / Das neue Krankenhaus / sein / wird / .", ["Das neue Krankenhaus wird bis nächstes Jahr fertiggestellt worden sein."]),
    ("in unserer Stadt / eröffnet / Das neue Einkaufszentrum / sein / wird / .", ["Das neue Einkaufszentrum wird in unserer Stadt eröffnet worden sein."]),
    ("bis morgen / abgeschlossen / Die Hausaufgaben / sein / werden / .", ["Die Hausaufgaben werden bis morgen abgeschlossen worden sein."]),
    ("von einem bekannten Autor / geschrieben / Das Buch / sein / wird / .", ["Das Buch wird von einem bekannten Autor geschrieben worden sein."]),
    ("bis nächstes Semester / beendet / Der Kurs / sein / wird / .", ["Der Kurs wird bis nächstes Semester beendet worden sein."]),
    ("von vielen Touristen / besucht / Die Altstadt / sein / wird / .", ["Die Altstadt wird von vielen Touristen besucht worden sein."]),
    ("bis Montag / repariert / Mein Fahrrad / sein / wird / .", ["Mein Fahrrad wird bis Montag repariert worden sein."]),
    ("bis morgen Abend / veröffentlicht / Der Bericht / sein / wird / .", ["Der Bericht wird bis morgen Abend veröffentlicht worden sein."]),
]
FUTUR_NOTE = "Futur I im Passiv braucht „werden“ zweimal (wird … werden); die Wortliste im Buch nennt es nur einmal."


def _set(title, rows, label, instruction, page):
    return exercise(title, [transform(n, src, pats, label) for n, (src, pats) in enumerate(rows, start=1)], f"{instruction} (Buch S. {page})")


GRAMMATIK_SETS = [
    _set("Aufgabe 1: Aktiv → Passiv (Präsens)", PRAESENS, "Passiv (Präsens)",
         "Wandeln Sie die folgenden Sätze vom Aktiv (Präsens) ins Passiv um. Die Angabe „von …“ ist freiwillig.", 64),
    _set("Aufgabe 2: Aktiv → Passiv (Präteritum)", PRAETERITUM, "Passiv (Präteritum)",
         "Wandeln Sie die folgenden Sätze vom Aktiv (Präteritum) ins Passiv um. Die Angabe „von …“ ist freiwillig.", 65),
    _set("Aufgabe 3: Aktiv → Passiv (Perfekt)", PERFEKT, "Passiv (Perfekt)",
         "Wandeln Sie die folgenden Sätze vom Aktiv (Perfekt) ins Passiv um. Die Angabe „von …“ ist freiwillig.", 66),
    _set("Aufgabe 4: Aktiv → Passiv (Plusquamperfekt)", PLUSQUAM, "Passiv (Plusquamperfekt)",
         "Wandeln Sie die folgenden Sätze vom Aktiv (Plusquamperfekt) ins Passiv um. Die Angabe „von …“ ist freiwillig.", 67),
    _set("Aufgabe 5: Passiv Futur I — Wortstellung", FUTUR1, "Satz im Passiv (Futur I)",
         "Bringen Sie die Wörter in die richtige Reihenfolge, um korrekte Sätze im Passiv (Futur I) zu bilden. " + FUTUR_NOTE, 68),
    _set("Aufgabe 6: Passiv Futur II — Wortstellung", FUTUR2, "Satz im Passiv (Futur II)",
         "Bringen Sie die Wörter in die richtige Reihenfolge, um korrekte Sätze im Passiv (Futur II) zu bilden.", 69),
]

# ---------- Lesen ----------
HAMBURG = [
    ("Letzten Freitag [[1]] (müssen) ich zu einer Konferenz nach Hamburg fahren. Da ich in Österreich, in Graz, wohne, habe ich mich [[2]] "
     "(entscheiden), nach dem Ende der Konferenz nicht gleich nach Hause zu fliegen. Ich [[3]] (wollen) das Wochenende in Hamburg verbringen und die "
     "Stadt entdecken.", {"1": ["musste"], "2": ["entschieden"], "3": ["wollte"]}),
    ("Samstagmorgen habe ich an einer Tour durch den Alten Botanischen Garten [[4]] (teilnehmen). Dieser Garten ist eine kleine Oase in der "
     "Stadtmitte. Ich studiere Biologie, deshalb interessiere ich mich vor allem für Pflanzen und fotografiere sie gern. Ich habe dort einige schöne "
     "Fotos [[5]] (machen).", {"4": ["teilgenommen"], "5": ["gemacht"]}),
    ("Danach bin ich in ein Café [[6]] (gehen), das mir der Rezeptionist im Hotel [[7]] (empfehlen) hat. Dort habe ich zufällig eine alte "
     "Schulfreundin [[8]] (treffen)! Das [[9]] (sein) eine Überraschung! Ich [[10]] (haben) keine Ahnung, dass sie jetzt in Hamburg wohnt.",
     {"6": ["gegangen"], "7": ["empfohlen"], "8": ["getroffen"], "9": ["war"], "10": ["hatte"]}),
    ("Sie studiert dort Sprachwissenschaft. Sie hat mir ihren Freund [[11]] (vorstellen), der an der Uni arbeitet. Wir haben uns ein bisschen "
     "[[12]] (unterhalten).", {"11": ["vorgestellt"], "12": ["unterhalten"]}),
    ("Ich habe dann noch das Johannes-Brahms-Museum [[13]] (besichtigen) und bin auf den Spuren des berühmten Komponisten durch Hamburg [[14]] "
     "(laufen). Dazu habe ich eine App aus dem Internet [[15]] (herunterladen), die mich durch die Stadt [[16]] (führen) hat. Ich [[17]] (finden) "
     "das sehr interessant.", {"13": ["besichtigt"], "14": ["gelaufen"], "15": ["heruntergeladen"], "16": ["geführt"], "17": ["fand"]}),
    ("Am Abend habe ich meine Schulfreundin und ihren Freund [[18]] (wiedersehen). Wir haben etwas [[19]] (essen) und ein Glas Wein [[20]] "
     "(trinken). Der Weg zum Hotel hat etwas länger [[21]] (dauern) als geplant, ich bin leider in den falschen Bus [[22]] (einsteigen). Dadurch "
     "habe ich Hamburg auch bei Nacht [[23]] (kennenlernen) und das war eigentlich ganz schön.",
     {"18": ["wiedergesehen"], "19": ["gegessen"], "20": ["getrunken"], "21": ["gedauert"], "22": ["eingestiegen"], "23": ["kennengelernt"]}),
]
LESEN_1 = [gap(f"Ergänzen Sie die Verben im Präteritum oder im Partizip Perfekt ({n}).", text, gaps, points=len(gaps),
               explanation="Lösung (VIZU, nach der Grammatik): " + ", ".join(f"{k}. {v[0]}" for k, v in gaps.items()))
           for n, (text, gaps) in enumerate(HAMBURG, start=1)]
HAMBURG_TEXT = "\n\n".join(t for t, _ in HAMBURG)
for _k in range(1, 24):
    HAMBURG_TEXT = HAMBURG_TEXT.replace(f"[[{_k}]]", "…………")

GRUEN = (
    "Von den 72 Städten über 100 000 Einwohner, die es in Deutschland gibt, hatten viele gern ein „grünes“ Image. Sie loben ihre Grünflächen und die "
    "damit verbundene gute Lebensqualität ihrer Bürger. Allein in Berlin gibt es 2 500 öffentliche Gärten und Parks und die meisten Berliner denken, "
    "ihre Stadt ist die „Grünste Stadt Deutschlands“. Auch die Städte Hannover und Halle an der Saale werben mit diesem Titel.\n\n"
    "Wie es mit der Vegetation in den Städten wirklich aussieht, zeigen jetzt Satellitenfotos aus dem Weltall. Die Zeitung Berliner Morgenpost hat "
    "185 dieser Fotos ausgewertet und die Grünflächen in den Städten gemessen und verglichen. Diese Ergebnisse haben nicht nur die Berliner "
    "überrascht, denn Berlin landet im Vergleich der 14 Städte mit mehr als 500 000 Einwohnern nur auf Platz 8, hinter Hannover (Rang 7) und vor "
    "Köln (Rang 9).\n\n"
    "Spitzenreiter ist Hamburg mit 71 Prozent grünen Flächen, gefolgt von Dortmund mit rund 70 Prozent. Für die meisten Stadtbewohner spielen "
    "öffentliche Grünflächen wie Stadtparks oder Wiesen eine immer größere Rolle. Grünanlagen dienen zur Erholung der Menschen und sie sind gut für "
    "das Stadtklima. Bäume und Pflanzen nehmen Schadstoffe auf und sorgen auf diese Weise für saubere Luft. Sie wirken außerdem bei hohen "
    "Temperaturen abkühlend und helfen, den Straßenlärm zu reduzieren.\n\n"
    "Die grünsten Großstädte (ab 500 000 Einwohner), Stand 2011: 1. Hamburg 71,4 % · 2. Dortmund 70,7 % · 3. Stuttgart 69,9 % · 4. Dresden 69,4 % · "
    "5. Bremen 68,2 % · 6. Essen 68 % · 7. Hannover 65,2 % · 8. Berlin 59,0 % · 9. Köln 58,4 % · 10. Frankfurt/Main 58,2 %")
LESEN_2 = [
    tf("In Berlin gibt es 2 500 öffentliche Gärten und Parks.", True, "„Allein in Berlin gibt es 2 500 öffentliche Gärten und Parks …“"),
    tf("Berlin ist die grünste Stadt Deutschlands.", False, "Das denken nur die meisten Berliner — „Spitzenreiter ist Hamburg …“; Berlin liegt auf Platz 8."),
    tf("Die Zeitung Berliner Morgenpost hat 185 Satellitenfotos ausgewertet.", True, "„Die Zeitung Berliner Morgenpost hat 185 dieser Fotos ausgewertet …“"),
    tf("Berlin liegt im Vergleich der 14 Städte auf Platz 7.", False, "„… nur auf Platz 8, hinter Hannover (Rang 7) …“"),
    tf("Hamburg hat den höchsten Anteil an Grünflächen.", True, "„Spitzenreiter ist Hamburg mit 71 Prozent grünen Flächen …“"),
    tf("Grünanlagen helfen, die Luft sauber zu halten und den Lärm zu verringern.", True,
       "„… sorgen auf diese Weise für saubere Luft … und helfen, den Straßenlärm zu reduzieren.“"),
]

# ---------- Hören ----------
W1 = ["Land", "müde", "Wein", "Hund", "Tierhaarallergie", "Hühner", "Parks", "allein"]
D1 = (
    "Karla: Willst du denn dein ganzes Leben in Städten verbringen? Du musst doch auch mal eine andere Erfahrung machen!\n"
    "Kurt: Bitte, Karla, was soll ich denn auf dem [[1]]? Alle Wege sind weit, ob du ins Kino gehen oder vielleicht mal ein Theater oder Konzert "
    "besuchen willst! Und wann würden wir dann noch unsere Freunde sehen und mit ihnen ausgehen?\n"
    "Karla: Das ist doch kein Argument. Wann gehen wir denn schon abends weg? Dazu sind wir doch immer viel zu [[2]]!\n"
    "Kurt: Aber wir könnten, wenn wir wollten!\n"
    "Karla: Ja, aber was meinst du, wie erholsam es wäre, abends einfach bei einem Glas [[3]] in unserem Garten zu sitzen oder noch einen "
    "Spaziergang zu machen. Wir könnten einen [[4]] haben und eine Katze und …\n"
    "Kurt: Meine Liebe, vergiss bitte nicht, dass ich eine [[5]] habe.\n"
    "Karla: Ja, ja, ist schon gut … Also kein Hund. Vielleicht [[6]]!\n"
    "Kurt: Was hast du denn? Hier gibt es schließlich auch [[7]] zum Spazierengehen!\n"
    "Karla: Ja, mit Unmengen von anderen Leuten! Wo du auch bist, nie bist du [[8]]!")
K1 = dict(zip([str(i) for i in range(1, 9)], W1))
W2 = ["Komposthaufen", "Urlaub", "Nachbarn", "Miete", "shoppen", "Jeans", "Garten", "Zivilisation"]
D2 = (
    "Kurt: Möglicherweise fühlst du dich auf dem Land sehr schnell zu allein …\n"
    "Karla: Und dann die Ruhe! Hier hat man nachts das Gefühl, als würde einem die Straßenbahn über den Bettdecke fahren! Und so ein Häuschen auf dem "
    "Land, wo du nur den Wind in den Bäumen rauschen hörst …\n"
    "Kurt: Karla, du hast vielleicht romantische Vorstellungen! Den Wind hörst du heute nur noch mitten im Wald in den Bäumen rauschen. Und, bei aller "
    "Liebe, ich ziehe nicht mit dir mitten in den Wald! Ein bisschen [[1]] hätte ich schon gerne!\n"
    "Karla: Das will ich ja auch. Und es sollten natürlich ein paar Geschäfte in der Nähe sein. Aber ich würde auch gern selbst Gemüse im [[2]] anbauen! "
    "Und unseren Biomüll könnte ich auf einen [[3]] werfen, und daraus wird dann wieder Erde.\n"
    "Kurt: Hast du eigentlich eine Ahnung, wie viel Zeit so ein Garten braucht?\nKarla: Klar! Und davon träume ich seit Jahren!\n"
    "Kurt: Und was machst du, wenn wir in [[4]] fahren? Deine Pflanzen vertrocknen lassen?\n"
    "Karla: Da gibt es doch bestimmt nette [[5]], die in dieser Zeit den Garten gießen.\n"
    "Kurt: Schau doch, jetzt sind wir in einer Viertelstunde im Büro. Wenn wir rausziehen aufs Land, brauchen wir mindestens eine Stunde!\n"
    "Karla: Aber dafür zahlen wir viel weniger [[6]]. Und wenn wir unsere Freunde sehen wollen, laden wir sie einfach übers Wochenende zu uns ein.\n"
    "Kurt: Und all die Einkaufsmöglichkeiten hier? Du bist doch diejenige, die so gern [[7]] geht!\n"
    "Karla: Da siehst du mal, wie sparsam wir leben werden! Keine tolle Boutique mehr. Dann bin ich halt leider nicht mehr so schick gekleidet.\n"
    "Kurt: Oh, ich seh' dich schon nur noch in [[8]] und alten Pullis rumlaufen, mit Erde unter den Fingernägeln.")
K2 = {"1": "Zivilisation", "2": "Garten", "3": "Komposthaufen", "4": "Urlaub", "5": "Nachbarn", "6": "Miete", "7": "shoppen", "8": "Jeans"}
HOEREN = [
    gap("Aufgabe 1: Hören Sie den Dialog und ergänzen Sie die passenden Wörter (1–8).", D1, {k: {"accepted": [v], "options": W1} for k, v in K1.items()},
        points=8, explanation="Lösung (VIZU, nach dem Kontext): " + ", ".join(f"{k}. {v}" for k, v in K1.items())),
    gap("Aufgabe 2: Hören Sie den Dialog und ergänzen Sie die passenden Wörter (1–8).", D2, {k: {"accepted": [v], "options": W2} for k, v in K2.items()},
        points=8, explanation="Lösung (VIZU, nach dem Kontext): " + ", ".join(f"{k}. {v}" for k, v in K2.items())),
]

# ---------- Schreiben / Sprechen ----------
HAYTAM = (
    "Von: Haytam · An: Mein Freund / Meine Freundin · Betreff: Party\n\nLieber Haytam\nWie geht's es dir? Hoffentlich geht es dir jetzt besser. Mir "
    "geht es zurzeit super Schade, dass du nicht dabei warst eigentlich haben wir einen unvergesslichen Abend mit unserem freundkreis verbracht.\n"
    "Zuerst haben wir Musik gehört dann haben wir viel getanzt, zum Schluss haben wir einen leckeren Kuchen gegessen, die meine Mutter für uns "
    "gebacken hat und wir Orangeat getränkt\nIch habe viele Geschenk bekommene aber Abdo hat mir eine Gitarre geschenkt, dieses hat mir besonders "
    "gefallen, weil ich für Musik sehr interessier wie Ware es, wenn wir uns zusammen morgen nach der schule bei mir zu haus treffen, so kann ich "
    "dir alle Geschenke zeigen.\nLas von dir schnell zu hören\nLiebe Grüße")
MUSTER_INTERNET = (
    "Vorteile und Nachteile des Internets\nDas Thema „Vorteile und Nachteile des Internets“ finde ich sehr interessant. Deshalb möchte ich meine Meinung "
    "dazu schreiben.\nMeiner Meinung nach hat das Internet sowohl Vorteile als auch Nachteile. Einerseits können wir schnell Informationen finden, "
    "online lernen und mit Familie oder Freunden in Kontakt bleiben. Außerdem erleichtert das Internet den Alltag, weil man viele Dinge bequem von zu "
    "Hause aus erledigen kann.\nAndererseits verbringen viele Menschen zu viel Zeit im Internet. Außerdem gibt es Risiken wie Betrug oder "
    "Datendiebstahl. Deshalb sollte man vorsichtig sein und persönliche Daten nicht überall eingeben.\nInsgesamt ist das Internet sehr nützlich, "
    "wenn man es verantwortungsvoll und bewusst nutzt.")
MUSTER_KONZERT = (
    "Lisa: Hast du Lust, morgen Abend ein Konzert zu besuchen?\nMax: Ja, gern! Wann genau findet es statt?\n"
    "Lisa: Morgen gibt es viele Konzerte. Die meisten beginnen um 20 Uhr. Wir könnten uns um 18 Uhr treffen und etwas essen.\n"
    "Max: Gute Idee! Welche Musik möchtest du hören?\nLisa: Ich interessiere mich für Jazz. Es gibt ein tolles Jazz-Konzert im Stadttheater.\n"
    "Max: Perfekt! Wo können wir die Eintrittskarten kaufen?\nLisa: Wir können die Tickets online kaufen, das ist billiger. Alternativ können wir sie "
    "auch an der Abendkasse holen.\nMax: Okay, dann kaufen wir sie online. Und was ziehen wir an?\n"
    "Lisa: Ich denke, wir sollten schicke, aber bequeme Kleidung tragen.\nMax: Einverstanden! Dann sehen wir uns morgen um 18 Uhr.\n"
    "Lisa: Super! Ich freue mich schon!")
MUSTER_LAND = (
    "Guten Tag zusammen. Heute möchte ich über das Thema „Das Leben auf dem Land oder in der Stadt“ sprechen.\nIch bin in einer Stadt aufgewachsen und "
    "lebe auch heute dort. Deshalb kenne ich das Stadtleben gut. Trotzdem besuche ich manchmal meine Verwandten auf dem Land. Dort ist es ruhig und "
    "die Natur gefällt mir sehr.\nDas Leben in der Stadt hat viele Vorteile. Es gibt gute Schulen, Universitäten, Krankenhäuser und viele "
    "Einkaufsmöglichkeiten. Außerdem fahren Busse und Bahnen regelmäßig. Allerdings gibt es auch Nachteile, zum Beispiel viel Verkehr, Lärm und hohe "
    "Lebenshaltungskosten.\nAuf dem Land ist die Luft sauber und das Leben ruhiger. Man hat mehr Platz und kann sich besser entspannen. Allerdings "
    "gibt es dort weniger öffentliche Verkehrsmittel und nicht so viele Freizeitmöglichkeiten.\nMeiner Meinung nach ist das Leben in der Stadt "
    "praktischer. Trotzdem wäre es schön, ein kleines Haus auf dem Land zu haben, um sich am Wochenende zu erholen.\nVielen Dank für Ihre "
    "Aufmerksamkeit. Haben Sie Fragen?")
MUSTER_STADT = (
    "Wenn es möglich ist, würde ich in Berlin wohnen. Berlin ist eine moderne und kreative Stadt. Hier gibt es viele kulturelle Angebote, Museen, "
    "Theater und Konzerte. Die Stadt ist international und man kann Menschen aus der ganzen Welt treffen. Außerdem gibt es viele Grünflächen und "
    "Parks, die zum Entspannen einladen. Die Verkehrsanbindung ist sehr gut, und man kommt schnell überall hin. Deshalb wäre Berlin für mich die "
    "perfekte Stadt zum Leben.")

STADTLEBEN = [
    ("mitten im Geschehen sein", "im Zentrum von wichtigen Ereignissen oder Aktivitäten sein", "voqealarning markazida bo'lmoq"),
    ("im Stau stehen", "mit dem Auto nicht vorankommen, weil viel Verkehr ist", "tirbandlikda qolmoq"),
    ("keine Zeit haben", "sehr beschäftigt sein", "vaqt topa olmaslik"),
    ("Kontakte knüpfen", "neue Leute kennenlernen und Verbindungen aufbauen", "aloqalar o'rnatmoq"),
    ("einkaufen gehen", "in Geschäfte gehen, um Dinge zu kaufen", "xarid qilishga chiqmoq"),
    ("öffentliche Verkehrsmittel nutzen", "Bus, Bahn usw. benutzen", "jamoat transportidan foydalanmoq"),
    ("Kulturangebote nutzen", "z. B. Theater, Kino, Museum besuchen", "madaniy tadbirlardan foydalanmoq"),
    ("zur Miete wohnen", "in einer Wohnung leben, die man nicht gekauft hat", "ijarada yashamoq"),
    ("Hochhäuser prägen das Stadtbild", "viele hohe Gebäude bestimmen das Aussehen einer Stadt", "baland binolar shaharga xos ko'rinish beradi"),
    ("in der Menge untergehen", "in einer großen Menschenmenge nicht auffallen", "odamlar orasida yo'qolib ketmoq"),
]
WORDS = [{"word": w, "translation": uz, "example": f"Bedeutung: {de}", "group": "Stadtleben"} for w, de, uz in STADTLEBEN]

UEBUNGEN = [
    exercise("Welche Passivform ist richtig? (Beispiele aus dem Buch)", [
        example_gap("Die Texte ___ jeden Tag korrigiert.", "werden", ["werden", "wurden", "sind"], "Präsens: werden + Partizip II."),
        example_gap("Die Wohnung ___ gestern gereinigt.", "wurde", ["wurde", "wird", "ist"], "Präteritum: wurde + Partizip II."),
        example_gap("Die Aufgaben sind schon erledigt ___.", "worden", ["worden", "geworden", "werden"], "Perfekt: sind + Partizip II + worden."),
        example_gap("Die Bücher ___ bereits gelesen worden.", "waren", ["waren", "wurden", "sind"], "Plusquamperfekt: waren … worden."),
        example_gap("Das Projekt wird nächste Woche beendet ___.", "werden", ["werden", "worden", "wurde"], "Futur I: wird … werden."),
        example_gap("Bis 2030 wird die Brücke gebaut ___.", "worden sein", ["worden sein", "werden", "geworden"], "Futur II: wird … worden sein."),
    ], "Wählen Sie die richtige Form (Tabelle im Buch, S. 63).", source="vizu"),
]

ABSCHLUSSTEST = [
    mc("Wie bildet man das Passiv Präteritum?", ["wurde + Partizip II", "werden + Partizip II", "ist + Partizip II + worden"], "A", "Buch S. 63."),
    mc("Wie bildet man das Passiv Futur II?", ["wird + Partizip II + worden sein", "wird + Partizip II + werden", "war + Partizip II + worden"], "A", "Buch S. 63."),
    example_gap("Neue Autos ___ von der Firma produziert.", "werden", ["werden", "wird", "wurden"], "Präsens Plural."),
    example_gap("Das Museum ist von uns besucht ___.", "worden", ["worden", "geworden", "werden"]),
    example_gap("Mein Fahrrad wird am Montag repariert ___.", "werden", ["werden", "worden", "sein"]),
    example_gap("Ich habe dort einige schöne Fotos ___.", "gemacht", ["gemacht", "machte", "machen"], "Lesen Aufgabe 1: Partizip Perfekt."),
    example_gap("Das ___ eine Überraschung!", "war", ["war", "ist gewesen", "wurde"], "Lesen Aufgabe 1: Präteritum von sein."),
    mc("Welche Stadt hat laut Text den höchsten Anteil an Grünflächen?", ["Hamburg", "Berlin", "Dortmund"], "A", "Lesen Aufgabe 2."),
    mc("„im Stau stehen“ bedeutet …", ["mit dem Auto nicht vorankommen, weil viel Verkehr ist", "sehr beschäftigt sein",
                                         "in einer Wohnung leben, die man nicht gekauft hat"], "A", "Wortschatz Stadtleben."),
    mc("„zur Miete wohnen“ — o'zbekchasi?", ["ijarada yashamoq", "aloqalar o'rnatmoq", "xarid qilishga chiqmoq"], "A", "Wortschatz Stadtleben."),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 4. Unterricht", source="vizu", page=61, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: In welcher bekannten Stadt würden Sie wohnen?", page=62,
             prompt="Wenn es möglich ist, in welcher bekannten Stadt würden Sie wohnen? Sprechen Sie über eine bekannte Stadt, in der Sie gerne wohnen "
                    "würden. Dauer: ca. 2–3 Minuten. Ziel: freies Sprechen über Ideen, Vorteile und persönliche Vorlieben.",
             questions=["Berlin?", "München?", "Köln?"], min_duration=60, max_duration=180, metadata={"book_samples": [MUSTER_STADT]}),
        base(L, "grammatik", 1, "Grammatik: Passiv-Strukturen", page="63-69", rules=[{"title": "Passiv-Strukturen", "html": GRAMMAR_HTML}],
             exercises=GRAMMATIK_SETS,
             metadata={"note": "Lösungen der Umformungen von VIZU (eindeutig nach der Grammatik; „von …“ freiwillig)."}),
        base(L, "lesen", 1, "Lesen Aufgabe 1: Ein Wochenende in Hamburg", page=70,
             instruction="Lesen Sie den Text und ergänzen Sie die Verben im Präteritum oder im Partizip Perfekt.",
             passages=[{"title": "Hamburg — Blog", "text": HAMBURG_TEXT}], questions=LESEN_1, max_score=23,
             metadata=key_meta("vizu", "Verbformen von VIZU nach der Grammatik — bitte prüfen. Seitenkopf im Buch: „B2 4.Unterricht“.")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: Grüne Großstädte in Deutschland", page=71, instruction="Lesen Sie den Text und entscheiden Sie: Richtig oder Falsch?",
             passages=[{"title": "Grüne Großstädte in Deutschland", "text": GRUEN}], questions=LESEN_2, max_score=len(LESEN_2), metadata=key_meta("vizu")),
        base(L, "hoeren", 1, "Hören Aufgabe 1 + 2: Karla und Kurt — Stadt oder Land?", page="72-73", audio_file=AUDIO["vizu-b1-l04-hoeren-01"],
             instruction="Hören Sie den Dialog und ergänzen Sie die passenden Wörter. Sie hören den Text zweimal. Tipps: Hören Sie zuerst die ganze "
                         "Konversation. Achten Sie auf den Zusammenhang. Es gibt 8 Lücken.",
             questions=HOEREN, max_score=16,
             metadata=key_meta("vizu", "Lösung von VIZU nach dem Kontext (Wörterliste) — nach dem Anhören in Lösung bestätigen. "
                                       "Eine Audiodatei für Aufgabe 1 und 2.")),
        base(L, "schreiben", 1, "Schreiben Aufgabe 1: E-Mail — Antwort an Haytam", page=74, task_type="email",
             prompt="Sie haben diese E-Mail von Ihrem Freund Haytam bekommen. Schreiben Sie ihm eine E-Mail (ca. 80–100 Wörter) und antworten Sie auf "
                    "seine Nachricht.\n\n" + HAYTAM + "\n\nSchreiben Sie etwas zu den Punkten:\n1. Bedanken Sie sich für die Einladung und sagen Sie, "
                    "dass Sie gern kommen.\n2. Schreiben Sie, ob Sie auch ein Geschenk für Abdo mitbringen möchten.\n3. Fragen Sie, ob es noch etwas "
                    "Besonderes auf der Party gibt (Spiele, Fotos …).\n4. Schlagen Sie vor, wann und wo Sie sich treffen können.\n\nTipps: Schreiben "
                    "Sie freundlich und persönlich. Antworten Sie auf alle vier Punkte. Achten Sie auf die richtige Rechtschreibung und Grammatik.",
             audience="Ihr Freund Haytam (informell)", min_words=80, max_words=120, time_limit=25,
             metadata={"note": "Die E-Mail von Haytam ist im Buch mit Fehlern gedruckt — so übernommen. Keine Musterlösung im Buch."}),
        base(L, "schreiben", 2, "Schreiben Teil 2: Forumsbeitrag — Vorteile und Nachteile des Internets", page=75, task_type="opinion",
             prompt="Sie möchten einen Beitrag für ein Online-Forum schreiben. Lesen Sie den Text und schreiben Sie einen Beitrag (ca. 80–100 Wörter).\n\n"
                    "Schreiben Sie etwas zu den Punkten:\n1. Nennen Sie Ihre Meinung zum Thema „Vorteile und Nachteile des Internets“.\n"
                    "2. Beschreiben Sie, wie Sie das Internet im Alltag nutzen.\n3. Geben Sie einen Rat, wie man das Internet sicher und sinnvoll benutzen kann.",
             audience="Online-Forum", min_words=80, max_words=120, time_limit=25,
             ai_instructions="Musterbeitrag aus dem Buch (Referenz):\n" + MUSTER_INTERNET, metadata={"musterloesung": MUSTER_INTERNET}),
        base(L, "sprechen", 1, "Sprechen Teil 1: Gespräch — Konzertbesuch planen", page=76, topic="Konzertbesuch",
             prompt="Sprechen Sie mit Ihrem Partner / Ihrer Partnerin über das Thema „Konzertbesuch“. Planen Sie gemeinsam einen Konzertbesuch. "
                    "Benutzen Sie die vier Punkte.",
             questions=["Wann? — Wann möchtet ihr das Konzert besuchen?", "Was für ein Konzert? — Welche Musik möchtet ihr hören? (Jazz oder Rock)",
                        "Wo Eintrittskarten kaufen? — Wo könnt ihr die Tickets kaufen?", "Was anziehen? — Was zieht ihr zum Konzert an?"],
             response_type="dialog", min_duration=60, max_duration=180, sample_answer=MUSTER_KONZERT,
             speech_goal="Gemeinsam einen Konzertbesuch planen: Zeit, Musik, Tickets, Kleidung.",
             keywords=["Hast du Lust", "Wir könnten", "Gute Idee", "Einverstanden", "Ich freue mich"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Präsentation — Das Leben auf dem Land oder in der Stadt", page=77,
             topic="Das Leben auf dem Land oder in der Stadt",
             prompt="Halten Sie eine Präsentation zum Thema „Das Leben auf dem Land oder in der Stadt“.",
             questions=["Eigene Erfahrungen", "Vorteile und Nachteile", "Eigene Meinung"],
             response_type="monolog", preparation_time=300, min_duration=90, max_duration=180, sample_answer=MUSTER_LAND,
             speech_goal="Präsentation: eigene Erfahrungen, Vor- und Nachteile von Stadt und Land, eigene Meinung.",
             keywords=["Heute möchte ich über", "Vorteile", "Allerdings", "Meiner Meinung nach", "Vielen Dank für Ihre Aufmerksamkeit"]),
        base(L, "wortschatz", 1, "Wortschatz: Stadtleben", page=78, words=WORDS, exercises=meaning_sets(WORDS), auto_practice=False,
             metadata={"note": "Buch: Redewendung, Bedeutung (auf Deutsch) und Übersetzung (usbekisch) — die Bedeutung steht beim Beispiel."}),
        base(L, "schreiben", 3, "Wortschatz-Aufgabe: Stadtleben — eigene Sätze", page=78, task_type="other",
             prompt="Hier sind 10 wichtige Redewendungen zum Thema „Stadtleben“. Lesen Sie die Redewendungen, ihre Bedeutungen und schreiben Sie eigene "
                    "Sätze.\n\n" + "\n".join(f"{i}. {w} — {de}" for i, (w, de, _) in enumerate(STADTLEBEN, start=1)),
             min_words=40, max_words=300, time_limit=20, metadata={"note": "Ish varag'i (Beispielsatz — Ihr eigener Satz) — o'qituvchi tekshiradi."}),
        base(L, "uebungen", 1, "Übungen: B1 4. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 4. Unterricht", source="vizu",
             instruction="Abschlusstest zu Passiv-Strukturen und Stadtleben (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 4. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
