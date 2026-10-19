"""B1 2. Unterricht — Meine Ziele für die Zukunft — Grammatik: Finalsätze (book pp. 25-41).

Book: title p.25, Frage des Themas (Was planen Sie in der Zukunft?) p.26,
Finalsätze damit / um … zu p.27, Grammatik Aufgabe 1-3 (Sätze weiterschreiben,
open) pp.28-30, Lesen Aufgabe 1 (Zusammenfassung: Nomen ergänzen, word bank)
p.31, Lesen Aufgabe 2 (Ich werde Architekt) p.32, Lesen Aufgabe 3 (Ich werde
Ärztin) p.33, Hören Aufgabe 1 + 2 (Martha und Max, word banks) pp.34-35, Hören
Aufgabe 3 (Conrad und Ute, word bank; the page header says "1. Unterricht",
the audio file is "2.Unterricht Aufgabe 3") p.36, Schreiben Teil 1 (informeller
Brief, Muster) p.37, Schreiben Teil 2 (Beitrag, Muster) p.38, Sprechen Teil 1
(gemeinsam planen, Muster-Dialog) p.39, Sprechen Teil 2 (Präsentation, Muster)
p.40, Wichtige Redewendungen für Modul 2 p.41.

Keys: no key printed in this lesson. Lesen 1-3 and the word-bank Hören tasks
are decided by VIZU (the word fitting the gap / the quoted sentence) and held
for verification in Lösung; Hören 3 gap 2 fits "Arbeit" and "Stelle" — both
accepted until an admin has listened. The book's Muster texts are kept as
printed (they contain spelling mistakes) — used only as the AI reference."""

from . import base, completion, example_gap, exercise, gap, intro_html, key_meta, meaning_sets, mc, redewendungen, summary_html, tf

L = 2
LESSON_TITLE = "Meine Ziele für die Zukunft"
LESSON_DESCRIPTION = "Thema: Meine Ziele für die Zukunft · Grammatik: Finalsätze (damit, um … zu)"
AUDIO = {"vizu-b1-l02-hoeren-01": "2.Unterricht Aufgabe 1-2.m4a", "vizu-b1-l02-hoeren-02": "2.Unterricht Aufgabe 3.m4a"}

EINFUEHRUNG_HTML = intro_html(
    2, "Meine Ziele für die Zukunft", "Finalsätze (damit, um … zu)",
    ["maqsadni aytish: damit (har xil ega) va um … zu (bir xil ega);",
     "kelajak rejalari, kasb va ta'lim haqida gapirish;",
     "muhim iboralar: eine Entscheidung treffen, in Betracht ziehen, Maßnahmen ergreifen …"],
    ["kelajakdagi rejalaringiz va maqsadlaringiz haqida gapirasiz;",
     "kasb tanlash haqidagi matnlarni tushunasiz;",
     "dialoglarni tinglab, tushib qolgan so'zlarni to'ldirasiz;",
     "do'stingizga norasmiy xat va forumga qisqa maqola yozasiz;",
     "sherigingiz bilan dastur rejalashtirasiz va „Kinder oder Karriere“ mavzusida taqdimot qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(2, [
    "<strong>damit</strong>: verschiedene Subjekte — Hauptsatz + , damit + Subjekt + … + Verb (am Ende): Meine Eltern sparen Geld, damit ich studieren kann.",
    "<strong>um … zu</strong>: dasselbe Subjekt — Hauptsatz + , um + … + zu + Infinitiv: Er spart Geld, um ein Auto zu kaufen.",
    "<strong>Redewendungen:</strong> zum Ausdruck bringen, eine Entscheidung treffen, in Betracht ziehen, Einfluss nehmen auf, eine Rolle spielen, "
    "Maßnahmen ergreifen, Priorität haben, im Voraus planen, sich engagieren für, eine Herausforderung annehmen.",
])

GRAMMAR_HTML = (
    "<h3>Finalsätze — Ziel oder Zweck ausdrücken</h3>"
    "<table><thead><tr><th>1. DAMIT</th><th>2. UM … ZU</th></tr></thead><tbody>"
    "<tr><td><strong>Regel:</strong> „damit“ benutzt man, wenn die zwei Sätze <strong>verschiedene Subjekte</strong> haben.</td>"
    "<td><strong>Regel:</strong> „um … zu“ benutzt man, wenn beide Sätze <strong>dasselbe Subjekt</strong> haben.</td></tr>"
    "<tr><td><strong>Struktur:</strong> Hauptsatz + , damit + Subjekt + … + Verb<br>Das Verb steht am Ende.</td>"
    "<td><strong>Struktur:</strong> Hauptsatz + , um + … + zu + Infinitiv<br>Nach „zu“ kommt der Infinitiv.</td></tr>"
    "<tr><td>• Ich lerne Deutsch, damit ich in Deutschland arbeiten kann.<br>• Meine Eltern sparen Geld, damit ich studieren kann.<br>"
    "• Wir trainieren viel, damit wir gesund bleiben.<br>• Er erklärt alles langsam, damit die Schüler ihn verstehen können.</td>"
    "<td>• Ich lerne Deutsch, um in Deutschland zu arbeiten.<br>• Er spart Geld, um ein Auto zu kaufen.<br>"
    "• Wir üben jeden Tag, um die Prüfung zu bestehen.<br>• Sie geht früh schlafen, um fit zu bleiben.</td></tr></tbody></table>"
)

