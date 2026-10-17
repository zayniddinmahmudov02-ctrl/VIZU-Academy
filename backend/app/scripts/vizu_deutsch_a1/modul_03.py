"""Modul 3 — Das Leben in der Stadt — Grammatik: haben und sein, bestimmte und
unbestimmte Artikel (book pp. 27-36).

Book pages: 27 cover, 28 Frage des Themas, 29 haben / sein, 30 Aufgaben
(30 sentences), 31 Artikel table, 32 Artikel test (20), 33 Lesen (two
texts, no questions), 34 Hören (restaurant dialogues 1-7; 8-12 repeat 1-5),
35 Schreiben (haben oder sein, 20 sentences), 36 Sprechen, 37 Wortschatz.
(The .docx edition of the book lacks p.35 — the PDF is the source.)

Book corrections: p.30 sentences 16 and 29 are the same ("Es ___ klein") and
p.32 questions 13 and 20 are the same ("___ Kind spielt im Park") — each is
asked once. p.35 sentence 11 "Gestern ___ wir im Café" needs the past
(waren) although the task says Präsens; only "waren" is accepted, with a
note. The Lesen / Hören questions and the free writing task are created by
VIZU from the book's texts (source "vizu")."""

from . import (
    forward_vocab_set,
    article_set, base, choice_gap, exercise, html_table, intro_html, match, mc, pairs, reverse_vocab_set, summary_html, text_gap, tf,
    vocab_match_sets, words,
)

L = 3
LESSON_TITLE = "Das Leben in der Stadt"
LESSON_DESCRIPTION = "Thema: Das Leben in der Stadt · Grammatik: haben und sein, bestimmte und unbestimmte Artikel"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 3 — Das Leben in der Stadt (Buch, S. 27)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    3, "Das Leben in der Stadt", "haben und sein, bestimmte und unbestimmte Artikel",
    ["„haben“ (ega bo'lmoq) va „sein“ (bo'lmoq) fe'llarini barcha shaxslarda tuslash;",
     "aniq (der / die / das) va noaniq (ein / eine) artikllarni Nominativ, Akkusativ, Dativ va Genitivda ishlatish;",
     "restoran va shahar hayotiga oid so'zlarni o'rganish;",
     "restoranda stol, menyu, taom va hisobni so'rash."],
    ["„Ich habe Hunger. Ich bin müde. Wir sind zu Hause.“ kabi gaplarni tuzasiz;",
     "„Ich sehe den Mann. Ich gebe der Frau einen Apfel.“ — artiklni to'g'ri tanlaysiz;",
     "Tom va Anna haqidagi matnlarni o'qib, savollarga javob berasiz;",
     "restorandagi dialoglarni tinglab tushunasiz va o'zingiz mehmon sifatida gapira olasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(3, [
    "<strong>haben:</strong> ich habe, du hast, er/sie/es hat, wir haben, ihr habt, sie/Sie haben.",
    "<strong>sein:</strong> ich bin, du bist, er/sie/es ist, wir sind, ihr seid, sie/Sie sind.",
    "<strong>Artikel (Nominativ / Akkusativ / Dativ):</strong> der / den / dem (Maskulin), die / die / der (Feminin), "
    "das / das / dem (Neutrum), die / die / den (Plural); ein / einen / einem, eine / eine / einer.",
    "<strong>Im Restaurant:</strong> Ich hätte gern einen Tisch. · Kann ich die Speisekarte haben? · Ich nehme … · Die Rechnung, bitte.",
])

# ============================================================
# Grammatik (pp. 29-32)
# ============================================================

_HABEN_SEIN = (
    "<h3>HABEN — ega bo'lmoq</h3>"
    + html_table(["Shaxs", "haben", "Ma'nosi", "Misol"],
                 [["ich", "habe", "menda bor", "Ich habe ein Buch. — Menda kitob bor."], ["du", "hast", "senda bor", "Du hast Zeit. — Senda vaqt bor."],
                  ["er / sie / es", "hat", "unda bor", "Er hat einen Bruder. — Uning akasi bor."],
                  ["wir", "haben", "bizda bor", "Wir haben eine Schule. — Bizning maktabimiz bor."],
                  ["ihr", "habt", "sizlarda bor", "Ihr habt viele Freunde. — Sizlarning do'stlaringiz bor."],
                  ["sie / Sie", "haben", "ularda / sizda bor", "Sie haben eine Frage. — Ularda / Sizda savol bor."]])
    + "<h3>SEIN — bo'lmoq</h3>"
    + html_table(["Shaxs", "sein", "Ma'nosi", "Misol"],
                 [["ich", "bin", "menman", "Ich bin Lehrer. — Men o'qituvchiman."], ["du", "bist", "sansan", "Du bist müde. — Sen charchagansan."],
                  ["er / sie / es", "ist", "u ...dir", "Sie ist Studentin. — U talaba (qiz)."], ["wir", "sind", "bizmiz", "Wir sind zu Hause. — Biz uydamiz."],
                  ["ihr", "seid", "sizlarsiz", "Ihr seid pünktlich. — Sizlar vaqtida keldingiz."],
                  ["sie / Sie", "sind", "ular / sizsiz", "Sie sind freundlich. — Siz muloyimsiz."]])
)

