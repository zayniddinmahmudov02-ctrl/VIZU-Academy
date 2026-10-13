"""Modul 6 — Essen und Trinken — Grammatik: Modalverben, nicht / kein (book pp. 59-69).

p.67 (Schreiben: Sätze aus Wörtern bilden): a free-text answer would have to
know every correct word order, so each sentence is a choice between the
book's sentence and two wrong word orders (verb at the end / subject + verb
moved to the end) — never another correct order.
p.64 sentence 1 "Ich habe heute ___ Zeit" stands in the book's nicht column,
but only "keine" is correct German; "Ich trinke ___ Kaffee" accepts nicht
and keinen as the book's note on p.63 shows both.
Hören (p.66): only sentences 1-5 are decided by the pictures and the word
list (Brot, Butter, Marmelade, Käse, Wurst); the rest is set by an admin
after listening (key_pending)."""

from . import (
    article_set, base, choice_gap, exercise, gap, html_table, intro_html, match, mc, reverse_vocab_set, short, summary_html, text_gap, tf, ul,
    vocab_match_sets, word_order_mc, words,
)

L = 6
LESSON_TITLE = "Essen und Trinken"
LESSON_DESCRIPTION = "Thema: Essen und Trinken · Grammatik: Modalverben, nicht und kein"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 6 — Essen und Trinken (Buch, S. 59)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    6, "Essen und Trinken", "Modalverben (können, müssen, wollen, sollen, dürfen, mögen), nicht und kein",
    ["modal fe'llarni tuslash va gapda ishlatish: Ich kann gut kochen. Du musst Gemüse essen.;",
     "asosiy fe'l gap oxirida turishini bilish: Ich möchte Tee trinken.;",
     "inkor qilish: nicht (fe'l, sifat, butun gap) va kein / keine / keinen (ot bilan);",
     "ovqat va ichimlik nomlarini o'rganish: das Brot, der Käse, das Obst, der Saft …"],
    ["„Zum Frühstück esse ich Brot mit Butter. Ich trinke keinen Kaffee.“ — ovqatlanish odatlaringizni aytasiz;",
     "„Darf ich hier sitzen? Kannst du kochen?“ kabi savollar berasiz;",
     "Markusning ovqatlanish odatlari haqidagi matnni o'qib tushunasiz;",
     "ovqat haqidagi gaplarni tinglab, yetishmayotgan so'zlarni yozasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(6, [
    "<strong>Modalverben:</strong> ich kann / muss / will / soll / darf / mag · du kannst / musst / willst / sollst / darfst / magst · "
    "wir können / müssen / wollen / sollen / dürfen / mögen.",
    "<strong>Satzbau:</strong> Modalverb auf Position 2, Infinitiv am Ende — Ich muss heute Hausaufgaben machen.",
    "<strong>nicht:</strong> Ich esse nicht. Das ist nicht gut. · <strong>kein:</strong> Ich habe kein Geld / keine Zeit / keinen Hund.",
    "<strong>Essen und Trinken:</strong> zum Frühstück, zum Mittagessen, zum Abendessen; das Brot, die Butter, der Käse, das Obst, das Gemüse, der Saft.",
])

