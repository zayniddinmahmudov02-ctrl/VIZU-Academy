"""Modul 8 — Mein Urlaub in Deutschland — Grammatik: Perfekt (book pp. 80-88).

p.83: each sentence asks for the Präsens form and the Perfekt (Hilfsverb +
Partizip II) — imported as one Lückentext per sentence (3 gaps, partial
credit). Where the book's sentence starts with an ambiguous "Sie", both the
singular (sie) and plural / polite (Sie) forms are accepted.

Book corrections: task 4 sentence 3 repeats task 1 sentence 9 ("Wir ___
unsere Freunde. (besuchen)") — asked once. Task 4 sentence 6 prints
"gehören" for "Sie ___ die Regeln" (key: hat gehört) — the verb is hören.
The Hören gaps are decided by the infinitives in brackets (Perfekt forms)."""

from . import (
    article_set, base, choice_gap, exercise, gap, gap_paragraphs, html_table, intro_html, match, mc, reverse_vocab_set, summary_html, tf, ul,
    vocab_match_sets, words,
)

L = 8
LESSON_TITLE = "Mein Urlaub in Deutschland"
LESSON_DESCRIPTION = "Thema: Mein Urlaub in Deutschland · Grammatik: Perfekt"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 8 — Mein Urlaub in Deutschland (Buch, S. 80)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    8, "Mein Urlaub in Deutschland", "Perfekt (o'tgan zamon — og'zaki nutqda)",
    ["Perfekt tuzilishi: haben / sein + Partizip II (gap oxirida) — Ich habe Pizza gegessen.;",
     "qachon sein ishlatilishini bilish: harakat va holat o'zgarishi — Ich bin nach Berlin gefahren.;",
     "Partizip II yasash: gemacht, gesehen, besucht, studiert, eingekauft, aufgestanden;",
     "ta'til va sayohatga oid so'zlarni o'rganish: der Urlaub, das Hotel, am Strand, die Wanderung."],
    ["„Letzten Sommer bin ich nach Spanien gereist. Ich habe in einem Hotel gewohnt.“ — ta'tilingiz haqida gapirasiz;",
     "Ispaniyadagi ta'til haqidagi matnni o'qib, savollarga javob berasiz;",
     "Shveytsariyadagi sayohat haqidagi matnni tinglab, Perfekt shakllarini yozasiz;",
     "ta'tildan keyingi suhbatda o'qituvchining savollariga javob berasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(8, [
    "<strong>Perfekt:</strong> Subjekt + haben / sein (Position 2) + … + Partizip II (Ende): Ich habe gestern gearbeitet. Er ist gekommen.",
    "<strong>sein:</strong> gehen → ist gegangen, kommen → ist gekommen, fahren → ist gefahren, fliegen → ist geflogen, aufstehen → ist aufgestanden.",
    "<strong>Partizip II:</strong> ge…t (gemacht, gelernt) · ge…en (gesehen, gegessen) · ohne ge- (besucht, verstanden, studiert) · trennbar (eingekauft, aufgeräumt).",
    "<strong>Urlaub:</strong> Ich bin nach … gereist. Ich habe in einem Hotel gewohnt. Das Wetter war schön. Der Urlaub hat mir gut gefallen.",
])

