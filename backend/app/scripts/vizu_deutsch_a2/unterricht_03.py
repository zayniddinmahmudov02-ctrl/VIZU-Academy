"""A2 3. Unterricht — Bleiben Sie gesund und fit — Grammatik: Imperativsätze (book pp. 31-40).

Book: Frage p.32, Imperativ p.33, Imperativ-Übung (open: du / ihr / Sie for
ten complaints) p.34, Lesen (two texts, A1-A12) pp.35-36, Hören (doctor's
advice, eight Richtig/Falsch, no transcript) p.37, Schreiben (Thema + E-Mail)
p.38, Sprechen p.39, Wortschatz (60 words) p.40.

Keys: Lesen and Hören from "Vizu-Antworten A2". The Imperativ-Übung has open
answers (any sensible advice) — a written task checked by the teacher.
Typos fixed: "Was nachen" -> "Was machen" (handout), "empfehlt" ->
"empfiehlt" (Hören A5)."""

from . import (
    article_set, base, exercise, forward_vocab_set, intro_html, mc, numbered_words, reverse_vocab_set, summary_html, tf, vocab_match_sets,
)

L = 3
LESSON_TITLE = "Bleiben Sie gesund und fit"
LESSON_DESCRIPTION = "Thema: Bleiben Sie gesund und fit · Grammatik: Imperativsätze"
AUDIO = {"vizu-a2-l03-hoeren-01": "A2.  3.Unterricht Hören.mp3"}

EINFUEHRUNG_HTML = intro_html(
    3, "Bleiben Sie gesund und fit", "Imperativ (du / ihr / Sie)",
    ["Imperativni du, ihr va Sie shakllarida tuzish: Lerne! · Lernt! · Lernen Sie!;",
     "maslahat va iltimos aytish (Trink mehr Wasser! · Schlafen Sie mehr!);",
     "salomatlik, kasallik va sog'lom turmush tarzi so'zlarini o'rganish."],
    ["sog'lig'ingiz uchun nima qilishingizni aytasiz;",
     "sog'lom turmush va kasallikda nima qilish haqidagi matnlarni tushunasiz;",
     "shifokor maslahatlarini tinglab, to'g'ri yoki noto'g'ri ekanini aniqlaysiz;",
     "kasalxonadagi dugonangizni ko'rishga borish haqida e-mail yozasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(3, [
    "<strong>Imperativ mit du:</strong> Du lernst Deutsch. → Lerne Deutsch! (Subjekt und -st fallen weg) — Komm hier! · Lies das Buch!",
    "<strong>Imperativ mit ihr:</strong> Ihr lernt Deutsch. → Lernt Deutsch! (Subjekt fällt weg, -t bleibt)",
    "<strong>Imperativ mit Sie:</strong> Sie lernen Deutsch. → Lernen Sie Deutsch! (Verb am Anfang, Sie bleibt)",
    "<strong>Merke:</strong> Höflich mit „Sie“, freundlich mit „du“ und „ihr“.",
    "<strong>Wortschatz:</strong> die Gesundheit, die Ernährung, die Bewegung, die Erkältung, das Fieber, die Apotheke, sich ausruhen, vermeiden.",
])

GRAMMAR_HTML = (
    "<h3>Imperativ (Aufforderung)</h3><p>Der Imperativ wird benutzt, um jemanden zu etwas <strong>aufzufordern</strong>, <strong>zu bitten</strong> "
    "oder zu einem <strong>Verhalten</strong> zu bewegen.</p>"
    "<table><thead><tr><th></th><th>1. Imperativ mit du</th><th>2. Imperativ mit ihr</th><th>3. Imperativ mit Sie</th></tr></thead><tbody>"
    "<tr><td>Struktur</td><td>Du lernst Deutsch. → <strong>Lerne Deutsch!</strong></td><td>Ihr lernt Deutsch. → <strong>Lernt Deutsch!</strong></td>"
    "<td>Sie lernen Deutsch. → <strong>Lernen Sie Deutsch!</strong></td></tr>"
    "<tr><td>Regel</td><td>Subjekt „du“ fällt weg · Endung -st fällt weg · Verbstamm + e/Ø</td>"
    "<td>Subjekt „ihr“ fällt weg · Endung -t bleibt · Verbstamm + t</td><td>Verb steht am Anfang · Sie bleibt im Satz · Endung -en bleibt</td></tr>"
    "<tr><td>Beispiele</td><td>Komm hier! · Mach die Hausaufgabe! · Lies das Buch! · Lerne Deutsch!</td>"
    "<td>Kommt hier! · Macht die Hausaufgabe! · Lest das Buch! · Lernt Deutsch!</td>"
    "<td>Kommen Sie bitte hier! · Machen Sie die Hausaufgabe! · Lesen Sie das Buch! · Lernen Sie Deutsch!</td></tr></tbody></table>"
    "<p><strong>Merke:</strong> Der Imperativ ist kurz und direkt. Achte auf die richtige Form! Höflich mit „Sie“, freundlich mit „du“ und „ihr“.</p>"
    "<h4>Beispiel (Unterrichtsblatt)</h4><ul><li>Ich habe Kopfschmerzen. → Nimm eine Tablette! (du)</li>"
    "<li>Wir haben Kopfschmerzen. → Trinkt mehr Wasser! (ihr)</li><li>Ich habe Kopfschmerzen. → Schlafen Sie noch mehr! (Sie)</li></ul>"
)
COMPLAINTS = ["Ich habe Kopfschmerzen.", "Ich fühle mich sehr müde.", "Ich habe Halsschmerzen.", "Ich habe Fieber.", "Ich habe Rückenschmerzen.",
              "Ich bin erkältet.", "Ich habe Husten.", "Ich habe Stress.", "Ich fühle mich schwach.", "Mir ist kalt."]