_ARTIKEL = (
    "<p><strong>Maskulin:</strong> der / des / dem / den · <strong>Feminin:</strong> die / der / der / die · "
    "<strong>Neutrum:</strong> das / des / dem / das · <strong>Plural:</strong> die / der / den / die</p>"
    + html_table(
        ["Geschlecht — Kasus", "Aniq artikel (der / die / das / die)", "Noaniq artikel (ein / eine)"],
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
)

_Q = "Setzen Sie haben oder sein in der richtigen Form ein."
# book p.30, sentences 1-30 without 29 (= 16)
_HS = [("Ich ___ ein Buch (kitob).", ["habe"]), ("Du ___ müde (charchagan).", ["bist"]), ("Er ___ Hunger (ochlik).", ["hat"]),
       ("Wir ___ zu Hause (uyda).", ["sind"]), ("Ihr ___ viele Freunde (ko'p do'stlar).", ["habt"]),
       ("Sie ___ Lehrer (o'qituvchi).", ["sind", "ist"]), ("Ich ___ eine Katze (mushuk).", ["habe"]), ("Du ___ pünktlich (vaqtida).", ["bist"]),
       ("Sie ___ ein Haus (uy).", ["haben", "hat"]), ("Wir ___ glücklich (baxtli).", ["sind"]), ("Er ___ krank (kasal).", ["ist"]),
       ("Ihr ___ ein Fahrrad (velosiped).", ["habt"]), ("Sie ___ viele Bücher (ko'p kitoblar).", ["haben", "hat"]),
       ("Ich ___ Zeit (vaqt).", ["habe"]), ("Du ___ laut (shovqinli).", ["bist"]), ("Es ___ klein (kichik).", ["ist"]),
       ("Wir ___ Schüler (o'quvchi).", ["sind"]), ("Ihr ___ Spaß (havo, quvnoqlik).", ["habt"]), ("Er ___ einen Bruder (aka).", ["hat"]),
       ("Sie ___ freundlich (muloyim).", ["sind", "ist"]), ("Ich ___ Hunger (ochlik).", ["habe"]), ("Du ___ eine Katze (mushuk).", ["hast"]),
       ("Er ___ zu Hause (uyda).", ["ist"]), ("Wir ___ viele Bücher (ko'p kitoblar).", ["haben"]), ("Ihr ___ müde (charchagan).", ["seid"]),
       ("Sie ___ ein Auto (mashina).", ["haben", "hat"]), ("Ich ___ glücklich (baxtli).", ["bin"]), ("Du ___ freundlich (muloyim).", ["bist"]),
       ("Wir ___ Lehrer (o'qituvchi).", ["sind"])]
HABEN_SEIN = [text_gap(s, a, _Q, explanation=("Sie (Siz / ular) → " + a[0] + "; sie (u) → " + a[1] + ".") if len(a) > 1 else None) for s, a in _HS]

# book p.32 without question 20 (= 13)
ARTIKEL_TEST = [
    mc("___ Mann liest ein Buch. (Odam kitob o'qiyapti.)", ["Der", "Die", "Das"], "A"),
    mc("Ich sehe ___ Frau im Garten. (Men ayolni bog'da ko'ryapman.)", ["Der", "Die", "Das"], "B"),
    mc("___ Kind spielt im Park. (Bola bog'da o'ynayapti.)", ["Der", "Die", "Das"], "C"),
    mc("Ich gebe ___ Mann ein Geschenk. (Men odamga sovg'a berayapman.)", ["Der", "Dem", "Den"], "B", "Dativ, Maskulin: dem."),
    mc("Das Buch ___ Kindes ist interessant. (Bolaning kitobi qiziqarli.)", ["Des", "Der", "Dem"], "A", "Genitiv, Neutrum: des Kindes."),
    mc("Ich sehe ___ Kinder auf der Straße. (Men bolalarni ko'ryapman.)", ["Die", "Den", "Das"], "A", "Akkusativ, Plural: die."),
    mc("Ich gebe ___ Frau einen Apfel. (Men ayolga olma berayapman.)", ["Die", "Der", "Dem"], "B", "Dativ, Feminin: der."),
    mc("___ Vater arbeitet in einer Firma. (Ota firmada ishlaydi.)", ["Der", "Die", "Das"], "A"),
    mc("Ich sehe ___ Kind im Garten. (Men bolani bog'da ko'ryapman.)", ["Den", "Das", "Die"], "B"),
    mc("___ Spielsachen der Kinder sind neu. (Bolalarning o'yinchoqlari yangi.)", ["Die", "Der", "Des"], "A"),
    mc("___ Mann liest ein Buch. (Bir odam kitob o'qiyapti.)", ["Ein", "Eine", "Einer"], "A"),
    mc("Ich sehe ___ Frau im Garten. (Men bir ayolni bog'da ko'ryapman.)", ["Ein", "Eine", "Einer"], "B"),
    mc("___ Kind spielt im Park. (Bir bola bog'da o'ynayapti.)", ["Ein", "Eine", "Einer"], "A"),
    mc("Ich gebe ___ Mann ein Geschenk. (Men bir odamga sovg'a berayapman.)", ["Ein", "Einen", "Einem"], "C", "Dativ, Maskulin: einem."),
    mc("Ich gebe ___ Frau einen Apfel. (Men bir ayolga olma berayapman.)", ["Ein", "Eine", "Einer"], "C", "Dativ, Feminin: einer."),
    mc("___ Mann arbeitet in einer Firma. (Bir odam firmada ishlaydi.)", ["Ein", "Eine", "Einer"], "A"),
    mc("Ich sehe ___ Kind im Garten. (Men bir bolani bog'da ko'ryapman.)", ["Ein", "Eine", "Einem"], "A"),
    mc("Ich sehe ___ Frau im Park. (Men bir ayolni ko'ryapman.)", ["Ein", "Eine", "Einer"], "B"),
    mc("Ich gebe ___ Kind ein Spielzeug. (Men bir bolaga o'yinchoq berayapman.)", ["Ein", "Eine", "Einem"], "C", "Dativ, Neutrum: einem."),
]

# ============================================================
# Schreiben (p. 35) — the book's haben / sein task + VIZU free task
# ============================================================

_P35 = [("Ich ___ heute viel Zeit.", ["habe"]), ("Du ___ sehr müde.", ["bist"]), ("Er ___ einen Bruder.", ["hat"]),
        ("Wir ___ heute in der Stadt.", ["sind"]), ("Ihr ___ ein schönes Haus.", ["habt"]), ("Sie ___ Lehrerin.", ["ist", "sind"]),
        ("Ich ___ einen Kaffee.", ["habe"]), ("Anna ___ sehr freundlich.", ["ist"]), ("Wir ___ viele Aufgaben.", ["haben"]),
        ("Die Kinder ___ im Park.", ["sind"]), ("Gestern ___ wir im Café.", ["waren"]), ("Mein Vater ___ Arzt.", ["ist"]),
        ("Ich ___ ein neues Buch.", ["habe"]), ("Du ___ heute sehr aktiv.", ["bist"]), ("Das Wetter ___ schön.", ["ist"]),
        ("Wir ___ am Wochenende frei.", ["haben", "sind"]), ("Ihr ___ gute Freunde.", ["seid", "habt"]), ("Ich ___ zwanzig Jahre alt.", ["bin"]),
        ("Er ___ Fußballspieler.", ["ist"]), ("Sie ___ aus Deutschland.", ["ist", "sind"])]
_P35_NOTE = {
    "Gestern ___ wir im Café.": "„Gestern“ (kecha) — o'tgan zamon: Gestern waren wir im Café. (Kitobda topshiriq „Präsens“ deydi, lekin bu gapda faqat „waren“ to'g'ri.)",
    "Wir ___ am Wochenende frei.": "Ikkalasi ham to'g'ri: Wir haben am Wochenende frei. / Wir sind am Wochenende frei.",
    "Ihr ___ gute Freunde.": "Ihr seid gute Freunde (do'stsizlar) yoki Ihr habt gute Freunde (yaxshi do'stlaringiz bor).",
    "Sie ___ Lehrerin.": "sie (u) ist; Sie (Siz) sind.",
    "Sie ___ aus Deutschland.": "sie (u) ist; sie / Sie (ular / Siz) sind.",
}
P35 = [text_gap(s, a, "Ergänzen Sie die richtige Form von haben oder sein im Präsens.", explanation=_P35_NOTE.get(s)) for s, a in _P35]

# ============================================================
# Lesen (p. 33) and Hören (p. 34)
# ============================================================

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
    mc("Was hat Tom vorbereitet?", ["Gemüse, Fleisch und andere Zutaten", "Nur Kuchen", "Getränke"], "A",
       "„Tom hat viel Gemüse, Fleisch und andere Zutaten vorbereitet.“", passage=1),
    mc("Warum ist Tom zufrieden?", ["Weil er frei hat", "Weil die Gäste das Essen mögen", "Weil er nicht müde ist"], "B",
       "„Er ist zufrieden, weil die Gäste das Essen mögen.“", passage=1),
    mc("Was macht Anna im Restaurant?", ["Sie kocht.", "Sie bringt den Gästen das Essen.", "Sie bezahlt die Rechnung."], "B",
       "„Sie bringt den Gästen das Essen.“", passage=2),
    tf("Anna hat immer gute Laune.", True, "„Sie hat immer gute Laune.“", passage=2),
    mc("Wie ist Anna bei der Arbeit?", ["Langsam und unfreundlich", "Schnell und freundlich", "Müde und traurig"], "B",
       "„Sie ist schnell und freundlich.“", passage=2),
    tf("Anna hat keinen Spaß an ihrer Arbeit.", False, "„… aber sie hat Spaß an ihrer Arbeit.“", passage=2),
    mc("Warum ist Anna am Ende zufrieden?", ["Weil die Gäste glücklich sind", "Weil das Restaurant leer ist", "Weil sie viel Geld hat"], "A",
       "„Sie ist zufrieden, weil die Gäste glücklich sind.“", passage=2),
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
    mc("Für wie viele Personen ist der Tisch reserviert?", ["Für eine Person", "Für zwei Personen", "Für vier Personen"], "B",
       "„Ja, wir haben einen Tisch für zwei Personen.“"),
    mc("Was trinkt Gast 1?", ["Ein Glas Wasser", "Einen Apfelsaft", "Einen Kaffee"], "A", "„Ich habe gern ein Glas Wasser.“"),
    mc("Was möchte Gast 2 trinken?", ["Wasser", "Einen Apfelsaft", "Tee"], "B", "„Ich habe Lust auf einen Apfelsaft.“"),
    mc("Was bestellt Gast 1?", ["Pizza Margherita", "Das Schnitzel mit Pommes", "Einen Salat"], "B", "„Ich nehme das Schnitzel mit Pommes.“"),
    mc("Was bestellt Gast 2?", ["Die Pizza Margherita", "Das Schnitzel", "Eine Suppe"], "A", "„Ich nehme die Margherita.“"),
    tf("Die Gäste haben Allergien.", False, "„Nein, ich habe keine Allergien. — Ich auch nicht.“"),
    tf("Das Essen war lecker und frisch.", True, "„… das Essen war sehr lecker … alles war frisch.“"),
    mc("Möchten die Gäste noch einen Kaffee oder ein Dessert?", ["Ja, einen Kaffee", "Ja, ein Dessert", "Nein, sie sind satt"], "C",
       "„Nein, danke. Wir haben genug. — Ja, wir sind satt.“"),
]