# ---------- Lesen ----------
NOMEN = ["Arbeitsplatz", "Berufsentscheidung", "Arbeit", "Verbrechen", "Personal", "Studien", "Dinge", "Ausbildung", "Arbeitsmarkt", "Fächern",
         "Fähigkeiten"]
ZUSAMMENFASSUNG_TEXT = (
    "Wenn man auf der Suche nach dem richtigen Beruf ist, muss man zwei [[1]] beachten. Erstens: Welche Interessen und [[2]] bringen die jungen "
    "Leute mit? Und zweitens: Welcher Beruf bietet gute Zukunftsaussichten und einen sicheren [[3]]?\n"
    "Grundlage für jede [[4]] sollten natürlich das Interesse und das Können sein. Aber auch über die Berufsperspektiven sollte man nachdenken. "
    "[[5]] zum Thema Berufe mit Zukunft haben ergeben, dass Fachkräfte mit einer [[6]] in den Bereichen Technik, Naturwissenschaften oder Mathematik "
    "beste Chancen auf dem [[7]] haben. Auch Ärzte oder Krankenschwestern bzw. Krankenpfleger werden benötigt.\n"
    "Im Bereich der Altenpflege gibt es schon jetzt zu wenig [[8]]. Polizisten und Anwälte werden ebenfalls immer [[9]] finden, denn das [[10]] "
    "stirbt leider nicht aus. Für Lehrer in den [[11]] Deutsch und Geschichte, für Übersetzer und für Verkäufer bestehen nicht so gute "
    "Zukunftsaussichten.")
ZUSAMMENFASSUNG_KEY = {"1": "Dinge", "2": "Fähigkeiten", "3": "Arbeitsplatz", "4": "Berufsentscheidung", "5": "Studien", "6": "Ausbildung",
                       "7": "Arbeitsmarkt", "8": "Personal", "9": "Arbeit", "10": "Verbrechen", "11": "Fächern"}
LESEN_1 = [gap(f"Ergänzen Sie in der Zusammenfassung die Nomen ({n}). Wörter: " + " • ".join(NOMEN), para,
               {g: [ZUSAMMENFASSUNG_KEY[g]] for g in ids}, points=len(ids),
               explanation="Lösung (VIZU): " + ", ".join(f"{g}. {ZUSAMMENFASSUNG_KEY[g]}" for g in ids))
           for n, (para, ids) in enumerate(zip(ZUSAMMENFASSUNG_TEXT.split("\n"), [["1", "2", "3"], ["4", "5", "6", "7"], ["8", "9", "10", "11"]]),
                                           start=1)]

TEXT_ARCHITEKT = (
    "Mein Traumberuf ist Architekt. Ich interessiere mich schon seit meiner Kindheit für Gebäude und Design. Deshalb möchte ich Architektur studieren, "
    "um moderne und schöne Häuser zu entwerfen.\n\nIch lerne jeden Tag Deutsch, damit ich später auch in Deutschland arbeiten kann. Außerdem "
    "verbessere ich meine Mathematikkenntnisse, um gute Lösungen für Bauprojekte zu finden.\n\nIch möchte kreativ sein und verantwortungsvoll "
    "arbeiten. Deshalb übe ich mit verschiedenen Computerprogrammen, damit ich professionelle Pläne erstellen kann.\n\nIn der Zukunft möchte ich "
    "Häuser bauen, damit sich die Menschen darin sicher und wohl fühlen.")
LESEN_2 = [
    tf("Der Autor möchte Lehrer werden.", False, "„Mein Traumberuf ist Architekt.“"),
    tf("Er studiert Architektur, um moderne Häuser zu entwerfen.", True, "„… möchte ich Architektur studieren, um moderne und schöne Häuser zu entwerfen.“"),
    tf("Er lernt Deutsch, damit er später in Deutschland arbeiten kann.", True, "„Ich lerne jeden Tag Deutsch, damit ich später auch in Deutschland arbeiten kann.“"),
    tf("Mathematik ist für ihn nicht wichtig.", False, "„Außerdem verbessere ich meine Mathematikkenntnisse, um gute Lösungen für Bauprojekte zu finden.“"),
    tf("Er möchte Häuser bauen, damit sich die Menschen wohl fühlen.", True,
       "„In der Zukunft möchte ich Häuser bauen, damit sich die Menschen darin sicher und wohl fühlen.“"),
]
TEXT_AERZTIN = (
    "Mein Traumberuf ist Ärztin. Ich möchte Medizin studieren, um kranken Menschen zu helfen.\n\nIch lerne fleißig Biologie und Chemie, damit ich "
    "später eine gute Ärztin werde. Außerdem verbessere ich meine Kommunikationsfähigkeiten, um gut mit den Patienten zu sprechen.\n\nIch arbeite "
    "regelmäßig im Krankenhaus als Praktikantin, damit ich mehr Erfahrung sammeln kann. Mein Ziel ist es, Menschen zu behandeln und ihr Leben zu "
    "verbessern.\n\nIn Zukunft möchte ich in einem modernen Krankenhaus arbeiten, damit ich vielen Menschen helfen kann.")
