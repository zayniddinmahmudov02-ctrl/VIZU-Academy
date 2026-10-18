"""A2 7. Unterricht — Reisen im Alltag und Mobilität — Grammatik: Präpositionen (book pp. 73-83).

Book: Frage p.74, Präpositionen pp.75-76, Grammatik-Aufgabe (30 x A/B/C) p.77,
Lesen (Verkehrsmittel, twelve Richtig/Falsch) pp.78-79, Hören (Max und Sara,
15 questions numbered 1-14 and 16, no transcript, no key) p.80, Schreiben
(Thema + E-Mail an Reisebüro) p.81, Sprechen p.82, Wörter worksheet (30)
p.83; the handout lists 50 words with translations (word list).

Keys: "Vizu-Antworten A2" has none. Lesen: decided by the quoted sentence.
Präpositionen: graded only where exactly one option is correct German; five
questions have no unambiguous answer and are NOT auto-graded (listed in the
metadata for the admin): 2 "Wir gehen ___ den Bahnhof" (bei/zu/von — "zu den
Bahnhof" is wrong, zu + Dativ), 9 "Ich stelle mein Fahrrad ___ dem Haus"
(stellen → vor das Haus), 18 "Der Zug fährt ___ Berlin" (durch and nach are
both correct), 25 "Ich fahre ___ meinen Freund" (zu meinen is wrong), 26
"Ich komme ___ dem Zug" (zu / mit / von are all correct). Hören waits for an
admin (key_pending); questions 7 and 8 are printed identically. Audio: the
two files "A2 7.Unterricht Text 1 / Text 2" belong to the one Hören task."""

from . import (
    article_set, base, exercise, forward_vocab_set, html_table, intro_html, mc, mc_pending, numbered_words, reverse_vocab_set, summary_html, tf,
    vocab_match_sets,
)

L = 7
LESSON_TITLE = "Reisen im Alltag und Mobilität"
LESSON_DESCRIPTION = "Thema: Reisen im Alltag und Mobilität · Grammatik: Präpositionen (Dativ, Akkusativ, Wechselpräpositionen)"
AUDIO = {"vizu-a2-l07-hoeren-01": ["A2 7.Unterricht Text 1.mp3", "A2 7.Unterricht Text 2.mp3"]}

EINFUEHRUNG_HTML = intro_html(
    7, "Reisen im Alltag und Mobilität", "Präpositionen mit Dativ, Akkusativ und Wechselpräpositionen",
    ["Dativ (aus, bei, mit, nach, seit, von, zu …) va Akkusativ (für, um, durch, gegen, ohne …) predloglarini bilish;",
     "Wechselpräpositionen: Wo? → Dativ, Wohin? → Akkusativ;",
     "transport va sayohat so'zlarini o'rganish."],
    ["qaysi transport bugun eng qulay ekanini aytasiz;",
     "nemislar qaysi transportdan foydalanishi haqidagi matnni tushunasiz;",
     "Max va Saraning sayohat hikoyalarini tinglaysiz;",
     "sayohat agentligiga e-mail yozasiz va oxirgi sayohatingiz haqida gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(7, [
    "<strong>Dativ:</strong> aus, bei, mit, nach, seit, von, zu, außer, gegenüber, entgegen, ab — Ich fahre mit dem Bus.",
    "<strong>Akkusativ:</strong> für, um, durch, gegen, ohne, entlang, bis — Ich gehe durch den Park.",
    "<strong>Wechselpräpositionen:</strong> in, auf, über, neben, an, hinter, vor, zwischen, unter — Wo? Dativ (Ich bin in dem Raum.) · "
    "Wohin? Akkusativ (Ich gehe in den Raum.)",
    "<strong>Wortschatz:</strong> die Reise, der Flughafen, buchen, ankommen, abfahren, der Fahrplan, die Unterkunft, die Sehenswürdigkeit.",
])

