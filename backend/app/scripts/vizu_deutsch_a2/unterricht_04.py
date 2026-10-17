"""A2 4. Unterricht — Tagesablauf und Zeitmanagement — Grammatik: Infinitiv mit zu (book pp. 41-52).

Book: Frage p.42, Regeln p.43, Aufgabe 1 / 2 (join two sentences, open
wording) pp.44-45, Lesen Aufgabe 1-3 (Richtig / Falsch / Der Text sagt
nichts dazu) pp.46-48, Hören (Familie Mannsberg, 12 questions, no transcript,
no key) p.49, Schreiben p.50, Sprechen p.51, Wortschatz (50 words) p.52.

Keys: "Vizu-Antworten A2" has none for this lesson. Lesen: decided by the
quoted sentence of the text. Handout gap exercises (60 x zu + Infinitiv,
30 x um / ohne / anstatt … zu): exactly one correct form each — the verb
given in brackets with "zu" (separable verbs: auf-zu-stehen). Hören waits
for an admin to set the key after listening (key_pending, stays a draft).
The book's Aufgabe 1 / 2 allow several correct sentences: a written task
checked by the teacher. Audio: the three files "A2 4.Unterricht Text 1-3"
belong to the one Hören task."""

from . import (
    article_set, base, exercise, forward_vocab_set, gap, intro_html, mc, mc_pending, numbered_words, reverse_vocab_set, summary_html,
    vocab_match_sets,
)

L = 4
LESSON_TITLE = "Tagesablauf und Zeitmanagement"
LESSON_DESCRIPTION = "Thema: Tagesablauf und Zeitmanagement · Grammatik: Infinitiv mit zu"
AUDIO = {"vizu-a2-l04-hoeren-01": ["A2 4.Unterricht Text 1.mp3", "A2 4.Unterricht Text 2.mp3", "A2 4.Unterricht Text 3.mp3"]}

EINFUEHRUNG_HTML = intro_html(
    4, "Tagesablauf und Zeitmanagement", "Infinitiv mit „zu“ (um … zu, ohne … zu, anstatt … zu)",
    ["„zu + Infinitiv“ ni fe'l, sifat va otdan keyin qo'llash: Ich versuche, Deutsch zu lernen.;",
     "ajraluvchi fe'llarda zu o'rtada turishini bilish: aufzustehen, einzukaufen;",
     "modal fe'llardan keyin zu ishlatilmasligini eslab qolish;",
     "kun tartibi va vaqtni rejalash so'zlarini o'rganish."],
    ["kuningizni qanday rejalashtirishingizni aytasiz;",
     "Ali, Lena va Martinning kundalik hayoti haqidagi matnlarni tushunasiz;",
     "bo'sh vaqtingiz haqida matn va dam olish kuniga taklif e-mailini yozasiz;",
     "dam olish kuningiz haqida gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(4, [
    "<strong>Zwei Verben:</strong> Ich versuche, Deutsch zu lernen. · Er plant, nach Deutschland zu fahren.",
    "<strong>Nach Adjektiven / Nomen:</strong> Es ist wichtig, Deutsch zu lernen. · Ich habe Lust, einen Film zu sehen.",
    "<strong>Trennbare Verben:</strong> Ich plane, morgen einzukaufen. · Wir versuchen, früh aufzustehen.",
    "<strong>Keine „zu“ bei Modalverben:</strong> Ich kann gut Deutsch sprechen.",
    "<strong>Merksatz:</strong> Ich hoffe, die Prüfung zu bestehen.",
])

