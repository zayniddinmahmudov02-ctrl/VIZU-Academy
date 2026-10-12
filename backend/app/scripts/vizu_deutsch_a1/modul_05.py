"""Modul 5 — Mein Tagesablauf — Grammatik: Fragesätze und Uhrzeiten (book pp. 47-58).

p.51 asks for a Ja/Nein question AND a W-Frage per sentence. The Ja/Nein
question has one correct form and is auto-graded; for the W-Frage the book's
answer sheet gives one expected question (accepted together with the
obvious alternatives) — other correct W-questions are possible, so that set
is marked as practice in its instruction."""

from . import base, choice_gap, exercise, gap, html_table, match, mc, short, tf, ul, words

L = 5

_JA_NEIN = (
    "<h3>Ja / Nein — savollar</h3>"
    "<p><strong>Qoida:</strong> savolda fe'l 1-o'rinda bo'ladi va du / ihr / Sie ga mos tuslanadi. "
    "Javob faqat „Ja, …“ yoki „Nein, …“ bilan beriladi. „Ja“ — ha, „Nein“ — yo'q.</p>"
    "<p><strong>So'z tartibi:</strong> Fe'l + du / ihr / Sie + …? — Masalan: <em>Lernst du Deutsch?</em></p>"
    + html_table(["Infinitiv", "du", "ihr", "Sie"], [["lernen", "lernst", "lernt", "lernen"], ["wohnen", "wohnst", "wohnt", "wohnen"]])
    + html_table(["", "du (singular, tanish)", "ihr (plural, tanish)", "Sie (singular / plural, rasmiy)"],
                 [["Oddiy gap", "Du lernst Deutsch. (Sen nemis tilini o'rganasan)", "Ihr lernt Deutsch. (Sizlar nemis tilini o'rganasizlar)",
                   "Sie lernen Deutsch. (Siz nemis tilini o'rganasiz)"],
                  ["Ja/Nein savol", "Lernst du Deutsch?", "Lernt ihr Deutsch?", "Lernen Sie Deutsch?"],
                  ["Eslatma", "du → fe'lga -st qo'shiladi (lernst)", "ihr → fe'lga -t qo'shiladi (lernt)", "Sie → fe'l o'zgarishsiz qoladi (lernen)"]])
)
_W_FRAGEN = (
    "<h3>W-Fragesätze</h3>"
    "<p>W-so'z savolga ma'no beradi. <strong>Fe'l doimo ikkinchi o'rinda</strong> bo'ladi. So'roq belgisi (?) oxirida yoziladi. "
    "Javob gapda tartib odatiy holatda bo'ladi. Ich va wir bilan odatda savol qilinmaydi; du, ihr, Sie bilan W-Fragen bo'ladi.</p>"
    "<p><strong>Tuzilishi:</strong> W-so'z + fe'l + du / ihr / Sie + … ?</p>"
    + html_table(["W-so'z", "Ma'nosi", "W-so'z", "Ma'nosi"],
                 [["Was", "nima", "Wohin", "qayerga"], ["Wo", "qayerda", "Woher", "qayerdan"], ["Wann", "qachon", "Welche", "qaysi"],
                  ["Warum", "nega", "Wie viel", "qancha"], ["Wie", "qanday", "Wer", "kim"]])
    + html_table(["", "du", "ihr", "Sie"],
                 [["Oddiy gap", "Du lernst Deutsch.", "Ihr wohnt in Berlin.", "Sie arbeiten heute."],
                  ["W-Fragen", "Was lernst du? Wann lernst du?", "Wo wohnt ihr? Warum wohnt ihr in Berlin?",
                   "Warum arbeiten Sie heute? Wann arbeiten Sie?"]])
)
_UHRZEIT = (
    "<h3>Rasmiy soatlar (Uhrzeit — formal)</h3>"
    "<p>Stunden (1–24) + Minuten (00–59) + Uhr. 24-soat tizimi ishlatiladi. Soatni aytishda <strong>um</strong> ishlatiladi: "
    "Der Zug kommt um 18:45 Uhr. — Poyezd soat 18:45 da keladi.</p>"
    + html_table(["Raqam bilan", "Misol jumla"],
                 [["08:00", "Es ist acht Uhr."], ["09:15", "Es ist neun Uhr fünfzehn."], ["12:30", "Es ist zwölf Uhr dreißig."],
                  ["14:45", "Es ist vierzehn Uhr fünfundvierzig."], ["18:05", "Es ist achtzehn Uhr fünf."],
                  ["23:50", "Es ist dreiundzwanzig Uhr fünfzig."], ["00:00", "Es ist null Uhr."]])
    + "<h3>Norasmiy soatlar (informal / umgangssprachlich)</h3>"
    "<p>12-soat tizimi ishlatiladi; „Uhr“ ko'pincha ishlatilmaydi. <strong>halb</strong> = yarim (keyingi soatga qarab), "
    "<strong>Viertel nach</strong> = 15 daqiqa o'tgan, <strong>Viertel vor</strong> = 15 daqiqa kam, <strong>vor</strong> = … daqiqa kam, "
    "<strong>nach</strong> = … daqiqa o'tgan.</p>"
    + html_table(["Raqam bilan", "Misol jumla"],
                 [["08:00", "Es ist acht."], ["09:15", "Es ist Viertel nach neun."], ["12:30", "Es ist halb eins."],
                  ["14:45", "Es ist Viertel vor drei."], ["08:25", "Es ist fünf vor halb neun."], ["08:35", "Es ist fünf nach halb neun."],
                  ["18:05", "Es ist fünf nach sechs."], ["23:50", "Es ist zehn vor zwölf."], ["00:00", "Es ist zwölf."]])
    + "<p><strong>Wie spät ist es?</strong> — Soat necha bo'ldi?</p>"
)

