"""A2 5. Unterricht — Wohnen und Lebensraum — Grammatik: Kausalsätze mit weil und da (book pp. 53-62).

Book: Frage p.54, Kausalsätze p.55, Grammatik-Aufgabe (30 pairs, weil / da)
p.56, Lesen (Lebensstil der Deutschen, 16 questions + 5 open questions)
pp.57-58, Hören (Steigende Mieten, 10 questions, no transcript) p.59,
Schreiben (Thema + E-Mail) p.60, Sprechen p.61, Wortschatz worksheet (30
words: translation + example) p.62; the lesson handout lists 50 words with
translations (used for the word list).

Keys: Hören from "Vizu-Antworten A2" — except question 5: the sheet says
"C) Schwimmen im Meer" for "Was machen viele Menschen in Berlin?" (copied from
the Lesen text, which says Fahrrad fahren), so that question waits for an
admin decision after listening (key_pending). Lesen: decided by the quoted
sentence of the text. Weil / da: the pattern of the two columns (Hauptsatz +
weil … Verb; Da … Verb, Verb + Subjekt …) gives one sentence; the accepted
answers also allow the natural word order of Satz 2 (es heute heiß ist).
Book Lesen Q9 prints "Saft nur" twice — the handout options are used."""

from . import (
    article_set, base, exercise, forward_vocab_set, intro_html, mc, mc_pending, numbered_words, reverse_vocab_set, short, summary_html,
    vocab_match_sets,
)

L = 5
LESSON_TITLE = "Wohnen und Lebensraum"
LESSON_DESCRIPTION = "Thema: Wohnen und Lebensraum · Grammatik: Kausalsätze – weil und da"
AUDIO = {"vizu-a2-l05-hoeren-01": "A2 5.Unterricht Hören.mp3"}

EINFUEHRUNG_HTML = intro_html(
    5, "Wohnen und Lebensraum", "Kausalsätze – weil und da",
    ["sababni weil va da bilan aytish: Ich bleibe zu Hause, weil ich krank bin. · Da ich krank bin, bleibe ich zu Hause.;",
     "ergash gapda fe'l oxirda turishini qo'llash;",
     "uy-joy, shahar va qishloq hayoti so'zlarini o'rganish."],
    ["qayerda yashashni xohlashingizni va nima uchunligini aytasiz;",
     "nemislarning turmush tarzi haqidagi matnni tushunasiz;",
     "Germaniyadagi ijara narxlari haqidagi audioni tushunasiz;",
     "yangi kvartirangizga do'stingizni taklif qilib e-mail yozasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(5, [
    "<strong>weil</strong> (Alltagssprache): Hauptsatz + weil + Nebensatz (Verb am Ende) — Ich bleibe zu Hause, weil ich krank bin.",
    "<strong>da</strong> (formeller): Da + Nebensatz, Hauptsatz (Verb 2) — Da ich krank bin, bleibe ich zu Hause.",
    "<strong>Merksatz:</strong> weil und da → Grund (Warum?). Beide leiten Nebensätze ein. Das Verb steht am Ende.",
    "<strong>Wortschatz:</strong> die Wohnung, die Miete, der Vermieter, der Nachbar, auf dem Land, gemütlich, günstig, der Lebensstil.",
])