RULES_HTML = (
    "<h3>Infinitiv mit „zu“ – Regeln</h3>"
    "<h4>1. Zwei Verben im Satz</h4><ul><li>Ich versuche, Deutsch zu lernen.</li><li>Wir hoffen, dich zu sehen.</li>"
    "<li>Er plant, nach Deutschland zu fahren.</li></ul>"
    "<h4>2. Nach bestimmten Verben</h4><ul><li>Sie fängt an, Sport zu treiben.</li><li>Er versucht, früher nach Hause zu kommen.</li>"
    "<li>Wir haben vergessen, das Fenster zu schließen.</li></ul>"
    "<h4>3. Nach Adjektiven</h4><ul><li>Es ist wichtig, Deutsch zu lernen.</li><li>Es ist schwer, diese Aufgabe zu lösen.</li>"
    "<li>Es ist interessant, neue Leute kennenzulernen.</li></ul>"
    "<h4>4. Nach Nomen</h4><ul><li>Ich habe Lust, einen Film zu sehen.</li><li>Wir haben Zeit, dir zu helfen.</li>"
    "<li>Sie hat die Möglichkeit, im Ausland zu studieren.</li></ul>"
    "<h4>5. Trennbare Verben</h4><ul><li>Ich plane, morgen einzukaufen.</li><li>Er hat vergessen, das Licht auszumachen.</li>"
    "<li>Wir versuchen, früh aufzustehen.</li></ul>"
    "<h4>6. Keine „zu“ bei Modalverben</h4><ul><li>Ich kann gut Deutsch sprechen.</li><li>Wir müssen lange arbeiten.</li>"
    "<li>Sie will nach Deutschland reisen.</li></ul>"
    "<p><strong>Merksatz: zu + Infinitiv</strong> — Ich hoffe, die Prüfung zu bestehen.</p>"
)
INFINITIVGRUPPE_HTML = (
    "<h3>Infinitivgruppe: um … zu, ohne … zu, anstatt … zu (Unterrichtsblatt)</h3>"
    "<ul><li><strong>um … zu</strong> — maqsad: Ich lerne Deutsch, um in Deutschland arbeiten zu können.</li>"
    "<li><strong>ohne … zu</strong> — biror ishni qilmasdan: Er geht aus dem Haus, ohne etwas zu sagen.</li>"
    "<li><strong>anstatt … zu</strong> — o'rniga: Er spielt Fußball, anstatt zu lernen.</li></ul>"
    "<p>„zu“ steht direkt vor dem Infinitiv am Ende; bei trennbaren Verben in der Mitte: das Licht aus<strong>zu</strong>machen.</p>"
)

SEPARABLE = ("kennen", "auf", "aus", "an", "zu", "ein", "mit", "fern", "vor")


def zu_inf(verb: str) -> str:
    """lernen -> zu lernen; trennbar: aufstehen -> aufzustehen (only the
    prefixes of the verbs in this lesson)."""
    for p in SEPARABLE:
        if verb.startswith(p) and len(verb) > len(p) + 2:
            return f"{p}zu{verb[len(p):]}"
    return f"zu {verb}"


_ZU = [  # handout p.4: (sentence with ___, verb)
    ("Ich versuche, Deutsch ___.", "lernen"), ("Wir planen, morgen nach Berlin ___.", "fahren"), ("Sie hofft, bald eine Arbeit ___.", "finden"),
    ("Er versucht, früher ___.", "kommen"), ("Ich beginne, ein neues Buch ___.", "lesen"), ("Wir hoffen, die Prüfung ___.", "bestehen"),
    ("Ich versuche, mehr Sport ___.", "machen"), ("Er versucht, seine Freunde ___.", "treffen"), ("Wir planen, am Wochenende ___.", "reisen"),
    ("Sie versucht, jeden Tag Deutsch ___.", "sprechen"), ("Er beginnt, ein Buch ___.", "lesen"), ("Ich versuche, mehr Wasser ___.", "trinken"),
    ("Wir planen, im Sommer nach Italien ___.", "reisen"), ("Sie hofft, ihre Freunde ___.", "sehen"), ("Ich verspreche, dir morgen ___.", "helfen"),
    ("Er vergisst, das Fenster ___.", "schließen"), ("Wir versuchen, früher ___.", "kommen"), ("Sie beginnt, Deutsch ___.", "lernen"),
    ("Ich hoffe, bald nach Deutschland ___.", "fahren"), ("Er versucht, eine Lösung ___.", "finden"),
    ("Es ist wichtig, jeden Tag Deutsch ___.", "lernen"), ("Es ist schwer, diese Aufgabe ___.", "lösen"),
    ("Es ist interessant, neue Leute ___.", "kennenlernen"), ("Es ist schön, Zeit mit der Familie ___.", "verbringen"),
    ("Es ist gesund, viel Wasser ___.", "trinken"), ("Es ist gefährlich, hier ___.", "schwimmen"), ("Es ist einfach, diese Übung ___.", "machen"),
    ("Es ist wichtig, pünktlich ___.", "sein"), ("Es ist schön, Musik ___.", "hören"), ("Es ist schwierig, Deutsch perfekt ___.", "sprechen"),
    ("Ich habe Zeit, dir ___.", "helfen"), ("Sie hat Lust, einen Film ___.", "sehen"), ("Wir haben die Möglichkeit, im Ausland ___.", "studieren"),
    ("Ich habe keine Zeit, heute ___.", "kommen"), ("Er hat Angst, einen Fehler ___.", "machen"), ("Sie hat den Wunsch, Arzt ___.", "werden"),
    ("Wir haben die Chance, ein neues Projekt ___.", "starten"), ("Ich habe die Hoffnung, bald eine Arbeit ___.", "finden"),
    ("Sie hat die Idee, ein Buch ___.", "schreiben"), ("Er hat die Möglichkeit, nach Deutschland ___.", "reisen"),
    ("Ich versuche, morgen früh ___.", "aufstehen"), ("Er hat vergessen, das Licht ___.", "ausmachen"), ("Wir planen, heute Abend ___.", "ausgehen"),
    ("Sie versucht, früher ___.", "ankommen"), ("Ich hoffe, dich morgen ___.", "anrufen"), ("Er beginnt, sein Zimmer ___.", "aufräumen"),
    ("Wir versuchen, das Fenster ___.", "aufmachen"), ("Sie vergisst oft, die Tür ___.", "zumachen"), ("Ich plane, morgen ___.", "einkaufen"),
    ("Er versucht, das Radio ___.", "anmachen"), ("Ich hoffe, dich bald ___.", "sehen"), ("Wir versuchen, jeden Tag Deutsch ___.", "lernen"),
    ("Es ist wichtig, gesund ___.", "leben"), ("Ich habe Lust, heute ins Kino ___.", "gehen"), ("Er hat vergessen, seine Hausaufgaben ___.", "machen"),
    ("Sie beginnt, ein neues Lied ___.", "lernen"), ("Wir planen, am Wochenende ___.", "reisen"), ("Es ist schön, neue Freunde ___.", "finden"),
    ("Ich habe Zeit, heute Sport ___.", "machen"), ("Er versucht, früh ___.", "aufstehen"),
]


