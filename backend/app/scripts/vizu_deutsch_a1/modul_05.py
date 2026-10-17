"""Modul 5 — Mein Tagesablauf — Grammatik: Fragesätze und Uhrzeiten (book pp. 47-58).

p.51 asks for a Ja/Nein question AND a W-Frage per sentence. The Ja/Nein
question has one correct form. A W-Frage has several correct forms, so each
task names the question word (the one of the book's answer sheet) — then the
answer is unique. Sentence 3 is printed "Sie arbeitet heute" with person
"Sie": both readings are accepted.

p.53 shows 12 clock faces ("Trage beide Uhrzeiten ein"). The pictures can't
be part of a text question, so the times they show (9:15, 1:30, 12:00, 8:30,
8:15, 10:30, 3:45, 5:00, 1:45, 12:30 — 5:00 and 12:00 appear twice) are
given as numbers and read informally (VIZU adaptation). The older answer
sheet's times did not match these clocks.

p.55 Hören: the times are only in the audio (A1-5.mp3). The older answer
sheet is not reliable for this edition, so the gaps are left for the admin
(key_pending); its values are kept as a hint in the item metadata."""

from . import (
    forward_vocab_set,
    article_set, base, choice_gap, exercise, gap, html_table, intro_html, match, mc, reverse_vocab_set, short, summary_html, tf, ul,
    vocab_match_sets, words,
)

L = 5
LESSON_TITLE = "Mein Tagesablauf"
LESSON_DESCRIPTION = "Thema: Mein Tagesablauf · Grammatik: Fragesätze und Uhrzeiten"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 5 — Mein Tagesablauf (Buch, S. 47)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    5, "Mein Tagesablauf", "Fragesätze (Ja/Nein- und W-Fragen) und Uhrzeiten",
    ["Ja/Nein-savollar tuzish: fe'l birinchi o'rinda — Lernst du Deutsch?;",
     "W-savollar tuzish: W-so'z + fe'l + shaxs — Wo wohnst du? Wann stehst du auf?;",
     "soatni rasmiy (neun Uhr fünfzehn) va norasmiy (Viertel nach neun, halb zehn) aytish;",
     "kun tartibi iboralarini o'rganish: aufstehen, frühstücken, Mittag essen, ins Bett gehen."],
    ["„Ich stehe um 7 Uhr auf. Um halb acht frühstücke ich.“ — kun tartibingizni aytasiz;",
     "do'stingizdan kun tartibi haqida so'raysiz: „Wann stehst du auf? Was machst du am Abend?“;",
     "Tom va Annaning kun tartibi haqidagi matnlarni o'qib tushunasiz;",
     "hafta oxiri haqidagi matnni tinglab, soatlarni yozasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(5, [
    "<strong>Ja/Nein-Frage:</strong> Fe'l + shaxs + …? — Lernst du Deutsch? Wohnt ihr in Berlin? Arbeiten Sie heute?",
    "<strong>W-Frage:</strong> W-so'z + fe'l + shaxs + …? — Was lernst du? Wo wohnt ihr? Wann arbeiten Sie?",
    "<strong>W-Wörter:</strong> wer, was, wo, wohin, woher, wann, warum, wie, wie viel, welche, mit wem.",
    "<strong>Uhrzeit:</strong> formell 9:15 = neun Uhr fünfzehn · informell Viertel nach neun; 9:30 = halb zehn; 9:45 = Viertel vor zehn.",
    "<strong>Tagesablauf:</strong> Ich stehe um … Uhr auf. Ich frühstücke um … Um … Uhr esse ich Mittag. Um … Uhr gehe ich ins Bett.",
])

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
    ("Sie arbeitet heute.", ["Arbeitet sie heute?", "Arbeiten Sie heute?"], ["Wann arbeitet sie?", "Wann arbeiten Sie?"]),
    ("Er spielt Tennis.", ["Spielt er Tennis?"], ["Was spielt er?"]),
    ("Sie tanzt gern.", ["Tanzt sie gern?"], ["Was macht sie gern?"]),
    ("Es arbeitet heute.", ["Arbeitet es heute?"], ["Wann arbeitet es?"]),
    ("Du liest ein Buch.", ["Liest du ein Buch?"], ["Was liest du?"]),
    ("Ihr macht Hausaufgaben.", ["Macht ihr Hausaufgaben?"], ["Was macht ihr?"]),
    ("Sie besuchen Freunde.", ["Besuchen Sie Freunde?"], ["Wen besuchen Sie?"]),
    ("Er kocht heute.", ["Kocht er heute?"], ["Was macht er heute?"]),
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
def _w_word(question: str) -> str:
    return "Wie viel" if question.startswith("Wie viel") else question.split()[0]