LESEN_3 = [
    tf("Die Autorin möchte Ärztin werden.", True, "„Mein Traumberuf ist Ärztin.“"),
    tf("Sie studiert Medizin, um kranken Menschen zu helfen.", True, "„Ich möchte Medizin studieren, um kranken Menschen zu helfen.“"),
    tf("Sie lernt keine Biologie.", False, "„Ich lerne fleißig Biologie und Chemie …“"),
    tf("Sie macht ein Praktikum im Krankenhaus.", True, "„Ich arbeite regelmäßig im Krankenhaus als Praktikantin …“"),
    tf("Sie möchte später vielen Menschen helfen.", True, "„… damit ich vielen Menschen helfen kann.“"),
]

# ---------- Hören ----------
W_1 = ["eingeladen", "Wochenende", "eifersüchtig", "Egoismus", "Freund", "Mountainbike-Touren"]
DIALOG_1 = (
    "Martha und Max sind schon seit zwei Jahren zusammen, aber sie leben nicht zusammen. Nun hat Martha Benjamin, einen guten Freund aus ihrer "
    "Studienzeit, wieder getroffen und möchte mit ihm am Wochenende zum Skifahren gehen.\n"
    "Martha: Du, ich denke, das wird richtig toll. Seine Eltern sind auf ihrer Hütte in den Bergen, und er fährt übers [[1]] zu ihnen. Ich finde das "
    "wahnsinnig nett von ihm, dass er mich dazu [[2]] hat!\nMax: …\nMartha: Max?\nMax: Hmm?\nMartha: Was ist denn? Was hast du denn?\n"
    "Max: Was ich habe? Du erzählst mir so einfach, dass du das Wochenende mit einem anderen Mann und seinen Eltern in den Bergen verbringst und "
    "fragst mich dann ganz unschuldig, was ich habe?\nMartha: Max, komm, du bist doch wohl nicht etwa [[3]]?\nMax: Natürlich nicht!\n"
    "Martha: Aber warum bist du dann so wütend?\n"
    "Max: Du kommst noch nicht einmal auf die Idee, dass du mich vielleicht fragen könntest, ob es mir recht ist! Du bist einfach das Wochenende "
    "nicht da, hast eine schöne Zeit mit einem anderen Mann und ich bin dir ganz egal! So was von [[4]] habe ich ja noch nie erlebt!\n"
    "Martha: Ach ja, und wenn du deine [[5]] planst, hast du mich da jemals gefragt?\nMax: Das ist ja was anderes, das mache ich mit meinen Freunden!\n"
    "Martha: Ich fahre auch mit einem [[6]] zum Skifahren!\nMax: Aber das ist ein Mann!")
KEY_1 = {"1": "Wochenende", "2": "eingeladen", "3": "eifersüchtig", "4": "Egoismus", "5": "Mountainbike-Touren", "6": "Freund"}
W_2 = ["vertrauen", "enttäuscht", "Ruhe", "liebe", "Problem", "Schwiegereltern"]
DIALOG_2 = (
    "Max: Vielleicht wären sie gern deine zukünftigen [[1]]?\n…\nMartha: … Aber ich muss schon zugeben, so ganz toll würde ich das auch nicht "
    "finden. Du musst mir halt [[2]].\nMax: Das tue ich ja, Martha. Aber dass du nicht vorher mit mir darüber redest und es mit mir besprichst, ob du "
    "die Einladung annehmen sollst oder nicht – das hat mich echt [[3]].\nMax: Vielleicht sollten wir noch eine Nacht darüber schlafen und morgen "
    "noch einmal darüber reden, in aller [[4]].\nMartha: Ich [[5]] dich doch!\nMax: Ich dich doch auch. Das ist ja das [[6]]!")
KEY_2 = {"1": "Schwiegereltern", "2": "vertrauen", "3": "enttäuscht", "4": "Ruhe", "5": "liebe", "6": "Problem"}
HOEREN_1 = [
    gap("Aufgabe 1: Hören Sie den Dialog und ergänzen Sie die Lücken (1–6) mit den passenden Wörtern.", DIALOG_1,
        {k: {"accepted": [v], "options": W_1} for k, v in KEY_1.items()}, points=6,
        explanation="Lösung (VIZU, nach dem Kontext): " + ", ".join(f"{k}. {v}" for k, v in KEY_1.items())),
    gap("Aufgabe 2: Hören Sie den Dialog und ergänzen Sie die Lücken (1–6) mit den passenden Wörtern.", DIALOG_2,
        {k: {"accepted": [v], "options": W_2} for k, v in KEY_2.items()}, points=6,
        explanation="Lösung (VIZU, nach dem Kontext): " + ", ".join(f"{k}. {v}" for k, v in KEY_2.items())),
]
W_3 = ["Arbeit", "Messe", "Nachteil", "Stelle", "Englischkurs", "Karrieremöglichkeiten", "Urlaubstage", "Schule", "Dienstreisen",
       "Fremdsprachenkenntnisse", "Besprechungen", "Meeting", "Präsentation"]