_PERFEKT = (
    "<p><strong>Perfekt</strong> — o'tmishda bo'lib o'tgan ish-harakatni aytish uchun ishlatiladi. Ko'proq og'zaki nutqda ishlatiladi. "
    "O'zbekchasi: qildim, bordim, yedim kabi. Ich habe gelernt. — Men o'rgandim. Er ist gekommen. — U keldi.</p>"
    "<p><strong>Tuzilishi:</strong> Subjekt + haben / sein + Objekt + Partizip II. — Ich habe gestern eine Pizza gegessen.</p>"
    + html_table(["haben qachon ishlatiladi", "sein qachon ishlatiladi"],
                 [["-ieren fe'llar: studieren → hat studiert, telefonieren → hat telefoniert", "Harakat fe'llari / joy o'zgarishi: gehen → ist gegangen, kommen → ist gekommen"],
                  ["sich fe'llar: sich freuen → hat sich gefreut, sich waschen → hat sich gewaschen", "Harakat va holat o'zgarishi: fahren → ist gefahren, fliegen → ist geflogen"],
                  ["O'timli (Akkusativ) fe'llar: essen → hat gegessen, kaufen → hat gekauft", "Holat o'zgarishi: aufstehen → ist aufgestanden"],
                  ["Tinch holat fe'llari: arbeiten → hat gearbeitet, schlafen → hat geschlafen", ""]])
    + "<h3>Partizip II — Perfekt zamonida ishlatiladigan fe'l shakli, gap oxirida keladi</h3>"
    + html_table(["Fe'l turi", "Qoidasi", "Misollar"],
                 [["Kuchli (unregelmäßig) fe'llar", "ge + o'zgargan fe'l asosi + en", "sehen → gesehen, essen → gegessen"],
                  ["Kuchsiz (regelmäßig) fe'llar", "ge + fe'l asosi + t", "machen → gemacht, lernen → gelernt, suchen → gesucht"],
                  ["Ajralmaydigan fe'llar (be-, er-, ver-, zer-, miss-, ent-, emp-)", "„ge“ qo'shilmaydi", "besuchen → besucht"],
                  ["-ieren bilan tugagan fe'llar", "ge qo'shilmaydi, oxiri -t", "studieren → studiert, telefonieren → telefoniert"],
                  ["Ajraladigan fe'llar (ab-, an-, auf-, aus-, bei-, ein-, mit-, nach-, vor-, zu-, zurück-, zusammen-)",
                   "prefiks + ge + fe'l", "aufstehen → aufgestanden, einkaufen → eingekauft"]])
)


def _pf(subj: str, rest: str, verb: str, praes: list[str], aux: list[str], part: list[str], hint: str = "") -> dict:
    text = f"{subj} [[1]] {rest} ({verb}) → {subj} [[2]] [[3]].{(' ' + hint) if hint else ''}"
    return gap("Präsens → Perfekt: ergänzen Sie.", text, {"1": praes, "2": aux, "3": part},
               explanation=f"{praes[0]} → {aux[0]} … {part[0]}")


def _sep(word: str, prefix: str) -> list[str]:
    return [f"{word} {prefix}", f"{word} … {prefix}", f"{word} ... {prefix}"]