_MODAL = (
    "<p>Modalfe'l 2-o'rinda tuslanadi, asosiy fe'l <strong>infinitivda gap oxirida</strong> turadi.</p>"
    + html_table(["", "können — qila olmoq / mumkin", "müssen — majbur bo'lmoq / kerak", "wollen — xohlamoq"],
                 [["ich", "kann (Fußball spielen)", "muss (arbeiten)", "will (Deutsch lernen)"],
                  ["du", "kannst (Deutsch sprechen)", "musst (lernen)", "willst (schlafen)"],
                  ["er / sie / es", "kann (Auto fahren)", "muss (gehen)", "will (essen)"],
                  ["wir", "können (heute lernen)", "müssen (warten)", "wollen (bleiben)"],
                  ["ihr", "könnt (schnell kommen)", "müsst (kommen)", "wollt (gehen)"],
                  ["sie / Sie", "können (mir helfen)", "müssen (helfen)", "wollen (fragen)"],
                  ["Misol", "Kannst du Deutsch sprechen? — Ja, ich kann Deutsch sprechen.",
                   "Musst du heute arbeiten? — Ja, ich muss heute arbeiten.", "Willst du Deutsch lernen? — Ja, ich will Deutsch lernen."]])
    + html_table(["", "sollen — kerak (maslahat / buyruq)", "dürfen — mumkin / ruxsat", "mögen — yoqtirmoq / xohlamoq"],
                 [["ich", "soll (lernen)", "darf (gehen)", "mag (Kaffee trinken)"],
                  ["du", "sollst (kommen)", "darfst (fragen)", "magst (Musik hören)"],
                  ["er / sie / es", "soll (helfen)", "darf (bleiben)", "mag (lesen)"],
                  ["wir", "sollen (warten)", "dürfen (sprechen)", "mögen (Filme sehen)"],
                  ["ihr", "sollt (zuhören)", "dürft (essen)", "mögt (Sport machen)"],
                  ["sie / Sie", "sollen (antworten)", "dürfen (sitzen)", "mögen (Ruhe haben)"],
                  ["Misol", "Soll ich anfangen? — Ja, du sollst anfangen.", "Darf ich hier sitzen? — Ja, du darfst hier sitzen.",
                   "Magst du Kaffee trinken? — Ja, ich mag Kaffee trinken."]])
)
_NICHT_KEIN = (
    html_table(["", "nicht — „emas“", "kein — „hech qaysi / yo'q“"],
               [["Qachon ishlatiladi", "Fe'lni, sifatni, ravishni yoki butun gapni inkor qilish: Ich spiele nicht. — Men o'ynamayman. "
                 "Das ist nicht gut. — Bu yaxshi emas. Ich mag den Film nicht. — Men filmni yoqtirmayman.",
                 "Otlar bilan (der / die / das → kein, plural → keine); „no / not any“ ma'nosi."],
                ["Strukturasi", "Subjekt + Verb + nicht + qolgan gap", "Subjekt + Verb + kein / keine + Nomen"],
                ["Misollar", "Ich esse nicht. — Men yemayman. Er ist nicht müde. — U charchamagan. "
                 "Wir haben nicht genug Zeit. — Bizda yetarli vaqt yo'q.",
                 "Ich habe kein Geld. — Menda pul yo'q. Sie hat keine Zeit. — Unda vaqt yo'q. Wir sehen keinen Hund. — Biz itni ko'rmayapmiz."]])
    + "<p><strong>Eslatma:</strong> nicht — fe'lni, sifatni yoki butun gapni inkor qiladi; kein / keine — ot (Nomen) bilan ishlatiladi. "
      "Ich trinke <strong>keinen</strong> Kaffee.</p>"
)