def _zu_q(n: int, sentence: str, verb: str) -> dict:
    answer = zu_inf(verb)
    return gap("Ergänzen Sie mit zu + Infinitiv.", f"{n}. {sentence.replace('___', '[[1]]')} ({verb})", {"1": [answer]},
               explanation=f"{sentence.replace('___', answer)}" + (" — trennbares Verb: zu steht in der Mitte." if "zu" in answer and " " not in answer
                                                                    else ""))


ZU_SETS = [exercise(f"zu + Infinitiv ({a}–{a + 19})", [_zu_q(a + i, s, v) for i, (s, v) in enumerate(_ZU[a - 1:a + 19])],
                    "Ergänzen Sie die Sätze mit zu + Infinitiv (dars varag'i).") for a in (1, 21, 41)]

_UOA = [  # handout p.6: (main clause, middle words, verb, connector)
    ("Ich lerne Deutsch", "in Deutschland", "arbeiten", "um"), ("Er spart Geld", "ein neues Auto", "kaufen", "um"),
    ("Wir gehen früh schlafen", "morgen fit", "sein", "um"), ("Sie trainiert jeden Tag", "das Spiel", "gewinnen", "um"),
    ("Ich fahre in die Stadt", "neue Schuhe", "kaufen", "um"), ("Er liest viele Bücher", "mehr", "lernen", "um"),
    ("Wir machen eine Pause", "uns", "ausruhen", "um"), ("Sie geht ins Fitnessstudio", "gesund", "bleiben", "um"),
    ("Ich kaufe Obst", "gesund", "essen", "um"), ("Er fährt nach Deutschland", "Deutsch", "lernen", "um"),
    ("Er geht aus dem Haus", "etwas", "sagen", "ohne"), ("Sie schläft ein", "das Licht", "ausmachen", "ohne"),
    ("Wir gehen nach Hause", "etwas", "essen", "ohne"), ("Er verlässt das Zimmer", "sich", "verabschieden", "ohne"),
    ("Sie liest das Buch", "alles", "verstehen", "ohne"), ("Ich gehe ins Bett", "", "fernsehen", "ohne"), ("Wir fahren nach Hause", "Musik", "hören", "ohne"),
    ("Er geht vorbei", "mich", "sehen", "ohne"), ("Sie verlässt das Haus", "die Tür", "schließen", "ohne"),
    ("Ich gehe aus", "meine Freunde", "informieren", "ohne"),
    ("Er spielt Fußball", "", "lernen", "anstatt"), ("Sie sieht fern", "Hausaufgaben", "machen", "anstatt"), ("Wir gehen spazieren", "", "arbeiten", "anstatt"),
    ("Er schläft lange", "früh", "aufstehen", "anstatt"), ("Sie kauft Kleidung", "Geld", "sparen", "anstatt"), ("Ich höre Musik", "", "lernen", "anstatt"),
    ("Wir spielen Spiele", "das Zimmer", "aufräumen", "anstatt"), ("Er telefoniert", "", "arbeiten", "anstatt"),
    ("Sie geht ins Café", "zu Hause", "bleiben", "anstatt"), ("Ich sehe einen Film", "ein Buch", "lesen", "anstatt"),
]


def _uoa_q(n: int, main: str, middle: str, verb: str, conn: str) -> dict:
    tail = f"{verb} zu können" if conn == "um" else zu_inf(verb)
    hint = "(um / können)" if conn == "um" else f"({conn} / zu)"
    text = f"{n}. {main}, [[1]] {middle + ' ' if middle else ''}[[2]]. {hint}"
    full = f"{main}, {conn} {middle + ' ' if middle else ''}{tail}."
    return gap("Ergänzen Sie mit um … zu, ohne … zu oder anstatt … zu.", text, {"1": [conn], "2": [tail]}, points=2, explanation=full)