DIALOG_3_A = (
    "Conrad: Hallo Ute, wie geht's?\nUte: Danke, gut. Und dir?\nConrad: Auch gut. Ich habe viel zu tun. Was macht dein neuer Job?\n"
    "Ute: Ich bin mit meinem neuen Job sehr zufrieden, er ist sehr interessant. Ich verdiene mehr als bei meiner alten Stelle und habe auch bessere "
    "[[1]]. Außerdem ist die [[2]] viel abwechslungsreicher.\n"
    "Conrad: Ja, ich kann mich noch daran erinnern, dass du deinen alten Job ein bisschen langweilig fandst, oder?\n"
    "Ute: Ja, das stimmt. Der einzige [[3]] ist, dass ich jetzt weniger [[4]] habe. Aber ich muss viele [[5]] machen und die sind ja auch ein "
    "bisschen wie Urlaub.\n"
    "Conrad: Ich weiß nicht. Wenn ich auf [[6]] bin, renne ich von einem [[7]] zum nächsten und habe keine Zeit, die Stadt zu besichtigen.")
DIALOG_3_B = (
    "Ute: Na ja, mal sehen. Jedenfalls muss ich nächste Woche nach Hannover, um unsere Produkte auf einer [[8]] zu präsentieren. Die [[9]] ist auf "
    "Englisch, das ist auch neu für mich.\nConrad: Sprichst du denn so gut Englisch?\n"
    "Ute: Mein Englisch muss ich noch ein bisschen verbessern, aber die Firma bezahlt einen [[10]] für mich und eine Kollegin. Wie sind deine [[11]]?\n"
    "Conrad: Gut. Wir haben ja [[12]] auf Deutsch, Englisch oder Französisch.\nUte: Ach, Französisch, das muss ich auch noch lernen.\n"
    "Conrad: Das schaffst du schon. Du warst ja auch in der [[13]] immer sehr fleißig …")
KEY_3 = {"1": ["Karrieremöglichkeiten"], "2": ["Arbeit", "Stelle"], "3": ["Nachteil"], "4": ["Urlaubstage"], "5": ["Dienstreisen"],
         "6": ["Dienstreisen"], "7": ["Meeting"], "8": ["Messe"], "9": ["Präsentation"], "10": ["Englischkurs"], "11": ["Fremdsprachenkenntnisse"],
         "12": ["Besprechungen"], "13": ["Schule"]}
HOEREN_2 = [
    gap("Hören Sie den Text und ergänzen Sie die Lücken (1–7). Wörter: " + " • ".join(W_3), DIALOG_3_A, {k: KEY_3[k] for k in "1234567"},
        points=7, explanation="Lösung (VIZU, nach dem Kontext): " + ", ".join(f"{k}. {' / '.join(KEY_3[k])}" for k in "1234567")),
    gap("Hören Sie den Text und ergänzen Sie die Lücken (8–13). Wörter: " + " • ".join(W_3), DIALOG_3_B,
        {k: KEY_3[k] for k in ("8", "9", "10", "11", "12", "13")}, points=6,
        explanation="Lösung (VIZU, nach dem Kontext): " + ", ".join(f"{k}. {KEY_3[k][0]}" for k in ("8", "9", "10", "11", "12", "13"))),
]

# ---------- Schreiben / Sprechen ----------
MUSTER_BRIEF = (
    "Lieber Haytam\nWie geht's es dir? Hoffentlich ist alles Gut. Mir geht es zurzeit super\nGestern habe ich einen guten film im Kino gesehen, der "
    "Film heißt “Lupin”\nEr ist ein französischer Film, Der Film war sehr interessant und fantatisch besonders Musik, war wunderbar und harmoniert "
    "perfekt mit dem film\nder Film steht Assane Diop, der als Teenager eine schreckliche Erfahrung machen muss: Sein geliebter Vater wird eines "
    "Verbrechens bezichtigt, dass dieser Assanes Ansicht nach nie begangen hat. Kurz nach seiner Verhaftung stirb sein Vater im Gefängnis.\nWas hat "
    "mir am besten gefällt war, dass „Asani“ sein Leben der umschulde seinen Vater widmete hat das war so emotional\nWie wäre es, wenn wir am "
    "Freitagabend zusammen ins Kino gehen und diesen Film sehen, ich bin sicher, er wird dir gefallen\nLas von dir schnell zu hören\nLiebe Grüße")
