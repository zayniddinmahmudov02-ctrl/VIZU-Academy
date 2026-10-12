"""Modul 11 — Wohnen in Deutschland — Grammatik: Adjektive — Steigerung (book pp. 108-116)."""

from . import base, choice_gap, exercise, gap, html_table, match, mc, mc_pending, tf, words

L = 11

_STEIG = (
    "<p>Nemis tilida sifatlarning darajalanishi (Adjektiv-Steigerung) uch bosqichda bo'ladi: <strong>Positiv, Komparativ</strong> va "
    "<strong>Superlativ</strong>.</p>"
    "<p><strong>Positiv</strong> — sifatning oddiy shakli (gut, groß, billig). <strong>Komparativ</strong> ikki narsa yoki holatni solishtirish "
    "uchun ishlatiladi va sifat oxiriga <strong>-er</strong> qo'shiladi (groß → größer, billig → billiger); ba'zi sifatlarda unli umlaut "
    "(ä, ö, ü) ga o'zgaradi (alt → älter, groß → größer). <strong>Superlativ</strong> „eng“ ma'nosini bildiradi va odatda "
    "<strong>am + sifat + -sten</strong> shaklida yasaladi (am größten, am billigsten); sifat d, t, s, ß, z bilan tugasa, talaffuz uchun "
    "<strong>-esten</strong> qo'shiladi (laut → am lautesten). Ayrim sifatlar qoidaga bo'ysunmaydi: gut → besser → am besten, viel → mehr → am meisten.</p>"
    + html_table(["Positiv", "Komparativ", "Superlativ"],
                 [["gut (yaxshi)", "besser (yaxshiroq)", "am besten (eng yaxshi)"], ["viel (ko'p)", "mehr (ko'proq)", "am meisten (eng ko'p)"],
                  ["gern (xush ko'rib)", "lieber (ko'proq xush ko'rib)", "am liebsten (eng xush ko'rib)"], ["hoch (baland)", "höher (balandroq)", "am höchsten (eng baland)"],
                  ["nah (yaqin)", "näher (yaqinroq)", "am nächsten (eng yaqin)"], ["alt (eski / qari)", "älter (eskiroq / yoshi kattaroq)", "am ältesten (eng eski)"],
                  ["jung (yosh)", "jünger (yoshroq)", "am jüngsten (eng yosh)"], ["groß (katta)", "größer (kattaroq)", "am größten (eng katta)"],
                  ["lang (uzun)", "länger (uzunroq)", "am längsten (eng uzun)"], ["kalt (sovuq)", "kälter (sovuqroq)", "am kältesten (eng sovuq)"],
                  ["schnell (tez)", "schneller (tezroq)", "am schnellsten (eng tez)"], ["billig (arzon)", "billiger (arzonroq)", "am billigsten (eng arzon)"],
                  ["teuer (qimmat)", "teurer (qimmatroq)", "am teuersten (eng qimmat)"], ["schön (chiroyli)", "schöner (chiroyliroq)", "am schönsten (eng chiroyli)"],
                  ["klein (kichik)", "kleiner (kichikroq)", "am kleinsten (eng kichik)"], ["langsam (sekin)", "langsamer (sekinroq)", "am langsamsten (eng sekin)"],
                  ["fleißig (tirishqoq)", "fleißiger (tirishqoqroq)", "am fleißigsten (eng tirishqoq)"],
                  ["freundlich (xushmuomala)", "freundlicher (xushmuomalaroq)", "am freundlichsten (eng xushmuomala)"],
                  ["laut (shovqinli)", "lauter (shovqinliroq)", "am lautesten (eng shovqinli)"], ["sauber (toza)", "sauberer (tozaroq)", "am saubersten (eng toza)"]])
)


def _st(text: str, komp: str, sup: str, sup_article: str | None, expl: str | None = None) -> dict:
    sups = [sup] + ([f"{sup_article} {sup}"] if sup_article else [])
    return gap("Komparativ und Superlativ: ergänzen Sie.", text, {"1": [komp], "2": sups}, explanation=expl or f"{komp} — {sup}")