BLOCK1 = [
    _pf("Wir", "oft im Park.", "spielen", ["spielen"], ["haben"], ["gespielt"]),
    _pf("Er", "heute Abend Pizza.", "kochen", ["kocht"], ["hat"], ["gekocht"]),
    _pf("Ihr", "gerne Musik.", "tanzen", ["tanzt"], ["habt"], ["getanzt"]),
    _pf("Sie", "auf den Bus.", "warten", ["wartet", "warten"], ["hat", "haben"], ["gewartet"]),
    _pf("Ich", "immer auf Fragen.", "antworten", ["antworte"], ["habe"], ["geantwortet"]),
    _pf("Du", "viele Fragen.", "fragen", ["fragst"], ["hast"], ["gefragt"]),
    _pf("Wir", "unsere Freunde.", "besuchen", ["besuchen"], ["haben"], ["besucht"]),
    _pf("Er", "Radio.", "hören", ["hört"], ["hat"], ["gehört"]),
    _pf("Ihr", "miteinander.", "sprechen", ["sprecht"], ["habt"], ["gesprochen"]),
    _pf("Ich", "Brot im Supermarkt.", "kaufen", ["kaufe"], ["habe"], ["gekauft"]),
    _pf("Du", "jeden Tag Klavier.", "üben", ["übst"], ["hast"], ["geübt"]),
    _pf("Wir", "lange im Garten.", "arbeiten", ["arbeiten"], ["haben"], ["gearbeitet"]),
    _pf("Sie", "viel für die Schule.", "lernen", ["lernen", "lernt"], ["haben", "hat"], ["gelernt"]),
    _pf("Ich", "jeden Morgen Sport.", "machen", ["mache"], ["habe"], ["gemacht"]),
    _pf("Er", "gern Fußball.", "spielen", ["spielt"], ["hat"], ["gespielt"]),
    _pf("Ihr", "oft am Wochenende.", "tanzen", ["tanzt"], ["habt"], ["getanzt"]),
    _pf("Du", "für das Abendessen.", "kochen", ["kochst"], ["hast"], ["gekocht"]),
    _pf("Wir", "auf den Zug.", "warten", ["warten"], ["haben"], ["gewartet"]),
]
BLOCK2 = [
    _pf("Wir", "das Buch.", "lesen", ["lesen"], ["haben"], ["gelesen"]),
    _pf("Er", "gestern ins Kino.", "gehen", ["geht"], ["ist"], ["gegangen"]),
    _pf("Ihr", "hoch in den Himmel.", "fliegen", ["fliegt"], ["seid"], ["geflogen"]),
    _pf("Sie", "den Ball.", "nehmen", ["nimmt", "nehmen"], ["hat", "haben"], ["genommen"]),
    _pf("Ich", "den Hund.", "finden", ["finde"], ["habe"], ["gefunden"]),
    _pf("Du", "spät nach Hause.", "kommen", ["kommst"], ["bist"], ["gekommen"]),
    _pf("Wir", "das Geschenk.", "geben", ["geben"], ["haben"], ["gegeben"]),
    _pf("Er", "die Aufgabe.", "vergessen", ["vergisst"], ["hat"], ["vergessen"]),
    _pf("Ihr", "im Garten.", "laufen", ["lauft"], ["seid"], ["gelaufen"]),
    _pf("Sie", "die Stadt.", "sehen", ["sieht", "sehen"], ["hat", "haben"], ["gesehen"]),
    _pf("Ich", "meine Schlüssel.", "verlieren", ["verliere"], ["habe"], ["verloren"]),
    _pf("Du", "gestern Abend Pizza.", "essen", ["isst"], ["hast"], ["gegessen"]),
    _pf("Wir", "viel im Urlaub.", "fahren", ["fahren"], ["sind"], ["gefahren"]),
    _pf("Er", "nach Hause.", "gehen", ["geht"], ["ist"], ["gegangen"]),
    _pf("Ich", "das Bild.", "lesen", ["lese"], ["habe"], ["gelesen"]),
    _pf("Ihr", "den Ball.", "werfen", ["werft"], ["habt"], ["geworfen"]),
    _pf("Sie", "auf die Idee.", "kommen", ["kommt", "kommen"], ["ist", "sind"], ["gekommen"]),
    _pf("Du", "das Lied.", "singen", ["singst"], ["hast"], ["gesungen"]),
]
BLOCK3 = [
    _pf("Wir", "die Tür.", "zumachen", _sep("machen", "zu"), ["haben"], ["zugemacht"]),
    _pf("Er", "das Geschenk.", "mitbringen", _sep("bringt", "mit"), ["hat"], ["mitgebracht"]),
    _pf("Ihr", "früh am Morgen.", "aufstehen", _sep("steht", "auf"), ["seid"], ["aufgestanden"]),
    _pf("Sie", "mich gestern.", "anrufen", _sep("ruft", "an") + _sep("rufen", "an"), ["hat", "haben"], ["angerufen"]),
    _pf("Ich", "die Wohnung.", "aufräumen", _sep("räume", "auf"), ["habe"], ["aufgeräumt"]),
    _pf("Du", "Lebensmittel.", "einkaufen", _sep("kaufst", "ein"), ["hast"], ["eingekauft"]),
    _pf("Wir", "zusammen im Projekt.", "mitmachen", _sep("machen", "mit"), ["haben"], ["mitgemacht"]),
    _pf("Er", "aufmerksam.", "zuhören", _sep("hört", "zu"), ["hat"], ["zugehört"]),
]
BLOCK4 = [
    _pf("Er", "die Rechnung.", "bezahlen", ["bezahlt"], ["hat"], ["bezahlt"]),
    _pf("Ihr", "den Plan.", "erklären", ["erklärt"], ["habt"], ["erklärt"]),
    _pf("Sie", "die Regeln.", "hören", ["hört", "hören"], ["hat", "haben"], ["gehört"]),
    _pf("Ich", "ein Paket.", "bekommen", ["bekomme"], ["habe"], ["bekommen"]),
    _pf("Du", "den Schlüssel.", "verlieren", ["verlierst"], ["hast"], ["verloren"]),
    _pf("Wir", "eine tolle Erfahrung.", "erleben", ["erleben"], ["haben"], ["erlebt"]),
    _pf("Er", "ein neues Museum.", "entdecken", ["entdeckt"], ["hat"], ["entdeckt"]),
]