UOA_SETS = [exercise(title, [_uoa_q(a + i, *row) for i, row in enumerate(_UOA[a - 1:a + 9])], "Dars varag'i: bog'lovchi va zu-infinitivni yozing.")
            for title, a in (("um … zu (können)", 1), ("ohne … zu", 11), ("anstatt … zu", 21))]

JOIN_1 = [("Ich habe keine Zeit.", "Ich gehe einkaufen."), ("Er ist zu müde.", "Er arbeitet nicht heute Abend."), ("Wir haben Hunger.", "Wir gehen ins Restaurant."),
          ("Sie möchte Geld sparen.", "Sie kauft ein günstiges Auto."), ("Ich habe viel Arbeit.", "Ich muss heute länger bleiben."),
          ("Er hat Kopfschmerzen.", "Er nimmt eine Tablette."), ("Wir wollen fit bleiben.", "Wir machen jeden Tag Sport."),
          ("Es ist kalt draußen.", "Ich ziehe eine Jacke an."), ("Sie hat keine Erfahrung.", "Sie bekommt Hilfe von ihrem Freund."),
          ("Ich möchte Deutsch lernen.", "Ich suche einen guten Kurs.")]
JOIN_2 = [("Ich möchte früh aufstehen.", "Ich will pünktlich zur Arbeit kommen."), ("Er lernt jeden Tag Deutsch.", "Er möchte die Prüfung bestehen."),
          ("Wir kaufen ein Ticket.", "Wir wollen das Konzert sehen."), ("Sie geht zum Arzt.", "Sie will ihre Gesundheit kontrollieren."),
          ("Ich spare Geld.", "Ich möchte mir ein neues Handy kaufen."), ("Er macht Sport.", "Er will fit und gesund bleiben."),
          ("Wir üben viel.", "Wir wollen besser Deutsch sprechen."), ("Sie fragt nach dem Weg.", "Sie will den Bahnhof finden."),
          ("Ich lese Bücher.", "Ich möchte meinen Wortschatz verbessern."), ("Sie arbeitet hart.", "Sie will Erfolg im Beruf haben.")]

# ---------- Lesen (pp.46-48) ----------
TEXT_ALI = (
    "Ali ist 15 Jahre alt und Schüler. Er besucht eine Schule in seiner Stadt. Sein Tag beginnt früh am Morgen.\n\nAli steht jeden Tag um 7 Uhr auf. "
    "Zuerst wäscht er sich und putzt seine Zähne. Danach frühstückt er mit seiner Familie. Zum Frühstück isst er oft Brot mit Käse und trinkt Tee "
    "oder Milch.\n\nUm 7:30 Uhr geht Ali zur Schule. Die Schule beginnt um 8 Uhr. In der Schule hat er viele Fächer, zum Beispiel Deutsch, "
    "Mathematik, Englisch und Geschichte. Er hört den Lehrern zu, macht Übungen und schreibt manchmal Tests.\n\nDer Unterricht endet meistens um "
    "14 Uhr. Danach geht Ali nach Hause. Zu Hause isst er zuerst zu Mittag und ruht sich ein bisschen aus.\n\nAm Nachmittag macht Ali seine "
    "Hausaufgaben. Danach hat er Zeit für seine Hobbys. Er spielt sehr gern Fußball mit seinen Freunden im Park. Manchmal hört er auch Musik oder "
    "spielt Computerspiele.\n\nAm Abend isst Ali mit seiner Familie zu Abend. Danach spricht er mit seinen Eltern oder sieht ein bisschen fern. "
    "Bevor er schlafen geht, bereitet er seine Schultasche für den nächsten Tag vor. Um 22 Uhr geht Ali ins Bett.")
TEXT_LENA = (
    "Lena ist 25 Jahre alt und Studentin. Sie studiert an der Universität Kunst und Design, weil sie sehr gern malt und zeichnet.\n\nLena steht "
    "meistens um 8 Uhr auf. Danach duscht sie und frühstückt. Zum Frühstück trinkt sie Kaffee und isst Brot oder Joghurt.\n\nUm 9 Uhr fährt Lena "
    "mit dem Bus oder mit dem Fahrrad zur Universität. Am Vormittag hat sie Vorlesungen und Seminare. Dort lernt sie viel über Kunst, Farben und "
    "verschiedene Zeichentechniken.\n\nNach den Vorlesungen geht Lena oft zu einem Zeichenkurs. Dieser Kurs ist sehr wichtig für sie, weil sie "
    "später als Designerin arbeiten möchte. Im Kurs malt sie Bilder, zeichnet Menschen oder Gebäude und lernt neue Techniken.\n\nAm Nachmittag "
    "geht sie nach Hause oder in die Bibliothek. Dort macht sie ihre Hausaufgaben oder arbeitet an Projekten für die Universität.\n\nAm Abend hat "
    "Lena mehr Freizeit. Manchmal trifft sie ihre Freunde in einem Café oder geht spazieren. Oft hört sie Musik oder liest ein interessantes Buch."
    "\n\nBevor sie schlafen geht, plant Lena ihren nächsten Tag und schreibt ihre Aufgaben auf. Um 23 Uhr geht sie schlafen.")