GRAMMAR_HTML = (
    "<h3>Kausalsätze: weil und da (A2)</h3>"
    "<h4>Was sind Kausalsätze?</h4><ul><li>Kausalsätze erklären den Grund (Warum?).</li><li>Sie beantworten die Frage: Warum?</li>"
    "<li>weil und da leiten Nebensätze ein.</li></ul>"
    "<h4>Wichtige Regeln (A2)</h4><ul><li>Nach weil und da steht das <strong>Verb am Ende</strong>.</li><li>Es handelt sich um Nebensätze.</li>"
    "<li>Komma trennen Hauptsatz und Nebensatz.</li></ul>"
    "<table><thead><tr><th>WEIL – Alltagssprache</th><th>DA – formeller</th></tr></thead><tbody>"
    "<tr><td>weil = Grund (Warum?) · sehr häufig in der Alltagssprache · Verb steht am Ende</td>"
    "<td>da = Grund, Ursache (formal) · oft in der Schriftsprache · Verb steht am Ende</td></tr>"
    "<tr><td><strong>Struktur:</strong> Hauptsatz (Verb 2) + weil + Nebensatz (Verb Ende)</td>"
    "<td><strong>Struktur:</strong> da + Nebensatz (Verb Ende), Hauptsatz (Verb 2)</td></tr>"
    "<tr><td>Ich bleibe zu Hause, weil ich krank bin.<br>Ich lerne Deutsch, weil ich in Deutschland arbeiten möchte.<br>Er kommt nicht, weil er keine "
    "Zeit hat.<br>Wir gehen spazieren, weil das Wetter schön ist.<br>Sie ist müde, weil sie wenig geschlafen hat.</td>"
    "<td>Da ich krank bin, bleibe ich zu Hause.<br>Da er keine Zeit hat, kommt er nicht.<br>Da das Wetter schön ist, gehen wir spazieren.<br>"
    "Da sie müde ist, geht sie früh schlafen.<br>Da ich viel lerne, mache ich Fortschritte.</td></tr></tbody></table>"
    "<h4>Satzstellungen vergleichen</h4><p>mit weil: Ich lerne Deutsch, weil ich arbeiten möchte. · mit da: Da ich arbeiten möchte, lerne ich Deutsch.</p>"
    "<p><strong>Merksatz:</strong> weil und da → Grund (Warum?). Beide leiten Nebensätze ein. Das Verb steht am Ende.</p>"
)


def _variants(sentence: str) -> list[str]:
    out = [sentence]
    if "," in sentence:
        out.append(sentence.replace(",", ""))
    return out


def kausal(n: int, s1: str, s2: str, answers: list[str]) -> dict:
    accepted = []
    for a in answers:
        accepted += _variants(a)
    conj = "weil" if n <= 15 else "da"
    return short(f"{n}. {s1} + {s2} → mit „{conj}“", accepted, explanation=answers[0], max_length=200)


WEIL = [
    (2, "Er geht früh schlafen.", "Er ist sehr müde.", ["Er geht früh schlafen, weil er sehr müde ist."]),
    (3, "Wir lernen Deutsch.", "Wir wollen in Deutschland arbeiten.", ["Wir lernen Deutsch, weil wir in Deutschland arbeiten wollen."]),
    (4, "Sie kauft Obst.", "Sie möchte gesund essen.", ["Sie kauft Obst, weil sie gesund essen möchte."]),
    (5, "Ich fahre mit dem Fahrrad.", "Mein Auto ist kaputt.", ["Ich fahre mit dem Fahrrad, weil mein Auto kaputt ist."]),
    (6, "Er trinkt viel Wasser.", "Es ist heiß heute.", ["Er trinkt viel Wasser, weil es heute heiß ist.", "Er trinkt viel Wasser, weil es heiß heute ist."]),
    (7, "Wir gehen ins Kino.", "Der Film ist interessant.", ["Wir gehen ins Kino, weil der Film interessant ist."]),
    (8, "Ich mache Sport.", "Ich will fit bleiben.", ["Ich mache Sport, weil ich fit bleiben will."]),
    (9, "Sie arbeitet am Wochenende.", "Sie braucht Geld.", ["Sie arbeitet am Wochenende, weil sie Geld braucht."]),
    (10, "Ich gehe nicht raus.", "Es regnet stark.", ["Ich gehe nicht raus, weil es stark regnet."]),
    (11, "Er liest jeden Tag.", "Er liebt Bücher.", ["Er liest jeden Tag, weil er Bücher liebt."]),
    (12, "Wir essen zu Hause.", "Wir haben kein Geld.", ["Wir essen zu Hause, weil wir kein Geld haben."]),
    (13, "Ich lerne viel.", "Ich habe bald eine Prüfung.", ["Ich lerne viel, weil ich bald eine Prüfung habe."]),
    (14, "Sie besucht ihre Freundin.", "Sie hat Zeit.", ["Sie besucht ihre Freundin, weil sie Zeit hat."]),
    (15, "Er kauft Blumen.", "Seine Frau hat Geburtstag.", ["Er kauft Blumen, weil seine Frau Geburtstag hat."]),
]
DA = [
    (17, "Er bleibt zu Hause.", "Er fühlt sich schlecht.", ["Da er sich schlecht fühlt, bleibt er zu Hause."]),
    (18, "Wir gehen spazieren.", "Das Wetter ist schön.", ["Da das Wetter schön ist, gehen wir spazieren."]),
    (19, "Sie öffnet das Fenster.", "Es ist warm im Zimmer.", ["Da es im Zimmer warm ist, öffnet sie das Fenster.", "Da es warm im Zimmer ist, öffnet sie das Fenster."]),
    (20, "Ich kaufe ein Ticket.", "Ich möchte reisen.", ["Da ich reisen möchte, kaufe ich ein Ticket."]),
    (21, "Er fährt nach Berlin.", "Er hat Urlaub.", ["Da er Urlaub hat, fährt er nach Berlin."]),
    (22, "Wir machen eine Pause.", "Wir sind müde.", ["Da wir müde sind, machen wir eine Pause."]),
    (23, "Ich nehme eine Jacke.", "Es ist kalt draußen.", ["Da es draußen kalt ist, nehme ich eine Jacke.", "Da es kalt draußen ist, nehme ich eine Jacke."]),
    (24, "Sie lernt jeden Abend.", "Sie hat eine Prüfung.", ["Da sie eine Prüfung hat, lernt sie jeden Abend."]),
    (25, "Er ruft seinen Freund an.", "Er braucht Hilfe.", ["Da er Hilfe braucht, ruft er seinen Freund an."]),
    (26, "Wir gehen einkaufen.", "Der Kühlschrank ist leer.", ["Da der Kühlschrank leer ist, gehen wir einkaufen."]),
    (27, "Ich bleibe länger im Büro.", "Ich habe viel Arbeit.", ["Da ich viel Arbeit habe, bleibe ich länger im Büro."]),
    (28, "Sie trinkt Tee.", "Sie hat Halsschmerzen.", ["Da sie Halsschmerzen hat, trinkt sie Tee."]),
    (29, "Er steht früh auf.", "Er muss zur Arbeit.", ["Da er zur Arbeit muss, steht er früh auf."]),
    (30, "Wir bleiben zu Hause.", "Wir haben Besuch.", ["Da wir Besuch haben, bleiben wir zu Hause."]),
]
KAUSAL_SETS = [
    exercise("Kausalsätze mit weil (2–15)", [kausal(*row) for row in WEIL],
             "Bilden Sie Kausalsätze mit weil. Beispiel 1: Ich bleibe zu Hause, weil ich krank bin."),
    exercise("Kausalsätze mit da (17–30)", [kausal(*row) for row in DA],
             "Bilden Sie Kausalsätze mit da. Beispiel 16: Da ich den Bus verpasst habe, komme ich zu spät."),
]

