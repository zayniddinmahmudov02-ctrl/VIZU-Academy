"""Modul 3 — Das Leben in der Stadt — Grammatik: haben und sein, bestimmte und
unbestimmte Artikel (book pp. 27-37).

The book's p.35 "Schreiben" page is a haben/sein gap exercise with fixed
answers; it is placed in Grammatik (auto-graded). The free writing task and
the Lesen / Hören questions are created by VIZU (the book has texts and the
restaurant dialogues without questions)."""

from . import base, choice_gap, exercise, html_table, match, mc, text_gap, tf, words

L = 3

_HABEN_SEIN = (
    "<h3>HABEN — ega bo'lmoq</h3>"
    + html_table(["Shaxs", "haben", "Misol"],
                 [["ich", "habe", "Ich habe ein Buch. — Menda kitob bor."], ["du", "hast", "Du hast Zeit. — Senda vaqt bor."],
                  ["er / sie / es", "hat", "Er hat einen Bruder. — Uning akasi bor."], ["wir", "haben", "Wir haben eine Schule. — Bizning maktabimiz bor."],
                  ["ihr", "habt", "Ihr habt viele Freunde. — Sizlarning do'stlaringiz bor."],
                  ["sie / Sie", "haben", "Sie haben eine Frage. — Ularda / Sizda savol bor."]])
    + "<h3>SEIN — bo'lmoq</h3>"
    + html_table(["Shaxs", "sein", "Misol"],
                 [["ich", "bin", "Ich bin Lehrer. — Men o'qituvchiman."], ["du", "bist", "Du bist müde. — Sen charchagansan."],
                  ["er / sie / es", "ist", "Sie ist Studentin. — U talaba (qiz)."], ["wir", "sind", "Wir sind zu Hause. — Biz uydamiz."],
                  ["ihr", "seid", "Ihr seid pünktlich. — Sizlar vaqtida keldingiz."], ["sie / Sie", "sind", "Sie sind freundlich. — Siz muloyimsiz."]])
)

_ARTIKEL = html_table(
    ["Geschlecht / Kasus", "Aniq artikel (der / die / das / die)", "Noaniq artikel (ein / eine)"],
    [
        ["<strong>Maskulin</strong> — Nominativ", "Der Lehrer liest ein Buch.", "Ein Lehrer liest ein Buch."],
        ["Maskulin — Genitiv", "Des Lehrers Buch ist interessant.", "—"],
        ["Maskulin — Dativ", "Ich gebe dem Lehrer ein Buch.", "Ich gebe einem Lehrer ein Buch."],
        ["Maskulin — Akkusativ", "Ich sehe den Lehrer.", "Ich sehe einen Lehrer."],
        ["<strong>Feminin</strong> — Nominativ", "Die Lehrerin liest ein Buch.", "Eine Lehrerin liest ein Buch."],
        ["Feminin — Genitiv", "Der Lehrerin Buch ist interessant.", "—"],
        ["Feminin — Dativ", "Ich gebe der Lehrerin ein Buch.", "Ich gebe einer Lehrerin ein Buch."],
        ["Feminin — Akkusativ", "Ich sehe die Lehrerin.", "Ich sehe eine Lehrerin."],
        ["<strong>Neutrum</strong> — Nominativ", "Das Buch ist interessant.", "Ein Buch ist interessant."],
        ["Neutrum — Genitiv", "Des Buches Inhalt ist wichtig.", "—"],
        ["Neutrum — Dativ", "Ich gebe dem Buch Aufmerksamkeit.", "Ich gebe einem Buch Aufmerksamkeit."],
        ["Neutrum — Akkusativ", "Ich lese das Buch.", "Ich lese ein Buch."],
        ["<strong>Plural</strong> — Nominativ", "Die Lehrer lesen Bücher.", "—"],
        ["Plural — Genitiv", "Der Lehrer Bücher sind wichtig.", "—"],
        ["Plural — Dativ", "Ich gebe den Lehrern Bücher.", "—"],
        ["Plural — Akkusativ", "Ich sehe die Lehrer.", "—"],
    ],
)