STEIG_EX = [
    _st("Kanada ist groß, die USA ist [[1]] (groß), Russland ist [[2]] Land der Welt.", "größer", "größte", "das"),
    _st("Der Nil ist lang, der Amazonas ist [[1]] (lang), der [[2]] Fluss der Welt ist der Amazonas.", "länger", "längste", None),
    _st("Der Kilimandscharo ist hoch, der Elbrus ist [[1]] (hoch), der Mount Everest ist [[2]] Berg der Welt.", "höher", "höchste", "der"),
    _st("Deutsch ist schwierig, Russisch ist [[1]] (schwierig), Chinesisch ist die [[2]] Sprache der Welt.", "schwieriger", "schwierigste", None),
    _st("Ein Auto ist schnell, ein Zug ist [[1]] (schnell), ein Flugzeug ist das [[2]] Verkehrsmittel.", "schneller", "schnellste", None),
    _st("Der Sommer in Deutschland ist warm, der Sommer in Spanien ist [[1]] (warm), der Sommer in der Wüste ist der [[2]].", "wärmer", "wärmste", None),
    _st("Gold ist teuer, Platin ist [[1]] (teuer), Diamanten sind die [[2]] Steine der Welt.", "teurer", "teuersten", None),
    _st("Ein Dorf ist klein, eine Stadt ist [[1]], eine Metropole ist die [[2]] Wohnform.", "größer", "größte", None,
        "Tarjima: shahar undan kattaroq, megapolis eng katta → größer — größte."),
    _st("Ein See ist tief, das Schwarze Meer ist [[1]] (tief), der Pazifik ist der [[2]] Ozean der Welt.", "tiefer", "tiefste", None),
    _st("Ein Hund ist intelligent, ein Delfin ist [[1]] (intelligent), der Mensch ist das [[2]] Lebewesen.", "intelligenter", "intelligenteste", None),
    _st("Ein Elefant ist schwer, ein Nashorn ist [[1]] (schwer), der Blauwal ist das [[2]] Tier der Welt.", "schwerer", "schwerste", None),
    _st("Ein Dorf ist ruhig, eine Kleinstadt ist [[1]] (ruhig), ein Bergdorf ist der [[2]] Ort.", "ruhiger", "ruhigste", None),
    _st("Ein Buch ist interessant, ein Film ist [[1]] (interessant), eine Serie ist das [[2]] Medium.", "interessanter", "interessanteste", None),
    _st("Ein Haus ist alt, ein Schloss ist [[1]] (alt), eine Pyramide ist das [[2]] Bauwerk der Welt.", "älter", "älteste", None),
    _st("Ein Fluss ist breit, ein Meer ist [[1]] (breit), ein Ozean ist das [[2]] Gewässer der Welt.", "breiter", "breiteste", None),
]

TEXT = ("Deutschland hat viele Städte. Jede Stadt ist anders. Manche Städte sind groß, andere sind ruhig oder teuer. Hier sind einige bekannte "
        "Städte in Deutschland.\n\nBerlin ist die Hauptstadt von Deutschland. Die Stadt ist sehr lebendig. Berlin ist größer als viele andere "
        "Städte. Es gibt viele Museen, Geschichte und Kultur. Das Leben in Berlin ist günstiger als in München.\n\nMünchen liegt im Süden von "
        "Deutschland. München ist eine saubere Stadt. Sie ist teurer als Berlin. Die Stadt ist ruhig und gut organisiert. Viele Menschen mögen "
        "München.\n\nHamburg liegt im Norden von Deutschland. Hamburg ist eine große Stadt. Sie ist kleiner als Berlin. Die Stadt hat einen großen "
        "Hafen. Hamburg ist ruhiger als Berlin.\n\nKöln liegt am Rhein. Die Stadt ist bekannt für den Kölner Dom. Köln ist lebendig und freundlich. "
        "Die Stadt ist nicht so groß wie Berlin.\n\nHeidelberg ist eine kleine Stadt. Sie ist ruhiger als Berlin und Hamburg. Viele Studierende "
        "leben dort. Die Altstadt ist sehr schön.\n\nFrankfurt am Main liegt in der Mitte von Deutschland. Die Stadt ist sehr modern. Frankfurt ist "
        "bekannt für Banken und hohe Häuser. Die Stadt ist größer als Heidelberg.\n\nStuttgart liegt im Süden von Deutschland. Stuttgart ist eine "
        "ruhige Stadt. Viele Autos kommen aus Stuttgart. Die Stadt ist kleiner als München.\n\nDüsseldorf liegt am Rhein. Die Stadt ist modern und "
        "sauber. Düsseldorf ist bekannt für Mode und Messen. Sie ist ruhiger als Berlin.")