_DAT = [["aus (…dan, ichidan)", "Ich komme aus der Schule."], ["bei (yonida, huzurida)", "Ich bin beim Arzt."], ["mit (bilan)", "Ich gehe mit meinem Freund."],
        ["nach (…ga, tomon)", "Ich fahre nach Deutschland."], ["seit (…dan beri)", "Ich lerne Deutsch seit einem Jahr."],
        ["von (…dan)", "Das Geschenk ist von meiner Mutter."], ["zu (…ga, oldiga)", "Ich gehe zum Lehrer."],
        ["außer (…dan tashqari)", "Außer meinem Bruder kommt niemand."], ["gegenüber (ro‘parasida)", "Die Bank ist gegenüber dem Hotel."],
        ["entgegen (qarshi tomonga)", "Er läuft dem Hund entgegen."], ["ab (…dan boshlab)", "Ab Montag habe ich Unterricht."]]
_AKK = [["für (…uchun)", "Das Geschenk ist für den Lehrer."], ["um (atrofida)", "Wir sitzen um den Tisch."], ["durch (…orqali)", "Ich gehe durch den Park."],
        ["gegen (qarshi)", "Er spielt gegen den Freund."], ["ohne (…siz)", "Ich komme ohne dich."], ["entlang (bo‘ylab)", "Wir gehen den Fluss entlang."],
        ["bis (…gacha)", "Ich bleibe bis nächsten Montag hier."]]
_WECHSEL = [["in (ichida / ichiga)", "Ich bin in dem Raum.", "Ich gehe in den Raum."],
            ["auf (ustida / ustiga)", "Das Buch ist auf dem Tisch.", "Ich lege das Buch auf den Tisch."],
            ["über (ustida / ustiga)", "Die Lampe ist über dem Tisch.", "Ich hänge die Lampe über den Tisch."],
            ["neben (yonida / yoniga)", "Ich sitze neben dem Freund.", "Ich setze mich neben den Freund."],
            ["an (yonida / tegib / yoniga)", "Das Bild ist an der Wand.", "Ich hänge das Bild an die Wand."],
            ["hinter (orqasida / orqasiga)", "Der Hund ist hinter dem Haus.", "Der Hund läuft hinter das Haus."],
            ["vor (oldida / oldiga)", "Ich stehe vor dem Haus.", "Ich gehe vor das Haus."],
            ["zwischen (orasida / orasiga)", "Ich sitze zwischen den Freunden.", "Ich setze mich zwischen die Freunde."],
            ["unter (ostida / ostiga)", "Die Katze ist unter dem Tisch.", "Die Katze geht unter den Tisch."]]
RULES = [
    {"title": "Präpositionen mit Dativ und Akkusativ", "html": "<h3>Präpositionen mit Dativ</h3>" + html_table(["Präposition", "Beispiel (Misol)"], _DAT)
     + "<h3>Präpositionen mit Akkusativ</h3>" + html_table(["Präposition", "Beispiel (Misol)"], _AKK)
     + "<p><strong>Merke dir!</strong> Dativ: Frage mit „Wo?“ · Akkusativ: Frage mit „Wohin?“</p>"},
    {"title": "Wechselpräpositionen", "html": "<h3>Wo? (Dativ – qayerda?) und Wohin? (Akkusativ – qayerga?)</h3>"
     + html_table(["Präposition", "WO? (Dativ)", "WOHIN? (Akkusativ)"], _WECHSEL)
     + "<h3>Übersicht</h3>" + html_table(["Dativ Präpositionen", "Akkusativ Präpositionen", "Wechselpräpositionen"], [
         ["aus, bei, mit, nach, seit, von, zu, außer, gegenüber, entgegen, ab", "für, um, durch, gegen, ohne, entlang, bis",
          "in, auf, über, neben, an, hinter, vor, zwischen, unter"]])
     + "<p><strong>Merke dir!</strong> Dativ = Wo? · Akkusativ = Wohin? · Wechselpräpositionen können beides!</p>"},
]