_Q = "Setzen Sie haben oder sein in der richtigen Form ein."
_HS = [("Ich ___ ein Buch (kitob).", ["habe"]), ("Du ___ müde (charchagan).", ["bist"]), ("Er ___ Hunger (ochlik).", ["hat"]),
       ("Wir ___ zu Hause (uyda).", ["sind"]), ("Ihr ___ viele Freunde (ko'p do'stlar).", ["habt"]),
       ("Sie ___ Lehrer (o'qituvchi).", ["sind", "ist"]), ("Ich ___ eine Katze (mushuk).", ["habe"]), ("Du ___ pünktlich (vaqtida).", ["bist"]),
       ("Sie ___ ein Haus (uy).", ["haben", "hat"]), ("Wir ___ glücklich (baxtli).", ["sind"]), ("Er ___ krank (kasal).", ["ist"]),
       ("Ihr ___ ein Fahrrad (velosiped).", ["habt"]), ("Sie ___ viele Bücher (ko'p kitoblar).", ["haben", "hat"]),
       ("Ich ___ Zeit (vaqt).", ["habe"]), ("Du ___ laut (shovqinli).", ["bist"]), ("Es ___ klein (kichik).", ["ist"]),
       ("Wir ___ Schüler (o'quvchi).", ["sind"]), ("Ihr ___ Spaß (quvnoqlik).", ["habt"]), ("Er ___ einen Bruder (aka).", ["hat"]),
       ("Sie ___ freundlich (muloyim).", ["sind", "ist"]), ("Ich ___ Hunger (ochlik).", ["habe"]), ("Du ___ eine Katze (mushuk).", ["hast"]),
       ("Er ___ zu Hause (uyda).", ["ist"]), ("Wir ___ viele Bücher (ko'p kitoblar).", ["haben"]), ("Ihr ___ müde (charchagan).", ["seid"]),
       ("Sie ___ ein Auto (mashina).", ["haben", "hat"]), ("Ich ___ glücklich (baxtli).", ["bin"]), ("Du ___ freundlich (muloyim).", ["bist"]),
       ("Es ___ klein (kichik).", ["ist"]), ("Wir ___ Lehrer (o'qituvchi).", ["sind"])]
HABEN_SEIN = [text_gap(s, a, _Q, explanation=("Sie (Siz / ular) → " + a[0] + "; sie (u) → " + a[1] + ".") if len(a) > 1 else None) for s, a in _HS]

_P35 = [("Ich ___ heute viel Zeit.", ["habe"]), ("Du ___ sehr müde.", ["bist"]), ("Er ___ einen Bruder.", ["hat"]),
        ("Wir ___ heute in der Stadt.", ["sind"]), ("Ihr ___ ein schönes Haus.", ["habt"]), ("Sie ___ Lehrerin.", ["ist", "sind"]),
        ("Ich ___ einen Kaffee.", ["habe"]), ("Anna ___ sehr freundlich.", ["ist"]), ("Wir ___ viele Aufgaben.", ["haben"]),
        ("Die Kinder ___ im Park.", ["sind"]), ("Gestern ___ wir im Café.", ["waren", "sind"]), ("Mein Vater ___ Arzt.", ["ist"]),
        ("Ich ___ ein neues Buch.", ["habe"]), ("Du ___ heute sehr aktiv.", ["bist"]), ("Das Wetter ___ schön.", ["ist"]),
        ("Wir ___ am Wochenende frei.", ["haben", "sind"]), ("Ihr ___ gute Freunde.", ["seid", "habt"]), ("Ich ___ zwanzig Jahre alt.", ["bin"]),
        ("Er ___ Fußballspieler.", ["ist"]), ("Sie ___ aus Deutschland.", ["ist", "sind"])]
P35 = [text_gap(s, a, "Ergänzen Sie die richtige Form von haben oder sein im Präsens.",
                explanation="Gestern → o'tgan zamon: waren." if s.startswith("Gestern") else None) for s, a in _P35]