TEXT = (
    "In Deutschland leben etwa 84 Millionen Menschen. Viele wohnen in großen Städten wie Berlin, Hamburg, München und Köln. Diese Städte sind modern, "
    "sauber und gut organisiert. Es gibt viele Büros, Geschäfte, Schulen und Universitäten. In den Städten leben viele junge Menschen, Studenten und "
    "Familien.\n\nDer Lebensstil der Deutschen ist oft strukturiert. Viele Menschen stehen früh auf, meistens um 6 oder 7 Uhr. Sie frühstücken schnell "
    "und gehen dann zur Arbeit oder zur Schule. Die Arbeit beginnt oft um 8 Uhr und endet am Nachmittag. Viele Menschen arbeiten fünf Tage in der "
    "Woche, von Montag bis Freitag.\n\nNach der Arbeit haben viele Menschen Freizeit. Sie gehen spazieren, treffen Freunde oder machen Sport. In "
    "Städten wie Berlin fahren viele Menschen Fahrrad oder gehen joggen im Park. Sport und Gesundheit sind für viele Deutsche wichtig.\n\nAuch das "
    "Essen spielt eine große Rolle. Zum Frühstück essen viele Menschen Brot mit Käse oder Marmelade und trinken Kaffee oder Tee. Zum Mittag essen sie "
    "oft warmes Essen, zum Beispiel Fleisch, Gemüse oder Nudeln. Am Abend essen viele Menschen nur etwas Kleines wie Brot oder Salat. Am Wochenende "
    "kochen Familien oft zusammen oder gehen in ein Restaurant.\n\nDie Deutschen mögen Ordnung und Pünktlichkeit. Sie kommen meistens pünktlich zur "
    "Arbeit, zur Schule oder zu Terminen. Das ist sehr wichtig im Alltag. Viele planen ihren Tag genau und machen Listen.\n\nDer Verkehr in "
    "Deutschland ist sehr gut organisiert. In großen Städten gibt es Busse, Straßenbahnen, U-Bahnen und Züge. Viele Menschen benutzen öffentliche "
    "Verkehrsmittel, weil sie schnell und praktisch sind. Andere fahren mit dem Fahrrad oder mit dem Auto.\n\nDas Leben in großen Städten ist oft "
    "schnell und manchmal stressig. Es gibt viel Verkehr und viele Menschen. In kleineren Städten oder Dörfern ist das Leben ruhiger. Dort haben die "
    "Menschen mehr Zeit und die Natur ist näher.\n\nZusammengefasst kann man sagen: Der Lebensstil der Deutschen ist aktiv, organisiert, pünktlich "
    "und oft gesund.")