# ============================================================
# Wortschatz (p. 37) — book groups and translations
# ============================================================

WORDS = (
    words([("der", "Mann", "odam, erkak"), ("die", "Frau", "ayol"), ("das", "Kind", "bola"), ("der", "Vater", "ota"), ("die", "Mutter", "ona"),
           ("der", "Freund", "do'st (erkak)"), ("die", "Freundin", "do'st (ayol)"), ("die", "Kinder", "bolalar"), ("der", "Kellner", "ofitsant"),
           ("die", "Kellnerin", "ofitsant ayol")], "Shaxslar va kasblar")
    + words([("haben", "ega bo'lmoq"), ("sein", "bo'lmoq"), ("lesen", "o'qimoq"), ("sehen", "ko'rmoq"), ("geben", "berish"), ("nehmen", "olish"),
             ("arbeiten", "ishlamoq"), ("kochen", "pishirmoq"), ("trinken", "ichmoq"), ("essen", "yeymoq"), ("bezahlen", "to'lamoq"),
             ("finden", "topmoq"), ("schlafen", "uxlamoq"), ("lernen", "o'rganmoq"), ("mögen", "yoqtirmoq"), ("brauchen", "kerak bo'lmoq"),
             ("es gibt", "bor bo'lmoq")], "Fe'llar (A1 daraja)")
    + words([("gut", "yaxshi"), ("lecker", "mazali"), ("frisch", "yangi"), ("groß", "katta"), ("klein", "kichik"), ("schön", "chiroyli"),
             ("sauber", "toza"), ("freundlich", "do'stona, samimiy"), ("beschäftigt", "band, ishlaydigan"), ("müde", "charchagan"),
             ("zufrieden", "mamnun"), ("hungrig", "och"), ("durstig", "chanqoq"), ("glücklich", "baxtli"), ("voll", "to'la, gavjum"),
             ("schnell", "tez"), ("manchmal", "ba'zan")], "Sifatlar va boshqa so'zlar")
    + words([("das", "Buch", "kitob"), ("das", "Auto", "mashina"), ("das", "Handy", "telefon"), ("der", "Schlüssel", "kalit"),
             ("der", "Stift", "ruchka"), ("das", "Spielzeug", "o'yinchoq"), ("die", "Lampe", "chiroq"), ("das", "Kleid", "ko'ylak")],
            "Buyumlar va narsalar")
    + words([("das", "Restaurant", "restoran"), ("der", "Tisch", "stol"), ("der", "Stuhl", "stul"), ("die", "Speisekarte", "menyu"),
             ("das", "Essen", "taom"), ("das", "Getränk", "ichimlik"), ("die", "Rechnung", "hisob"), ("der", "Kaffee", "qahva"),
             ("der", "Saft", "sharbat"), ("das", "Wasser", "suv"), ("das", "Brot", "non"), ("die", "Pizza", "pitsa"),
             ("das", "Schnitzel", "schnitzel"), ("die", "Pommes", "kartoshka frit")], "Mehmonxona / restoran so'zlari")
)