_SENTENCES = [
    ("Du lernst Deutsch.", ["Lernst du Deutsch?"], ["Was lernst du?"]),
    ("Ihr wohnt in Berlin.", ["Wohnt ihr in Berlin?"], ["Wo wohnt ihr?"]),
    ("Sie arbeiten heute.", ["Arbeiten Sie heute?", "Arbeitet sie heute?"], ["Wann arbeiten Sie?", "Warum arbeiten Sie heute?"]),
    ("Er spielt Tennis.", ["Spielt er Tennis?"], ["Was spielt er?"]),
    ("Sie tanzt gern.", ["Tanzt sie gern?"], ["Was macht sie gern?"]),
    ("Es arbeitet heute.", ["Arbeitet es heute?"], ["Wann arbeitet es?"]),
    ("Du liest ein Buch.", ["Liest du ein Buch?"], ["Was liest du?"]),
    ("Ihr macht Hausaufgaben.", ["Macht ihr Hausaufgaben?"], ["Was macht ihr?"]),
    ("Sie besuchen Freunde.", ["Besuchen Sie Freunde?"], ["Wen besuchen Sie?"]),
    ("Er kocht heute.", ["Kocht er heute?"], ["Was macht er heute?", "Wann kocht er?"]),
    ("Du gehst ins Kino.", ["Gehst du ins Kino?"], ["Wohin gehst du?"]),
    ("Ihr spielt Fußball.", ["Spielt ihr Fußball?"], ["Was spielt ihr?"]),
    ("Sie lesen Zeitung.", ["Lesen Sie Zeitung?"], ["Was lesen Sie?"]),
    ("Es schwimmt im See.", ["Schwimmt es im See?"], ["Wo schwimmt es?"]),
    ("Du schreibst einen Brief.", ["Schreibst du einen Brief?"], ["Was schreibst du?"]),
    ("Ihr hört Musik.", ["Hört ihr Musik?"], ["Was hört ihr?"]),
    ("Er fährt nach Berlin.", ["Fährt er nach Berlin?"], ["Wohin fährt er?"]),
    ("Sie fährt nach München.", ["Fährt sie nach München?"], ["Wohin fährt sie?"]),
    ("Es schläft viel.", ["Schläft es viel?"], ["Wie viel schläft es?", "Wieviel schläft es?"]),
    ("Du kaufst ein neues Buch.", ["Kaufst du ein neues Buch?"], ["Was kaufst du?"]),
]
JA_NEIN_EX = [short(f"Bilden Sie eine Ja/Nein-Frage: {s}", ja, max_length=120) for s, ja, _ in _SENTENCES]
W_EX = [short(f"Bilden Sie eine W-Frage: {s}", w, max_length=120, explanation="Kitob kaliti: " + w[0]) for s, _, w in _SENTENCES]