LESEN = [
    mc("Wie viele Menschen leben in Deutschland?", ["50 Millionen", "84 Millionen", "100 Millionen"], "B", "„In Deutschland leben etwa 84 Millionen Menschen.“"),
    mc("Wo leben viele Menschen in Deutschland?", ["Nur in Dörfern", "In großen Städten", "In Bergen"], "B", "„Viele wohnen in großen Städten …“"),
    mc("Welche Stadt ist im Text genannt?", ["Paris", "Berlin", "Rom"], "B", "„… wie Berlin, Hamburg, München und Köln.“"),
    mc("Wann stehen viele Deutsche auf?", ["Um 10 Uhr", "Um 12 Uhr", "Um 6 oder 7 Uhr"], "C", "„… meistens um 6 oder 7 Uhr.“"),
    mc("Wann beginnt die Arbeit oft?", ["Um 8 Uhr", "Um 10 Uhr", "Um 12 Uhr"], "A", "„Die Arbeit beginnt oft um 8 Uhr …“"),
    mc("Wie viele Tage arbeiten viele Menschen?", ["3 Tage", "5 Tage", "7 Tage"], "B", "„Viele Menschen arbeiten fünf Tage in der Woche …“"),
    mc("Was machen viele Menschen nach der Arbeit?", ["Schlafen nur", "Machen Sport oder treffen Freunde", "Arbeiten weiter"], "B",
       "„Sie gehen spazieren, treffen Freunde oder machen Sport.“"),
    mc("Was machen viele Menschen in Berlin?", ["Fliegen", "Fahrrad fahren", "Schwimmen im Meer"], "B",
       "„In Städten wie Berlin fahren viele Menschen Fahrrad …“"),
    mc("Was trinken Deutsche oft zum Frühstück?", ["Cola", "Kaffee oder Tee", "Saft nur"], "B", "„… und trinken Kaffee oder Tee.“"),
    mc("Was essen viele Deutsche zum Abend?", ["Nur Fleisch", "Nur Suppe", "Brot oder Salat"], "C", "„Am Abend essen viele Menschen nur etwas Kleines wie Brot oder Salat.“"),
    mc("Was ist für Deutsche wichtig?", ["Unordnung", "Pünktlichkeit", "Langsamkeit"], "B", "„Die Deutschen mögen Ordnung und Pünktlichkeit.“"),
    mc("Wie planen viele Deutsche ihren Tag?", ["Gar nicht", "Sehr genau", "Zufällig"], "B", "„Viele planen ihren Tag genau und machen Listen.“"),
    mc("Welche Verkehrsmittel gibt es in großen Städten?", ["Nur Autos", "Bus, U-Bahn, Züge", "Nur Fahrräder"], "B",
       "„In großen Städten gibt es Busse, Straßenbahnen, U-Bahnen und Züge.“"),
    mc("Warum benutzen viele Menschen öffentliche Verkehrsmittel?", ["Weil sie teuer sind", "Weil sie schnell und praktisch sind", "Weil sie langsam sind"],
       "B", "„… weil sie schnell und praktisch sind.“"),
    mc("Wie ist das Leben in großen Städten?", ["Langsam", "Ruhig", "Schnell und stressig"], "C", "„Das Leben in großen Städten ist oft schnell und manchmal stressig.“"),
    mc("Wie ist das Leben in kleinen Städten oder Dörfern?", ["Laut", "Ruhiger", "Gefährlich"], "B", "„In kleineren Städten oder Dörfern ist das Leben ruhiger.“"),
]
_K = "Javob: Vizu-Antworten A2 (5. Unterricht, Hören)."
HOEREN = [
    mc("Worum geht es im Text?", ["Essen", "Mieten in Deutschland", "Schule"], "B", _K),
    mc("Was passiert mit den Mieten?", ["Sie bleiben gleich", "Sie sinken", "Sie steigen"], "C", _K),
    mc("Wo sind die Mieten sehr hoch?", ["In Dörfern", "In großen Städten", "In Bergen"], "B", _K),
    mc("Was kostet eine Wohnung in München?", ["500–700 Euro", "800–1000 Euro", "1500–2100 Euro"], "B", _K),
    mc_pending("Was machen viele Menschen in Berlin?", ["Fliegen", "Fahrrad fahren", "Schwimmen im Meer"]),
    mc("Wie viele Tage arbeiten viele Menschen?", ["3 Tage", "5 Tage", "7 Tage"], "B", _K),
    mc("Warum steigen die Mieten?", ["Wenige Menschen", "Wohnungen sind leer", "Viele ziehen in Städte"], "C", _K),
    mc("Wie sind die Mieten in Berlin?", ["Sehr niedrig", "1000–1200 Euro", "300 Euro"], "B", _K),
    mc("Wie sind die Mieten in kleinen Städten?", ["Sehr teuer", "Günstiger", "Gleich"], "B", _K),
    mc("Wieviel kostet eine Wohnung?", ["450–700 Euro", "150–700 Euro", "2000 Euro"], "A", _K + " (Kitobda D) ham „2000 Euro“ — takror, olib tashlandi.)"),
]

