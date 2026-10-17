"""A2 8. Unterricht — Konsum, Werbung und Produkte — Grammatik: trotzdem (Gegensatz) (book pp. 84-93).

Book: Frage p.85, trotzdem p.86, Grammatik-Aufgaben A/B/C p.87, Lesen (Konsum,
Werbung und Umwelt; ten questions) pp.88-89, Hören (Einkauf von Susanna und
Johann, 6 + 6 questions, no transcript) p.90, Schreiben (Thema + E-Mail)
p.91, Sprechen p.92, Wortschatzmethode (five word sets, write a text) p.93.
The handout adds "Wichtige Begriffe" with translations (word list) and 20
"Trotzdem …" sentences.

Keys: Lesen and Hören from "Vizu-Antworten A2". The book's Grammatik-Aufgaben
(A: gaps partly misprinted, B: open sentences, C: rewrite) and the handout's
"Trotzdem …" sentences have open answers — "wird von dem Lehrer korrigiert":
written tasks for the teacher."""

from . import (
    article_set, base, exercise, forward_vocab_set, intro_html, mc, numbered_words, reverse_vocab_set, summary_html, vocab_match_sets,
)

L = 8
LESSON_TITLE = "Konsum, Werbung und Produkte"
LESSON_DESCRIPTION = "Thema: Konsum, Werbung und Produkte · Grammatik: trotzdem (Gegensatz)"
AUDIO = {"vizu-a2-l08-hoeren-01": "A2 8.Unterricht.mp3"}

EINFUEHRUNG_HTML = intro_html(
    8, "Konsum, Werbung und Produkte", "trotzdem (Gegensatz)",
    ["„trotzdem“ bilan qarama-qarshilik ifodalash: Es regnet. Trotzdem gehen wir spazieren.;",
     "trotzdem va aber farqini bilish;",
     "xarid, reklama va iste'mol so'zlarini o'rganish."],
    ["odamlar nima uchun keraksiz narsalar sotib olishini muhokama qilasiz;",
     "iste'mol, reklama va atrof-muhit haqidagi matnni tushunasiz;",
     "Susanna va Johannning xaridlari haqidagi audioni tushunasiz;",
     "onlayn va do'kondan xarid qilish haqida gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(8, [
    "<strong>trotzdem</strong> zeigt einen starken Gegensatz: Die Situation ist negativ oder schwierig, aber das Ergebnis ist anders.",
    "<strong>Satzbau:</strong> Ich bin müde. Trotzdem lerne ich Deutsch. (trotzdem auf Position 1 → Verb auf Position 2)",
    "<strong>Vergleich:</strong> Ich bin müde, aber ich lerne Deutsch. · Ich bin müde. Trotzdem lerne ich Deutsch.",
    "<strong>Wortschatz:</strong> der Konsum, das Einkommen, die Werbung, der Einfluss, die Umwelt, der Müll, nachhaltig, die Qualität.",
])