WORTSCHATZ_SETS = [*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)]

# ============================================================
# Übungen / Abschlusstest
# ============================================================

UEBUNGEN_SETS = [
    exercise("haben oder sein? (Lesen & Hören)", [
        choice_gap("Tom ___ Koch.", ["ist", "hat", "bin"], "ist", explanation="Lesen: „Tom ist Koch“."),
        choice_gap("Tom ___ viele Rezepte.", ["hat", "ist", "habt"], "hat", explanation="Lesen: „Er hat viele Rezepte.“"),
        choice_gap("Anna ___ immer gute Laune.", ["hat", "ist", "hast"], "hat", explanation="Lesen: „Sie hat immer gute Laune.“"),
        choice_gap("Die Gäste ___ glücklich.", ["sind", "haben", "seid"], "sind", explanation="Lesen: „… weil die Gäste glücklich sind.“"),
        choice_gap("Wir ___ Durst.", ["haben", "sind", "habt"], "haben", explanation="Hören: „Ja, wir haben Durst.“"),
        choice_gap("Ich ___ Hunger.", ["habe", "bin", "hat"], "habe", explanation="Hören: „Ja, ich habe Hunger.“"),
        choice_gap("Wir ___ satt.", ["sind", "haben", "seid"], "sind", explanation="Hören: „Ja, wir sind satt.“"),
        choice_gap("Das Restaurant ___ heute sehr voll.", ["ist", "hat", "sind"], "ist", explanation="Lesen: „Heute ist das Restaurant sehr voll.“"),
    ], "Darsdagi matnlar asosida haben yoki sein ni tanlang.", source="vizu"),
    exercise("Artikel im Restaurant", [
        choice_gap("Ich nehme ___ Schnitzel. (das Schnitzel)", ["das", "den", "die"], "das", explanation="Akkusativ, Neutrum: das."),
        choice_gap("Ich bringe Ihnen ___ Rechnung. (die Rechnung)", ["die", "der", "den"], "die", explanation="Akkusativ, Feminin: die."),
        choice_gap("Kann ich ___ Speisekarte haben? (die Speisekarte)", ["die", "den", "das"], "die"),
        choice_gap("Wir haben ___ Tisch für zwei Personen. (der Tisch)", ["einen", "ein", "eine"], "einen", explanation="Akkusativ, Maskulin: einen."),
        choice_gap("Ich möchte ___ Glas Wasser. (das Glas)", ["ein", "einen", "eine"], "ein", explanation="Akkusativ, Neutrum: ein."),
        choice_gap("Der Kellner gibt ___ Gast die Rechnung. (der Gast)", ["dem", "den", "der"], "dem", explanation="Dativ, Maskulin: dem."),
    ], "Restoran gaplarida to'g'ri artiklni tanlang.", source="vizu"),
    reverse_vocab_set(WORDS),
]