JA_NEIN_EX = [short(f"Bilden Sie eine Ja/Nein-Frage: {s}", ja, max_length=120,
                    explanation="Kitobdagi gap „Sie arbeitet“ — sie (u): Arbeitet sie heute? / Sie (Siz): Arbeiten Sie heute?" if s.startswith("Sie arbeitet") else None)
              for s, ja, _ in _SENTENCES]
W_EX = [short(f"Bilden Sie eine W-Frage mit „{_w_word(w[0])}“: {s}", w, max_length=120, explanation=w[0]) for s, _, w in _SENTENCES]

# the clocks of p.53 in book order (5:00 and 12:00 appear twice there)
_TIMES = [("09:15", ["Viertel nach neun"]), ("01:30", ["halb zwei"]), ("12:00", ["zwölf Uhr", "zwölf"]), ("08:30", ["halb neun"]),
          ("08:15", ["Viertel nach acht"]), ("10:30", ["halb elf"]), ("03:45", ["Viertel vor vier"]), ("05:00", ["fünf Uhr", "fünf"]),
          ("01:45", ["Viertel vor zwei"]), ("12:30", ["halb eins"])]
UHR_EX = [short(f"Es ist {t} Uhr. Wie sagt man das informell? (Es ist …)", acc + [f"Es ist {a}" for a in acc], max_length=60) for t, acc in _TIMES]

TEXT_TOM = ("Hallo! Ich heiße Tom. Ich bin 20 Jahre alt. Ich studiere an der Universität. Ich stehe um 06:45 Uhr auf, frühstücke um 07:15 Uhr "
            "und gehe um 07:45 Uhr zur Uni. Um 12:15 Uhr esse ich Mittag, danach lerne ich um 13:00 Uhr in der Bibliothek. Um 16:30 Uhr gehe "
            "ich nach Hause, spiele um 17:30 Uhr Tennis mit Freunden, esse um 19:00 Uhr Abendessen, sehe um 20:30 Uhr fern oder höre Musik "
            "und gehe um 22:45 Uhr ins Bett.")
TEXT_ANNA = ("Hallo! Ich heiße Anna. Ich bin 19 Jahre alt. Ich arbeite in einem Café. Ich stehe um 07:00 Uhr auf, frühstücke um 07:30 Uhr, "
             "trinke Kaffee und gehe um 08:00 Uhr zur Arbeit. Um 12:30 Uhr esse ich Mittag, arbeite weiter bis 16:00 Uhr, gehe dann einkaufen "
             "oder treffe Freunde. Um 18:30 Uhr esse ich Abendessen, lerne um 19:30 Uhr Deutsch oder lese ein Buch, sehe um 21:00 Uhr fern "
             "und gehe um 22:30 Uhr ins Bett.")
TEXT_TOM_UZ = ("Salom! Mening ismim Tom. Men 20 yoshdaman. Men universitetda o'qiyman. Men soat 06:45da uyg'onaman, 07:15da nonushta qilaman "
               "va 07:45da universitetga boraman. 12:15da tushlik qilaman, keyin 13:00da kutubxonada o'qiyman. 16:30da uyga qaytaman, 17:30da "
               "do'stlar bilan tennis o'ynayman, 19:00da kechki ovqat qilaman, 20:30da televizor tomosha qilaman yoki musiqa tinglayman va 22:45da yotaman.")
TEXT_ANNA_UZ = ("Salom! Mening ismim Anna. Men 19 yoshdaman. Men bir kafeda ishlayman. Men soat 07:00da uyg'onaman, 07:30da nonushta qilaman, "
                "qahva ichaman va 08:00da ishga boraman. 12:30da tushlik qilaman, keyin 16:00gacha ishlayman, so'ng do'konlarga boraman yoki "
                "do'stlarim bilan uchrashaman. 18:30da kechki ovqat qilaman, 19:30da nemis tilini o'qiyman yoki kitob o'qiyman, 21:00da televizor "
                "tomosha qilaman va 22:30da yotaman.")