# p.77 — (number, sentence, options, answer, explanation)
_PRAEP = [
    (1, "Ich fahre jeden Tag ___ dem Bus zur Arbeit.", ["mit", "durch", "für"], "A", "mit + Dativ: mit dem Bus."),
    (3, "Ich komme ___ der Arbeit nach Hause.", ["aus", "mit", "für"], "A", "aus + Dativ (kitobdagi variantlardan yagona to'g'risi)."),
    (4, "Er fährt ___ Deutschland.", ["über", "mit", "nach"], "C", "Länder / Städte: nach Deutschland."),
    (5, "Ich warte ___ den Zug.", ["mit", "auf", "durch"], "B", "warten auf + Akkusativ."),
    (6, "Wir laufen ___ den Park.", ["zu", "durch", "bei"], "B", "durch + Akkusativ: durch den Park."),
    (7, "Ich gehe ___ meinen Freund zur Uni.", ["gegen", "ohne", "mit"], "B", "ohne + Akkusativ: ohne meinen Freund (mit braucht Dativ: mit meinem)."),
    (8, "Der Bus hält ___ dem Supermarkt.", ["durch", "vor", "für"], "B", "Wo? vor + Dativ: vor dem Supermarkt."),
    (10, "Ich gehe ___ das Haus.", ["in", "seit", "bei"], "A", "Wohin? in + Akkusativ: in das Haus."),
    (11, "Ich bin schon ___ dem Bus.", ["durch", "in", "für"], "B", "Wo? in + Dativ: in dem Bus."),
    (12, "Wir fahren ___ dem Taxi.", ["zu", "von", "mit"], "C", "mit + Dativ: mit dem Taxi."),
    (13, "Ich komme ___ dir.", ["gegen", "ohne", "mit"], "C", "mit + Dativ: mit dir (ohne / gegen brauchen Akkusativ: dich)."),
    (14, "Er läuft ___ die Straße.", ["bei", "über", "mit"], "B", "Wohin? über + Akkusativ: über die Straße."),
    (15, "Wir gehen ___ die Brücke.", ["zu", "seit", "über"], "C", "über + Akkusativ: über die Brücke."),
    (16, "Ich sitze ___ meinem Freund im Zug.", ["neben", "durch", "für"], "A", "Wo? neben + Dativ: neben meinem Freund."),
    (17, "Ich setze mich ___ meinen Freund.", ["aus", "neben", "seit"], "B", "Wohin? neben + Akkusativ: neben meinen Freund."),
    (19, "Ich fahre ___ der Stadt.", ["bei", "durch", "in"], "C", "Wo? in + Dativ: in der Stadt (durch braucht Akkusativ)."),
    (20, "Ich fahre ___ die Stadt.", ["in", "von", "seit"], "A", "Wohin? in + Akkusativ: in die Stadt."),
    (21, "Der Bus kommt ___ der Haltestelle.", ["mit", "für", "von"], "C", "von + Dativ: von der Haltestelle."),
    (22, "Ich gehe ___ dem Bahnhof.", ["ohne", "zu", "durch"], "B", "zu + Dativ: zu dem Bahnhof (zum Bahnhof)."),
    (23, "Wir warten ___ den Bus.", ["mit", "auf", "bei"], "B", "warten auf + Akkusativ."),
    (24, "Ich bleibe ___ Montag in der Stadt.", ["seit", "mit", "bis"], "C", "bis Montag (…gacha)."),
    (27, "Ich gehe ___ dich ins Kino.", ["gegen", "ohne", "mit"], "B", "ohne + Akkusativ: ohne dich (mit braucht Dativ: mit dir)."),
    (28, "Die Haltestelle ist ___ dem Hotel.", ["nach", "gegenüber", "mit"], "B", "gegenüber + Dativ (Kitob: Die Bank ist gegenüber dem Hotel)."),
    (29, "___ meinem Bruder fahre ich oft.", ["Für", "Mit", "Durch"], "B", "mit + Dativ: mit meinem Bruder."),
    (30, "___ morgen fahre ich nach Berlin.", ["Bei", "Für", "Ab"], "C", "ab (…dan boshlab): ab morgen."),
]
NOT_GRADED = {
    2: "Wir gehen ___ den Bahnhof. (A bei, B zu, C von) — „zu den Bahnhof“ ist falsch (zu + Dativ: zum Bahnhof).",
    9: "Ich stelle mein Fahrrad ___ dem Haus. (A bei, B vor, C mit) — stellen fragt „Wohin?“: vor das Haus.",
    18: "Der Zug fährt ___ Berlin. (A durch, B nach, C mit) — durch und nach sind beide richtig.",
    25: "Ich fahre ___ meinen Freund. (A gegen, B zu, C ohne) — „zu meinen Freund“ ist falsch (zu + Dativ: zu meinem Freund).",
    26: "Ich komme ___ dem Zug. (A zu, B mit, C von) — zu, mit und von sind alle möglich.",
}
PRAEP = [mc(f"{n}. {s}", o, a, e) for n, s, o, a, e in _PRAEP]