LESEN = [
    mc("Welche Stadt ist die Hauptstadt?", ["Hamburg", "Berlin", "München"], "B"),
    mc("Welche Stadt liegt im Süden?", ["Köln", "Hamburg", "München"], "C"),
    mc("Welche Stadt hat einen großen Hafen?", ["Frankfurt", "Hamburg", "Stuttgart"], "B"),
    mc("Welche Stadt ist größer als Hamburg?", ["München", "Berlin", "Köln"], "B"),
    mc("Welche Stadt liegt am Rhein und hat den Dom?", ["Düsseldorf", "Köln", "Frankfurt"], "B"),
    mc("Welche Stadt ist klein und ruhig?", ["Berlin", "Hamburg", "Heidelberg"], "C"),
    mc("Welche Stadt ist modern und bekannt für Banken?", ["Stuttgart", "Düsseldorf", "Frankfurt"], "C"),
    mc("Welche Stadt ist bekannt für Mode und Messen?", ["Köln", "Hamburg", "Düsseldorf"], "C"),
    mc("Welche Stadt ist größer als Heidelberg?", ["Heidelberg", "Frankfurt", "Dorf"], "B"),
    mc("Welche Stadt ist teurer als Berlin?", ["Heidelberg", "München", "Köln"], "B"),
    mc("Welche Stadt liegt im Norden?", ["Hamburg", "München", "Stuttgart"], "A"),
    mc("Welche Stadt ist ruhiger als Berlin?", ["Berlin", "München", "Hamburg"], "C", "„Hamburg ist ruhiger als Berlin.“"),
]

HOEREN = [
    mc("Wie viele Personen wohnen zusammen?", ["Drei", "Vier", "Fünf"], "B"),
    mc("Wer erzählt die Geschichte?", ["Max", "Tom", "Anna"], "A"),
    mc("Was studiert Max?", ["Design", "Informatik", "Deutsch"], "B"),
    mc("Wer putzt oft die Küche?", ["Tom", "Lisa", "Max"], "A"),
    mc("Wer kocht gern?", ["Anna", "Tom", "Max"], "A"),
    mc("Wer ist kreativ?", ["Max", "Lisa", "Anna"], "B"),
    mc("Wo essen sie zusammen?", ["Küche", "Zimmer", "Bad"], "A"),
    mc("Wie ist die WG?", ["Laut", "Ruhig", "Alt"], "B"),
]

_W = [("groß", "katta"), ("klein", "kichik"), ("teuer", "qimmat"), ("billig", "arzon"), ("ruhig", "tinch"), ("laut", "shovqinli"), ("sauber", "toza"),
      ("alt", "eski"), ("neu", "yangi"), ("modern", "zamonaviy"), ("gemütlich", "shinam"), ("hell", "yorug'"), ("dunkel", "qorong'i"), ("großzügig", "keng"),
      ("nah", "yaqin"), ("fern", "uzoq"), ("hoch", "baland"), ("niedrig", "past"), ("warm", "iliq"), ("kalt", "sovuq"), ("schön", "chiroyli"),
      ("hässlich", "xunuk"), ("bequem", "qulay"), ("ordentlich", "tartibli"), ("freundlich", "xushmuomala")]
_N = [("die", "Wohnung", "kvartira"), ("das", "Haus", "uy"), ("das", "Zimmer", "xona"), ("die", "Miete", "ijara"), ("der", "Balkon", "balkon"),
      ("die", "Küche", "oshxona"), ("das", "Bad", "hammom"), ("das", "Wohnzimmer", "mehmonxona"), ("der", "Vermieter", "uy egasi"), ("der", "Mieter", "ijarachi"),
      ("wohnen", "yashamoq"), ("leben", "yashamoq, hayot kechirmoq"), ("mieten", "ijaraga olmoq"), ("bezahlen", "to'lamoq"), ("suchen", "qidirmoq"),
      ("finden", "topmoq"), ("der", "Nachbar", "qo'shni"), ("die", "Stadt", "shahar"), ("das", "Dorf", "qishloq"), ("das", "Gebäude", "bino"),
      ("der", "Aufzug", "lift"), ("die", "Heizung", "isitish tizimi"), ("das", "Fenster", "deraza"), ("die", "Tür", "eshik"), ("der", "Boden", "pol")]