LESEN = [
    mc("Um wie viel Uhr steht Tom auf?", ["06:00 Uhr", "06:45 Uhr", "07:15 Uhr"], "B", passage=1),
    mc("Was macht Tom um 07:15 Uhr?", ["Er geht zur Universität.", "Er frühstückt.", "Er spielt Tennis."], "B", passage=1),
    mc("Wann frühstückt Anna?", ["Um 07:00 Uhr", "Um 07:30 Uhr", "Um 08:00 Uhr"], "B", passage=2),
    mc("Was macht Anna nach der Arbeit?", ["Sie lernt Deutsch.", "Sie geht einkaufen oder trifft Freunde.", "Sie spielt Tennis."], "B", passage=2),
    mc("Um wie viel Uhr isst Anna Abendessen?", ["Um 18:30 Uhr", "Um 19:30 Uhr", "Um 21:00 Uhr"], "A", passage=2),
    mc("Um wie viel Uhr geht Tom ins Bett?", ["22:45 Uhr", "21:00 Uhr", "23:00 Uhr"], "A", passage=1),
]

HOEREN_TEXT = (
    "Hallo! Ich heiße Tom. Ich möchte euch von meinem Wochenende erzählen. Am Samstag stehe ich um [[1]] Uhr auf. Ich frühstücke um [[2]] Uhr und danach gehe ich spazieren. Um [[3]] Uhr treffe ich meine "
    "Freunde und wir spielen Fußball im Park. Um [[4]] Uhr esse ich Mittag zu Hause. Am Nachmittag lerne ich ein bisschen Deutsch und lese "
    "ein Buch. Um [[5]] Uhr gehe ich einkaufen und danach esse ich Abendessen. Am Abend sehe ich fern oder höre Musik. Um [[6]] Uhr gehe ich "
    "ins Bett.\nAm Sonntag stehe ich etwas später auf, um [[7]] Uhr. Ich frühstücke gemütlich und danach helfe ich meiner Mutter im Haus. "
    "Um [[8]] Uhr gehe ich mit meiner Familie ins Café oder wir essen zusammen zu Hause. Am Nachmittag gehe ich oft ins Kino oder treffe "
    "Freunde. Abends mache ich meine Hausaufgaben und lese ein Buch. Um [[9]] Uhr gehe ich schlafen.\n"
    "Mein Wochenende ist meistens interessant und ich habe viel Spaß mit meiner Familie und meinen Freunden."
)
# set by an admin after listening (accept e.g. "8:00", "08:00", "8.00", "8 Uhr")
HOEREN_GAPS = {str(i): [] for i in range(1, 10)}
OLD_SHEET_HINT = "Eski javoblar varag'i (tekshirilmagan): 1) 08:00 2) 08:30 3) 11:00 4) 13:00 5) 18:00 6) 23:00 7) 09:00 8) 12:00 9) 22:00"