_TIMES = [("09:15", ["Viertel nach neun"]), ("06:30", ["halb sieben"]), ("01:00", ["ein Uhr", "eins"]), ("08:15", ["Viertel nach acht"]),
          ("04:50", ["zehn vor fünf"]), ("09:20", ["zwanzig nach neun"]), ("05:00", ["fünf Uhr", "fünf"]), ("01:45", ["Viertel vor zwei"]),
          ("09:45", ["Viertel vor zehn"]), ("06:00", ["sechs Uhr", "sechs"]), ("12:30", ["halb eins"])]
UHR_EX = [short(f"Es ist {t} Uhr. Wie sagt man das informell? (Es ist …)", acc + [f"Es ist {a}" for a in acc], max_length=60) for t, acc in _TIMES]

TEXT_TOM = ("Hallo! Ich heiße Tom. Ich bin 20 Jahre alt. Ich studiere an der Universität. Ich stehe um 06:45 Uhr auf, frühstücke um 07:15 Uhr "
            "und gehe um 07:45 Uhr zur Uni. Um 12:15 Uhr esse ich Mittag, danach lerne ich um 13:00 Uhr in der Bibliothek. Um 16:30 Uhr gehe "
            "ich nach Hause, spiele um 17:30 Uhr Tennis mit Freunden, esse um 19:00 Uhr Abendessen, sehe um 20:30 Uhr fern oder höre Musik "
            "und gehe um 22:45 Uhr ins Bett.")
TEXT_ANNA = ("Hallo! Ich heiße Anna. Ich bin 19 Jahre alt. Ich arbeite in einem Café. Ich stehe um 07:00 Uhr auf, frühstücke um 07:30 Uhr, "
             "trinke Kaffee und gehe um 08:00 Uhr zur Arbeit. Um 12:30 Uhr esse ich Mittag, arbeite weiter bis 16:00 Uhr, gehe dann einkaufen "
             "oder treffe Freunde. Um 18:30 Uhr esse ich Abendessen, lerne um 19:30 Uhr Deutsch oder lese ein Buch, sehe um 21:00 Uhr fern "
             "und gehe um 22:30 Uhr ins Bett.")
LESEN = [
    mc("Um wie viel Uhr steht Tom auf?", ["06:00 Uhr", "06:45 Uhr", "07:15 Uhr"], "B", passage=1),
    mc("Was macht Tom um 07:15 Uhr?", ["Er geht zur Universität.", "Er frühstückt.", "Er spielt Tennis."], "B", passage=1),
    mc("Wann frühstückt Anna?", ["Um 07:00 Uhr", "Um 07:30 Uhr", "Um 08:00 Uhr"], "B", passage=2),
    mc("Was macht Anna nach der Arbeit?", ["Sie lernt Deutsch.", "Sie geht einkaufen oder trifft Freunde.", "Sie spielt Tennis."], "B", passage=2),
    mc("Um wie viel Uhr isst Anna Abendessen?", ["Um 18:30 Uhr", "Um 19:30 Uhr", "Um 21:00 Uhr"], "A", passage=2),
    mc("Um wie viel Uhr geht Tom ins Bett?", ["22:45 Uhr", "21:00 Uhr", "23:00 Uhr"], "A", passage=1),
]

_T = lambda *xs: [x for t in xs for x in (t, t.lstrip("0"), t.replace(":", "."), t.lstrip("0").replace(":", "."), t + " Uhr", t.lstrip("0") + " Uhr")]  # noqa: E731
HOEREN_TEXT = (
    "Am Samstag stehe ich um [[1]] Uhr auf. Ich frühstücke um [[2]] Uhr und danach gehe ich spazieren. Um [[3]] Uhr treffe ich meine "
    "Freunde und wir spielen Fußball im Park. Um [[4]] Uhr esse ich Mittag zu Hause. Am Nachmittag lerne ich ein bisschen Deutsch und lese "
    "ein Buch. Um [[5]] Uhr gehe ich einkaufen und danach esse ich Abendessen. Am Abend sehe ich fern oder höre Musik. Um [[6]] Uhr gehe ich "
    "ins Bett.\nAm Sonntag stehe ich etwas später auf, um [[7]] Uhr. Ich frühstücke gemütlich und danach helfe ich meiner Mutter im Haus. "
    "Um [[8]] Uhr gehe ich mit meiner Familie ins Café oder wir essen zusammen zu Hause. Am Nachmittag gehe ich oft ins Kino oder treffe "
    "Freunde. Abends mache ich meine Hausaufgaben und lese ein Buch. Um [[9]] Uhr gehe ich schlafen."
)
HOEREN_GAPS = {"1": _T("08:00"), "2": _T("08:30"), "3": _T("11:00"), "4": _T("13:00"), "5": _T("18:00"), "6": _T("23:00"),
               "7": _T("09:00"), "8": _T("12:00"), "9": _T("22:00")}