GRAMMAR_HTML = (
    "<h3>trotzdem (Gegensatz)</h3><p>Es regnet. → Trotzdem …</p>"
    "<h4>Bedeutung</h4><ul><li>„trotzdem“ zeigt einen starken Gegensatz zwischen zwei Aussagen.</li>"
    "<li>Eine Situation ist negativ oder schwierig, aber das Ergebnis ist anders.</li></ul>"
    "<h4>Beispiele</h4><ul><li>Ich bin müde. <strong>Trotzdem</strong> lerne ich Deutsch.</li><li>Es regnet. <strong>Trotzdem</strong> gehen wir spazieren.</li>"
    "<li>Er hat kein Geld. <strong>Trotzdem</strong> kauft er ein Handy.</li><li>Sie hat viel Stress. <strong>Trotzdem</strong> sieht sie gut aus.</li>"
    "<li>Ich habe keine Zeit. <strong>Trotzdem</strong> komme ich mit.</li><li>Wir sind spät. <strong>Trotzdem</strong> warten sie auf uns.</li>"
    "<li>Er versteht die Aufgabe nicht. <strong>Trotzdem</strong> macht er weiter.</li><li>Sie ist krank. <strong>Trotzdem</strong> geht sie zur Arbeit.</li>"
    "<li>Das Wetter ist schlecht. <strong>Trotzdem</strong> fahren wir ans Meer.</li><li>Ich habe Hunger. <strong>Trotzdem</strong> esse ich nichts.</li>"
    "<li>Er ist sehr alt. <strong>Trotzdem</strong> arbeitet er jeden Tag.</li><li>Wir haben wenig Platz. <strong>Trotzdem</strong> laden wir viele Gäste ein.</li>"
    "<li>Sie ist nervös. <strong>Trotzdem</strong> spricht sie vor vielen Menschen.</li><li>Er hat keine Lust. <strong>Trotzdem</strong> hilft er uns.</li></ul>"
    "<h4>Vergleich: aber</h4><ul><li>Ich bin müde, <strong>aber</strong> ich lerne Deutsch.</li><li>Ich bin müde. <strong>Trotzdem</strong> lerne ich Deutsch.</li></ul>"
    "<p>Nach „trotzdem“ (Position 1) steht das Verb auf Position 2; nach „aber“ bleibt die normale Wortstellung.</p>"
)
_TROTZDEM_20 = ["Ich bin müde. → Trotzdem … (Beispiel: Ich bin müde, trotzdem gehe ich zur Arbeit.)",
                "Es regnet. → Trotzdem … (Beispiel: Es regnet, trotzdem gehe ich spazieren.)",
                "Ich habe wenig Zeit. → Trotzdem … (Beispiel: Ich habe wenig Zeit, trotzdem mache ich meine Hausaufgaben.)",
                "Er ist krank.", "Wir haben kein Geld.", "Sie hat viel Stress.", "Ich habe Angst.", "Es ist sehr kalt.", "Ich habe keine Lust.",
                "Er hat wenig gelernt.", "Wir sind spät.", "Ich verstehe das Thema nicht.", "Sie ist traurig.", "Ich habe viel Arbeit.", "Es ist schwierig.",
                "Ich habe Kopfschmerzen.", "Er ist alt.", "Wir sind müde.", "Ich habe kein Auto.", "Sie hat keine Erfahrung."]
_B = ["Ich / müde sein / lernen / Deutsch", "Es / kalt sein / gehen / ich / schwimmen", "Sie / Angst haben / sie / sprechen / trotzdem",
      "Wir / kein Geld haben / ein Geschenk / kaufen", "Er / krank sein / zur Arbeit / kommen", "Ich / wenig Zeit haben / ein Buch / lesen",
      "Du / müde sein / Sport / machen", "Sie / viele Aufgaben haben / sich / ausruhen", "Wir / Probleme haben / weiterhin / arbeiten",
      "Ich / schlecht fühlen / heute / glücklich sein"]
_C = ["Ich bin müde, aber ich gehe zur Schule.", "Es regnet, aber ich gehe spazieren.", "Sie haben viel Geld, trotzdem kaufen sie nichts.",
      "Wir sind spät, aber wir nehmen den Bus.", "Er ist krank, aber er geht zur Arbeit.", "Ich habe keine Zeit, aber ich lese ein Buch.",
      "Du hast Angst, aber du machst die Prüfung.", "Sie ist müde, aber sie fährt mit dem Auto.", "Wir haben Hunger, aber wir essen nichts.",
      "Ich bin traurig, aber ich lache."]

TEXT = (
    "Heute leben wir in einer Konsumgesellschaft. Menschen kaufen immer mehr Produkte – besonders online. Studien zeigen, dass Konsum eng mit unserem "
    "Einkommen verbunden ist. In vielen entwickelten Ländern geben Menschen einen großen Teil ihres Geldes für Produkte und Dienstleistungen aus.\n\n"
    "Werbung hat dabei einen starken Einfluss. Jeden Tag sehen wir Werbung im Internet, auf dem Handy und im Fernsehen. Besonders soziale Medien spielen "
    "eine große Rolle. Firmen benutzen Influencer und moderne Marketing-Strategien, um Produkte attraktiver zu machen. Trotzdem kaufen viele Menschen "
    "Dinge, die sie nicht wirklich brauchen.\n\nEin großes Problem ist die Umwelt. Laut OECD produziert eine Person im Durchschnitt etwa 552 kg Müll pro "
    "Jahr. In der Europäischen Union sind es etwa 500 kg Müll pro Person jährlich.\n\nAuch Plastik ist ein großes Problem. Eine Person produziert "
    "ungefähr 36 kg Plastikmüll pro Jahr.\n\nNoch schlimmer ist elektronischer Müll. Im Jahr 2022 wurden weltweit 62 Millionen Tonnen Elektroschrott "
    "produziert – und diese Zahl wächst jedes Jahr.\n\nEin weiteres Beispiel ist Lebensmittelverschwendung. Etwa ein Drittel aller Lebensmittel weltweit "
    "wird weggeworfen. Das sind ungefähr 931 Millionen Tonnen pro Jahr.\n\nDiese Zahlen zeigen: Zu viel Konsum hat negative Folgen für die Umwelt.\n\n"
    "Ich denke, wir sollten bewusster leben. Man muss nicht alles kaufen, was man in der Werbung sieht. Es ist besser, weniger zu konsumieren, Produkte "
    "länger zu benutzen und auf Qualität zu achten. Außerdem sollten wir mehr recyceln und nachhaltige Produkte wählen.\n\nMerke: Jeder Kauf ist eine "
    "Entscheidung – für dich und für unsere Umwelt!")