WORDS = (
    words([("lernen", "o'rganmoq"), ("arbeiten", "ishlamoq"), ("wohnen", "yashamoq"), ("schlafen", "uxlash"), ("spielen", "o'ynamoq"),
           ("tanzen", "raqsga tushmoq"), ("lesen", "o'qimoq"), ("schreiben", "yozmoq"), ("essen", "yemoq"), ("trinken", "ichmoq"),
           ("gehen", "bormoq")], "Fe'llar")
    + words([("um … Uhr", "… da"), ("morgens", "ertalab"), ("mittags", "tush payti"), ("nachmittags", "tushdan keyin"),
             ("abends", "kechqurun"), ("nachts", "tun"), ("heute", "bugun"), ("am Wochenende", "hafta oxiri")], "Vaqt & kun")
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


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("Das richtige Fragewort", [
        choice_gap("___ stehst du auf? — Um sieben Uhr.", ["Wann", "Wo", "Was"], "Wann"),
        choice_gap("___ wohnst du? — In Taschkent.", ["Wo", "Wohin", "Wer"], "Wo"),
        choice_gap("___ isst du zum Frühstück? — Brot und Käse.", ["Was", "Wann", "Wie"], "Was"),
        choice_gap("___ spielst du Tennis? — Mit meinen Freunden.", ["Mit wem", "Wer", "Wohin"], "Mit wem"),
        choice_gap("___ lernst du Deutsch? — Ich möchte in Deutschland studieren.", ["Warum", "Wann", "Wo"], "Warum"),
        choice_gap("___ spät ist es? — Es ist halb acht.", ["Wie", "Was", "Wann"], "Wie"),
        choice_gap("___ Musik hörst du gern? — Popmusik.", ["Welche", "Wer", "Wo"], "Welche"),
        choice_gap("___ arbeitet Anna? — In einem Café.", ["Wo", "Wohin", "Woher"], "Wo", explanation="Lesen: „Ich arbeite in einem Café.“"),
    ], "Javobga mos savol so'zini tanlang.", source="vizu"),
    exercise("Wie spät ist es? (Lesen)", [
        choice_gap("Tom steht um 06:45 Uhr auf. — Informell: um ___ sieben.", ["Viertel vor", "Viertel nach", "halb"], "Viertel vor"),
        choice_gap("Anna frühstückt um 07:30 Uhr. — Informell: um ___.", ["halb acht", "halb sieben", "Viertel nach sieben"], "halb acht"),
        choice_gap("Tom isst um 12:15 Uhr Mittag. — Informell: um ___.", ["Viertel nach zwölf", "Viertel vor zwölf", "halb eins"], "Viertel nach zwölf"),
        choice_gap("Anna geht um 22:30 Uhr ins Bett. — Informell: um ___.", ["halb elf", "halb zehn", "halb zwölf"], "halb elf"),
        choice_gap("Tom geht um 22:45 Uhr ins Bett. — Formell: um ___ Uhr fünfundvierzig.", ["zweiundzwanzig", "zwölf", "zwanzig"], "zweiundzwanzig"),
    ], "Lesen matnidagi soatlarni boshqacha ayting.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 5", source="vizu", page=47, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Warum stellt man die Zeit in Deutschland um?", page=48,
             prompt="Warum stellen wir die Zeit in Deutschland um (Sommerzeit / Winterzeit)? Was wissen Sie darüber? "
                    "(Tageslicht besser nutzen, Energie sparen, Tagesrhythmus, Tradition)",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Fragesätze und Uhrzeiten", page="49-53",
             rules=[{"title": "Ja / Nein — Fragen", "html": _JA_NEIN}, {"title": "W-Fragesätze", "html": _W_FRAGEN},
                    {"title": "Die Uhrzeiten", "html": _UHRZEIT}],
             exercises=[
                 exercise("Aufgaben: Ja/Nein-Fragen (20)", JA_NEIN_EX, "Bilden Sie aus jedem Satz eine Ja/Nein-Frage."),
                 exercise("Aufgaben: W-Fragen (20)", W_EX, "Bilden Sie aus jedem Satz eine W-Frage mit dem angegebenen Fragewort."),
                 exercise("Aufgabe: Wie viel Uhr ist es? (informell)", UHR_EX,
                          "Kitobdagi soatlar (53-bet) raqam bilan berilgan. Soatni norasmiy yozing (z. B. „Viertel nach neun“).", source="vizu"),
             ]),
        base(L, "lesen", 1, "Lesen: Der Tagesablauf von Tom und Anna", page=54,
             instruction="Lesen Sie die Texte und antworten Sie auf die Fragen.",
             passages=[{"title": "Tom", "text": f"{TEXT_TOM}\n\nO'zbekcha tarjima: {TEXT_TOM_UZ}"},
                       {"title": "Anna", "text": f"{TEXT_ANNA}\n\nO'zbekcha tarjima: {TEXT_ANNA_UZ}"}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Mein Wochenende", page=55, audio_file="A1-5.mp3", key_pending=True,
             instruction="Hören Sie den Text und füllen Sie die Lücken mit der richtigen Uhrzeit aus.",
             metadata={"book_page": 55, "note": "Soatlar faqat audiodan aniqlanadi — admin A1-5.mp3 ni tinglab javoblarni belgilaydi. " + OLD_SHEET_HINT},
             questions=[gap("Mein Wochenende — tragen Sie die Uhrzeiten ein.", HOEREN_TEXT, HOEREN_GAPS, points=9)]),
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
        base(L, "wortschatz", 1, "Wortschatz Modul 5", page=58, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 5", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 5", source="vizu",
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
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 5", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