TEXT_MARTIN = (
    "Martin ist 35 Jahre alt und arbeitet als Architekt. Sein Beruf gefällt ihm sehr, weil er gern Gebäude plant und kreativ arbeitet.\n\nMartin "
    "steht jeden Morgen um 6:30 Uhr auf. Danach duscht er und frühstückt. Er trinkt Kaffee und liest kurz die Nachrichten auf seinem Handy.\n\n"
    "Um 7:30 Uhr fährt er ins Büro. Seine Arbeit beginnt um 8 Uhr. Im Büro arbeitet Martin an verschiedenen Bauprojekten. Er zeichnet Pläne, "
    "arbeitet am Computer und spricht mit seinen Kollegen.\n\nManchmal hat er auch Meetings mit Kunden, um neue Ideen für Gebäude zu besprechen. "
    "Er erklärt seine Pläne und hört die Wünsche der Kunden.\n\nUm 13 Uhr macht Martin Mittagspause. Oft geht er mit seinen Kollegen in ein "
    "kleines Restaurant in der Nähe. Am Nachmittag arbeitet er weiter an seinen Projekten. Er kontrolliert Baupläne, macht neue Zeichnungen und "
    "schreibt E-Mails.\n\nUm 17 Uhr endet seine Arbeit. Danach fährt Martin nach Hause. Am Abend macht er oft Sport oder geht spazieren. Manchmal "
    "liest er Bücher über Architektur oder sieht einen Film.\n\nBevor er schlafen geht, bereitet er sich auf den nächsten Arbeitstag vor. Um "
    "22:30 Uhr geht Martin ins Bett.")
_RFN = ["Richtig", "Falsch", "Der Text sagt nichts dazu"]


def rfn(statement: str, answer: str, quote: str, passage: int) -> dict:
    return mc(statement, _RFN, answer, quote, passage=passage)


LESEN = [
    rfn("Ali ist 15 Jahre alt.", "A", "„Ali ist 15 Jahre alt und Schüler.“", 1),
    rfn("Ali steht jeden Tag um 7 Uhr auf.", "A", "„Ali steht jeden Tag um 7 Uhr auf.“", 1),
    rfn("Die Schule beginnt um 9 Uhr.", "B", "„Die Schule beginnt um 8 Uhr.“", 1),
    rfn("Nach der Schule macht Ali seine Hausaufgaben.", "A", "„Am Nachmittag macht Ali seine Hausaufgaben.“", 1),
    rfn("Ali spielt gern Fußball mit seinen Freunden.", "A", "„Er spielt sehr gern Fußball mit seinen Freunden im Park.“", 1),
    rfn("Ali geht um 23 Uhr schlafen.", "B", "„Um 22 Uhr geht Ali ins Bett.“", 1),
    rfn("Lena ist 25 Jahre alt und Studentin.", "A", "„Lena ist 25 Jahre alt und Studentin.“", 2),
    rfn("Lena studiert Kunst und Design.", "A", "„Sie studiert an der Universität Kunst und Design …“", 2),
    rfn("Lena steht jeden Tag um 6 Uhr auf.", "B", "„Lena steht meistens um 8 Uhr auf.“", 2),
    rfn("Nach den Vorlesungen geht Lena oft zu einem Zeichenkurs.", "A", "„Nach den Vorlesungen geht Lena oft zu einem Zeichenkurs.“", 2),
    rfn("Am Nachmittag geht Lena manchmal in die Bibliothek.", "A", "„Am Nachmittag geht sie nach Hause oder in die Bibliothek.“", 2),
    rfn("Lena arbeitet als Lehrerin.", "B", "„Lena ist … Studentin … weil sie später als Designerin arbeiten möchte.“", 2),
    rfn("Martin ist Architekt und 35 Jahre alt.", "A", "„Martin ist 35 Jahre alt und arbeitet als Architekt.“", 3),
    rfn("Martin steht jeden Morgen um 6:30 Uhr auf.", "A", "„Martin steht jeden Morgen um 6:30 Uhr auf.“", 3),
    rfn("Martin arbeitet in einem Krankenhaus.", "B", "„Um 7:30 Uhr fährt er ins Büro.“", 3),
    rfn("Im Büro plant Martin neue Gebäude.", "A", "„Im Büro arbeitet Martin an verschiedenen Bauprojekten. Er zeichnet Pläne …“", 3),
    rfn("Martin macht um 13 Uhr Mittagspause.", "A", "„Um 13 Uhr macht Martin Mittagspause.“", 3),
    rfn("Martin geht um 21 Uhr schlafen.", "B", "„Um 22:30 Uhr geht Martin ins Bett.“", 3),
]