TEXT = (
    "In Deutschland benutzen viele Menschen verschiedene Verkehrsmittel. Sie fahren zur Arbeit, zur Schule oder in den Urlaub. Die wichtigsten "
    "Verkehrsmittel sind das Auto, der Bus, der Zug und das Flugzeug. Viele Deutsche fahren mit dem Auto. Besonders in großen Städten wie Berlin, "
    "Hamburg und München gibt es sehr viele Autos. Viele Familien haben ein eigenes Auto. Sie fahren am Wochenende oft in die Natur oder besuchen "
    "Freunde in anderen Städten. Das Auto ist sehr bequem. Man kann fahren, wann man will und wohin man will. Aber es gibt auch Probleme: In der Stadt "
    "gibt es oft Stau, und Parkplätze sind schwer zu finden. Außerdem ist das Auto teuer.\n\nViele Menschen benutzen den Bus im Alltag. In Städten wie "
    "Leipzig und Dresden fahren Busse jeden Tag sehr oft. Schüler fahren mit dem Bus zur Schule, und viele Erwachsene fahren zur Arbeit. Der Bus ist "
    "nicht teuer und sehr praktisch für kurze Strecken. Auch in kleinen Städten und Dörfern ist der Bus wichtig. Aber Busse sind manchmal langsam, "
    "besonders im Verkehr. Oft sind sie auch voll, und man muss auf den Fahrplan warten.\n\nDer Zug ist in Deutschland sehr beliebt. Die Deutsche Bahn "
    "verbindet viele große Städte wie Frankfurt am Main, Köln und Stuttgart. Viele Menschen fahren mit dem Zug zur Arbeit oder reisen in andere Städte. "
    "Mit schnellen Zügen wie ICE kann man sehr schnell fahren. Zum Beispiel fährt man von Berlin nach München in etwa 4 Stunden. Im Zug kann man lesen, "
    "Musik hören oder arbeiten. Das ist sehr angenehm. Aber manchmal sind Züge teuer, und es gibt Verspätungen.\n\nFür lange Reisen benutzen viele "
    "Deutsche das Flugzeug. Große Flughäfen gibt es in Frankfurt am Main, Berlin und München. Viele Menschen fliegen in den Urlaub, zum Beispiel nach "
    "Spanien, Italien oder in die Türkei. Das Flugzeug ist sehr schnell und gut für lange Strecken. Aber es ist oft teuer. Außerdem muss man am "
    "Flughafen lange warten. Fliegen ist auch nicht gut für die Umwelt.\n\nAm Ende kann man sagen: Jedes Verkehrsmittel hat Vorteile und Nachteile. "
    "Die Menschen wählen das Verkehrsmittel nach der Situation. Für kurze Strecken benutzen sie oft den Bus oder das Auto. Für lange Reisen nehmen sie "
    "den Zug oder das Flugzeug.")