WORDS = (
    words([("lernen", "o'rganmoq"), ("arbeiten", "ishlamoq"), ("wohnen", "yashamoq"), ("schlafen", "uxlamoq"), ("spielen", "o'ynamoq"),
           ("tanzen", "raqsga tushmoq"), ("lesen", "o'qimoq"), ("schreiben", "yozmoq"), ("essen", "yemoq"), ("trinken", "ichmoq"),
           ("gehen", "bormoq")], "Fe'llar")
    + words([("um … Uhr", "soat … da"), ("morgens", "ertalab"), ("mittags", "tush payti"), ("nachmittags", "tushdan keyin"),
             ("abends", "kechqurun"), ("nachts", "tun(da)"), ("heute", "bugun"), ("am Wochenende", "hafta oxiri")], "Vaqt & kun")
    + words([("das", "Haus", "uy"), ("die", "Straße", "ko'cha"), ("das", "Büro", "idora"), ("das", "Café", "kafe"), ("der", "Park", "park"),
             ("die", "Bibliothek", "kutubxona"), ("die", "Schule", "maktab"), ("die", "Universität", "universitet")], "Joy nomlari")
    + words([("aufstehen", "uyg'onmoq"), ("frühstücken", "nonushta qilmoq"), ("Mittag essen", "tushlik qilmoq"),
             ("Abendessen essen", "kechki ovqat qilmoq"), ("fernsehen", "televizor tomosha qilmoq"), ("Musik hören", "musiqa tinglamoq"),
             ("ins Kino gehen", "kinoga bormoq"), ("Hausaufgaben machen", "uy vazifasini qilmoq"), ("spazieren gehen", "sayr qilmoq"),
             ("einkaufen gehen", "xaridga bormoq")], "Kundalik iboralar")
    + words([("wer", "kim"), ("was", "nima"), ("wo", "qayerda"), ("wann", "qachon"), ("warum", "nima uchun"), ("mit wem", "kim bilan"),
             ("welche", "qaysi"), ("wie", "qanday"), ("wohin", "qayerga")], "Savol so'zlari")
    + words([("ja", "ha"), ("nein", "yo'q"), ("gern", "yoqtirmoq, xohlash"), ("viel Spaß", "ko'p zavq"), ("interessant", "qiziqarli"),
             ("zu Hause", "uyda")], "Boshqa muhim so'zlar")
)


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage des Themas: Warum stellt man die Zeit in Deutschland um?", page=48,
             prompt="Warum stellen wir die Zeit in Deutschland um (Sommerzeit / Winterzeit)? Was wissen Sie darüber? "
                    "(Tageslicht besser nutzen, Energie sparen, Tagesrhythmus, Tradition)",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Fragesätze und Uhrzeiten", page="49-53",
             rules=[{"title": "Ja / Nein — Fragen", "html": _JA_NEIN}, {"title": "W-Fragesätze", "html": _W_FRAGEN},
                    {"title": "Die Uhrzeiten", "html": _UHRZEIT}],
             exercises=[
                 exercise("Aufgaben: Ja/Nein-Fragen (20)", JA_NEIN_EX, "Bilden Sie aus jedem Satz eine Ja/Nein-Frage."),
                 exercise("Aufgaben: W-Fragen (20)", W_EX,
                          "Bilden Sie aus jedem Satz eine W-Frage. Hinweis: Es gibt manchmal mehrere richtige W-Fragen; "
                          "bewertet wird die Lösung aus dem Buch."),
                 exercise("Aufgabe: Wie viel Uhr ist es? (informell)", UHR_EX, "Schreiben Sie die Uhrzeit informell (z. B. „Viertel nach neun“)."),
             ]),
        base(L, "lesen", 1, "Lesen: Der Tagesablauf von Tom und Anna", page=54,
             instruction="Lesen Sie die Texte und antworten Sie auf die Fragen.",
             passages=[{"title": "Tom", "text": TEXT_TOM}, {"title": "Anna", "text": TEXT_ANNA}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Mein Wochenende", page=55, audio_file="A1-5.mp3",
             instruction="Hören Sie den Text und füllen Sie die Lücken mit der richtigen Uhrzeit aus.",
             metadata={"book_page": 55, "note": "Javoblar kitobning javoblar varag'idan; audio yuklanganda admin tekshirsin."},
             questions=[gap("Meine Wochenende — tragen Sie die Uhrzeiten ein.", HOEREN_TEXT, HOEREN_GAPS, points=9)]),
        base(L, "schreiben", 1, "Schreiben: Mein Tagesablauf", page=56,
             prompt="Schreiben Sie über Ihren Tagesablauf. Benutzen Sie die Beispiele und schreiben Sie vollständige Sätze:\n"
                    "Kirish: Hallo! Ich heiße … Ich bin … Jahre alt. Ich bin … / Ich arbeite als …\n"
                    "Ertalab: Ich stehe um … Uhr auf. Ich frühstücke um … Ich gehe um … Uhr zur Schule / Arbeit.\n"
                    "Tushlik: Um … Uhr esse ich Mittag. Ich lerne / arbeite / spiele um … Uhr. Ich treffe Freunde um … Uhr.\n"
                    "Kechqurun: Ich esse um … Uhr Abendessen. Am Abend sehe ich fern / höre Musik / lese ein Buch. Um … Uhr gehe ich ins Bett.\n"
                    "Yakun: Mein Tag ist interessant. / Ich habe viel Spaß.",
             task_type="description", min_words=40, max_words=120, time_limit=20,
             support_phrases=["Ich stehe um … Uhr auf.", "Um … Uhr esse ich Mittag.", "Am Abend …", "Um … Uhr gehe ich ins Bett.",
                              "Mein Tag ist interessant."]),
        base(L, "sprechen", 1, "Sprechen: Fragen zum Alltag", page=57, topic="Mein Tagesablauf",
             prompt="Beantworte die Fragen. Sprich in vollständigen Sätzen und erzähle mehr!",
             questions=["Lernst du Deutsch?", "Arbeitest du heute?", "Wohnst du in Berlin?", "Magst du Pizza?", "Hast du Geschwister?",
                        "Trinkst du Kaffee?", "Spielst du Fußball?", "Gehst du zur Schule?", "Isst du gern Obst?", "Fährst du mit dem Fahrrad?",
                        "Wie heißt du?", "Wo wohnst du?", "Was machst du gern?", "Wann stehst du auf?", "Mit wem spielst du Fußball?",
                        "Warum lernst du Deutsch?", "Was isst du zum Frühstück?", "Wo gehst du einkaufen?", "Welche Musik hörst du gern?",
                        "Wie spät ist es jetzt?"],
             response_type="monolog", min_duration=30, max_duration=180,
             speech_goal="Ja/Nein-Fragen und W-Fragen zum Alltag in ganzen Sätzen beantworten, mit Uhrzeiten.",
             keywords=["Ja", "Nein", "um … Uhr", "gern"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 5", page=58, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 5", source="vizu",
             instruction="Savol gaplar, soatlar va kundalik so'zlar bo'yicha yakuniy test.",
             questions=[
                 mc("Welche Frage ist richtig?", ["Du lernst Deutsch?", "Lernst du Deutsch?", "Deutsch lernst du?"], "B"),
                 mc("Welche W-Frage ist richtig?", ["Wo wohnst du?", "Wo du wohnst?", "Du wohnst wo?"], "A"),
                 choice_gap("___ kommst du? — Aus Usbekistan.", ["Woher", "Wohin", "Wann"], "Woher"),
                 choice_gap("___ gehst du? — Ins Kino.", ["Wo", "Wohin", "Wer"], "Wohin"),
                 choice_gap("___ heißt du? — Ich heiße Anna.", ["Wie", "Was", "Wer"], "Wie"),
                 mc("08:30 — informell:", ["halb acht", "halb neun", "Viertel nach acht"], "B"),
                 mc("14:45 — informell:", ["Viertel vor drei", "Viertel nach drei", "halb drei"], "A"),
                 mc("„Es ist zehn vor zwölf.“ — Wie spät ist es?", ["11:50", "12:10", "10:50"], "A"),
                 tf("„aufstehen“ bedeutet „uyg'onmoq“.", True),
                 match("Was passt zusammen?", ["wann", "warum", "wer", "wohin"], ["qachon", "nima uchun", "kim", "qayerga", "qanday"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