MUSTER_BEITRAG = (
    "Das Thema Arbeit an Feiertagen und Sonntagen verbieten finde ich sehr interessant, daher möchte ich meine Meinung dazu äußern. Ich bin der "
    "Meinung, dass man Arbeit an Feiertagen und Sonntagen grundsätzlich verbieten sollte.\nHeutzutage leiden viele Mitarbeiter unter Stress, "
    "insbesondere wenn sie unter Zeitdruck arbeiten und viele Überstunden machen. Wenn man an Feiertagen und Sonntagen nicht arbeiten muss, kann man "
    "viele Aktivitäten wie Sport, Reisen, Lesen usw. machen. Außerdem kann man nicht nur auf ihre Familie aufpassen, sondern auch viele schöne "
    "Stunden mit ihren Freunden verbringen. Was daher hilft, Stress abzubauen und genannte Energie zu tanken, um eine neue Woche zu starten.\nAus "
    "dem schon genannten Gründen kann ich sagen, dass die Arbeit am Freitag und Sonntag verboten sollte.")
MUSTER_PLANEN = (
    "Kandidat 1: Hallo! Nächste Woche kommen drei deutsche Kollegen. — Kandidat 2: Hallo! Schön! Was möchten wir mit ihnen machen?\n"
    "Kandidat 1: Wir können ihnen die Altstadt zeigen. Dort gibt es viele schöne Gebäude. — Kandidat 2: Gute Idee! Und was noch? Vielleicht das "
    "Waffenmuseum?\n"
    "Kandidat 1: Ja, das ist interessant. Wie fahren wir? — Kandidat 2: Unser Chef fährt mit. Und du und ich.\n"
    "Kandidat 1: Ich habe ein Auto. Ich kann fahren. — Kandidat 2: Am Samstag. Vormittags Altstadt und Museum, nachmittags Kaffee trinken.\n"
    "Kandidat 1: Super! Wer kommt mit? — Kandidat 2: Ich kenne ein marokkanisches Restaurant. Sehr lecker!\n"
    "Kandidat 1: Wann machen wir das? — Kandidat 2: Einverstanden! Ich freue mich.\n"
    "Kandidat 1: Klingt gut! Und zum Abendessen? — Kandidat 2: Bis dann! Tschüss!\n"
    "Kandidat 1: Perfekt! Dann machen wir das so.\nKandidat 1: Ich auch! Bis nächste Woche!\n"
    "(Im Buch stehen die Sätze in zwei Spalten; die Antworten von Kandidat 2 gehören jeweils zur Frage davor.)")
MUSTER_PRAESENTATION = (
    "Heute spreche ich über das Thema „Kinder oder Karriere“. Ich habe keine persönliche Erfahrung damit, aber meine Schwester ist verheiratet und "
    "hat zwei Kinder. Sie hat mir erzählt, dass sie in der Babypause eine Fortbildung gemacht hat. So hat sie bessere Chancen für den Wiedereinstieg "
    "ins Berufsleben bekommen.\nIn meinem Umfeld ist die Situation ähnlich. In Marokko bleiben viele Frauen zu Hause, um sich um ihre Kinder zu "
    "kümmern. Es ist nicht immer leicht, Familie und Arbeit zu verbinden.\nKinder haben viele Vorteile. Wenn man ein Kind hat, fühlt man sich nie "
    "allein. Die Kinder bringen Freude und Wärme in die Familie. Karriere hat auch Vorteile. Man kann viel Geld verdienen und hat mehr Möglichkeiten "
    "im Leben.\nEs gibt aber auch Nachteile. Ein Kind braucht viel Zeit und Aufmerksamkeit, und es kostet viel Geld. Für eine Karriere hat man oft "
    "wenig Zeit für die Familie und man muss viel arbeiten. Das kann anstrengend sein.\nMeiner Meinung nach ist es wichtig, zuerst eine gute "
    "Karriere aufzubauen. Wenn man einen sicheren Job hat, kann man später ein Kind bekommen und ihm ein gutes Leben ermöglichen.")

WORDS = redewendungen([
    ("zum Ausdruck bringen", "seine Gefühle oder Meinung sagen", "Ich möchte meine Dankbarkeit zum Ausdruck bringen."),
    ("eine Entscheidung treffen", "sich für eine Möglichkeit entscheiden", "Wir müssen heute eine wichtige Entscheidung treffen."),
    ("in Betracht ziehen", "etwas als Möglichkeit denken", "Ich ziehe in Betracht, im Ausland zu studieren."),
    ("Einfluss nehmen auf", "etwas verändern oder beeinflussen", "Eltern nehmen großen Einfluss auf ihre Kinder."),
    ("eine Rolle spielen", "wichtig sein oder eine Bedeutung haben", "Kommunikation spielt eine große Rolle im Berufsleben."),
    ("Maßnahmen ergreifen", "etwas tun, um ein Ziel zu erreichen", "Wir müssen schnell Maßnahmen ergreifen, um das Problem zu lösen."),
    ("Priorität haben", "wichtiger sein als andere Dinge", "Gesundheit hat für mich oberste Priorität."),
    ("im Voraus planen", "frühzeitig Pläne machen und vorbereiten", "Wir sollten unsere Reise im Voraus planen."),
    ("sich engagieren für", "sich für etwas einsetzen und aktiv sein", "Viele junge Leute engagieren sich für Umweltschutz."),
    ("eine Herausforderung annehmen", "eine schwierige Aufgabe mit Motivation akzeptieren", "Ich nehme jede neue Herausforderung gern an."),
], "Wichtige Redewendungen für Modul 2")