TEXT_GESUND = (
    "Viele Menschen möchten gesund bleiben. Gesundheit ist sehr wichtig für ein gutes Leben. Wenn wir gesund sind, fühlen wir uns stark und haben "
    "mehr Energie im Alltag. Aber manchmal arbeiten Menschen viel und haben wenig Zeit für ihre Gesundheit. Trotzdem kann man jeden Tag kleine Dinge "
    "machen, um gesund zu bleiben.\n\nEin wichtiger Punkt ist gesunde Ernährung. Es ist gut, jeden Tag Obst und Gemüse zu essen. Zum Beispiel Äpfel, "
    "Bananen, Tomaten oder Karotten. Diese Lebensmittel haben viele Vitamine und sind gut für den Körper. Man sollte auch genug Wasser trinken, "
    "ungefähr zwei Liter am Tag. Zu viel Fast Food, Zucker oder Cola ist nicht gut für die Gesundheit.\n\nAuch Bewegung ist sehr wichtig. Man muss "
    "nicht jeden Tag intensiven Sport machen. Ein Spaziergang, Radfahren oder ein bisschen Gymnastik zu Hause ist schon sehr gut. Bewegung hilft dem "
    "Körper und macht auch gute Laune.\n\nAußerdem braucht der Körper genug Schlaf. Erwachsene schlafen am besten sieben oder acht Stunden pro Nacht. "
    "Wenn man gut schläft, ist man am nächsten Tag konzentriert und aktiv. Kleine gesunde Gewohnheiten können also unser Leben deutlich verbessern.")
TEXT_KRANK = (
    "Manchmal werden Menschen krank. Das ist ganz normal. Viele Menschen bekommen zum Beispiel eine Erkältung, Husten, Kopfschmerzen oder Fieber. "
    "Wenn man krank ist, fühlt man sich oft schwach und müde. In dieser Situation ist es wichtig, gut auf den eigenen Körper zu achten.\n\nZuerst "
    "sollte man sich ausruhen. Der Körper braucht Zeit, um wieder gesund zu werden. Deshalb ist es besser, zu Hause zu bleiben und viel zu schlafen. "
    "Ruhe hilft dem Körper, schneller gesund zu werden.\n\nAuch viel trinken ist sehr wichtig. Wasser, Tee oder warme Suppe sind gut für den Körper. "
    "Besonders Tee mit Honig und Zitrone hilft oft bei Halsschmerzen und Husten. Viele Menschen trinken auch Ingwertee, weil er den Körper wärmt.\n\n"
    "Manchmal braucht man auch Medikamente. In der Apotheke kann man Tabletten gegen Schmerzen oder Fieber kaufen. Man sollte aber immer die "
    "Informationen lesen und die richtige Menge nehmen.\n\nWenn man nach einigen Tagen nicht besser wird, sollte man zum Arzt gehen. Der Arzt "
    "untersucht den Patienten und gibt eine passende Behandlung. Mit Ruhe, gesunder Nahrung und genug Flüssigkeit wird man meistens bald wieder gesund.")