ABSCHLUSSTEST = [
    choice_gap("Ich ___ heute keine Zeit.", ["habe", "bin", "hat"], "habe"),
    choice_gap("Wir ___ sehr müde.", ["haben", "sind", "seid"], "sind"),
    choice_gap("Ihr ___ pünktlich.", ["seid", "habt", "sind"], "seid"),
    choice_gap("Er ___ eine Schwester.", ["ist", "hat", "habt"], "hat"),
    choice_gap("Du ___ Zeit für mich.", ["bist", "hast", "hat"], "hast"),
    mc("___ Frau arbeitet im Restaurant.", ["Der", "Die", "Das"], "B"),
    mc("Ich sehe ___ Kellner.", ["der", "den", "dem"], "B", "Akkusativ, Maskulin: den."),
    mc("Ich gebe ___ Kellnerin das Geld.", ["der", "die", "dem"], "A", "Dativ, Feminin: der."),
    mc("Das ist ___ Tisch. (bir stol)", ["ein", "eine", "einen"], "A"),
    mc("„die Rechnung“ — o'zbekchasi qaysi?", ["menyu", "hisob", "ichimlik"], "B"),
    tf("„durstig“ bedeutet „chanqoq“.", True),
    tf("Anna ist Köchin im Restaurant. (Lesen)", False, "Lesen: „Anna ist Kellnerin“ — Tom ist Koch."),
    mc("Was sagt man im Restaurant am Ende?", ["Kann ich die Rechnung haben?", "Ich hätte gern einen Tisch.", "Haben Sie Allergien?"], "A"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 3", source="vizu", page=27, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Welche Städte wissen Sie in Deutschland?", page=28,
             prompt="Welche Städte wissen Sie in Deutschland? Nennen Sie Städte (z. B. Berlin, München, Hamburg, Köln, Frankfurt) "
                    "und sagen Sie einen Satz zu einer Stadt.",
             min_duration=10, max_duration=90),
        base(L, "wortschatz", 1, "Wortschatz Modul 3", page=37, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "grammatik", 1, "Grammatik: haben und sein, Artikel", page="29-32",
             rules=[{"title": "Haben und sein", "html": _HABEN_SEIN},
                    {"title": "Bestimmte und unbestimmte Artikel", "html": _ARTIKEL}],
             exercises=[
                 exercise("Aufgaben: haben oder sein (29)", HABEN_SEIN, _Q + " (Kitob, 30-bet.)"),
                 exercise("Test: Artikel (19)", ARTIKEL_TEST, "Wählen Sie den richtigen Artikel. (Kitob, 32-bet.)"),
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
        base(L, "schreiben_uebungen", 1, "Schreiben: haben oder sein (Buch S. 35)", page=35,
             exercises=[exercise("Aufgabe: haben oder sein im Präsens (20)", P35,
                                 "Ergänzen Sie die richtige Form von haben oder sein im Präsens. Tipp: Achten Sie auf das Personalpronomen. (Kitob, 35-bet.)")]),
        base(L, "schreiben", 1, "Schreiben: Ein Abend im Restaurant", source="vizu",
             prompt="Sie waren mit einem Freund / einer Freundin im Restaurant. Schreiben Sie 5–7 Sätze:\n"
                    "Wer war dabei? Was haben Sie getrunken und gegessen? Wie war das Essen? Wie war der Kellner / die Kellnerin?\n"
                    "Benutzen Sie haben und sein.",
             task_type="description", min_words=30, max_words=80, time_limit=15,
             support_phrases=["Ich habe Hunger / Durst.", "Ich nehme …", "Das Essen ist lecker.", "Der Kellner ist freundlich.", "Ich bin satt."],
             metadata={"note": "Kitobda bu modul uchun erkin yozma topshiriq yo'q — VIZU qo'shimcha topshirig'i."}),
        base(L, "uebungen", 1, "Übungen Modul 3", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 3", source="vizu",
             instruction="haben / sein, artikllar va restoran so'zlari bo'yicha yakuniy test.", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 3", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