_Q = "Setzen Sie das richtige Modalverb in der passenden Form ein."
_MV = [("Ich ___ (können) Deutsch sprechen.", ["kann"]), ("Du ___ (müssen) Hausaufgaben machen.", ["musst"]),
       ("Er ___ (wollen) ein Buch lesen.", ["will"]), ("Wir ___ (mögen) Filme sehen.", ["mögen"]), ("Ihr ___ (dürfen) jetzt kommen.", ["dürft"]),
       ("Sie ___ (sollen) mir helfen. (menga yordam berishi kerak)", ["sollen", "soll"]), ("Ich ___ (mögen) Kaffee trinken.", ["mag"]),
       ("Du ___ (dürfen) eine Frage stellen.", ["darfst"]), ("Er ___ (können) Auto fahren.", ["kann"]), ("Wir ___ (wollen) zu Hause bleiben.", ["wollen"]),
       ("Ihr ___ (können) schnell laufen.", ["könnt"]), ("Sie ___ (mögen) Ruhe haben.", ["mögen", "mag"]), ("Ich ___ (müssen) arbeiten.", ["muss"]),
       ("Du ___ (wollen) schlafen.", ["willst"]), ("Er ___ (dürfen) essen.", ["darf"]), ("Wir ___ (sollen) lernen.", ["sollen"]),
       ("Ihr ___ (müssen) Fragen beantworten.", ["müsst"]), ("Sie ___ (können) Deutsch sprechen. (nemischa gapira oladilar)", ["können"]),
       ("Ich ___ (können) Fußball spielen.", ["kann"]), ("Du ___ (müssen) zum Arzt gehen.", ["musst"]), ("Er ___ (sollen) mir helfen.", ["soll"]),
       ("Wir ___ (dürfen) warten.", ["dürfen"]), ("Ihr ___ (mögen) Musik hören.", ["mögt"]), ("Sie ___ (wollen) zu Hause bleiben.", ["wollen", "will"]),
       ("Ich ___ (mögen) ein Buch lesen.", ["mag"]), ("Du ___ (dürfen) gehen.", ["darfst"]), ("Er ___ (können) eine Frage stellen.", ["kann"]),
       ("Wir ___ (sollen) antworten.", ["sollen"]), ("Ihr ___ (dürfen) essen.", ["dürft"]),
       ("Sie ___ (müssen) lernen. (o'rganishlari kerak)", ["müssen"])]
MODAL_EX = [text_gap(s, a, _Q, explanation=f"Javob: {a[0]}" + (f" (sie — u: {a[1]})" if len(a) > 1 else "")) for s, a in _MV]

_NK = "Ergänzen Sie die Sätze mit nicht oder kein in der richtigen Form."
NICHT_EX = [
    text_gap("Ich habe heute ___ Zeit.", ["keine"], _NK,
             explanation="Zeit — ot (Nomen), shuning uchun kein: Ich habe heute keine Zeit. (Kitobda bu gap „nicht“ ustunida berilgan.)"),
    text_gap("Er kann ___ Deutsch sprechen.", ["nicht", "kein"], _NK),
    text_gap("Wir gehen heute ___ ins Kino.", ["nicht"], _NK),
    text_gap("Sie hat ___ viel Geld.", ["nicht"], _NK),
    text_gap("Das Essen ist ___ gut.", ["nicht"], _NK),
    text_gap("Ich verstehe die Aufgabe ___.", ["nicht"], _NK),
    text_gap("Du musst ___ zu spät kommen.", ["nicht"], _NK),
    text_gap("Wir haben ___ genug Platz.", ["nicht"], _NK),
    text_gap("Er spielt ___ Fußball.", ["nicht", "kein"], _NK),
    text_gap("Ich trinke ___ Kaffee.", ["nicht", "keinen"], _NK, explanation="Kitob: „Ich trinke nicht Kaffee.“ / „Ich trinke keinen Kaffee.“"),
    text_gap("Ich habe ___ Geld.", ["kein"], _NK),
    text_gap("Sie hat ___ Bruder.", ["keinen"], _NK),
    text_gap("Wir sehen ___ Film.", ["keinen"], _NK),
    text_gap("Er trinkt ___ Alkohol.", ["keinen"], _NK),
    text_gap("Du hast ___ Zeit.", ["keine"], _NK),
    text_gap("Ich kaufe ___ Brot.", ["kein"], _NK),
    text_gap("Wir haben ___ Auto.", ["kein"], _NK),
    text_gap("Sie isst ___ Fleisch.", ["kein"], _NK),
    text_gap("Ihr bringt ___ Bücher.", ["keine"], _NK),
    text_gap("Er fragt ___ Fragen.", ["keine"], _NK),
]