_K = "Javob: Vizu-Antworten A2 (3. Unterricht, Lesen)."
LESEN = [
    mc("Warum ist Gesundheit wichtig?", ["Weil man dann mehr Energie hat", "Weil man mehr Geld verdient", "Weil man mehr arbeitet"], "A", _K, passage=1),
    mc("Was möchten viele Menschen?", ["Viel reisen", "Gesund bleiben", "Mehr schlafen"], "B", _K, passage=1),
    mc("Was soll man jeden Tag essen?", ["Fast Food", "Obst und Gemüse", "Nur Fleisch"], "B", _K, passage=1),
    mc("Wie viel Wasser soll man ungefähr am Tag trinken?", ["Ein Glas", "Zwei Liter", "Fünf Liter"], "B", _K, passage=1),
    mc("Welche Bewegung wird im Text genannt?", ["Spaziergang oder Radfahren", "Tanzen im Club", "Basketball spielen"], "A", _K, passage=1),
    mc("Wie viele Stunden sollen Erwachsene ungefähr schlafen?", ["3–4 Stunden", "5–6 Stunden", "7–8 Stunden"], "C", _K, passage=1),
    mc("Wie fühlen sich viele Menschen, wenn sie krank sind?", ["Stark und aktiv", "Schwach und müde", "Sehr glücklich"], "B", _K, passage=2),
    mc("Was soll man zuerst machen, wenn man krank ist?", ["Viel arbeiten", "Sich ausruhen", "Sport machen"], "B", _K, passage=2),
    mc("Was soll man trinken?", ["Wasser oder Tee", "Cola", "Nur Kaffee"], "A", _K, passage=2),
    mc("Was hilft oft bei Halsschmerzen?", ["Kaltes Wasser", "Tee mit Honig und Zitrone", "Eis"], "B", _K, passage=2),
    mc("Wo kann man Medikamente kaufen?", ["In der Apotheke", "In der Schule", "In der Bank"], "A", _K, passage=2),
    mc("Wann soll man zum Arzt gehen?", ["Wenn man gesund ist", "Wenn es nach einigen Tagen nicht besser wird", "Wenn man Hunger hat"], "B", _K, passage=2),
]
HOEREN = [
    tf("Der Arzt stellt sich am Anfang des Vortrags vor.", True),
    tf("Wenn man krank ist, soll man viel arbeiten.", False),
    tf("Der Arzt sagt, dass Ruhe für den Körper wichtig ist.", True),
    tf("Man soll Wasser oder warmen Tee trinken.", True),
    tf("Der Arzt empfiehlt ungesunde und schwere Nahrung.", False),
    tf("Frische Luft und ein Spaziergang können helfen.", True),
    tf("Man soll Stress vermeiden und sich entspannen.", True),
    tf("Wenn man nach einigen Tagen nicht besser wird, soll man zum Arzt gehen.", True),
]