_F = ["damit", "um", "weil"]
UEBUNGEN = [
    exercise("damit oder um … zu? (Beispielsätze aus dem Buch)", [
        example_gap("Ich lerne Deutsch, ___ ich in Deutschland arbeiten kann.", "damit", _F, "Subjekt im Nebensatz (ich) + Verb am Ende → damit."),
        example_gap("Meine Eltern sparen Geld, ___ ich studieren kann.", "damit", _F, "Verschiedene Subjekte (Eltern / ich) → damit."),
        example_gap("Er spart Geld, ___ ein Auto zu kaufen.", "um", _F, "Dasselbe Subjekt + zu + Infinitiv → um … zu."),
        example_gap("Wir üben jeden Tag, ___ die Prüfung zu bestehen.", "um", _F),
        example_gap("Er erklärt alles langsam, ___ die Schüler ihn verstehen können.", "damit", _F),
        example_gap("Sie geht früh schlafen, um fit ___ bleiben.", "zu", ["zu", "damit", "um"], "Nach „zu“ kommt der Infinitiv."),
        example_gap("Wir trainieren viel, damit wir gesund ___.", "bleiben", ["bleiben", "zu bleiben", "bleibt"], "Nach damit steht das Verb am Ende."),
        example_gap("Ich lerne Deutsch, um in Deutschland zu ___.", "arbeiten", ["arbeiten", "arbeite", "gearbeitet"]),
    ], "Wählen Sie die richtige Form. Alle Sätze stammen aus der Grammatik des Buches (S. 27).", source="vizu"),
]