ARTIKEL_TEST = [
    mc("___ Mann liest ein Buch. (Odam kitob o'qiyapti.)", ["Der", "Die", "Das"], "A"),
    mc("Ich sehe ___ Frau im Garten. (Men ayolni bog'da ko'ryapman.)", ["Der", "Die", "Das"], "B"),
    mc("___ Kind spielt im Park. (Bola bog'da o'ynayapti.)", ["Der", "Die", "Das"], "C"),
    mc("Ich gebe ___ Mann ein Geschenk. (Men odamga sovg'a berayapman.)", ["Der", "Dem", "Den"], "B"),
    mc("Das Buch ___ Kindes ist interessant. (Bolaning kitobi qiziqarli.)", ["Des", "Der", "Dem"], "A"),
    mc("Ich sehe ___ Kinder auf der Straße. (Men bolalarni ko'ryapman.)", ["Die", "Den", "Das"], "A"),
    mc("Ich gebe ___ Frau einen Apfel. (Men ayolga olma berayapman.)", ["Die", "Der", "Dem"], "B"),
    mc("___ Vater arbeitet in einer Firma. (Ota firmada ishlaydi.)", ["Der", "Die", "Das"], "A"),
    mc("Ich sehe ___ Kind im Garten. (Men bolani bog'da ko'ryapman.)", ["Den", "Das", "Die"], "B"),
    mc("___ Spielsachen der Kinder sind neu. (Bolalarning o'yinchoqlari yangi.)", ["Die", "Der", "Des"], "A"),
    mc("___ Mann liest ein Buch. (Bir odam kitob o'qiyapti.)", ["Ein", "Eine", "Einer"], "A"),
    mc("Ich sehe ___ Frau im Garten. (Men bir ayolni bog'da ko'ryapman.)", ["Ein", "Eine", "Einer"], "B"),
    mc("___ Kind spielt im Park. (Bir bola bog'da o'ynayapti.)", ["Ein", "Eine", "Einer"], "A"),
    mc("Ich gebe ___ Mann ein Geschenk. (Men bir odamga sovg'a berayapman.)", ["Ein", "Einen", "Einem"], "C"),
    mc("Ich gebe ___ Frau einen Apfel. (Men bir ayolga olma berayapman.)", ["Ein", "Eine", "Einer"], "C"),
    mc("___ Mann arbeitet in einer Firma. (Bir odam firmada ishlaydi.)", ["Ein", "Eine", "Einer"], "A"),
    mc("Ich sehe ___ Kind im Garten. (Men bir bolani bog'da ko'ryapman.)", ["Ein", "Eine", "Einem"], "A"),
    mc("Ich sehe ___ Frau im Park. (Men bir ayolni ko'ryapman.)", ["Ein", "Eine", "Einer"], "B"),
    mc("Ich gebe ___ Kind ein Spielzeug. (Men bir bolaga o'yinchoq berayapman.)", ["Ein", "Eine", "Einem"], "C"),
    mc("___ Kind spielt im Park. (Bir bola bog'da o'ynayapti.)", ["Ein", "Eine", "Einer"], "A"),
]

TEXT_TOM = ("Tom arbeitet in einem Restaurant. Er hat viele Rezepte. Er liebt es zu kochen. Heute ist das Restaurant sehr voll. "
            "Viele Gäste sind da. Tom hat viel Gemüse, Fleisch und andere Zutaten vorbereitet. Er ist sehr beschäftigt, aber er ist glücklich. "
            "Manchmal hat Tom Stress, aber er hat Spaß an seiner Arbeit. Am Ende des Tages ist Tom müde, aber er hat alles geschafft. "
            "Er ist zufrieden, weil die Gäste das Essen mögen.")
TEXT_ANNA = ("Anna arbeitet in demselben Restaurant. Sie hat immer gute Laune. Sie bringt den Gästen das Essen. Heute ist das Restaurant sehr voll. "
             "Viele Gäste sind da. Anna hat viele Bestellungen aufgenommen. Sie ist schnell und freundlich. Manchmal ist Anna gestresst, "
             "aber sie hat Spaß an ihrer Arbeit. Am Ende des Tages ist Anna müde, aber sie hat alles gut gemacht. "
             "Sie ist zufrieden, weil die Gäste glücklich sind.")