_M = ["Johan Mannsberg", "Anna Mannsberg", "Julio Mannsberg"]
HOEREN = [  # p.49, options as printed (A, B, C); the book has no key and no transcript
    mc_pending("Wer ist 45 Jahre alt?", ["Johan Mannsberg", "Anna Mannsberg", "Julio Mannsberg"]),
    mc_pending("Wer bereitet am Wochenende das Frühstück für die Familie vor?", ["Julio Mannsberg", "Anna Mannsberg", "Johan Mannsberg"]),
    mc_pending("Wer arbeitet manchmal im Garten?", ["Johan Mannsberg", "Julio Mannsberg", "Anna Mannsberg"]),
    mc_pending("Wer ist 18 Jahre alt?", ["Anna Mannsberg", "Johan Mannsberg", "Julio Mannsberg"]),
    mc_pending("Wer trifft sich am Wochenende oft mit Freunden?", ["Johan Mannsberg", "Julio Mannsberg", "Anna Mannsberg"]),
    mc_pending("Wer macht oft Hausarbeit am Vormittag?", ["Anna Mannsberg", "Johan Mannsberg", "Julio Mannsberg"]),
    mc_pending("Wer geht manchmal ins Kino mit Freunden?", ["Julio Mannsberg", "Anna Mannsberg", "Johan Mannsberg"]),
    mc_pending("Wer liest am Wochenende manchmal ein Buch?", ["Johan Mannsberg", "Julio Mannsberg", "Anna Mannsberg"]),
    mc_pending("Wer kocht gern Abendessen für die Familie?", ["Anna Mannsberg", "Julio Mannsberg", "Johan Mannsberg"]),
    mc_pending("Wer spielt gern Fußball mit Freunden?", ["Johan Mannsberg", "Julio Mannsberg", "Anna Mannsberg"]),
    mc_pending("Wer besucht am Sonntag manchmal Freunde?", ["Johan Mannsberg", "Anna Mannsberg", "Julio Mannsberg"]),
    mc_pending("Wer macht manchmal einen Familienausflug am Sonntag?", ["Anna Mannsberg", "Julio Mannsberg", "Johan Mannsberg"]),
]