WORDS = numbered_words([
    ("wohnen", "yashamoq"), ("der Wohnort", "yashash joyi"), ("die Wohnung", "kvartira"), ("das Haus", "uy"), ("das Gebäude", "bino"), ("das Zimmer", "xona"),
    ("die Miete", "ijara"), ("mieten", "ijaraga olmoq"), ("der Vermieter", "uy egasi"), ("der Nachbar", "qo‘shni"), ("die Stadt", "shahar"), ("das Dorf", "qishloq"),
    ("auf dem Land", "qishloqda"), ("das Stadtzentrum", "shahar markazi"), ("die Umgebung", "atrof-muhit"), ("die Natur", "tabiat"), ("ruhig", "tinch"),
    ("laut", "shovqinli"), ("modern", "zamonaviy"), ("alt", "eski"), ("groß", "katta"), ("klein", "kichik"), ("bequem", "qulay"), ("hell", "yorug‘"),
    ("dunkel", "qorong‘i"), ("sauber", "toza"), ("gemütlich", "shinam"), ("teuer", "qimmat"), ("günstig", "arzon"), ("neu", "yangi"),
    ("allein leben", "yolg‘iz yashamoq"), ("zusammen leben", "birga yashamoq"), ("die Familie", "oila"), ("die Freunde", "do‘stlar"),
    ("die Mitbewohner", "birga yashovchilar"), ("der Verkehr", "transport"), ("die U-Bahn", "metro"), ("der Bus", "avtobus"), ("der Supermarkt", "supermarket"),
    ("die Schule", "maktab"), ("das Krankenhaus", "shifoxona"), ("ich würde gern wohnen", "yashamoqchi bo‘lardim"), ("ich möchte leben", "yashamoqchiman"),
    ("für mich ist wichtig", "men uchun muhim"), ("ich finde", "menimcha"), ("weil", "chunki"), ("deshalb", "shuning uchun"), ("der Vorteil", "afzallik"),
    ("der Nachteil", "kamchilik"), ("der Lebensstil", "yashash tarzi")], "Wohnen und Lebensraum")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]