LESEN = [
    mc("Wo arbeitet Tom?", ["In einer Schule", "In einem Restaurant", "In einem Krankenhaus"], "B", "„Tom arbeitet in einem Restaurant.“", passage=1),
    mc("Was ist Tom von Beruf?", ["Kellner", "Koch", "Lehrer"], "B", "Überschrift: „Tom ist Koch“; „Er liebt es zu kochen.“", passage=1),
    tf("Heute sind nur wenige Gäste im Restaurant.", False, "„Heute ist das Restaurant sehr voll. Viele Gäste sind da.“", passage=1),
    mc("Was hat Tom vorbereitet?", ["Gemüse, Fleisch und andere Zutaten", "Nur Kuchen", "Getränke"], "A", passage=1),
    mc("Warum ist Tom zufrieden?", ["Weil er frei hat", "Weil die Gäste das Essen mögen", "Weil er nicht müde ist"], "B", passage=1),
    mc("Was macht Anna im Restaurant?", ["Sie kocht.", "Sie bringt den Gästen das Essen.", "Sie bezahlt die Rechnung."], "B", passage=2),
    tf("Anna hat immer gute Laune.", True, "„Sie hat immer gute Laune.“", passage=2),
    mc("Wie ist Anna bei der Arbeit?", ["Langsam und unfreundlich", "Schnell und freundlich", "Müde und traurig"], "B", passage=2),
    tf("Anna hat keinen Spaß an ihrer Arbeit.", False, "„… aber sie hat Spaß an ihrer Arbeit.“", passage=2),
    mc("Warum ist Anna am Ende zufrieden?", ["Weil die Gäste glücklich sind", "Weil das Restaurant leer ist", "Weil sie viel Geld hat"], "A", passage=2),
]

HOEREN_TRANSCRIPT = (
    "1) Kellner: Guten Tag! Haben Sie einen Tisch reserviert? — Gast 1: Ja, wir haben einen Tisch für zwei Personen. — "
    "Kellner: Sehr gut. Folgen Sie mir bitte. — Gast 2: Danke. Der Tisch ist sehr schön.\n"
    "2) Kellner: Möchten Sie etwas trinken? — Gast 1: Ja, wir haben Durst. Ich habe gern ein Glas Wasser. — "
    "Gast 2: Ich habe Lust auf einen Apfelsaft. — Kellner: Sehr gut. Ich bringe Ihnen gleich die Getränke.\n"
    "3) Kellner: Sind Sie bereit zu bestellen? — Gast 1: Ja, ich habe Hunger. Ich nehme das Schnitzel mit Pommes. — "
    "Gast 2: Ich habe schon lange Lust auf Pizza. Ich nehme die Margherita.\n"
    "4) Kellner: Sind Sie Allergiker? — Gast 1: Nein, ich habe keine Allergien. — Gast 2: Ich auch nicht.\n"
    "5) Kellner: Hat es Ihnen geschmeckt? — Gast 1: Ja, das Essen war sehr lecker. Wir haben alles genossen. — "
    "Gast 2: Ja, alles war frisch. Wir sind sehr zufrieden.\n"
    "6) Kellner: Möchten Sie noch einen Kaffee oder Dessert? — Gast 1: Nein, danke. Wir haben genug. — Gast 2: Ja, wir sind satt.\n"
    "7) Kellner: Alles klar. Ich bringe Ihnen die Rechnung. — Gast 1: Vielen Dank! Wir haben heute einen schönen Abend gehabt. — "
    "Gast 2: Ja, es war sehr schön."
)
HOEREN = [
    mc("Für wie viele Personen ist der Tisch reserviert?", ["Für eine Person", "Für zwei Personen", "Für vier Personen"], "B"),
    mc("Was trinkt Gast 1?", ["Ein Glas Wasser", "Einen Apfelsaft", "Einen Kaffee"], "A"),
    mc("Was möchte Gast 2 trinken?", ["Wasser", "Einen Apfelsaft", "Tee"], "B"),
    mc("Was bestellt Gast 1?", ["Pizza Margherita", "Das Schnitzel mit Pommes", "Einen Salat"], "B"),
    mc("Was bestellt Gast 2?", ["Die Pizza Margherita", "Das Schnitzel", "Eine Suppe"], "A"),
    tf("Die Gäste haben Allergien.", False, "„Nein, ich habe keine Allergien. — Ich auch nicht.“"),
    tf("Das Essen war lecker und frisch.", True),
    mc("Möchten die Gäste noch einen Kaffee oder ein Dessert?", ["Ja, einen Kaffee", "Ja, ein Dessert", "Nein, sie sind satt"], "C"),
]