WORDS = numbered_words([
    ("der Tagesablauf", "kun tartibi"), ("die Zeit", "vaqt"), ("der Morgen", "tong"), ("der Vormittag", "tushgacha vaqt"), ("der Nachmittag", "tushdan keyin"),
    ("der Abend", "kechqurun"), ("die Nacht", "tun"), ("aufstehen", "turmoq"), ("frühstücken", "nonushta qilmoq"), ("das Frühstück", "nonushta"),
    ("zur Schule gehen", "maktabga bormoq"), ("arbeiten", "ishlamoq"), ("lernen", "o‘rganmoq"), ("studieren", "universitetda o‘qimoq"),
    ("der Unterricht", "dars"), ("die Hausaufgaben", "uy vazifasi"), ("die Pause", "tanaffus"), ("die Freizeit", "bo‘sh vaqt"), ("das Hobby", "hobbi"),
    ("Sport machen", "sport bilan shug‘ullanish"), ("spazieren gehen", "sayr qilmoq"), ("Freunde treffen", "do‘stlar bilan uchrashmoq"),
    ("Musik hören", "musiqa tinglamoq"), ("fernsehen", "televizor ko‘rmoq"), ("lesen", "o‘qimoq"), ("schlafen", "uxlamoq"), ("planen", "rejalashtirmoq"),
    ("der Plan", "reja"), ("organisieren", "tashkil qilmoq"), ("die Aufgabe", "vazifa"), ("wichtig", "muhim"), ("pünktlich", "vaqtida"), ("die Arbeit", "ish"),
    ("das Büro", "ofis"), ("der Student", "talaba"), ("der Schüler", "o‘quvchi"), ("der Architekt", "arxitektor"), ("das Projekt", "loyiha"),
    ("der Kunde", "mijoz"), ("der Termin", "uchrashuv vaqti"), ("der Kalender", "kalendar"), ("die Liste", "ro‘yxat"), ("die Gewohnheit", "odat"),
    ("produktiv", "samarali"), ("sich ausruhen", "dam olmoq"), ("der Alltag", "kundalik hayot"), ("die Familie", "oila"), ("das Wochenende", "hafta oxiri"),
    ("einkaufen", "xarid qilmoq"), ("vorbereiten", "tayyorlamoq")], "Tagesablauf")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 4. Unterricht", source="vizu", page=41, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie planen Sie Ihren Tag?", page=42,
             prompt="Wie planen Sie Ihren Tag? Erzählen Sie über Ihren Tagesablauf.\n\nWortschatz: planen — rejalashtirmoq · Tagesablauf — kun tartibi · "
                    "aufstehen — uyg‘onmoq · Frühstück machen — nonushta qilmoq · arbeiten — ishlamoq · Mittagspause — tushlik tanaffusi · "
                    "Sport machen — sport bilan shug‘ullanish · Zeit verbringen — vaqt o‘tkazmoq · schlafen gehen — uxlashga ketmoq",
             min_duration=20, max_duration=120,
             metadata={"book_sample": "Ich plane meinen Tag jeden Morgen. Ich stehe um 7:00 Uhr auf, mache Frühstück und gehe zur Arbeit. Ich arbeite "
                                      "von 9:00 bis 17:00 Uhr mit einer Mittagspause. Nach der Arbeit mache ich Sport und verbringe Zeit mit meiner "
                                      "Familie. Abends lerne ich Deutsch und gehe um 23:00 Uhr schlafen."}),
        base(L, "grammatik", 1, "Grammatik: Infinitiv mit „zu“", page=43,
             rules=[{"title": "Infinitiv mit „zu“ – Regeln", "html": RULES_HTML}, {"title": "Infinitivgruppe: um / ohne / anstatt … zu", "html": INFINITIVGRUPPE_HTML}],
             exercises=ZU_SETS + UOA_SETS),
        base(L, "schreiben", 2, "Grammatik-Aufgabe: Verbinden Sie die zwei Sätze mit „zu“ + Infinitiv", page="44-45", task_type="other",
             prompt="Verbinden Sie die zwei Sätze mit „zu“ + Infinitiv (Aufgabe 1) bzw. mit „um … zu“ (Aufgabe 2). Schreiben Sie alle Sätze vollständig."
                    "\n\nAufgabe 1:\n" + "\n".join(f"{i}. {a} + {b}" for i, (a, b) in enumerate(JOIN_1, start=1))
                    + "\n\nAufgabe 2:\n" + "\n".join(f"{i}. {a} + {b}" for i, (a, b) in enumerate(JOIN_2, start=1)),
             min_words=80, max_words=400, time_limit=30,
             metadata={"note": "Bir nechta to'g'ri variant bor — o'qituvchi tekshiradi."},
             support_phrases=["Ich habe keine Zeit, einkaufen zu gehen.", "Ich möchte früh aufstehen, um pünktlich zur Arbeit zu kommen."]),
        base(L, "lesen", 1, "Lesen: Tagesablauf von Ali, Lena und Martin (Aufgabe 1-3)", page="46-48",
             instruction="Lesen Sie die Texte. Richtig, falsch oder steht nicht im Text?",
             passages=[{"title": "Ein Schultag von Ali (15 Jahre)", "text": TEXT_ALI}, {"title": "Der Alltag einer Studentin – Lena (25 Jahre)", "text": TEXT_LENA},
                       {"title": "Ein Arbeitstag von Martin – Architekt (35 Jahre)", "text": TEXT_MARTIN}],
             questions=LESEN, max_score=len(LESEN),
             metadata={"note": "Javob har bir savol izohida matndan iqtibos bilan (Vizu-Antworten da kalit yo'q)."}),
        base(L, "hoeren", 1, "Hören: Familie Mannsberg", page=49, audio_file="A2 4.Unterricht Text 1-3.mp3", key_pending=True,
             instruction="Hören Sie die Texte über Familie Mannsberg und wählen Sie die richtige Person (A, B oder C).", questions=HOEREN,
             metadata={"note": "Kitobda transkript ham, javob ham yo'q — admin audioni tinglab javoblarni belgilaydi. Audio: Text 1, 2, 3."}),
        base(L, "schreiben", 1, "Schreiben: Wie verbringe ich meine Zeit?", page=50, task_type="description",
             prompt="Schreiben Sie einen kurzen Text über Ihre Freizeit. Gehen Sie auf folgende Punkte ein:\n• Wann haben Sie Freizeit?\n"
                    "• Was machen Sie am Nachmittag oder am Abend?\n• Welche Hobbys haben Sie?\n• Treffen Sie Freunde oder Familie in Ihrer Freizeit?\n"
                    "• Was machen Sie am Wochenende?\n• Warum ist Freizeit wichtig für Sie?",
             min_words=60, max_words=150, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: Informelle E-Mail – Einladung am Wochenende", page=50, task_type="email",
             prompt="Ihr Freund / Ihre Freundin hat am Wochenende Zeit. Sie möchten ihn / sie zu sich nach Hause einladen. Schreiben Sie eine E-Mail.\n"
                    "• Begrüßung (z. B. Hallo …)\n• Warum schreiben Sie die E-Mail?\n• Einladung zum Wochenende (Wann?)\n• Was möchten Sie zusammen machen?\n"
                    "• Was soll Ihr Freund / Ihre Freundin mitbringen?\n• Abschluss und Grüße",
             audience="Freund / Freundin (informell)", min_words=40, max_words=100, time_limit=20,
             support_phrases=["Hallo …,", "Hast du am Samstag Zeit?", "Ich möchte dich zu mir einladen.", "Wir können zusammen …", "Bring bitte … mit.",
                              "Liebe Grüße"]),
        base(L, "sprechen", 1, "Sprechen: Mein Wochenende", page=51, topic="Mein Wochenende",
             prompt="Sprechen Sie über Ihr Wochenende. Gehen Sie auf folgende Punkte ein:",
             questions=["Wann beginnt Ihr Wochenende?", "Treffen Sie Freunde oder Familie?", "Was machen Sie am Samstag?", "Haben Sie Hobbys am Wochenende?",
                        "Was machen Sie am Sonntag?", "Was machen Sie am Abend?", "Warum mögen Sie das Wochenende?", "Was machen Sie am liebsten?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Über das eigene Wochenende sprechen: Zeiten, Aktivitäten, Personen, Gründe.",
             keywords=["am Samstag", "am Sonntag", "am Abend", "Freunde", "Familie", "weil"]),
        base(L, "wortschatz", 1, "Wortschatz: Tagesablauf und Zeitmanagement", page=52, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen: A2 4. Unterricht", source="vizu", exercises=[s for s in (
            exercise("zu oder kein zu?", [
                mc("Ich kann gut Deutsch ___.", ["sprechen", "zu sprechen", "sprechen zu"], "A", "Keine „zu“ bei Modalverben (Regel 6)."),
                mc("Es ist wichtig, Deutsch ___.", ["zu lernen", "lernen", "lernen zu"], "A", "Nach Adjektiven: zu + Infinitiv (Regel 3)."),
                mc("Ich plane, morgen ___.", ["einzukaufen", "zu einkaufen", "einkaufen"], "A", "Trennbares Verb: einzukaufen (Regel 5)."),
                mc("Wir müssen lange ___.", ["arbeiten", "zu arbeiten", "arbeiten zu"], "A", "Modalverb: kein zu."),
                mc("Ich habe Lust, einen Film ___.", ["zu sehen", "sehen", "gesehen"], "A", "Nach Nomen: zu + Infinitiv (Regel 4)."),
                mc("Wir versuchen, früh ___.", ["aufzustehen", "zu aufstehen", "aufstehen"], "A", "Trennbares Verb: aufzustehen."),
            ], "Kitobdagi qoidalar bo'yicha to'g'ri shaklni tanlang.", source="vizu"),
            reverse_vocab_set(WORDS),
        ) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 4. Unterricht", source="vizu",
             instruction="Infinitiv mit zu va kun tartibi so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Ich hoffe, die Prüfung ___.", ["zu bestehen", "bestehen", "bestehen zu"], "A", "Merksatz der Lektion."),
                 mc("Er hat vergessen, das Licht ___.", ["auszumachen", "zu ausmachen", "ausmachen"], "A"),
                 mc("Sie will nach Deutschland ___.", ["reisen", "zu reisen", "reisen zu"], "A", "Modalverb: kein zu."),
                 mc("Ich lerne Deutsch, ___ in Deutschland arbeiten zu können.", ["um", "ohne", "anstatt"], "A"),
                 mc("Er geht aus dem Haus, ___ etwas zu sagen.", ["ohne", "um", "weil"], "A"),
                 mc("Um wie viel Uhr geht Ali ins Bett?", ["Um 22 Uhr", "Um 23 Uhr", "Um 21 Uhr"], "A", "Lesen, Aufgabe 1."),
                 mc("Was studiert Lena?", ["Kunst und Design", "Medizin", "Architektur"], "A", "Lesen, Aufgabe 2."),
                 mc("„der Tagesablauf“ — o'zbekchasi?", ["kun tartibi", "bo'sh vaqt", "hafta oxiri"], "A"),
                 mc("„pünktlich“ — o'zbekchasi?", ["vaqtida", "samarali", "muhim"], "A"),
                 mc("„der Termin“ — o'zbekchasi?", ["uchrashuv vaqti", "ro'yxat", "reja"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 4. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