TEXT = ("Letzten Sommer bin ich nach Spanien gereist. Ich habe in einem Hotel am Strand gewohnt. Das Wetter war sehr schön und warm. Ich habe "
        "jeden Tag im Meer gebadet und habe viel Sonne getankt. Manchmal habe ich auch Volleyball am Strand gespielt. Ich habe Tapas gegessen "
        "und habe spanische Paella probiert. Jeden Abend bin ich spazieren gegangen und habe schöne Fotos gemacht. Ich habe viele nette Leute "
        "getroffen und wir haben zusammen gelacht.\n\n"
        "Ich habe auch eine Stadtbesichtigung gemacht. Ich habe viele interessante Gebäude gesehen und habe Souvenirs gekauft. Außerdem habe "
        "ich ein Museum besucht und habe viel über die Geschichte Spaniens gelernt.\n\n"
        "Mein Urlaub hat mir sehr gut gefallen. Ich habe mich entspannt und habe viel Spaß gehabt. Ich habe neue Freunde gefunden und ich habe "
        "schöne Erinnerungen gesammelt.")
LESEN = [
    mc("Wohin bist du letzten Sommer gereist?", ["Nach Italien", "Nach Spanien", "In die Schweiz"], "B", "Ich bin nach Spanien gereist."),
    mc("Wo hast du gewohnt?", ["Bei einer Gastfamilie", "In einem Hotel am Strand", "In einem Hostel"], "B"),
    mc("Wie war das Wetter?", ["Sehr schön und warm", "Kalt", "Regnerisch"], "A"),
    mc("Was hast du jeden Tag gemacht?", ["Ich habe im Meer gebadet und Sonne getankt.", "Ich habe gearbeitet.", "Ich habe Deutsch gelernt."], "A"),
    mc("Hast du am Strand gespielt?", ["Ja, ich habe Volleyball am Strand gespielt.", "Nein, nie.", "Ja, Fußball im Park."], "A"),
    mc("Was hast du gegessen?", ["Pizza und Pasta", "Tapas und Paella", "Schnitzel"], "B"),
    mc("Was hast du abends gemacht?", ["Ich bin spazieren gegangen und habe Fotos gemacht.", "Ich habe ferngesehen.", "Ich habe geschlafen."], "A"),
    mc("Hast du neue Leute getroffen?", ["Ja, ich habe viele nette Leute getroffen.", "Nein, niemanden.", "Nur meine Familie."], "A"),
    mc("Hast du Souvenirs gekauft?", ["Ja", "Nein", "Das steht nicht im Text."], "A"),
    mc("Hat dir dein Urlaub gefallen?", ["Ja, sehr gut.", "Nein, gar nicht.", "Er war langweilig."], "A"),
]