WORDS = (
    words([("der", "Mann", "odam, erkak"), ("die", "Frau", "ayol"), ("das", "Kind", "bola"), ("der", "Vater", "ota"), ("die", "Mutter", "ona"),
           ("der", "Freund", "do'st (erkak)"), ("die", "Freundin", "do'st (ayol)"), ("die", "Kinder", "bolalar"), ("der", "Kellner", "ofitsant"),
           ("die", "Kellnerin", "ofitsant ayol")], "Shaxslar va kasblar")
    + words([("haben", "ega bo'lmoq"), ("sein", "bo'lmoq"), ("lesen", "o'qimoq"), ("sehen", "ko'rmoq"), ("geben", "bermoq"), ("nehmen", "olmoq"),
             ("arbeiten", "ishlamoq"), ("kochen", "pishirmoq"), ("trinken", "ichmoq"), ("essen", "yemoq"), ("bezahlen", "to'lamoq"),
             ("finden", "topmoq"), ("schlafen", "uxlamoq"), ("lernen", "o'rganmoq"), ("mögen", "yoqtirmoq"), ("brauchen", "kerak bo'lmoq"),
             ("es gibt", "bor bo'lmoq")], "Fe'llar (A1 daraja)")
    + words([("gut", "yaxshi"), ("lecker", "mazali"), ("frisch", "yangi"), ("groß", "katta"), ("klein", "kichik"), ("schön", "chiroyli"),
             ("sauber", "toza"), ("freundlich", "do'stona, samimiy"), ("beschäftigt", "band"), ("müde", "charchagan"), ("zufrieden", "mamnun"),
             ("hungrig", "och"), ("durstig", "chanqoq"), ("glücklich", "baxtli"), ("voll", "to'la, gavjum"), ("schnell", "tez"),
             ("manchmal", "ba'zan")], "Sifatlar va boshqa so'zlar")
    + words([("das", "Buch", "kitob"), ("das", "Auto", "mashina"), ("das", "Handy", "telefon"), ("der", "Schlüssel", "kalit"),
             ("der", "Tisch", "stol"), ("der", "Stuhl", "stul"), ("der", "Stift", "ruchka"), ("das", "Spielzeug", "o'yinchoq"),
             ("die", "Lampe", "chiroq"), ("das", "Kleid", "ko'ylak")], "Buyumlar va narsalar")
    + words([("das", "Restaurant", "restoran"), ("die", "Rechnung", "hisob"), ("der", "Kaffee", "qahva"), ("der", "Saft", "sharbat"),
             ("das", "Wasser", "suv"), ("die", "Speisekarte", "menyu"), ("das", "Brot", "non"), ("das", "Essen", "taom"), ("die", "Pizza", "pitsa"),
             ("das", "Schnitzel", "shnitsel"), ("das", "Getränk", "ichimlik"), ("die", "Pommes", "kartoshka fri")], "Restoran so'zlari")
)


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage des Themas: Welche Städte wissen Sie in Deutschland?", page=28,
             prompt="Welche Städte wissen Sie in Deutschland? Nennen Sie Städte (z. B. Berlin, München, Hamburg, Köln, Frankfurt) "
                    "und sagen Sie einen Satz zu einer Stadt.",
             min_duration=10, max_duration=90),
        base(L, "grammatik", 1, "Grammatik: haben und sein, Artikel", page="29-32, 35",
             rules=[{"title": "Haben und sein", "html": _HABEN_SEIN},
                    {"title": "Bestimmte und unbestimmte Artikel", "html": _ARTIKEL}],
             exercises=[
                 exercise("Aufgaben: haben oder sein (30)", HABEN_SEIN, _Q),
                 exercise("Test: Artikel (20)", ARTIKEL_TEST, "Wählen Sie den richtigen Artikel."),
                 exercise("Schreiben-Aufgabe (Buch S. 35): haben oder sein im Präsens", P35,
                          "Ergänzen Sie die richtige Form von haben oder sein im Präsens. Tipp: Achten Sie auf das Personalpronomen."),
             ]),
        base(L, "lesen", 1, "Lesen: Tom ist Koch, Anna ist Kellnerin", page=33, source="vizu",
             instruction="Lesen Sie die Texte und beantworten Sie die Fragen.",
             metadata={"book_page": 33, "note": "Matnlar kitobdan; savollar VIZU tomonidan matn asosida tuzilgan."},
             passages=[{"title": "Tom ist Koch", "text": TEXT_TOM}, {"title": "Anna ist Kellnerin", "text": TEXT_ANNA}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Dialoge im Restaurant", page=34, source="vizu", audio_file="A1-3.mp3",
             instruction="Hören Sie die Dialoge im Restaurant und beantworten Sie die Fragen.",
             metadata={"book_page": 34, "note": "Dialoglar kitobdan (transkript); savollar VIZU tomonidan tuzilgan."},
             transcript=HOEREN_TRANSCRIPT, questions=HOEREN, max_score=len(HOEREN)),
        base(L, "schreiben", 1, "Schreiben: Ein Abend im Restaurant (VIZU qo'shimcha)", source="vizu",
             prompt="Sie waren mit einem Freund / einer Freundin im Restaurant. Schreiben Sie 5–7 Sätze:\n"
                    "Wer war dabei? Was haben Sie getrunken und gegessen? Wie war das Essen? Wie war der Kellner / die Kellnerin?\n"
                    "Benutzen Sie haben und sein.",
             task_type="description", min_words=30, max_words=80, time_limit=15,
             support_phrases=["Ich habe Hunger / Durst.", "Ich nehme …", "Das Essen ist lecker.", "Der Kellner ist freundlich.", "Ich bin satt."],
             metadata={"note": "Kitobda bu modul uchun erkin yozma topshiriq yo'q (S. 35 haben/sein mashqi Grammatik bo'limida)."}),
        base(L, "sprechen", 1, "Üben Sie die Dialoge im Restaurant!", page=36, topic="Im Restaurant",
             prompt="Spielen Sie den Gast. Lesen Sie den Dialog laut vor (Gast und Kellner) oder sprechen Sie die Rolle des Gastes frei.",
             questions=["Gast: Guten Tag! Ich hätte gern einen Tisch. — Kellner: Guten Tag! Natürlich, bitte folgen Sie mir. Hier ist Ihr Tisch.",
                        "Gast: Danke schön. Kann ich bitte die Speisekarte haben? — Kellner: Ja, hier bitte. Möchten Sie etwas trinken?",
                        "Gast: Ja, ein Wasser bitte. — Kellner: Kommt sofort.",
                        "Gast: Ich nehme die Pizza, bitte. — Kellner: Alles klar. Ich bringe das gleich.",
                        "Gast: Entschuldigung, kann ich noch Brot haben? — Kellner: Ja, natürlich. Bitte schön.",
                        "Gast: Vielen Dank! Das Essen schmeckt sehr gut. — Kellner: Das freut mich. Haben Sie alles, was Sie brauchen?",
                        "Gast: Ja, alles ist gut. Kann ich die Rechnung haben? — Kellner: Natürlich, hier bitte.",
                        "Gast: Danke schön! Auf Wiedersehen! — Kellner: Auf Wiedersehen und einen schönen Tag noch!"],
             response_type="dialog", min_duration=30, max_duration=120,
             speech_goal="Im Restaurant einen Tisch, die Speisekarte, ein Getränk, ein Essen und die Rechnung höflich erbitten.",
             keywords=["Speisekarte", "Ich nehme", "Rechnung", "bitte", "danke"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 3", page=37, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 3", source="vizu",
             instruction="haben / sein, artikllar va restoran so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Ich ___ heute keine Zeit.", ["habe", "bin", "hat"], "habe"),
                 choice_gap("Wir ___ sehr müde.", ["haben", "sind", "seid"], "sind"),
                 choice_gap("Ihr ___ gute Freunde.", ["seid", "habt", "sind"], "seid"),
                 choice_gap("Er ___ einen Bruder.", ["ist", "hat", "habt"], "hat"),
                 choice_gap("Du ___ Hunger.", ["bist", "hast", "hat"], "hast"),
                 mc("___ Frau arbeitet im Restaurant.", ["Der", "Die", "Das"], "B"),
                 mc("Ich sehe ___ Mann.", ["der", "den", "dem"], "B"),
                 mc("Ich gebe ___ Kind ein Buch.", ["dem", "den", "das"], "A"),
                 mc("Das ist ___ Tisch. (bir stol)", ["ein", "eine", "einen"], "A"),
                 mc("„die Rechnung“ — o'zbekchasi qaysi?", ["menyu", "hisob", "ichimlik"], "B"),
                 tf("„durstig“ bedeutet „chanqoq“.", True),
                 match("Was passt zusammen?", ["die Speisekarte", "das Getränk", "der Kellner", "lecker"],
                       ["menyu", "ichimlik", "ofitsant", "mazali", "kalit"], {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