WORKSHEET = ["wohnen", "die Wohnung", "das Haus", "das Zimmer", "die Miete", "der Vermieter", "der Nachbar", "die Stadt", "das Dorf", "auf dem Land",
             "die Natur", "ruhig", "laut", "modern", "groß", "klein", "sauber", "gemütlich", "teuer", "günstig", "die Familie", "die Freunde",
             "zusammen leben", "der Verkehr", "die U-Bahn", "der Bus", "die Schule", "das Krankenhaus", "ich möchte leben", "der Lebensstil"]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 5. Unterricht", source="vizu", page=53, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wo würden Sie wohnen?", page=54,
             prompt="Wo würden Sie wohnen — in der Stadt, auf dem Land oder in den Bergen? Warum?",
             questions=["In der Stadt?", "Auf dem Land?", "In den Bergen?"], min_duration=20, max_duration=120,
             metadata={"book_samples": [
                 "Ich würde in der Stadt wohnen. In der Stadt gibt es viele Geschäfte, Restaurants und Cafés. Außerdem kann man dort gut arbeiten und "
                 "studieren. Die öffentlichen Verkehrsmittel sind sehr praktisch. Deshalb finde ich das Leben in der Stadt interessant.",
                 "Ich würde auf dem Land wohnen. Dort ist es ruhig und die Luft ist sauber. Außerdem gibt es viel Natur und schöne Landschaften. Die "
                 "Menschen sind freundlich und hilfsbereit. Ich finde das Leben auf dem Land sehr angenehm.",
                 "Ich würde in den Bergen wohnen. Dort ist die Natur wunderschön und die Luft ist frisch. Ich mag die Ruhe und die schöne Aussicht. In "
                 "meiner Freizeit könnte ich wandern und viel Zeit in der Natur verbringen. Deshalb würde ich gerne in den Bergen leben."]}),
        base(L, "grammatik", 1, "Grammatik: Kausalsätze – weil und da", page="55-56", rules=[{"title": "Kausalsätze: weil und da", "html": GRAMMAR_HTML}],
             exercises=KAUSAL_SETS),
        base(L, "lesen", 1, "Lesen: Wie ist der Lebensstil der Deutschen?", page="57-58",
             instruction="Lesen Sie den Text und beantworten Sie die Fragen.", passages=[{"title": "Wie ist der Lebensstil der Deutschen?", "text": TEXT}],
             questions=LESEN, max_score=len(LESEN),
             metadata={"note": "Javob har bir savol izohida matndan iqtibos bilan (Vizu-Antworten da Lesen kaliti yo'q).",
                       "open_questions": ["In welchen Städten leben viele Menschen?", "Wann beginnt die Arbeit?", "Was machen die Deutschen in ihrer Freizeit?",
                                          "Was essen die Deutschen zum Frühstück?", "Was ist den Deutschen wichtig?"]}),
        base(L, "hoeren", 1, "Hören: Steigende Mieten in Deutschland!", page=59, audio_file="A2 5.Unterricht Hören.mp3", key_pending=True,
             instruction="Hören Sie den Text und wählen Sie die richtige Antwort (A, B oder C). Tipp: Hören Sie aufmerksam zu und wählen Sie die beste Antwort.",
             questions=HOEREN,
             metadata={"note": "5-savolning kaliti (Vizu-Antworten: C „Schwimmen im Meer“) mazmunga mos emas — admin audioni tinglab tasdiqlaydi."}),
        base(L, "schreiben", 1, "Schreiben: Mein Lebensstil und Wohnen", page=60, task_type="description",
             prompt="Schreiben Sie einen kurzen Text über das Thema. Schreiben Sie mindestens 80 Wörter.\n\nPunkte:\n"
                    "• Wo wohnen Sie? (in der Stadt oder auf dem Land?)\n• Wohnen Sie in einer Wohnung oder in einem Haus?\n"
                    "• Leben Sie zur Miete oder im eigenen Haus?\n• Mit wem wohnen Sie zusammen? (allein, mit Familie, mit Freunden?)\n"
                    "• Wie ist Ihre Wohnung oder Ihr Haus? (groß, klein, modern, ruhig?)\n• Gefällt Ihnen Ihr Lebensstil und Wohnort? Warum?",
             min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: E-Mail — Einladung in die neue Wohnung", page=60, task_type="email",
             prompt="Situation: Ihr Freund kommt in Ihre Stadt. Sie haben eine neue Wohnung. Sie möchten Ihren Freund einladen und schreiben ihm eine E-Mail."
                    "\n\nPunkte:\n• Erzählen Sie, dass Sie eine neue Wohnung haben.\n• Beschreiben Sie Ihre Wohnung (Zimmer, Lage, Größe).\n"
                    "• Laden Sie Ihren Freund ein.\n• Machen Sie einen Vorschlag für Datum und Uhrzeit.\n• Schreiben Sie, was Sie zusammen machen können.",
             audience="Ihr Freund (informell)", min_words=50, max_words=120, time_limit=20),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Übersetzung und Beispiel", page=62, task_type="other",
             prompt="Schreiben Sie die Übersetzung und ein Beispiel mit jedem Wort.\n\n" + "\n".join(f"{i}. {w}" for i, w in enumerate(WORKSHEET, start=1))
                    + "\n\nTipp: Lernen Sie die Wörter regelmäßig und verwenden Sie sie in Sätzen!",
             min_words=60, max_words=500, time_limit=40, metadata={"note": "Kitobdagi ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "sprechen", 1, "Sprechen: Wo würde ich wohnen?", page=61, topic="Wo würde ich wohnen?",
             prompt="Sprechen Sie über das Thema. Sprechen Sie mindestens 1–2 Minuten. Tipps: Sprechen Sie frei und verwenden Sie Ihre eigenen Ideen. "
                    "Begründen Sie Ihre Meinung. Verwenden Sie passende Wörter und Beschreibungen.",
             questions=["Wo würden Sie lieber wohnen? (in der Stadt oder auf dem Land?)", "Warum möchten Sie dort wohnen?",
                        "Möchten Sie in einer Wohnung oder in einem Haus leben?", "Leben Sie lieber allein oder mit Familie?",
                        "Wie soll Ihr Wohnort sein? (ruhig, modern, groß, klein?)", "Was ist für Sie wichtig: Natur oder Stadtleben?",
                        "Was sind die Vorteile und Nachteile?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Wunsch-Wohnort beschreiben und begründen (weil / da), Vor- und Nachteile nennen.",
             keywords=["Ich würde", "wohnen", "weil", "da", "Vorteil", "Nachteil"]),
        base(L, "wortschatz", 1, "Wortschatz: Wohnen und Lebensraum", page=62, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False,
             metadata={"note": "Tarjimalar dars varag'idan (50 so'z); kitobdagi 30 so'zlik ish varag'i alohida yozma topshiriq."}),
        base(L, "uebungen", 1, "Übungen: A2 5. Unterricht", source="vizu", exercises=[s for s in (
            exercise("weil oder da?", [
                mc("___ ich krank bin, bleibe ich zu Hause.", ["Da", "Weil ich", "Deshalb"], "A", "da + Nebensatz am Anfang."),
                mc("Ich bleibe zu Hause, weil ich krank ___.", ["bin", "ich bin", "sein"], "A", "Verb am Ende."),
                mc("Welche Konjunktion ist formeller?", ["da", "weil", "und"], "A", "da – formeller, oft in der Schriftsprache."),
                mc("Wir gehen spazieren, ___ das Wetter schön ist.", ["weil", "deshalb", "aber"], "A"),
                mc("Da er keine Zeit hat, ___ nicht.", ["kommt er", "er kommt", "er nicht kommt"], "A", "Nach dem Nebensatz: Verb + Subjekt."),
            ], "Kitobdagi qoida bo'yicha to'g'ri variantni tanlang.", source="vizu"),
            reverse_vocab_set(WORDS),
        ) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 5. Unterricht", source="vizu",
             instruction="Kausalsätze va uy-joy so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Er geht früh schlafen, weil er sehr müde ___.", ["ist", "sein", "war ist"], "A"),
                 mc("___ das Wetter schön ist, gehen wir spazieren.", ["Da", "Deshalb", "Aber"], "A"),
                 mc("Wo steht das Verb nach weil und da?", ["Am Ende", "Am Anfang", "Auf Position 2"], "A"),
                 mc("Wie viele Menschen leben in Deutschland?", ["Etwa 84 Millionen", "Etwa 50 Millionen", "Etwa 100 Millionen"], "A", "Lesen."),
                 mc("Wie ist das Leben in kleinen Städten oder Dörfern?", ["Ruhiger", "Lauter", "Stressiger"], "A", "Lesen."),
                 mc("„die Miete“ — o'zbekchasi?", ["ijara", "qo'shni", "uy egasi"], "A"),
                 mc("„günstig“ — o'zbekchasi?", ["arzon", "qimmat", "qulay"], "A"),
                 mc("„der Nachbar“ — o'zbekchasi?", ["qo'shni", "uy egasi", "birga yashovchi"], "A"),
                 mc("„auf dem Land“ — o'zbekchasi?", ["qishloqda", "shahar markazida", "tog'larda"], "A"),
                 mc("Ich wohne gern hier, ___ es ruhig ist.", ["weil", "deshalb", "trotzdem"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 5. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