WORDS = numbered_words([
    ("die Gesundheit", "sog‘liq"), ("gesund", "sog‘lom"), ("krank", "kasal"), ("der Körper", "tana"), ("die Energie", "energiya"),
    ("die Gewohnheit", "odat"), ("die Ernährung", "ovqatlanish"), ("das Lebensmittel", "oziq-ovqat"), ("das Obst", "meva"), ("das Gemüse", "sabzavot"),
    ("die Vitamine", "vitaminlar"), ("der Zucker", "shakar"), ("das Fast Food", "tez tayyor ovqat"), ("das Wasser", "suv"), ("die Bewegung", "harakat"),
    ("der Spaziergang", "sayr"), ("das Radfahren", "velosiped haydash"), ("die Gymnastik", "gimnastika"), ("der Schlaf", "uyqu"), ("die Ruhe", "dam olish"),
    ("die Erkältung", "shamollash"), ("der Husten", "yo‘tal"), ("das Fieber", "isitma"), ("die Kopfschmerzen", "bosh og‘rig‘i"),
    ("die Halsschmerzen", "tomoq og‘rig‘i"), ("die Rückenschmerzen", "bel og‘rig‘i"), ("die Tablette", "tabletka"), ("das Medikament", "dori"),
    ("die Apotheke", "dorixona"), ("der Arzt", "shifokor"), ("der Patient", "bemor"), ("die Untersuchung", "tekshiruv"), ("die Behandlung", "davolash"),
    ("die Krankheit", "kasallik"), ("die Flüssigkeit", "suyuqlik"), ("der Ingwer", "zanjabil"), ("der Honig", "asal"), ("die Zitrone", "limon"),
    ("die Suppe", "sho‘rva"), ("der Tee", "choy"), ("der Stress", "stress"), ("sich entspannen", "dam olmoq"), ("sich ausruhen", "hordiq chiqarmoq"),
    ("vermeiden", "oldini olmoq"), ("verbessern", "yaxshilamoq"), ("achten auf", "e’tibor bermoq"), ("konzentriert", "diqqatli"), ("aktiv", "faol"),
    ("stark", "kuchli"), ("gesund bleiben", "sog‘lom qolmoq"), ("genug", "yetarli"), ("täglich", "har kuni"), ("wichtig", "muhim"),
    ("helfen", "yordam bermoq"), ("trinken", "ichmoq"), ("essen", "yemoq"), ("schlafen", "uxlamoq"), ("laufen", "yugurmoq"),
    ("trainieren", "mashq qilmoq"), ("fit bleiben", "formani saqlamoq")], "Gesundheit und Fitness")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 3. Unterricht", source="vizu", page=31, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Was machen Sie für Ihre Gesundheit?", page=32,
             prompt="Was machen Sie für Ihre Gesundheit? Machen Sie eine kleine Präsentation.",
             questions=["Wie oft treiben Sie Sport?", "Wie ernähren Sie sich?", "Wie wichtig ist Ihnen Schlaf und Erholung?"],
             min_duration=20, max_duration=120,
             metadata={"book_sample": "Ich treibe Sport drei Mal pro Woche. Ich gehe ins Fitnessstudio und gehe auch gern spazieren. Ich ernähre mich "
                                      "gesund. Ich esse viel Obst, Gemüse und trinke viel Wasser. Schlaf und Erholung sind für mich sehr wichtig. Ich "
                                      "schlafe mindestens 7-8 Stunden pro Nacht und mache am Wochenende Pausen."}),
        base(L, "grammatik", 1, "Grammatik: Imperativ (Aufforderung)", page=33, rules=[{"title": "Imperativ", "html": GRAMMAR_HTML}]),
        base(L, "schreiben", 2, "Grammatik-Aufgabe: Imperativ – Übung (du / ihr / Sie)", page=34, task_type="other",
             prompt="Bilde den Imperativ im Singular (du), im Plural (ihr) und in der höflichen Form (Sie). Gib zu jedem Satz einen Rat in allen drei "
                    "Formen. Tipp: Achte auf die richtige Form!\n\nBeispiel: Ich habe Kopfschmerzen. → Nimm eine Tablette! · Trinkt mehr Wasser! · "
                    "Schlafen Sie noch mehr!\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(COMPLAINTS, start=1)),
             min_words=60, max_words=300, time_limit=25,
             metadata={"note": "Ochiq javobli mashq — Vizu-Antworten: „wird von dem Lehrer korrigiert“."},
             support_phrases=["Trink mehr Wasser!", "Ruh dich aus!", "Geht zum Arzt!", "Nehmen Sie eine Tablette!"]),
        base(L, "lesen", 1, "Lesen: Gesund bleiben im Alltag / Was kann man tun, wenn man krank ist?", page="35-36",
             instruction="Lesen Sie die Texte. Wählen Sie die richtige Antwort!",
             passages=[{"title": "Gesund bleiben im Alltag", "text": TEXT_GESUND}, {"title": "Was kann man tun, wenn man krank ist?", "text": TEXT_KRANK}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Die Empfehlungen eines Arztes", page=37, audio_file="A2.  3.Unterricht Hören.mp3",
             instruction="Sie hören die Empfehlungen eines Arztes. Finden Sie bitte, welche Aussagen richtig oder falsch sind.",
             questions=HOEREN, max_score=len(HOEREN)),
        base(L, "schreiben", 1, "Schreiben: Was tun Sie für Ihre Gesundheit?", page=38, task_type="description",
             prompt="Was tun Sie für Ihre Gesundheit? Schreiben Sie einen kurzen Text über das Thema. Schreiben Sie mindestens 80 Wörter.\n\nPunkte:\n"
                    "• Was machen Sie, um gesund zu bleiben?\n• Treiben Sie Sport oder bewegen Sie sich regelmäßig?\n"
                    "• Was essen oder trinken Sie für Ihre Gesundheit?\n• Wie wichtig ist Gesundheit für Sie?",
             min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: E-Mail an Alex — Besuch im Krankenhaus", page=38, task_type="email",
             prompt="Situation: Ihre Freundin ist im Krankenhaus. Sie möchten sie besuchen und schreiben Ihrem Freund Alex eine E-Mail.\n\nPunkte:\n"
                    "• Fragen Sie Alex, wie es Ihrer Freundin geht.\n• Fragen Sie, wann Sie sie besuchen können.\n"
                    "• Machen Sie einen Vorschlag für einen Besuchstermin.\n• Schreiben Sie, was Sie für Ihre Freundin mitbringen können.",
             audience="Ihr Freund Alex (informell)", min_words=40, max_words=100, time_limit=20,
             support_phrases=["Lieber Alex,", "Wie geht es …?", "Wann kann ich sie besuchen?", "Vielleicht am … um …?", "Ich kann … mitbringen.",
                              "Viele Grüße"]),
        base(L, "sprechen", 1, "Sprechen: Was tun Sie für Ihre Gesundheit?", page=39, topic="Gesundheit",
             prompt="Sprechen Sie über das Thema.",
             questions=["Treiben Sie Sport?", "Essen Sie gesund?", "Schlafen Sie genug?", "Was machen Sie für Ihre Körperpflege?"],
             response_type="monolog", min_duration=45, max_duration=150,
             speech_goal="Über die eigene Gesundheit sprechen: Sport, Ernährung, Schlaf, Körperpflege.",
             keywords=["Sport", "gesund", "schlafen", "Obst", "Gemüse", "Wasser"]),
        base(L, "wortschatz", 1, "Wortschatz: Gesundheit und Fitness", page=40, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen: A2 3. Unterricht", source="vizu", exercises=[s for s in (
            exercise("Imperativ: richtige Form", [
                mc("Du lernst Deutsch. → Imperativ (du)?", ["Lerne Deutsch!", "Lernst Deutsch!", "Lernen Deutsch!"], "A", "Subjekt und -st fallen weg."),
                mc("Ihr macht die Hausaufgabe. → Imperativ (ihr)?", ["Macht die Hausaufgabe!", "Mach die Hausaufgabe!", "Machen ihr die Hausaufgabe!"], "A",
                   "Subjekt fällt weg, -t bleibt."),
                mc("Sie lesen das Buch. → Imperativ (Sie)?", ["Lesen Sie das Buch!", "Lies das Buch!", "Sie lesen das Buch!"], "A",
                   "Verb am Anfang, Sie bleibt."),
                mc("Du liest das Buch. → Imperativ (du)?", ["Lies das Buch!", "Lest das Buch!", "Liest das Buch!"], "A", "Kitobdagi misol: Lies das Buch!"),
                mc("Ihr kommt hier. → Imperativ (ihr)?", ["Kommt hier!", "Komm hier!", "Kommen hier!"], "A", "Kitobdagi misol: Kommt hier!"),
                mc("Welche Form ist höflich?", ["Kommen Sie bitte hier!", "Komm hier!", "Kommt hier!"], "A", "Höflich mit „Sie“."),
            ], "Imperativning to'g'ri shaklini tanlang (kitobdagi qoida va misollar).", source="vizu"),
            reverse_vocab_set(WORDS),
        ) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 3. Unterricht", source="vizu",
             instruction="Imperativ va salomatlik so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Du trinkst zu wenig Wasser. → ___ mehr Wasser!", ["Trink", "Trinkst", "Trinken"], "A"),
                 mc("Ihr schlaft zu wenig. → ___ mehr!", ["Schlaft", "Schlaf", "Schlafen"], "A"),
                 mc("Sie arbeiten zu viel. → ___ weniger!", ["Arbeiten Sie", "Arbeite", "Arbeitet"], "A"),
                 mc("Was hilft oft bei Halsschmerzen?", ["Tee mit Honig und Zitrone", "Kaltes Wasser", "Eis"], "A", "Lesen, Text 2."),
                 mc("Wie viele Stunden sollen Erwachsene ungefähr schlafen?", ["7–8 Stunden", "3–4 Stunden", "10–12 Stunden"], "A", "Lesen, Text 1."),
                 tf("Wenn man nach einigen Tagen nicht besser wird, soll man zum Arzt gehen.", True, "Lesen, Text 2."),
                 mc("„die Apotheke“ — o'zbekchasi?", ["dorixona", "shifoxona", "do'kon"], "A"),
                 mc("„sich ausruhen“ — o'zbekchasi?", ["hordiq chiqarmoq", "yugurmoq", "mashq qilmoq"], "A"),
                 mc("„die Erkältung“ — o'zbekchasi?", ["shamollash", "isitma", "yo'tal"], "A"),
                 mc("„vermeiden“ — o'zbekchasi?", ["oldini olmoq", "yaxshilamoq", "e'tibor bermoq"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 3. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