HOEREN_TEXT = ("Vor einem Monat wollte ich nach Island reisen, aber ich [[1]] (sein) zuerst in die Schweiz [[2]] (fliegen). Ich [[3]] (sein) nach "
               "Zermatt [[4]] (fahren), weil ich die Berge sehen wollte. Zermatt ist eine kleine Stadt in den Alpen.\n"
               "Ich [[5]] (haben) in einem Hotel in der Nähe des Matterhorns [[6]] (übernachten). Das Hotel [[7]] (haben) mir sehr gut "
               "[[8]] (gefallen). Ich [[9]] (sein) jeden Tag in der Natur spazieren [[10]] (gehen) und [[11]] (haben) die schöne Landschaft "
               "[[12]] (bewundern).\nIch [[13]] (haben) viele Fotos [[14]] (machen). Ich [[15]] (haben) ein paar Wanderungen [[16]] (machen) "
               "und [[17]] (haben) frische Bergluft [[18]] (genießen). Ich [[19]] (haben) auch Schokolade und Käse [[20]] (probieren).\n"
               "Ich [[21]] (haben) neue Leute [[22]] (treffen) und wir [[23]] (haben) zusammen [[24]] (lachen). Ich [[25]] (haben) Souvenirs "
               "[[26]] (kaufen), zum Beispiel kleine Schokoladen und Postkarten.\nMeine Reise [[27]] (haben) mir sehr gut [[28]] (gefallen). "
               "Ich [[29]] (haben) mich [[30]] (entspannen) und [[31]] (haben) viele schöne Erinnerungen [[32]] (sammeln). Zermatt in der "
               "Schweiz [[33]] (sein) ein wunderbarer Ort, und ich [[34]] (möchten) dort wieder [[35]] (hinfahren).")
_KEY = [["bin"], ["geflogen"], ["bin"], ["gefahren"], ["habe"], ["übernachtet"], ["hat"], ["gefallen"], ["bin"], ["gegangen"], ["habe"],
        ["bewundert"], ["habe"], ["gemacht"], ["habe"], ["gemacht"], ["habe"], ["genossen"], ["habe"], ["probiert"], ["habe"], ["getroffen"],
        ["haben"], ["gelacht"], ["habe"], ["gekauft"], ["hat"], ["gefallen"], ["habe"], ["entspannt"], ["habe"], ["gesammelt"], ["war", "ist"],
        ["möchte"], ["hinfahren"]]
HOEREN_GAPS = {str(i): k for i, k in enumerate(_KEY, start=1)}

_W = [("der", "Urlaub", "ta'til"), ("reisen", "sayohat qilmoq"), ("reisen nach", "…ga sayohat qilmoq"), ("letzten Sommer", "o'tgan yoz"),
      ("wohnen", "yashamoq, qolmoq"), ("das", "Hotel", "mehmonxona"), ("am Strand", "plyajda"), ("das", "Wetter", "ob-havo"),
      ("schön", "chiroyli, yaxshi"), ("warm", "issiq"), ("baden", "cho'milmoq"), ("die Sonne tanken", "quyosh nurida toblanmoq"),
      ("Volleyball spielen", "voleybol o'ynamoq"), ("essen", "yemoq"), ("die", "Tapas", "tapas (ispan taomi)"), ("die", "Paella", "paella (ispan taomi)"),
      ("abends", "kechqurun"), ("spazieren gehen", "sayr qilmoq"), ("Fotos machen", "fotosurat tushirmoq"), ("nette Leute", "yoqimli odamlar"),
      ("lachen", "kulmoq"), ("die", "Stadtbesichtigung", "shahar bo'ylab sayohat / ekskursiya"), ("interessant", "qiziqarli"),
      ("die", "Gebäude", "binolar"), ("Souvenirs kaufen", "sovg'a sotib olmoq"), ("das", "Museum", "muzey"), ("die", "Geschichte", "tarix"),
      ("gefallen", "yoqmoq"), ("sich entspannen", "dam olmoq"), ("Spaß haben", "zavqlanmoq, rohatlanmoq"), ("neue Freunde finden", "yangi do'stlar topmoq"),
      ("Erinnerungen sammeln", "xotiralar to'plamoq"), ("die", "Alpen", "Alp tog'lari"), ("das", "Matterhorn", "Matterhorn tog'i"),
      ("die", "Natur", "tabiat"), ("bewundern", "hayratlanib tomosha qilmoq"), ("die", "Wanderung", "piyoda sayr, trekking"),
      ("die frische Luft", "toza havo"), ("Schokolade probieren", "shokolad tatib ko'rmoq"), ("Käse probieren", "pishloq tatib ko'rmoq"),
      ("zusammen lachen", "birga kulmoq"), ("hinfahren", "(bir joyga) borib kelmoq"), ("möchten", "xohlamoq"), ("zuerst", "avval, birinchi"),
      ("weiterreisen", "sayohatni davom ettirmoq"), ("klein", "kichik"), ("überall", "hamma joyda"), ("die", "Stadt", "shahar"),
      ("sehr gut", "juda yaxshi"), ("besonders", "ayniqsa, maxsus")]