_KL = "Javob: Vizu-Antworten A2 (8. Unterricht, Lesen)."
LESEN = [
    mc("Was bedeutet „Konsumgesellschaft“?", ["Menschen arbeiten wenig", "Menschen kaufen viele Produkte", "Menschen reisen viel"], "B", _KL),
    mc("Wo kaufen Menschen heute besonders viele Produkte?", ["im Supermarkt", "online", "in der Schule"], "B", _KL),
    mc("Womit ist Konsum eng verbunden?", ["mit dem Wetter", "mit dem Einkommen", "mit der Sprache"], "B", _KL),
    mc("Wo sehen wir Werbung jeden Tag?", ["nur im Radio", "nur im Kino", "im Internet, Fernsehen und Handy"], "C", _KL),
    mc("Wer zeigt oft Produkte im Internet?", ["Lehrer", "Influencer", "Ärzte"], "B", _KL),
    mc("Wie viel Müll produziert eine Person laut OECD pro Jahr?", ["200 kg", "552 kg", "1000 kg"], "B", _KL),
    mc("Wie viel Müll produziert eine Person in der EU ungefähr?", ["300 kg", "500 kg", "700 kg"], "B", _KL),
    mc("Wie viel Plastikmüll produziert eine Person pro Jahr?", ["10 kg", "36 kg", "100 kg"], "B", _KL),
    mc("Wie viel Elektroschrott wurde 2022 weltweit produziert?", ["20 Millionen Tonnen", "62 Millionen Tonnen", "100 Millionen Tonnen"], "B", _KL),
    mc("Was ist ein Problem laut Text?", ["zu wenig Werbung", "zu wenig Produkte", "zu viel Konsum"], "C", _KL),
]
_KH = "Javob: Vizu-Antworten A2 (8. Unterricht, Hören)."
HOEREN = [
    mc("Susanna: Wo kauft Susanna oft ein?", ["auf dem Markt", "im Supermarkt oder online", "nur im Dorf"], "B", _KH),
    mc("Susanna: Wie viel Geld gibt sie pro Woche aus?", ["50–60 Euro", "80–100 Euro", "120–150 Euro"], "B", _KH),
    mc("Susanna: Wie viel Milch kauft sie pro Woche?", ["1 Liter", "3 Liter", "2 Liter"], "C", _KH),
    mc("Susanna: Was trinkt Susanna jeden Tag?", ["Tee", "Kaffee", "Saft"], "B", _KH),
    mc("Susanna: Wie viele Fertiggerichte kauft sie pro Woche?", ["2–3", "keine", "5–6"], "A", _KH),
    mc("Susanna: Was kauft sie manchmal am Wochenende?", ["Gemüse", "Fleisch", "Schokolade"], "C", _KH),
    mc("Johann: Wo kauft Johann oft ein?", ["im Internet", "auf dem Markt", "im Einkaufszentrum"], "B", _KH),
    mc("Johann: Wie viel Geld gibt er pro Woche aus?", ["60–70 Euro", "90–100 Euro", "30–40 Euro"], "A", _KH),
    mc("Johann: Wie viel Kartoffeln kauft er pro Woche?", ["1 kg", "2 kg", "3 kg"], "B", _KH),
    mc("Johann: Wie viel Fleisch kauft er ungefähr?", ["1 kg", "200 g", "500 g"], "C", _KH),
    mc("Johann: Was trinkt Johann meistens?", ["Kaffee", "Wasser", "Cola"], "B", _KH),
    mc("Johann: Was macht er am Sonntag?", ["Er arbeitet.", "Er reist.", "Er kauft oder backt Kuchen."], "C", _KH),
]