_SB = [("ich / jeden Morgen / Brot / esse", ["Ich esse jeden Morgen Brot.", "Jeden Morgen esse ich Brot."]),
       ("Wasser / trinke / ich / oft", ["Ich trinke oft Wasser.", "Oft trinke ich Wasser."]),
       ("zum Mittagessen / Nudeln / ich / esse", ["Ich esse zum Mittagessen Nudeln.", "Zum Mittagessen esse ich Nudeln."]),
       ("ich / gern / Käse / esse", ["Ich esse gern Käse.", "Ich esse Käse gern."]),
       ("Saft / trinke / ich / zum Frühstück", ["Ich trinke zum Frühstück Saft.", "Zum Frühstück trinke ich Saft.", "Ich trinke Saft zum Frühstück."]),
       ("ich / darf / hier / sitzen", ["Ich darf hier sitzen.", "Hier darf ich sitzen."]),
       ("oft / ich / Obst / esse", ["Ich esse oft Obst.", "Oft esse ich Obst."]),
       ("ich / trinke / Milch / abends", ["Ich trinke abends Milch.", "Abends trinke ich Milch.", "Ich trinke Milch abends."]),
       ("ich / mag / Paprika", ["Ich mag Paprika."]),
       ("ich / muss / Hausaufgaben / machen", ["Ich muss Hausaufgaben machen."]),
       ("ich / Gemüse / oft / esse", ["Ich esse oft Gemüse.", "Oft esse ich Gemüse."]),
       ("Frühstück / ich / esse / Butter", ["Ich esse Butter zum Frühstück.", "Zum Frühstück esse ich Butter.", "Ich esse zum Frühstück Butter."]),
       ("ich / kann / gut / kochen", ["Ich kann gut kochen."]),
       ("ich / trinke / keinen / Kaffee", ["Ich trinke keinen Kaffee."]),
       ("ich / möchte / Tee / trinken", ["Ich möchte Tee trinken."]),
       ("ich / esse / nicht / viel / Schokolade", ["Ich esse nicht viel Schokolade."]),
       ("ich / manchmal / Wurst / esse", ["Ich esse manchmal Wurst.", "Manchmal esse ich Wurst."]),
       ("ich / koche / Kartoffeln / mit / Gemüse", ["Ich koche Kartoffeln mit Gemüse."]),
       ("ich / esse / Salat / gern", ["Ich esse gern Salat.", "Ich esse Salat gern."]),
       ("ich / kaufe / keine / Süßigkeiten", ["Ich kaufe keine Süßigkeiten."])]
SATZBAU = [word_order_mc(w, acc[0]) for w, acc in _SB]

TEXT = ("Hallo! Ich heiße Markus. Ich möchte über meine Essgewohnheit erzählen. Ich frühstücke jeden Tag um 7 Uhr. Zum Frühstück esse ich "
        "Brot, Butter, Marmelade und manchmal Käse oder Wurst. Ich trinke dazu Kaffee oder Tee.\n\n"
        "Mittags esse ich meistens Reis, Nudeln oder Kartoffeln mit Gemüse, Fleisch oder Fisch. Ich mag Salat, Tomaten, Gurken, Karotten "
        "und Paprika. Manchmal esse ich auch Suppe.\n\n"
        "Am Nachmittag esse ich oft Obst wie Äpfel, Bananen, Orangen oder Trauben. Ich trinke Wasser, Saft oder Milch.\n\n"
        "Abends esse ich Brot mit Käse oder Schinken. Manchmal koche ich auch ein warmes Gericht. Ich esse Fleisch wie Huhn, Rind oder "
        "Schwein. Ich mag auch Fisch wie Lachs oder Thunfisch.\n\n"
        "Ich liebe Süßigkeiten, Schokolade, Kuchen und Kekse. Ich esse sie aber nur selten. Ich achte auf gesunde Ernährung. Ich esse viel "
        "Obst und Gemüse, und ich trinke viel Wasser.")