ABSCHLUSSTEST = [
    mc("Wann benutzt man „damit“?", ["Wenn die zwei Sätze verschiedene Subjekte haben", "Wenn beide Sätze dasselbe Subjekt haben", "Nur in Fragen"],
       "A", "Buch S. 27: „damit“ benutzt man, wenn die zwei Sätze verschiedene Subjekte haben."),
    mc("Wann benutzt man „um … zu“?", ["Wenn beide Sätze dasselbe Subjekt haben", "Wenn die Sätze verschiedene Subjekte haben", "Nach „weil“"], "A",
       "Buch S. 27: „um … zu“ benutzt man, wenn beide Sätze dasselbe Subjekt haben."),
    example_gap("Er erklärt alles langsam, damit die Schüler ihn verstehen ___.", "können", ["können", "zu können", "kann"]),
    example_gap("Wir üben jeden Tag, um die Prüfung zu ___.", "bestehen", ["bestehen", "besteht", "bestanden"]),
    example_gap("Wir müssen heute eine wichtige Entscheidung ___.", "treffen", ["treffen", "machen", "nehmen"], "eine Entscheidung treffen."),
    example_gap("Gesundheit hat für mich oberste ___.", "Priorität", ["Priorität", "Rolle", "Maßnahme"], "Priorität haben."),
    example_gap("Kommunikation spielt eine große ___ im Berufsleben.", "Rolle", ["Rolle", "Priorität", "Entscheidung"], "eine Rolle spielen."),
    example_gap("Viele junge Leute engagieren sich ___ Umweltschutz.", "für", ["für", "auf", "um"], "sich engagieren für."),
    example_gap("Wir sollten unsere Reise im ___ planen.", "Voraus", ["Voraus", "Betracht", "Ausdruck"], "im Voraus planen."),
    mc("Warum möchte der Autor in „Ich werde Architekt“ Architektur studieren?", ["Um moderne und schöne Häuser zu entwerfen", "Um Lehrer zu werden",
       "Um in einem Krankenhaus zu arbeiten"], "A", "Lesen Aufgabe 2: „… um moderne und schöne Häuser zu entwerfen.“"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 2. Unterricht", source="vizu", page=25, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Was planen Sie in der Zukunft?", page=26, prompt="Was planen Sie in der Zukunft?",
             questions=["Ich möchte in Zukunft studieren. (Ich plane, an einer guten Universität zu studieren und meinen Traumberuf zu lernen.)",
                        "Ich möchte eine gute Karriere aufbauen. (Ich will in meinem Beruf erfolgreich sein, Erfahrung sammeln und Verantwortung übernehmen.)",
                        "Ich möchte viel reisen und die Welt entdecken. (Ich plane, verschiedene Länder zu besuchen, neue Kulturen kennenzulernen und "
                        "schöne Erinnerungen zu sammeln.)"],
             min_duration=30, max_duration=150,
             metadata={"book_phrases": {"Einleitung": ["In der Zukunft habe ich viele Pläne.", "Ein weiterer Plan ist meine Karriere.",
                                                        "Außerdem möchte ich die Welt entdecken."],
                                        "Schluss": ["Daran arbeite ich jeden Tag.", "Ich gebe mein Bestes, um meine Ziele zu erreichen.",
                                                    "Das Leben ist eine Reise, und ich möchte sie genießen."]}}),
        base(L, "grammatik", 1, "Grammatik: Finalsätze — damit und um … zu", page=27, rules=[{"title": "Finalsätze: damit / um … zu", "html": GRAMMAR_HTML}]),
        completion(L, 3, "Grammatik Aufgabe 1: Sätze mit „damit“", 28, "Machen Sie die Sätze mit „damit“ weiter.", [
            "Der Arzt gibt mir Medikamente, damit", "Meine Schwester ruft mich an, damit", "Die Eltern kaufen ihrem Kind Bücher, damit",
            "Der Chef erklärt die Aufgabe noch einmal, damit", "Wir fahren früher los, damit", "Der Lehrer schreibt neue Wörter an die Tafel, damit"]),
        completion(L, 4, "Grammatik Aufgabe 2: Sätze mit „um … zu“", 29, "Machen Sie die Sätze mit „um … zu“ weiter.", [
            "Ich besuche einen Sprachkurs, um", "Er spart seit Monaten Geld, um", "Wir fahren mit dem Fahrrad, um", "Sie liest deutsche Nachrichten, um",
            "Der Student macht ein Praktikum, um", "Ich benutze mein Handy nur kurz, um"]),
        completion(L, 5, "Grammatik Aufgabe 3: „damit“ oder „um … zu“", 30, "Machen Sie die Sätze weiter. Benutzen Sie „damit“ oder „um … zu“.", [
            "Meine Freundin lernt jeden Abend,", "Der Vater arbeitet auch am Wochenende,", "Wir gehen in die Bibliothek,", "Die Lehrerin wiederholt die Frage,",
            "Ich mache jeden Morgen Sport,", "Die Eltern kontrollieren die Internetnutzung ihrer Kinder,", "Er sieht deutsche Filme ohne Untertitel,",
            "Wir kaufen online Tickets,"]),
        base(L, "lesen", 1, "Lesen Aufgabe 1: Berufe mit Zukunft — Nomen ergänzen", page=31,
             instruction="Ergänzen Sie in der Zusammenfassung die Nomen. Arbeiten Sie zu zweit. (Beispiel: Wenn man auf der Suche nach dem richtigen "
                         "Beruf ist …)",
             passages=[{"title": "Berufe mit Zukunft — Zusammenfassung",
                        "text": "Wörter: " + " • ".join(NOMEN) + " • (Suche = Beispiel)\n\n" + ZUSAMMENFASSUNG_TEXT.replace("[[", "(").replace("]]", ")")}],
             questions=LESEN_1, max_score=11, metadata=key_meta("vizu")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: Ich werde Architekt", page=32, instruction="Lesen Sie den Text. Richtig oder Falsch?",
             passages=[{"title": "Lesetext 1 – Ich werde Architekt", "text": TEXT_ARCHITEKT}], questions=LESEN_2, max_score=len(LESEN_2),
             metadata=key_meta("vizu")),
        base(L, "lesen", 3, "Lesen Aufgabe 3: Ich werde Ärztin", page=33, instruction="Lesen Sie den Text. Richtig oder Falsch?",
             passages=[{"title": "Lesetext 2 – Ich werde Ärztin", "text": TEXT_AERZTIN}], questions=LESEN_3, max_score=len(LESEN_3),
             metadata=key_meta("vizu")),
        base(L, "hoeren", 1, "Hören Aufgabe 1 + 2: Martha und Max", page="34-35", audio_file=AUDIO["vizu-b1-l02-hoeren-01"],
             instruction="Hören Sie den Dialog und ergänzen Sie die Lücken mit den passenden Wörtern.", questions=HOEREN_1, max_score=12,
             metadata=key_meta("vizu", "Lösung von VIZU nach dem Kontext (Wörterliste) — nach dem Anhören in Lösung bestätigen. Audio „Aufgabe 1-2“ = beide Teile.")),
        base(L, "hoeren", 2, "Hören Aufgabe 3: Conrad und Ute — der neue Job", page=36, audio_file=AUDIO["vizu-b1-l02-hoeren-02"],
             instruction="Hören Sie den Text und ergänzen Sie die Lücken (1–13). Wörter: Arbeit • Messe • Nachteil • Stelle • Englischkurs • "
                         "Karrieremöglichkeiten • Urlaubstage • Schule • Dienstreisen (2 x) • Fremdsprachenkenntnisse • Besprechungen • Meeting • Präsentation",
             questions=HOEREN_2, max_score=13,
             metadata=key_meta("vizu", "Lösung von VIZU nach dem Kontext — Lücke 2 passt „Arbeit“ und „Stelle“ (beide akzeptiert); nach dem Anhören "
                                       "in Lösung festlegen. Seitenkopf im Buch: „1. Unterricht“, Audio-Datei: „2.Unterricht Aufgabe 3“.")),
        base(L, "schreiben", 1, "Schreiben Teil 1: Informeller Brief — ein Film", page=37, task_type="letter",
             prompt="Schreiben Sie einen informellen Brief (ca. 120 Wörter) an Ihren Freund / Ihre Freundin.\n\nSchreiben Sie etwas über:\n"
                    "1. einen Film, den Sie vor kurzem gesehen haben: Titel, Art des Films, Ihre Meinung dazu.\n"
                    "2. die Hauptfigur und die Geschichte: Was passiert im Film?\n"
                    "3. Ihre Empfehlung: Warum soll Ihr Freund / Ihre Freundin diesen Film auch sehen?\n\nSchreiben Sie etwa 100–120 Wörter.",
             audience="Ihr Freund / Ihre Freundin (informell)", min_words=100, max_words=140, time_limit=25,
             ai_instructions="Muster aus dem Buch (Referenz für Inhalt und Aufbau; das Muster enthält Rechtschreibfehler):\n" + MUSTER_BRIEF,
             metadata={"musterloesung": MUSTER_BRIEF}),
        base(L, "schreiben", 2, "Schreiben Teil 2: Beitrag — Arbeit am Feiertag und Sonntag verbieten", page=38, task_type="opinion",
             prompt="Klein Beitrag schreiben. Schreiben Sie einen kurzen Beitrag (ca. 80–100 Wörter) für ein Online-Magazin / ein Forum.\n\n"
                    "Schreiben Sie einen Beitrag zum Thema „Arbeit am Feiertag und Sonntag verbieten“. Gehen Sie dabei auf die folgenden Punkte ein:\n"
                    "1. Ihre Meinung zum Thema: Sind Sie dafür oder dagegen? Warum?\n"
                    "2. Vorteile und Nachteile: Welche Vor- und Nachteile hat es für Arbeitnehmer und Gesellschaft?\n"
                    "3. Ihre Lösung / Empfehlung: Was schlagen Sie vor? Wie kann man eine gute Balance finden?",
             audience="Online-Magazin / Forum", min_words=80, max_words=120, time_limit=25,
             ai_instructions="Muster aus dem Buch (Referenz):\n" + MUSTER_BEITRAG, metadata={"musterloesung": MUSTER_BEITRAG}),
        base(L, "sprechen", 1, "Sprechen Teil 1: Gemeinsam planen — Programm für deutsche Kollegen", page=39, topic="Ein touristisches Programm planen",
             prompt="Gemeinsam planen: Sie möchten für 3 deutsche Kollegen, die zum ersten Mal in Ihrer Stadt sind, ein touristisches Programm "
                    "organisieren. Ihre Aufgabe: Machen Sie Vorschläge. Fragen Sie nach Meinungen. Treffen Sie gemeinsam eine Entscheidung.",
             questions=["Was besichtigen?", "Wie hinfahren? (Fahrrad, Auto …)", "Wer kommt mit?", "Abendessen"],
             response_type="dialog", min_duration=60, max_duration=240, sample_answer=MUSTER_PLANEN,
             speech_goal="Gemeinsam ein Programm planen: Vorschläge machen, nach Meinungen fragen, gemeinsam entscheiden.",
             keywords=["Wir können", "Gute Idee", "Wie fahren wir?", "Einverstanden", "Klingt gut"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Präsentation — Kinder oder Karriere", page=40, topic="Kinder oder Karriere",
             prompt="Bereiten Sie eine kurze Präsentation vor und sprechen Sie dazu (ca. 2 Minuten). Halten Sie eine kurze Präsentation zum Thema "
                    "„Kinder oder Karriere“. Tipps: Sprechen Sie deutlich und in ganzen Sätzen. Begründen Sie Ihre Meinung. Sie können Beispiele geben.",
             questions=["Ihre Erfahrung mit diesem Thema", "Die Situation in Ihrem Land / in Ihrer Umgebung", "Vorteile von Kindern und von Karriere",
                        "Nachteile von Kindern und von Karriere", "Ihre Meinung: Was ist für Sie wichtiger? Warum?"],
             response_type="monolog", preparation_time=300, min_duration=90, max_duration=180, sample_answer=MUSTER_PRAESENTATION,
             speech_goal="Präsentation: Erfahrung, Situation im Heimatland, Vor- und Nachteile, eigene Meinung begründen.",
             keywords=["Heute spreche ich über", "Vorteile", "Nachteile", "Meiner Meinung nach", "um … zu", "damit"]),
        base(L, "wortschatz", 1, "Wortschatz: Wichtige Redewendungen für Modul 2", page=41, words=WORDS, exercises=meaning_sets(WORDS),
             auto_practice=False, metadata={"note": "Das Buch erklärt die Ausdrücke auf Deutsch (keine Übersetzung)."}),
        base(L, "uebungen", 1, "Übungen: B1 2. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 2. Unterricht", source="vizu",
             instruction="Abschlusstest zu Finalsätzen und Redewendungen (alle Sätze und Regeln aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 2. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