WORDS = numbered_words([
    ("der Konsum", "iste’mol"), ("das Einkommen", "daromad"), ("die Werbung", "reklama"), ("der Einfluss", "ta’sir"),
    ("der Influencer", "ijtimoiy tarmoqdagi mashhur shaxs"), ("die Umwelt", "atrof-muhit"), ("der Müll", "chiqindi"), ("der Elektroschrott", "elektron chiqindilar"),
    ("die Lebensmittelverschwendung", "oziq-ovqat isrofi"), ("nachhaltig", "barqaror / ekologik"), ("die Qualität", "sifat")], "Wichtige Begriffe")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), forward_vocab_set(WORDS)) if s]
DEFINITIONS = [
    ("der Konsum", "Das Kaufen und Benutzen von Produkten."), ("das Einkommen", "Das Geld, das eine Person verdient."),
    ("die Werbung", "Informationen oder Anzeigen, die Produkte zeigen und verkaufen."),
    ("der Einfluss", "Die Wirkung auf Menschen (z. B. Werbung beeinflusst unsere Entscheidungen)."),
    ("der Influencer", "Eine bekannte Person im Internet, die Produkte empfiehlt."), ("die Umwelt", "Natur, Luft, Wasser und unsere Umgebung."),
    ("der Müll", "Dinge, die wir wegwerfen."), ("der Elektroschrott", "Alte elektronische Geräte wie Handy oder Computer."),
    ("die Lebensmittelverschwendung", "Wenn Essen weggeworfen wird."), ("nachhaltig", "Gut für die Umwelt und für die Zukunft."),
    ("die Qualität", "Wie gut ein Produkt ist."),
]
VARIANTEN = {
    "Variante 1": ["kaufen", "der Preis", "günstig", "vergleichen", "online", "der Rabatt"],
    "Variante 2": ["die Werbung", "beeinflussen", "überzeugen", "das Angebot", "die Entscheidung", "auswählen"],
    "Variante 3": ["das Geschäft", "anprobieren", "die Qualität", "unterscheiden", "sofort", "die Erfahrung"],
    "Variante 4": ["bestellen", "die Lieferung", "dauern", "zurückgeben", "erhalten", "bequem"],
    "Variante 5": ["teuer", "sparen", "das Budget", "planen", "notwendig", "verzichten"],
}


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 8. Unterricht", source="vizu", page=84, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Warum kaufen die Menschen Dinge, die sie nicht wirklich brauchen?", page=85,
             prompt="Warum kaufen die Menschen Dinge, die sie nicht wirklich brauchen? Sprechen Sie über die drei Gründe.",
             questions=["A: Wegen Werbung und Mode", "B: Aus Emotionen und Gewohnheit", "C: Aus sozialem Druck"], min_duration=20, max_duration=120,
             metadata={"book_points": {
                 "A": ["Werbung macht uns Dinge schmackhaft.", "Modetrends ändern sich schnell.", "Markenprodukte wirken attraktiver.",
                       "Influencer zeigen viele Produkte.", "Rabatte und Sonderangebote locken.", "Wir wollen nicht „out“ sein."],
                 "B": ["Wir kaufen aus Langeweile.", "Einkaufen verbessert die Stimmung.", "Wir belohnen uns selbst.", "Gewohnheiten sind schwer zu ändern.",
                       "Impulskäufe passieren schnell.", "Wir möchten uns wichtig fühlen."],
                 "C": ["Wir wollen anderen gefallen.", "Freunde haben ähnliche Dinge.", "Soziale Medien erzeugen Druck.", "Wir vergleichen uns mit anderen.",
                       "Ansehen und Status spielen eine Rolle.", "Wir wollen dazugehören."]}}),
        base(L, "grammatik", 1, "Grammatik: trotzdem (Gegensatz)", page=86, rules=[{"title": "trotzdem (Gegensatz)", "html": GRAMMAR_HTML}]),
        base(L, "schreiben", 2, "Grammatik-Aufgaben: Sätze mit „trotzdem“", page=87, task_type="other",
             prompt="A2 8. Unterricht — Üben · Verstehen · Besser sprechen!\n\nB) Bilde passende Sätze mit „trotzdem“:\n"
                    + "\n".join(f"{i}. {s}" for i, s in enumerate(_B, start=1))
                    + "\n\nC) Fehler finden und korrigieren — schreibe die Sätze mit „trotzdem“:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(_C, start=1))
                    + "\n\nUnterrichtsblatt — Schreiben Sie 20 Sätze mit „trotzdem“:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(_TROTZDEM_20, start=1)),
             min_words=80, max_words=500, time_limit=40,
             metadata={"note": "Ochiq javobli mashqlar — Vizu-Antworten: „wird von dem Lehrer korrigiert“. Kitobdagi A-mashq (bo'sh joylar xato "
                               "chop etilgan) kiritilmadi."},
             support_phrases=["Ich bin müde. Trotzdem lerne ich Deutsch.", "Es ist kalt. Trotzdem gehe ich schwimmen."]),
        base(L, "lesen", 1, "Lesen: Konsum, Werbung und Umwelt — Die Realität hinter dem Kauf", page="88-89",
             instruction="Lesen Sie den Text und lösen Sie den Test.", passages=[{"title": "Konsum, Werbung und Umwelt: Die Realität hinter dem Kauf", "text": TEXT}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Einkauf von Susanna und Einkauf von Johann", page=90, audio_file="A2 8.Unterricht.mp3",
             instruction="Multiple-Choice-Test: Hören Sie den Text und wählen Sie die richtige Antwort (A, B oder C).", questions=HOEREN,
             max_score=len(HOEREN)),
        base(L, "schreiben", 1, "Schreiben: Was ist wichtig für mich beim Einkaufen?", page=91, task_type="description",
             prompt="Schreiben Sie einen kurzen Text über Ihr Einkaufen. Schreiben Sie mindestens 80 Wörter.\n\nPunkte:\n"
                    "• Was kaufen Sie oft ein? (Lebensmittel, Kleidung, Technik …)\n• Wo kaufen Sie ein? (Supermarkt, Online, Markt …)\n"
                    "• Was ist für Sie wichtig beim Einkaufen? (Preis, Qualität, Marke …)\n• Kaufen Sie lieber online oder im Geschäft? Warum?\n"
                    "• Wie oft gehen Sie einkaufen?\n• Haben Sie ein besonderes Einkaufserlebnis gehabt?",
             min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: E-Mail an meine Freundin — neuer Laptop", page=91, task_type="email",
             prompt="Info: Sie haben einen Laptop im Internet gekauft. Schreiben Sie eine E-Mail an Ihre Freundin. Schreiben Sie mindestens 80 Wörter.\n\n"
                    "Punkte:\n• Sagen Sie, dass Sie einen neuen Laptop gekauft haben.\n• Erzählen Sie, wo Sie ihn gekauft haben (Internet / Website).\n"
                    "• Beschreiben Sie den Preis und die Qualität.\n• Schreiben Sie über die Lieferung (schnell oder langsam?).\n"
                    "• Sagen Sie, ob Sie zufrieden sind oder nicht.\n• Fragen Sie Ihre Freundin nach ihrer Meinung.",
             audience="Ihre Freundin (informell)", min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Wort zu Wort Wortschatzmethode (Einkaufen A2)", page=93, task_type="description",
             prompt="Formulieren Sie mit den Wörtern einer Variante einen Text (Variante 2–5).\n\n"
                    + "\n".join(f"{k}: {', '.join(v)}" for k, v in VARIANTEN.items())
                    + "\n\nBeispiel (Variante 1) — Überschrift: Online einkaufen ist praktisch. Ich kaufe oft Kleidung online, weil der Preis für mich sehr "
                      "wichtig ist. Ich suche immer günstige Angebote und vergleiche Produkte im Internet. Online kann man viele Optionen finden, und "
                      "manchmal gibt es Rabatt.",
             min_words=40, max_words=200, time_limit=25),
        base(L, "sprechen", 1, "Sprechen: Online einkaufen oder im Geschäft kaufen", page=92, topic="Online einkaufen oder im Geschäft",
             prompt="Sprechen Sie über das Thema. Tipps: Sprich über beide Möglichkeiten. Gib Beispiele aus deinem Leben. Vergleiche und begründe. "
                    "Sage deine Meinung am Ende.",
             questions=["Was ist besser: Online einkaufen oder im Geschäft?", "Was sind die Vorteile vom Online-Einkauf?",
                        "Was sind die Nachteile vom Online-Einkauf?", "Was sind die Vorteile vom Einkaufen im Geschäft?", "Was machst du persönlich lieber und warum?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Online- und Geschäftseinkauf vergleichen, Vor- und Nachteile nennen, eigene Meinung begründen.",
             keywords=["Ich finde, dass", "Vorteil", "Nachteil", "weil", "trotzdem"],
             sample_answer="Ich finde, dass Online-Shopping sehr bequem ist, aber im Geschäft kann man Produkte direkt sehen. Man spart Zeit, hat viele "
                           "Angebote und kann von zu Hause bestellen. Man kann die Qualität nicht sofort prüfen und manchmal gibt es Lieferprobleme. Im "
                           "Geschäft kann man Produkte anfassen, ausprobieren und sofort mitnehmen. Ich kaufe lieber online / im Geschäft, weil …"),
        base(L, "wortschatz", 1, "Wortschatz: Wichtige Begriffe — Konsum und Umwelt", page="88", words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False,
             metadata={"note": "Dars varag'idagi „Wichtige Begriffe“ (tarjima bilan). OECD — xalqaro tashkilot.",
                       "definitions": {w: d for w, d in DEFINITIONS}}),
        base(L, "uebungen", 1, "Übungen: A2 8. Unterricht", source="vizu", exercises=[s for s in (
            exercise("trotzdem oder aber?", [
                mc("Ich bin müde. ___ lerne ich Deutsch.", ["Trotzdem", "Aber", "Weil"], "A", "Kitobdagi misol."),
                mc("Ich bin müde, ___ ich lerne Deutsch.", ["aber", "trotzdem", "deshalb"], "A", "aber + normale Wortstellung."),
                mc("Es regnet. Trotzdem ___ spazieren.", ["gehen wir", "wir gehen", "wir spazieren gehen"], "A", "Nach trotzdem: Verb auf Position 2."),
                mc("Er hat kein Geld. Trotzdem ___ ein Handy.", ["kauft er", "er kauft", "kaufen er"], "A"),
                mc("Was zeigt „trotzdem“?", ["einen Gegensatz", "einen Grund", "eine Bedingung"], "A"),
            ], "trotzdem: Verb auf Position 2 (kitob, 86-bet).", source="vizu"),
            reverse_vocab_set(WORDS),
        ) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 8. Unterricht", source="vizu",
             instruction="trotzdem va iste'mol so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Sie ist krank. Trotzdem ___ sie zur Arbeit.", ["geht", "gehen", "sie geht"], "A"),
                 mc("Es ist kalt. ___ gehe ich schwimmen.", ["Trotzdem", "Weil", "Wenn"], "A"),
                 mc("Wie viel Plastikmüll produziert eine Person pro Jahr?", ["ungefähr 36 kg", "ungefähr 10 kg", "ungefähr 100 kg"], "A", "Lesen."),
                 mc("Was ist ein Problem laut Text?", ["zu viel Konsum", "zu wenig Werbung", "zu wenig Produkte"], "A", "Lesen."),
                 mc("„die Werbung“ — o'zbekchasi?", ["reklama", "daromad", "sifat"], "A"),
                 mc("„nachhaltig“ — o'zbekchasi?", ["barqaror / ekologik", "qimmat", "tez"], "A"),
                 mc("„der Müll“ — o'zbekchasi?", ["chiqindi", "ta'sir", "iste'mol"], "A"),
                 mc("„das Einkommen“ — o'zbekchasi?", ["daromad", "xarajat", "chegirma"], "A"),
                 mc("Ich habe keine Zeit. Trotzdem ___ ich mit.", ["komme", "kommen", "kommst"], "A"),
                 mc("Welcher Satz ist richtig?", ["Wir sind spät. Trotzdem warten sie auf uns.", "Wir sind spät. Trotzdem sie warten auf uns.",
                                                  "Wir sind spät, trotzdem sie auf uns warten."], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 8. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