LESEN = [
    mc("Wann frühstückt Markus?", ["Um 6 Uhr", "Um 7 Uhr", "Um 8 Uhr"], "B", "„Ich frühstücke jeden Tag um 7 Uhr.“"),
    mc("Was isst Markus zum Frühstück?", ["Brot, Butter, Marmelade und manchmal Käse oder Wurst", "Reis und Fisch", "Obst und Kuchen"], "A"),
    mc("Was isst er mittags?", ["Nur Suppe", "Meistens Reis, Nudeln oder Kartoffeln mit Gemüse, Fleisch oder Fisch", "Brot mit Schinken"], "B"),
    mc("Was isst er am Nachmittag?", ["Oft Obst wie Äpfel, Bananen, Orangen oder Trauben", "Schokolade und Kekse", "Ein warmes Gericht"], "A"),
    mc("Was isst er abends?", ["Brot mit Käse oder Schinken", "Nur Obst", "Nudeln mit Gemüse"], "A", "„Abends esse ich Brot mit Käse oder Schinken.“"),
    tf("Markus isst jeden Tag viele Süßigkeiten.", False, "„Ich esse sie aber nur selten.“"),
    tf("Markus trinkt viel Wasser.", True),
]

_SENT = ["Ich esse jeden Morgen [[1]].", "Zum Frühstück esse ich [[2]].", "Ich streiche [[3]] auf mein Brot.", "Ich esse gern [[4]].",
         "Manchmal esse ich [[5]].", "Zum Mittagessen esse ich [[6]].", "Ich esse oft [[7]].", "Ich koche [[8]] mit Gemüse.",
         "Ich esse gern [[9]].", "Zum Abendessen esse ich [[10]].", "Ich esse viel [[11]].", "Ich esse oft [[12]].", "Ich kaufe frische [[13]].",
         "Ich schneide [[14]] für den Salat.", "Ich esse jeden Tag [[15]].", "Ich mag [[16]].", "Ich esse gern [[17]].", "Ich esse oft [[18]].",
         "Ich trinke [[19]].", "Ich trinke [[20]] zum Frühstück."]
HOEREN_GAPS = {str(i): [] for i in range(1, 21)}
HOEREN_GAPS.update({"1": ["Brot"], "2": ["Butter"], "3": ["Marmelade"], "4": ["Käse"], "5": ["Wurst"]})