WORDS = words(_W, "Urlaub")


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS, per_set=4), article_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("haben oder sein? (Lesen & Hören)", [
        choice_gap("Letzten Sommer ___ ich nach Spanien gereist.", ["bin", "habe", "hat"], "bin", explanation="Lesen: „Letzten Sommer bin ich nach Spanien gereist.“"),
        choice_gap("Ich ___ in einem Hotel am Strand gewohnt.", ["habe", "bin", "ist"], "habe"),
        choice_gap("Jeden Abend ___ ich spazieren gegangen.", ["bin", "habe", "hat"], "bin", explanation="gehen → ist gegangen."),
        choice_gap("Ich ___ Tapas gegessen.", ["habe", "bin", "hat"], "habe"),
        choice_gap("Mein Urlaub ___ mir sehr gut gefallen.", ["hat", "ist", "habe"], "hat"),
        choice_gap("Ich ___ nach Zermatt gefahren.", ["bin", "habe", "hat"], "bin", explanation="fahren → ist gefahren."),
    ], "Perfektda haben yoki sein ni tanlang.", source="vizu"),
    exercise("Partizip II", [
        mc("Partizip II von „reisen“:", ["gereist", "gereisen", "reist"], "A"),
        mc("Partizip II von „treffen“:", ["getroffen", "getrefft", "getraffen"], "A"),
        mc("Partizip II von „probieren“:", ["probiert", "geprobiert", "probieren"], "A", "-ieren: ge- qo'shilmaydi."),
        mc("Partizip II von „verstehen“:", ["verstanden", "geverstanden", "verstehte"], "A", "ver-: ge- qo'shilmaydi."),
        mc("Partizip II von „aufräumen“:", ["aufgeräumt", "geaufräumt", "aufräumt"], "A", "Ajraladigan fe'l: auf + ge + räumt."),
        mc("Partizip II von „finden“:", ["gefunden", "gefindet", "gefanden"], "A"),
    ], "To'g'ri Partizip II shaklini tanlang.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 8", source="vizu", page=80, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage: Was machen die Deutschen im Urlaub?", page=81,
             prompt="Was machen die Deutschen im Urlaub? Und was machen Sie gern im Urlaub?", min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Perfekt", page="82-83",
             rules=[{"title": "Perfekt", "html": _PERFEKT}],
             exercises=[
                 exercise("Aufgabe 1: regelmäßige Verben (Präsens → Perfekt)", BLOCK1,
                          "Beispiel: Ich lerne jeden Tag Deutsch. → Ich habe Deutsch gelernt."),
                 exercise("Aufgabe 2: unregelmäßige Verben (Präsens → Perfekt)", BLOCK2,
                          "Beispiel: Ich sehe heute Morgen viel. → Ich habe viel gesehen. Du fährst nach Berlin. → Du bist nach Berlin gefahren."),
                 exercise("Aufgabe 3: trennbare Verben (Präsens → Perfekt)", BLOCK3,
                          "Beispiel: Ich kaufe im Supermarkt ein. → Ich habe im Supermarkt eingekauft."),
                 exercise("Aufgabe 4: untrennbare Verben (Präsens → Perfekt)", BLOCK4,  # book sentence 3 = task 1 sentence 9
                          "Beispiel: Ich verstehe die Aufgabe. → Ich habe die Aufgabe verstanden. Präfixe: be-, ge-, er-, ver-, zer-, miss-, ent-, emp-."),
             ]),
        base(L, "lesen", 1, "Lesen: Mein Urlaub in Spanien", page=84,
             instruction="Lies den Text und beantworte die Fragen.",
             metadata={"book_page": 84, "note": "Savollar kitobdan; javob variantlari VIZU tomonidan (kitob javoblari asosida)."},
             passages=[{"title": "Mein Urlaub in Spanien", "text": TEXT}], questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Meine Reise nach Zermatt in der Schweiz", page=85, audio_file="A1-8.mp3",
             instruction="Hören Sie den Text und ergänzen Sie die Verben im Perfekt (Hilfsverb und Partizip II).",
             questions=gap_paragraphs("Meine Reise nach Zermatt — ergänzen Sie die Lücken", HOEREN_TEXT, HOEREN_GAPS)),
        base(L, "schreiben", 1, "Schreiben: Mein Urlaub", page=86,
             prompt="Schreiben Sie über Ihren Urlaub. Beantworten Sie die Fragen in ganzen Sätzen (Perfekt):\n"
                    "Wohin bist du gereist? Wann war dein Urlaub? Wo hast du gewohnt? Mit wem warst du? Was hast du gemacht? "
                    "Was hast du gegessen und getrunken? Was hat dir besonders gefallen? Hast du Souvenirs gekauft? Wie hast du dich gefühlt? "
                    "Möchtest du wieder dorthin fahren?",
             task_type="description", min_words=50, max_words=150, time_limit=25,
             support_phrases=["Ich bin nach … gefahren.", "Letzten Sommer habe ich Urlaub gemacht.", "Ich habe in einem Hotel gewohnt.",
                              "Ich bin mit meiner Familie gereist.", "Die Landschaft hat mir sehr gut gefallen.", "Ich möchte nächstes Jahr wieder dorthin fahren."]),
        base(L, "sprechen", 1, "Dialog: Nach dem Urlaub", page=87, topic="Nach dem Urlaub",
             prompt="Sie sind der Student / die Studentin. Beantworten Sie die Fragen des Lehrers über Ihren Urlaub (im Perfekt).",
             questions=["Wie war dein Urlaub?", "Wohin bist du gereist?", "Wo hast du gewohnt?", "Mit wem bist du gereist?", "Was hast du gemacht?",
                        "Hast du neue Leute getroffen?", "Welche Städte oder Orte hast du besucht?", "Hast du etwas Besonderes gemacht?",
                        "Hat dir dein Urlaub gefallen?", "Was hast du gegessen und getrunken?", "Möchtest du wieder dorthin reisen?"],
             response_type="dialog", min_duration=30, max_duration=180,
             speech_goal="Über eine Reise im Perfekt sprechen: Ziel, Unterkunft, Begleitung, Aktivitäten, Essen, Eindruck.",
             keywords=["Ich bin … gereist", "Ich habe … gewohnt", "Ich habe … gemacht"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 8: Urlaub", page=88, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 8", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 8", source="vizu",
             instruction="Perfekt va ta'til so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Ich ___ nach Berlin gefahren.", ["bin", "habe", "hat"], "bin"),
                 choice_gap("Wir ___ Pizza gegessen.", ["haben", "sind", "hat"], "haben"),
                 choice_gap("Er ist früh ___. (aufstehen)", ["aufgestanden", "aufgesteht", "geaufstanden"], "aufgestanden"),
                 mc("Partizip II von „besuchen“:", ["gebesucht", "besucht", "besuchen"], "B"),
                 mc("Partizip II von „studieren“:", ["gestudiert", "studiert", "studieren"], "B"),
                 mc("Partizip II von „sehen“:", ["gesehen", "gesieht", "gesah"], "A"),
                 mc("Partizip II von „einkaufen“:", ["eingekauft", "geeinkauft", "einkaufte"], "A"),
                 mc("Welcher Satz ist richtig?", ["Ich habe gestern gearbeitet.", "Ich bin gestern gearbeitet.", "Ich habe gestern arbeiten."], "A"),
                 mc("„der Urlaub“ — o'zbekchasi qaysi?", ["ta'til", "mehmonxona", "plyaj"], "A"),
                 tf("„sich entspannen“ bedeutet „dam olmoq“.", True),
                 match("Was passt zusammen?", ["baden", "die Wanderung", "das Wetter", "gefallen"], ["cho'milmoq", "piyoda sayr", "ob-havo", "yoqmoq", "muzey"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 8", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