LESEN = [
    tf("In Deutschland benutzen viele Menschen verschiedene Verkehrsmittel.", True, "„In Deutschland benutzen viele Menschen verschiedene Verkehrsmittel.“"),
    tf("Die Deutschen benutzen nur das Auto im Alltag.", False, "„Die wichtigsten Verkehrsmittel sind das Auto, der Bus, der Zug und das Flugzeug.“"),
    tf("In Städten wie Berlin gibt es viele Autos.", True, "„Besonders in großen Städten wie Berlin … gibt es sehr viele Autos.“"),
    tf("Das Auto ist unflexibel und unbequem.", False, "„Das Auto ist sehr bequem. Man kann fahren, wann man will und wohin man will.“"),
    tf("Busse sind oft günstig und praktisch.", True, "„Der Bus ist nicht teuer und sehr praktisch für kurze Strecken.“"),
    tf("Busse fahren nur in großen Städten.", False, "„Auch in kleinen Städten und Dörfern ist der Bus wichtig.“"),
    tf("Viele Schüler fahren mit dem Bus zur Schule.", True, "„Schüler fahren mit dem Bus zur Schule …“"),
    tf("Der Zug ist in Deutschland sehr unbeliebt.", False, "„Der Zug ist in Deutschland sehr beliebt.“"),
    tf("Mit dem Zug kann man lesen oder arbeiten.", True, "„Im Zug kann man lesen, Musik hören oder arbeiten.“"),
    tf("Das Flugzeug ist sehr langsam.", False, "„Das Flugzeug ist sehr schnell und gut für lange Strecken.“"),
    tf("Viele Deutsche fliegen in den Urlaub.", True, "„Viele Menschen fliegen in den Urlaub …“"),
    tf("Menschen wählen das Verkehrsmittel nach der Situation.", True, "„Die Menschen wählen das Verkehrsmittel nach der Situation.“"),
]
_MS, _SM = ["Max", "Sara"], ["Sara", "Max"]
HOEREN = [mc_pending(q, o) for q, o in [
    ("1. Wer kommt aus Madrid?", _MS), ("2. Wer ist 35 Jahre alt?", _SM), ("3. Wer reist mit dem Auto?", _MS), ("4. Wer reist mit dem Flugzeug?", _MS),
    ("5. Wer besucht Berlin?", _MS), ("6. Wer kommt aus München?", _MS), ("7. Wer fährt mit dem Bus?", _SM), ("8. Wer fährt mit dem Bus? (2)", _SM),
    ("9. Wer reist durch Europa?", _MS), ("10. Wer fliegt nach Rom?", _MS), ("11. Wer sieht den Hafen?", _MS), ("12. Wer besucht Paris?", _MS),
    ("13. Wer macht eine Reise durch Deutschland?", _SM), ("14. Wer findet den Bus langsam?", _SM), ("16. Wer hört Musik im Zug?", _MS)]]

WORDS = numbered_words([
    ("die Reise", "sayohat"), ("reisen", "sayohat qilmoq"), ("der Urlaub", "ta’til"), ("fahren", "bormoq (transportda)"), ("fliegen", "uchmoq"),
    ("der Zug", "poyezd"), ("der Bus", "avtobus"), ("das Auto", "mashina"), ("das Flugzeug", "samolyot"), ("die Stadt", "shahar"), ("das Land", "qishloq"),
    ("besuchen", "tashrif buyurmoq"), ("sehen", "ko‘rmoq"), ("gehen", "yurmoq"), ("machen", "qilmoq"), ("bleiben", "qolmoq"), ("wohnen", "yashamoq"),
    ("das Wetter", "ob-havo"), ("schön", "chiroyli"), ("interessant", "qiziqarli"), ("teuer", "qimmat"), ("billig", "arzon"), ("schnell", "tez"),
    ("langsam", "sekin"), ("bequem", "qulay"), ("der Flughafen", "aeroport"), ("das Ticket", "chipta"), ("buchen", "bron qilmoq"), ("ankommen", "yetib kelmoq"),
    ("abfahren", "jo‘nab ketmoq"), ("warten", "kutmoq"), ("der Fahrplan", "jadval"), ("die Reisezeit", "sayohat vaqti"), ("die Unterkunft", "turar joy"),
    ("das Hotel", "mehmonxona"), ("das Zimmer", "xona"), ("reservieren", "band qilmoq"), ("die Sehenswürdigkeit", "diqqatga sazovor joy"),
    ("das Museum", "muzey"), ("die Kirche", "cherkov"), ("das Foto", "rasm"), ("fotografieren", "suratga olmoq"), ("die Kultur", "madaniyat"),
    ("das Essen", "ovqat"), ("probieren", "sinab ko‘rmoq"), ("kaufen", "sotib olmoq"), ("die Reisegruppe", "sayohat guruhi"), ("allein", "yolg‘iz"),
    ("zusammen", "birga"), ("erleben", "boshdan kechirmoq")], "Reisen und Mobilität")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]