WORDS = (
    words([("deftig", "mazali, to'yimli"), ("frisch", "yangi, toza"), ("das", "Gericht", "taom"), ("das", "Frühstück", "nonushta"),
           ("das", "Mittagessen", "tushlik"), ("das", "Abendessen", "kechki ovqat")], "Frage des Themas: nützliche Wörter")
    + words([("das", "Brot", "non"), ("das", "Brötchen", "bulka"), ("das", "Croissant", "kruassan")], "Brotwaren — non mahsulotlari")
    + words([("die", "Butter", "sariyog'"), ("die", "Margarine", "margarin")], "Fette — yog' va yog'lar")
    + words([("die", "Marmelade", "murabbo"), ("die", "Schokolade", "shokolad"), ("der", "Kuchen", "piroq"), ("die", "Kekse", "pechenye"),
             ("das", "Eis", "muzqaymoq"), ("die", "Pralinen", "pralin"), ("die", "Torte", "tort")], "Aufstriche und Süßigkeiten")
    + words([("der", "Käse", "pishloq"), ("der", "Joghurt", "yogurt"), ("die", "Milch", "sut")], "Milchprodukte — sut mahsulotlari")
    + words([("die", "Wurst", "kolbasa"), ("das", "Huhn", "tovuq"), ("das", "Rind", "mol go'shti"), ("das", "Schwein", "cho'chqa go'shti"),
             ("das", "Fleisch", "go'sht")], "Fleisch und Wurst")
    + words([("der", "Fisch", "baliq"), ("der", "Lachs", "losos"), ("der", "Thunfisch", "ton"), ("die", "Forelle", "losos baliqi"),
             ("die", "Sardinen", "sardina"), ("die", "Garnelen", "krevetka")], "Fisch — baliq")
    + words([("der", "Salat", "salat"), ("die", "Karotten", "sabzi"), ("die", "Paprika", "bulg'or qalampiri"), ("die", "Tomaten", "pomidor"),
             ("die", "Gurken", "bodring"), ("der", "Brokkoli", "brokkoli"), ("das", "Gemüse", "sabzavot")], "Gemüse — sabzavotlar")
    + words([("die", "Äpfel", "olma"), ("die", "Bananen", "banan"), ("die", "Orangen", "apelsin"), ("die", "Trauben", "uzum"), ("die", "Birnen", "nok"),
             ("die", "Kirschen", "gilos"), ("das", "Obst", "mevalar")], "Obst — mevalar")
    + words([("das", "Wasser", "suv"), ("der", "Tee", "choy"), ("der", "Kaffee", "qahva"), ("der", "Saft", "sharbat"), ("die", "Limonade", "limonad"),
             ("der", "Kakao", "kakao"), ("das", "Bier", "pivo")], "Getränke — ichimliklar")
    + words([("die", "Suppe", "sho'rva"), ("die", "Nudeln", "makaron"), ("der", "Reis", "guruch"), ("die", "Kartoffeln", "kartoshka")],
            "Suppen und warme Speisen")
)


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS), article_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("Modalverben und kein (Lesen)", [
        choice_gap("Markus ___ Salat, Tomaten und Gurken.", ["mag", "mögt", "magst"], "mag", explanation="Lesen: „Ich mag Salat, Tomaten, Gurken …“"),
        choice_gap("Er ___ nicht viele Süßigkeiten essen. (sollen)", ["soll", "sollst", "sollen"], "soll"),
        choice_gap("___ du gut kochen? (können)", ["Kannst", "Kann", "Könnt"], "Kannst"),
        choice_gap("Wir ___ viel Wasser trinken. (müssen)", ["müssen", "muss", "müsst"], "müssen"),
        choice_gap("Ich esse ___ Fleisch. (inkor)", ["kein", "keine", "nicht"], "kein", explanation="das Fleisch → kein Fleisch."),
        choice_gap("Er trinkt ___ Milch. (inkor)", ["keine", "kein", "keinen"], "keine", explanation="die Milch → keine Milch."),
        choice_gap("Sie mag den Fisch ___.", ["nicht", "kein", "keinen"], "nicht", explanation="Aniq artiklli ot butun gapni inkor qiladi: nicht."),
        choice_gap("Markus isst Süßigkeiten nur ___. (kam)", ["selten", "oft", "jeden Tag"], "selten", explanation="Lesen: „Ich esse sie aber nur selten.“"),
    ], "Darsdagi grammatikani takrorlang.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 6", source="vizu", page=59, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage: Was essen die Deutschen?", page=60,
             prompt="Was essen die Deutschen? Was wissen Sie darüber (Frühstück, Mittagessen, Abendessen, beliebte Gerichte)? "
                    "Und was essen Sie gern?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Modalverben, nicht und kein", page="61-64",
             rules=[{"title": "Modalverben", "html": _MODAL}, {"title": "nicht und kein", "html": _NICHT_KEIN}],
             exercises=[
                 exercise("Übungen: Modalverben (30)", MODAL_EX, _Q),
                 exercise("Aufgabe: nicht oder kein (20)", NICHT_EX, _NK),
             ]),
        base(L, "lesen", 1, "Lesen: Meine Essgewohnheit", page=65,
             instruction="Lies den Text aufmerksam und beantworte die Fragen.",
             metadata={"book_page": 65, "note": "Savollar 1-5 kitobdan (javob variantlari VIZU tomonidan), 6-7 VIZU."},
             passages=[{"title": "Meine Essgewohnheit", "text": TEXT}], questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Essen und Trinken (Lückentext)", page=66, audio_file="A1-6.mp3", key_pending=True,
             instruction="Höre die Sätze und ergänze die fehlenden Wörter. Wörter zum Thema: Brot, Butter, Marmelade, Käse, Wurst, Reis, Suppe, "
                         "Fisch, Salat, Obst, Schokolade, Kuchen, Joghurt, Wasser, Kaffee, Saft.",
             questions=[gap("Höre die Sätze und ergänze die fehlenden Wörter.", "\n".join(_SENT), HOEREN_GAPS, points=20)]),
        base(L, "schreiben_uebungen", 1, "Schreiben: Sätze bilden (Buch S. 67)", page=67,
             exercises=[exercise("Sätze bilden (20)", SATZBAU, "Bilde Sätze aus den Wörtern: Welcher Satz ist richtig? Achte auf die Wortstellung! (Kitob, 67-bet.)")]),
        base(L, "schreiben", 1, "Schreiben: Meine Essgewohnheiten", source="vizu",
             prompt="Schreiben Sie über Ihre Essgewohnheiten (5–8 Sätze): Was essen und trinken Sie zum Frühstück, zum Mittagessen und zum "
                    "Abendessen? Was essen Sie gern, was nicht? Benutzen Sie mindestens zwei Modalverben (können, müssen, wollen, sollen, "
                    "dürfen, mögen) und nicht / kein.",
             task_type="description", min_words=40, max_words=100, time_limit=15,
             support_phrases=["Zum Frühstück esse ich …", "Ich trinke gern …", "Ich mag keinen / keine / kein …", "Ich muss / soll …",
                              "Ich esse nicht gern …"],
             metadata={"note": "Erkin yozma topshiriq VIZU tomonidan qo'shilgan (kitobdagi 67-bet — gap tuzish mashqi)."}),
        base(L, "sprechen", 1, "Sprechen: Essen und Trinken", page=68, topic="Essen und Trinken",
             prompt="Beantwortet die Fragen mit den richtigen Wörtern und sprecht. Antwortet mit vollständigen Sätzen.",
             questions=["Was essen Sie morgen zum Frühstück?", "Was trinken Sie zum Frühstück?", "Was essen Sie morgen Mittag?",
                        "Was trinken Sie zum Mittagessen?", "Was essen Sie morgen Abend?", "Was trinken Sie am Abend?", "Können Sie morgen frühstücken?",
                        "Möchten Sie Mittagessen essen?", "Dürfen Sie abends trinken?", "Müssen Sie Gemüse essen?", "Sollen Sie Obst essen?",
                        "Wollen Sie Kuchen essen?", "Haben Sie kein Fleisch zu Mittag?", "Haben Sie keine Süßigkeiten?", "Essen Sie nicht gern Fisch?",
                        "Trinken Sie nicht oft Kaffee?"],
             response_type="monolog", min_duration=30, max_duration=180,
             speech_goal="Über Essen und Trinken zu den Mahlzeiten sprechen; Modalverben sowie nicht / kein richtig benutzen.",
             keywords=["zum Frühstück", "Ich esse", "Ich trinke", "kein", "nicht", "können", "müssen"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 6: Essen und Trinken", page="60, 69", words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 6", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 6", source="vizu",
             instruction="Modalfe'llar, nicht / kein va ovqat so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Ich ___ gut kochen.", ["kann", "kannst", "können"], "kann"),
                 choice_gap("Du ___ heute Hausaufgaben machen.", ["musst", "muss", "müsst"], "musst"),
                 choice_gap("Wir ___ ins Kino gehen.", ["wollen", "will", "wollt"], "wollen"),
                 choice_gap("___ ich hier sitzen?", ["Darf", "Dürfen", "Darfst"], "Darf"),
                 mc("Wo steht das Infinitiv im Satz mit Modalverb?", ["Am Anfang", "Auf Position 2", "Am Ende"], "C"),
                 choice_gap("Ich habe ___ Zeit.", ["keine", "nicht", "kein"], "keine"),
                 choice_gap("Die Suppe ist ___ heiß.", ["nicht", "kein", "keine"], "nicht", explanation="Sifatni inkor qilish: nicht heiß."),
                 choice_gap("Er trinkt ___ Kaffee.", ["keinen", "kein", "nicht"], "keinen"),
                 mc("„die Gurken“ — o'zbekchasi qaysi?", ["bodring", "pomidor", "sabzi"], "A"),
                 mc("Was ist ein Getränk?", ["der Saft", "die Wurst", "der Reis"], "A"),
                 tf("„die Suppe“ bedeutet „sho'rva“.", True),
                 match("Was passt zusammen?", ["der Käse", "die Milch", "das Huhn", "die Trauben"], ["pishloq", "sut", "tovuq", "uzum", "baliq"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 6", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