WORDS = words(_W, "Adjektive") + words(_N, "Wörter")


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage des Themas: Ist die Wohnung teuer in der BRD?", page=109,
             prompt="Ist die Wohnung in Deutschland teuer? Wie hoch sind die Mietpreise in verschiedenen Städten? Warum sind Wohnungen in manchen "
                    "Städten teuer? Was kann man tun, um eine günstige Wohnung zu finden? Sagen Sie Ihre Meinung.",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Adjektive — Steigerung", page="110-111",
             rules=[{"title": "Adjektive — Steigerung", "html": _STEIG}],
             exercises=[exercise("Aufgaben: Die Top-3 Fakten der Welt (15)", STEIG_EX,
                                 "Ergänzen Sie den Komparativ und den Superlativ.")]),
        base(L, "lesen", 1, "Lesen: Die deutschen Städte", page=112,
             instruction="Lesen Sie den Text und wählen Sie die richtige Antwort.",
             passages=[{"title": "Die deutschen Städte", "text": TEXT}], questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Unsere Wohngemeinschaft", page=113, audio_file="A1-11.mp3",
             instruction="Hören Sie den Text und wählen Sie die richtige Antwort.",
             metadata={"book_page": 113, "note": "Javoblar kitobning javoblar varag'idan; audio yuklanganda admin tekshirsin."},
             questions=HOEREN, max_score=len(HOEREN)),
        base(L, "schreiben", 1, "Schreiben: Was mache ich zu Hause?", page=114,
             prompt="Schreiben Sie über Ihre Hausarbeit (Was mache ich zu Hause?):\n"
                    "Einleitung: Ich heiße … und ich bin oft zu Hause. In diesem Text schreibe ich über meine Hausarbeit.\n"
                    "Hauptteil: Was machen Sie zu Hause, wann und wo? (Am Morgen mache ich mein Bett und frühstücke in der Küche. Danach putze ich "
                    "mein Zimmer … Am Nachmittag … Am Abend …)\nSchluss: Ihre Meinung (Ich helfe zu Hause gern, weil Hausarbeit wichtig ist.)",
             task_type="description", min_words=40, max_words=120, time_limit=20,
             support_phrases=["Am Morgen mache ich …", "Danach putze ich …", "Am Abend koche ich …", "Ich helfe zu Hause gern, weil …"]),
        base(L, "sprechen", 1, "Sprechen: Mein(e) beste(r) Freund(in)", page=115, topic="Mein bester Freund / Meine beste Freundin",
             prompt="Sprechen Sie über Ihren besten Freund / Ihre beste Freundin. Beantworten Sie die Fragen.",
             questions=["Wie heißt dein(e) beste(r) Freund(in)?", "Wie alt ist er/sie?", "Wo wohnt er/sie?", "Wie sieht er/sie aus?",
                        "Was macht er/sie gern?", "Was macht deinen besten Freund / deine beste Freundin besonders?"],
             response_type="monolog", min_duration=30, max_duration=120,
             speech_goal="Eine Person beschreiben: Name, Alter, Wohnort, Aussehen, Hobbys, Charakter.",
             keywords=["Mein bester Freund heißt", "Er/Sie ist … Jahre alt", "Er/Sie wohnt", "Er/Sie ist groß / freundlich"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 11: Wohnen", page=116, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 11", source="vizu",
             instruction="Sifat darajalari va uy-joy so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Berlin ist ___ als Heidelberg. (groß)", ["größer", "großer", "am größten"], "größer"),
                 choice_gap("München ist ___ als Berlin. (teuer)", ["teurer", "teuerer", "teuer"], "teurer"),
                 choice_gap("Das ist das ___ Haus. (alt)", ["älteste", "alteste", "älter"], "älteste"),
                 mc("Komparativ von „gut“:", ["guter", "besser", "am besten"], "B"),
                 mc("Superlativ von „viel“:", ["am vielsten", "am meisten", "mehr"], "B"),
                 mc("Superlativ von „laut“:", ["am lautsten", "am lautesten", "am lauter"], "B"),
                 mc("„die Miete“ — o'zbekchasi qaysi?", ["ijara", "lift", "qo'shni"], "A"),
                 mc("„der Vermieter“ — o'zbekchasi qaysi?", ["uy egasi", "ijarachi", "qo'shni"], "A"),
                 tf("„billig“ bedeutet „arzon“.", True),
                 match("Was passt zusammen?", ["hell", "dunkel", "der Aufzug", "die Heizung"], ["yorug'", "qorong'i", "lift", "isitish tizimi", "eshik"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