WORKSHEET = ["der Flughafen", "das Ticket", "buchen", "ankommen", "abfahren", "warten", "der Fahrplan", "die Reisezeit", "die Unterkunft", "das Hotel",
             "reservieren", "die Sehenswürdigkeit", "das Museum", "die Kirche", "das Foto", "fotografieren", "die Kultur", "das Essen", "probieren", "kaufen",
             "die Reisegruppe", "allein", "zusammen", "erleben", "das Wetter", "schön", "interessant", "teuer", "schnell", "bequem"]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 7. Unterricht", source="vizu", page=73, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Welche Verkehrsmittel sind heute am praktischsten?", page=74,
             prompt="Welche Verkehrsmittel sind heute am praktischsten? Wählen Sie und begründen Sie Ihre Meinung.",
             questions=["A) Öffentliche Verkehrsmittel", "B) Eigenes Auto", "C) Flugzeug"], min_duration=20, max_duration=120,
             metadata={"book_points": {
                 "A": ["Busse und Bahnen sind in der Stadt leicht verfügbar und günstig.", "Man muss sich keine Gedanken über Parkplatzsuche machen.",
                       "Öffentliche Verkehrsmittel sind umweltfreundlicher als Autos.", "Man kann während der Fahrt lesen, arbeiten oder entspannen.",
                       "Viele Städte verbessern ständig ihr öffentliches Verkehrsnetz.", "Für Schüler, Studenten und Senioren gibt es meist Ermäßigungen."],
                 "B": ["Mit dem Auto ist man unabhängig und flexibel.", "Man kann jederzeit und überall hinfahren, wo man möchte.",
                       "Für Familien und Reisen ist das Auto sehr praktisch.", "Man kann bequem mit viel Gepäck reisen.",
                       "In ländlichen Gebieten ist das Auto oft die einzige Möglichkeit.", "Moderne Autos bieten Komfort, Sicherheit und viele nützliche Funktionen."],
                 "C": ["Flugzeuge sind ideal für lange Strecken und internationale Reisen.", "Man spart viel Zeit im Vergleich zu anderen Verkehrsmitteln.",
                       "Moderne Flughäfen bieten viele Services und Komfort.", "Flugreisen verbinden Menschen und Kulturen aus aller Welt.",
                       "Für Geschäftsreisen ist das Flugzeug oft die beste Wahl.", "Mit günstigen Angeboten kann Fliegen auch erschwinglich sein."]}}),
        base(L, "grammatik", 1, "Grammatik: Präpositionen", page="75-77", rules=RULES,
             exercises=[exercise("Wähle die richtige Präposition: A, B oder C (25 von 30)", PRAEP,
                                 "Kitob, 77-bet. 2, 9, 18, 25, 26-savollar avtomatik baholanmaydi: ularda bitta aniq to'g'ri javob yo'q.")],
             metadata={"book_page": "75-77", "not_graded": NOT_GRADED}),
        base(L, "lesen", 1, "Lesen: Welche Verkehrsmittel benutzen die Deutschen zur Reise?", page="78-79",
             instruction="Richtig oder falsch? Lies den Text und entscheide.", passages=[{"title": "Welche Verkehrsmittel benutzen die Deutschen zur Reise?",
                                                                                          "text": TEXT}],
             questions=LESEN, max_score=len(LESEN), metadata={"note": "Javob har bir savol izohida matndan iqtibos bilan."}),
        base(L, "hoeren", 1, "Hören Test: Reisen (Max und Sara)", page=80, audio_file="A2 7.Unterricht Text 1 + Text 2.mp3", key_pending=True,
             instruction="Sie hören 2 Geschichten von Personen. Finden Sie die richtige Antwort! Sie hören jeden Text einmal.", questions=HOEREN,
             metadata={"note": "Kalit va transkript yo'q — admin tinglab belgilaydi. Kitobda 15-savol yo'q; 7 va 8-savollar bir xil. Audio: Text 1 va Text 2."}),
        base(L, "schreiben", 1, "Schreiben: Womit mache ich Reise?", page=81, task_type="description",
             prompt="Text schreiben zum Thema: Womit mache ich Reise? Achte auf die Fragen und schreibe vollständige Sätze!\n"
                    "• Wohin möchte ich reisen?\n• Warum reise ich? (Arbeit, Urlaub, Familie …)\n• Mit welchem Verkehrsmittel fahre ich gerne?\n"
                    "• Warum reise ich so und nicht anders?",
             min_words=60, max_words=150, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: E-Mail an Reisebüro", page=81, task_type="email",
             prompt="Schreiben Sie eine E-Mail an das Reisebüro (An: info@reisebuero.de, Betreff: Zugfahrt-Buchung).\n"
                    "• Sagen Sie, dass Sie das Reisebüro schreiben.\n• Erklären Sie, warum Sie Ihre Flugtickets NICHT kaufen.\n"
                    "• Sagen Sie, dass Sie lieber mit dem Zug fahren möchten.\n• Fragen Sie nach einer Zugfahrt-Buchung.",
             audience="Reisebüro (formell)", min_words=50, max_words=120, time_limit=20,
             support_phrases=["Sehr geehrte Damen und Herren,", "ich schreibe Ihnen, weil …", "Ich möchte lieber mit dem Zug fahren.",
                              "Können Sie mir bitte …?", "Mit freundlichen Grüßen"]),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: 30 schwierige Wörter", page=83, task_type="other",
             prompt="Schreiben Sie die Übersetzung und einen Beispielsatz.\n\n" + "\n".join(f"{i}. {w}" for i, w in enumerate(WORKSHEET, start=1)),
             min_words=60, max_words=500, time_limit=40, metadata={"note": "Kitobdagi ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "sprechen", 1, "Sprechen: Meine letzte Reise (Präsentation)", page=82, topic="Meine letzte Reise",
             prompt="Präsentation machen zum Thema: Meine letzte Reise. Sprecht über eure letzte Reise. Benutzt die Fragen und erzählt ausführlich!",
             questions=["Wann und wohin bin ich gereist?", "Mit wem habe ich die Reise gemacht?", "Wie lange war ich dort?",
                        "Wie bin ich gereist? (Auto, Zug, Flugzeug …)", "Was habe ich in der Stadt gemacht?", "Was hat mir am besten gefallen?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Über die letzte Reise im Perfekt erzählen: wann, wohin, mit wem, wie lange, Verkehrsmittel, Erlebnisse.",
             keywords=["bin gereist", "mit dem Zug", "nach", "habe besucht", "hat mir gefallen"]),
        base(L, "wortschatz", 1, "Wortschatz: Reisen und Mobilität", page=83, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False,
             metadata={"note": "Tarjimalar dars varag'idan (50 so'z)."}),
        base(L, "uebungen", 1, "Übungen: A2 7. Unterricht", source="vizu", exercises=[s for s in (
            exercise("Wo? oder Wohin?", [
                mc("Das Buch ist auf ___ Tisch. (Wo?)", ["dem", "den", "der"], "A", "Wo? → Dativ."),
                mc("Ich lege das Buch auf ___ Tisch. (Wohin?)", ["den", "dem", "des"], "A", "Wohin? → Akkusativ."),
                mc("Das Bild ist an ___ Wand.", ["der", "die", "den"], "A", "Wo? → Dativ (die Wand → der Wand)."),
                mc("Ich hänge das Bild an ___ Wand.", ["die", "der", "dem"], "A", "Wohin? → Akkusativ."),
                mc("Welche Präposition steht immer mit Akkusativ?", ["durch", "mit", "bei"], "A"),
                mc("Welche Präposition steht immer mit Dativ?", ["seit", "für", "ohne"], "A"),
            ], "Wechselpräpositionen: Wo? → Dativ, Wohin? → Akkusativ (kitob, 76-bet).", source="vizu"),
            reverse_vocab_set(WORDS),
        ) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 7. Unterricht", source="vizu",
             instruction="Predloglar va sayohat so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Ich fahre ___ dem Zug nach Berlin.", ["mit", "durch", "für"], "A"),
                 mc("Das Geschenk ist ___ den Lehrer.", ["für", "mit", "von"], "A"),
                 mc("Ich gehe ___ den Raum. (Wohin?)", ["in", "aus", "bei"], "A"),
                 mc("Die Katze ist unter ___ Tisch.", ["dem", "den", "das"], "A"),
                 mc("Ich lerne Deutsch ___ einem Jahr.", ["seit", "für", "bis"], "A"),
                 tf("Der Zug ist in Deutschland sehr beliebt.", True, "Lesen."),
                 tf("Das Flugzeug ist gut für kurze Strecken.", False, "Lesen: gut für lange Strecken."),
                 mc("„der Flughafen“ — o'zbekchasi?", ["aeroport", "bekat", "vokzal"], "A"),
                 mc("„die Unterkunft“ — o'zbekchasi?", ["turar joy", "chipta", "jadval"], "A"),
                 mc("„abfahren“ — o'zbekchasi?", ["jo'nab ketmoq", "yetib kelmoq", "kutmoq"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 7. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
