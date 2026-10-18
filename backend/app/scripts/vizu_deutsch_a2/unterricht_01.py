"""A2 1. Unterricht — Beruf, Karriere und Ziele — Grammatik: Präsens, Präteritum und Perfekt (book pp. 3-18).

Book: Frage p.4, Grammatik tables pp.5-7, Aufgabe 1 / 2 pp.8-9, Lesen (three
interviews, six Richtig/Falsch each) pp.10-12, Hören p.13 + transcript p.14,
Musik Zeit p.15, Schreiben p.16, Sprechen p.17, Wortschatz (60 words) p.18.

Answer keys: Hören and the lesson handout ("A2. 1.Unterricht.pdf": 20
sentences, 18 Richtig/Falsch statements) from "Vizu-Antworten A2". The book's
own Aufgabe 1 / 2 print the verb forms next to every sentence; the gaps take
exactly those forms. The book's Lesen statements are decided by the quoted
sentence of the interview (explanation)."""

from . import (
    article_set, base, exercise, forward_vocab_set, gap, html_table, intro_html, mc, numbered_words, reverse_vocab_set, summary_html, tf,
    vocab_match_sets,
)

L = 1
LESSON_TITLE = "Beruf, Karriere und Ziele"
LESSON_DESCRIPTION = "Thema: Beruf, Karriere und Ziele · Grammatik: Präsens, Präteritum und Perfekt"
AUDIO = {"vizu-a2-l01-hoeren-01": "A2 1.Unterricht Hören.m4a"}

EINFUEHRUNG_HTML = intro_html(
    1, "Beruf, Karriere und Ziele", "Präsens, Präteritum und Perfekt (Satzbau)",
    ["uch zamonda gap tuzish: Aussagesatz, Fragesatz ohne / mit Fragewort, Modalverb bilan;",
     "Präteritum va Perfekt shakllarini (lernte / habe gelernt, fuhr / ist gefahren) qo'llash;",
     "kasblar, ta'lim va maqsadlar haqidagi so'zlarni o'rganish."],
    ["„Ich bin Koch. Ich arbeite in einem Restaurant.“ — kasbingiz haqida gapirasiz;",
     "„Als Kind habe ich … Später habe ich …“ — o'tmishingiz haqida gapirasiz;",
     "„Ich werde … / Ich möchte … werden, weil …“ — kelajak rejalaringizni aytasiz;",
     "uch oshpaz bilan intervyuni o'qib, Johann, Julia va Mikey haqidagi audioni tushunasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(1, [
    "<strong>Präsens:</strong> Ich lerne Deutsch. · Ich muss Deutsch lernen. · Lernst du Deutsch? · Warum musst du Deutsch lernen?",
    "<strong>Präteritum:</strong> Ich lernte Deutsch. · Ich musste Deutsch lernen. · Lerntest du Deutsch?",
    "<strong>Perfekt:</strong> Ich habe Deutsch gelernt. · Ich habe Deutsch lernen müssen. · Hast du Deutsch gelernt?",
    "<strong>Beruf:</strong> Ich bin Koch. · Ich möchte Arzt werden, weil … · Als Kind habe ich … · In Zukunft werde ich …",
    "<strong>Wortschatz:</strong> der Architekt, die Ärztin, die Berufswahl, die Erfahrung, erfolgreich, abschließen, bewundern, verdienen.",
])

# ---------- Grammatik (pp.5-7) ----------
_HEAD = ["Zamon", "Strukturasi", "Gap turi", "Misol (Deutsch)", "Tarjimasi (O‘zbekcha)"]
_PRAESENS = [
    ["Präsens", "Subj + Verb + Obj", "Aussagesatz", "Ich <strong>lerne</strong> Deutsch.", "Men nemis tilini o‘rganyapman."],
    ["Präsens", "Subj + Modalverb + Obj + Verb", "Aussagesatz mit Modalverb", "Ich <strong>muss</strong> Deutsch lernen.", "Men nemis tilini o‘rganishim kerak."],
    ["Präsens", "Verb + Subj + Obj?", "Fragesatz ohne Fragewort", "<strong>Lernst</strong> du Deutsch?", "Sen nemis tilini o‘rganyapsanmi?"],
    ["Präsens", "Fragewort + Verb + Subj + Obj?", "Fragesatz mit Fragewort", "Warum <strong>lernst</strong> du Deutsch?", "Nega sen nemis tilini o‘rganyapsan?"],
    ["Präsens", "Modalverb + Subj + Obj + Verb?", "Fragesatz mit Modalverb (ohne FW)", "<strong>Musst</strong> du Deutsch lernen?", "Sen nemis tilini o‘rganishing kerakmi?"],
    ["Präsens", "Fragewort + Modalverb + Subj + Obj + Verb?", "Fragesatz mit Modalverb (mit FW)", "Warum <strong>musst</strong> du Deutsch lernen?", "Nega sen nemis tilini o‘rganishing kerak?"],
]
_PRAETERITUM = [
    ["Präteritum", "Subj + Verb + Obj", "Aussagesatz", "Ich <strong>lernte</strong> Deutsch.", "Men nemis tilini o‘rgandim."],
    ["Präteritum", "Subj + Modalverb + Obj + Verb", "Aussagesatz mit Modalverb", "Ich <strong>musste</strong> Deutsch lernen.", "Men nemis tilini o‘rganishim kerak edi."],
    ["Präteritum", "Verb + Subj + Obj?", "Fragesatz ohne Fragewort", "<strong>Lerntest</strong> du Deutsch?", "Sen nemis tilini o‘rgandingmi?"],
    ["Präteritum", "Fragewort + Verb + Subj + Obj?", "Fragesatz mit Fragewort", "Warum <strong>lerntest</strong> du Deutsch?", "Nega sen nemis tilini o‘rganding?"],
    ["Präteritum", "Modalverb + Subj + Obj + Verb?", "Fragesatz mit Modalverb (ohne FW)", "<strong>Musstest</strong> du Deutsch lernen?", "Sen nemis tilini o‘rganishing kerak edimi?"],
    ["Präteritum", "Fragewort + Modalverb + Subj + Obj + Verb?", "Fragesatz mit Modalverb (mit FW)", "Warum <strong>musstest</strong> du Deutsch lernen?", "Nega sen nemis tilini o‘rganishing kerak edi?"],
]
_PERFEKT = [
    ["Perfekt", "Subj + haben/sein + Obj + Partizip II", "Aussagesatz", "Ich <strong>habe</strong> Deutsch <strong>gelernt</strong>.", "Men nemis tilini o‘rgandim."],
    ["Perfekt", "Subj + haben + Obj + Verb + Modalverb (Inf.)", "Aussagesatz mit Modalverb", "Ich <strong>habe</strong> Deutsch lernen <strong>müssen</strong>.", "Men nemis tilini o‘rganishimga to‘g‘ri keldi."],
    ["Perfekt", "Haben/sein + Subj + Obj + Partizip II?", "Fragesatz ohne Fragewort", "<strong>Hast</strong> du Deutsch gelernt?", "Sen nemis tilini o‘rgandingmi?"],
    ["Perfekt", "Fragewort + haben/sein + Subj + Obj + Partizip II?", "Fragesatz mit Fragewort", "Warum <strong>hast</strong> du Deutsch gelernt?", "Nega sen nemis tilini o‘rganding?"],
    ["Perfekt", "Haben + Subj + Obj + Verb + Modalverb (Inf.)?", "Fragesatz mit Modalverb (ohne FW)", "<strong>Hast</strong> du Deutsch lernen <strong>müssen</strong>?", "Sen nemis tilini o‘rganishga majbur bo‘ldingmi?"],
    ["Perfekt", "Fragewort + haben + Subj + Obj + Verb + Modalverb (Inf.)?", "Fragesatz mit Modalverb (mit FW)", "Warum <strong>hast</strong> du Deutsch lernen <strong>müssen</strong>?", "Nega sen nemis tilini o‘rganishga majbur bo‘lding?"],
]
RULES = [
    {"title": "1. Präsens", "html": html_table(_HEAD, _PRAESENS)
     + "<p><strong>Präsens – hozirgi zamon.</strong> Bu zamonda hozir sodir bo‘layotgan ishlar, odatlar, harakatlar va umumiy haqiqatlar ifodalanadi.</p>"},
    {"title": "2. Präteritum", "html": html_table(_HEAD, _PRAETERITUM)
     + "<p><strong>Präteritum – o‘tgan zamon.</strong> O‘tgan dagi voqealar, holatlar va harakatlar uchun ishlatiladi.</p>"},
    {"title": "3. Perfekt", "html": html_table(_HEAD, _PERFEKT)
     + "<p><strong>Perfekt</strong> – o‘tgan zamonning hozirgi natijasi bilan bog‘liq shakli. O‘tgandagi voqealar hozirgi holatimizga ta’sir qiladi.</p>"},
]


def _pp(sentence: str, praet: str, perf: str, keys: tuple, explanation: str) -> dict:
    """One book sentence: Präteritum line + Perfekt line as gaps; keys = the
    forms printed in the book next to the sentence."""
    text = f"{sentence}\nPrät.: {praet}\nPerf.: {perf}"
    gaps = {str(i): [k] for i, k in enumerate(keys, start=1)}
    return gap("Schreiben Sie den Satz im Präteritum und Perfekt.", text, gaps, points=len(keys), explanation=explanation)


AUFGABE_1 = [  # p.8 — forms printed in the book
    _pp("Ich lerne Deutsch.", "Ich [[1]] Deutsch.", "Ich [[2]] Deutsch [[3]].", ("lernte", "habe", "gelernt"), "Prät.: Ich lernte Deutsch. · Perf.: Ich habe Deutsch gelernt."),
    _pp("Wir besuchen unsere Großeltern.", "Wir [[1]] unsere Großeltern.", "Wir [[2]] unsere Großeltern [[3]].", ("besuchten", "haben", "besucht"),
        "Prät.: Wir besuchten unsere Großeltern. · Perf.: Wir haben unsere Großeltern besucht."),
    _pp("Er kauft ein neues Auto.", "Er [[1]] ein neues Auto.", "Er [[2]] ein neues Auto [[3]].", ("kaufte", "hat", "gekauft"),
        "Prät.: Er kaufte ein neues Auto. · Perf.: Er hat ein neues Auto gekauft."),
    _pp("Sie fährt nach Berlin.", "Sie [[1]] nach Berlin.", "Sie [[2]] nach Berlin [[3]].", ("fuhr", "ist", "gefahren"),
        "Prät.: Sie fuhr nach Berlin. · Perf.: Sie ist nach Berlin gefahren (fahren → sein)."),
    _pp("Ich lese ein interessantes Buch.", "Ich [[1]] ein interessantes Buch.", "Ich [[2]] ein interessantes Buch [[3]].", ("las", "habe", "gelesen"),
        "Prät.: Ich las ein interessantes Buch. · Perf.: Ich habe ein interessantes Buch gelesen."),
    _pp("Er schreibt eine E-Mail.", "Er [[1]] eine E-Mail.", "Er [[2]] eine E-Mail [[3]].", ("schrieb", "hat", "geschrieben"),
        "Prät.: Er schrieb eine E-Mail. · Perf.: Er hat eine E-Mail geschrieben."),
]
AUFGABE_2 = [  # p.9 — forms printed in the book
    _pp("Macht ihr heute Sport?", "[[1]] ihr heute Sport?", "[[2]] ihr heute Sport [[3]]?", ("Machtet", "Habt", "gemacht"),
        "Kitobda: (machtet) · (gemacht – haben) → Machtet ihr heute Sport? · Habt ihr heute Sport gemacht?"),
    _pp("Wo wohnst du?", "Wo [[1]] du?", "Wo [[2]] du [[3]]?", ("wohntest", "hast", "gewohnt"),
        "Kitobda: (wohnte) · (gewohnt – haben); du → wohntest: Wo wohntest du? · Wo hast du gewohnt?"),
    _pp("Gehst du oft spazieren?", "[[1]] du oft spazieren?", "[[2]] du oft spazieren [[3]]?", ("Gingst", "Bist", "gegangen"),
        "Kitobda: (gingst) · (gegangen – sein) → Gingst du oft spazieren? · Bist du oft spazieren gegangen?"),
    _pp("Sie arbeitet im Büro.", "Sie [[1]] im Büro.", "Sie [[2]] im Büro [[3]].", ("arbeitete", "hat", "gearbeitet"),
        "Kitobda: (arbeitete) · (gearbeitet – haben) → Sie arbeitete im Büro. · Sie hat im Büro gearbeitet."),
    _pp("Wir essen zusammen zu Abend.", "Wir [[1]] zusammen zu Abend.", "Wir [[2]] zusammen zu Abend [[3]].", ("aßen", "haben", "gegessen"),
        "Kitobda: (aßen) · (gegessen – haben) → Wir aßen zusammen zu Abend. · Wir haben zusammen zu Abend gegessen."),
    _pp("Er kommt um acht Uhr.", "Er [[1]] um acht Uhr.", "Er [[2]] um acht Uhr [[3]].", ("kam", "ist", "gekommen"),
        "Kitobda: (kam) · (gekommen – sein) → Er kam um acht Uhr. · Er ist um acht Uhr gekommen."),
]


def _hs(n: int, sentence: str, praet: str, perf: str | None, keys: tuple, answer: str) -> dict:
    """Lesson handout sentence n (answer: 'Vizu-Antworten A2', 1. Unterricht)."""
    text = f"{n}. {sentence}\nPrät.: {praet}" + (f"\nPerf.: {perf}" if perf else "")
    gaps = {str(i): [k] for i, k in enumerate(keys, start=1)}
    return gap("Schreiben Sie den Satz im Präteritum" + (" und Perfekt." if perf else "."), text, gaps, points=len(keys), explanation=answer)


HANDOUT_20 = [
    _hs(1, "Ich lerne Deutsch.", "Ich [[1]] Deutsch.", "Ich [[2]] Deutsch [[3]].", ("lernte", "habe", "gelernt"), "Ich lernte Deutsch. / Ich habe Deutsch gelernt."),
    _hs(2, "Musst du heute arbeiten?", "[[1]] du heute arbeiten?", None, ("Musstest",), "Musstest du heute arbeiten?"),
    _hs(3, "Wir besuchen unsere Großeltern.", "Wir [[1]] unsere Großeltern.", "Wir [[2]] unsere Großeltern [[3]].", ("besuchten", "haben", "besucht"),
        "Wir besuchten unsere Großeltern. / Wir haben unsere Großeltern besucht."),
    _hs(4, "Warum kannst du nicht kommen?", "Warum [[1]] du nicht kommen?", None, ("konntest",), "Warum konntest du nicht kommen?"),
    _hs(5, "Er kauft ein neues Auto.", "Er [[1]] ein neues Auto.", "Er [[2]] ein neues Auto [[3]].", ("kaufte", "hat", "gekauft"),
        "Er kaufte ein neues Auto. / Er hat ein neues Auto gekauft."),
    _hs(6, "Darf ich hier sitzen?", "[[1]] ich hier sitzen?", None, ("Durfte",), "Durfte ich hier sitzen?"),
    _hs(7, "Sie fährt nach Berlin.", "Sie [[1]] nach Berlin.", "Sie [[2]] nach Berlin [[3]].", ("fuhr", "ist", "gefahren"), "Sie fuhr nach Berlin. / Sie ist nach Berlin gefahren."),
    _hs(8, "Soll ich dir helfen?", "[[1]] ich dir helfen?", None, ("Sollte",), "Sollte ich dir helfen?"),
    _hs(9, "Wir machen die Hausaufgaben.", "Wir [[1]] die Hausaufgaben.", "Wir [[2]] die Hausaufgaben [[3]].", ("machten", "haben", "gemacht"),
        "Wir machten die Hausaufgaben. / Wir haben die Hausaufgaben gemacht."),
    _hs(10, "Warum willst du Deutsch lernen?", "Warum [[1]] du Deutsch lernen?", None, ("wolltest",), "Warum wolltest du Deutsch lernen?"),
    _hs(11, "Ich lese ein interessantes Buch.", "Ich [[1]] ein interessantes Buch.", "Ich [[2]] ein interessantes Buch [[3]].", ("las", "habe", "gelesen"),
        "Ich las ein interessantes Buch. / Ich habe ein interessantes Buch gelesen."),
    _hs(12, "Er sieht einen Film.", "Er [[1]] einen Film.", "Er [[2]] einen Film [[3]].", ("sah", "hat", "gesehen"), "Er sah einen Film. / Er hat einen Film gesehen."),
    _hs(13, "Wir gehen heute ins Kino.", "Wir [[1]] heute ins Kino.", "Wir [[2]] heute ins Kino [[3]].", ("gingen", "sind", "gegangen"),
        "Wir gingen heute ins Kino. / Wir sind heute ins Kino gegangen."),
    _hs(14, "Kannst du mir helfen?", "[[1]] du mir helfen?", None, ("Konntest",), "Konntest du mir helfen?"),
    _hs(15, "Sie trinkt Kaffee.", "Sie [[1]] Kaffee.", "Sie [[2]] Kaffee [[3]].", ("trank", "hat", "getrunken"), "Sie trank Kaffee. / Sie hat Kaffee getrunken."),
    _hs(16, "Ich nehme den Bus.", "Ich [[1]] den Bus.", "Ich [[2]] den Bus [[3]].", ("nahm", "habe", "genommen"), "Ich nahm den Bus. / Ich habe den Bus genommen."),
    _hs(17, "Warum kommst du so spät?", "Warum [[1]] du so spät?", "Warum [[2]] du so spät [[3]]?", ("kamst", "bist", "gekommen"),
        "Warum kamst du so spät? / Warum bist du so spät gekommen?"),
    _hs(18, "Wir bleiben zu Hause.", "Wir [[1]] zu Hause.", "Wir [[2]] zu Hause [[3]].", ("blieben", "sind", "geblieben"), "Wir blieben zu Hause. / Wir sind zu Hause geblieben."),
    _hs(19, "Er schreibt eine E-Mail.", "Er [[1]] eine E-Mail.", "Er [[2]] eine E-Mail [[3]].", ("schrieb", "hat", "geschrieben"),
        "Er schrieb eine E-Mail. / Er hat eine E-Mail geschrieben."),
    _hs(20, "Was bringst du mit?", "Was [[1]] du mit?", "Was [[2]] du [[3]]?", ("brachtest", "hast", "mitgebracht"), "Was brachtest du mit? / Was hast du mitgebracht?"),
]

# ---------- Lesen (pp.10-12) ----------
TEXT_FREDERICH = (
    "Interviewerin: Guten Tag, Herr Schuman. Was sind Sie von Beruf?\nFrederich Schuman: Guten Tag. Ich bin Koch. Ich arbeite in einem "
    "italienischen Restaurant und koche jeden Tag frische Gerichte.\n\nInterviewerin: Was machen Sie gerade in der Küche?\nFrederich Schuman: Im "
    "Moment backe ich eine Pizza. Ich bereite den Teig vor, schneide frisches Gemüse und lege Käse darauf. Die Pizza kommt gleich in den Ofen.\n\n"
    "Interviewerin: Haben Sie ein Geheimnis beim Kochen?\nFrederich Schuman: Ja, natürlich. Jede gute Pizza hat ein kleines Geheimnis. Ich benutze "
    "besondere Gewürze und sehr frische Zutaten. Das macht den Geschmack besser.\n\nInterviewerin: Warum mögen Sie Ihren Beruf?\nFrederich Schuman: "
    "Ich liebe meinen Beruf, weil ich kreativ sein kann. Ich koche gern für Menschen und sehe, wie sie mein Essen genießen. Das macht mich "
    "glücklich.\n\nInterviewerin: Ist Kochen schwer oder leicht?\nFrederich Schuman: Kochen ist manchmal schwer, weil die Küche stressig ist. Aber "
    "ich lerne jeden Tag etwas Neues und werde immer besser.")
TEXT_MARKUS = (
    "Interviewerin: Markus, was machst du im Moment?\nMarkus: Ich gehe noch zur Schule, aber ich helfe meinem Vater oft im Restaurant. In der Küche "
    "schneide ich Gemüse und bereite Zutaten vor.\n\nInterviewerin: Warum willst du Koch werden?\nMarkus: Kochen macht mir Spaß, und ich finde den "
    "Beruf interessant. Ich sehe jeden Tag, wie mein Vater arbeitet, und ich lerne viel von ihm.\n\nInterviewerin: Was wirst du nach der Schule "
    "machen?\nMarkus: Ich werde eine Kochschule besuchen und professionell kochen lernen. Danach werde ich im Restaurant meines Vaters arbeiten.\n\n"
    "Interviewerin: Welche Ziele hast du für die Zukunft?\nMarkus: Ich werde neue Gerichte entwickeln und viel Erfahrung sammeln. Vielleicht werde "
    "ich später mein eigenes Restaurant haben.\n\nInterviewerin: Glaubst du, dass du ein guter Koch wirst?\nMarkus: Ja, ich bin fleißig und "
    "motiviert. Ich werde viel üben und jeden Tag besser werden.")
TEXT_MICHAEL = (
    "Interviewerin: Herr Schuman, wo haben Sie früher gearbeitet?\nMichael: Ich arbeitete viele Jahre auf einem Kreuzfahrtschiff als Koch. Dort "
    "kochte ich für Hunderte von Gästen aus verschiedenen Ländern.\n\nInterviewerin: Wie war diese Arbeit für Sie?\nMichael: Die Arbeit war "
    "anstrengend, aber sehr interessant. Ich habe viele Länder gesehen und neue Küchen kennengelernt.\n\nInterviewerin: Haben Sie besondere "
    "Erinnerungen aus dieser Zeit?\nMichael: Ja, einmal haben wir ein großes Fest organisiert, und ich habe ein besonderes Menü vorbereitet. Die "
    "Gäste waren sehr zufrieden, und ich habe viel Lob bekommen.\n\nInterviewerin: Was haben Sie nach dieser Zeit gemacht?\nMichael: Später habe "
    "ich an Land gearbeitet und junge Köche ausgebildet. Ich habe mein Wissen weitergegeben und viele Schüler unterstützt.\n\nInterviewerin: "
    "Vermissen Sie Ihren Beruf heute?\nMichael: Ja, manchmal vermisse ich die Küche und die Atmosphäre. Aber ich habe meinen Beruf lange ausgeübt "
    "und bin zufrieden mit meinem Leben.")
PASSAGES = [
    {"title": "Mein Beruf — Mein Leben: Interview mit dem Koch Frederich Schuman (Präsens)", "text": TEXT_FREDERICH},
    {"title": "Ich will auch Koch werden: Interview mit Markus Schuman (Präsens + Futur I)", "text": TEXT_MARKUS},
    {"title": "Ich hatte auch meinen Beruf geliebt: Interview mit Michael Schuman (Präteritum + Perfekt)", "text": TEXT_MICHAEL},
]
LESEN_BOOK = [  # pp.10-12, Aufgabe 1-3
    tf("Frederich Schuman arbeitet in einem deutschen Restaurant.", False, "„Ich arbeite in einem italienischen Restaurant …“", passage=1),
    tf("Er bereitet gerade eine Pizza zu.", True, "„Im Moment backe ich eine Pizza. Ich bereite den Teig vor …“", passage=1),
    tf("Er benutzt keine Gewürze beim Kochen.", False, "„Ich benutze besondere Gewürze und sehr frische Zutaten.“", passage=1),
    tf("Er liebt seinen Beruf, weil er kreativ sein kann.", True, "„Ich liebe meinen Beruf, weil ich kreativ sein kann.“", passage=1),
    tf("Er findet Kochen immer leicht.", False, "„Kochen ist manchmal schwer, weil die Küche stressig ist.“", passage=1),
    tf("Er lernt jeden Tag etwas Neues und wird immer besser.", True, "„… ich lerne jeden Tag etwas Neues und werde immer besser.“", passage=1),
    tf("Markus arbeitet im Moment in einem deutschen Restaurant.", False, "„Ich gehe noch zur Schule, aber ich helfe meinem Vater oft im Restaurant.“",
       passage=2),
    tf("Markus möchte Koch werden, weil er Kochen langweilig findet.", False, "„Kochen macht mir Spaß, und ich finde den Beruf interessant.“", passage=2),
    tf("Nach der Schule wird Markus eine Kochschule besuchen.", True, "„Ich werde eine Kochschule besuchen und professionell kochen lernen.“", passage=2),
    tf("Markus möchte später sein eigenes Restaurant eröffnen.", True, "„Vielleicht werde ich später mein eigenes Restaurant haben.“", passage=2),
    tf("Markus glaubt nicht, dass er ein guter Koch werden kann.", False, "„Ja, ich bin fleißig und motiviert. Ich werde … jeden Tag besser werden.“",
       passage=2),
    tf("Markus will jeden Tag üben und besser werden.", True, "„Ich werde viel üben und jeden Tag besser werden.“", passage=2),
    tf("Michael Schuman arbeitete früher als Koch auf einem Kreuzfahrtschiff.", True, "„Ich arbeitete viele Jahre auf einem Kreuzfahrtschiff als Koch.“",
       passage=3),
    tf("Er fand seine Arbeit langweilig und anstrengend.", False, "„Die Arbeit war anstrengend, aber sehr interessant.“", passage=3),
    tf("Einmal hat Michael ein besonderes Menü für ein großes Fest vorbereitet.", True,
       "„… einmal haben wir ein großes Fest organisiert, und ich habe ein besonderes Menü vorbereitet.“", passage=3),
    tf("Nach dieser Zeit hat er nur in Restaurants gearbeitet.", False, "„Später habe ich an Land gearbeitet und junge Köche ausgebildet.“", passage=3),
    tf("Er hat sein Wissen an junge Köche weitergegeben.", True, "„Ich habe mein Wissen weitergegeben und viele Schüler unterstützt.“", passage=3),
    tf("Michael vermisst seinen Beruf heute überhaupt nicht.", False, "„Ja, manchmal vermisse ich die Küche und die Atmosphäre.“", passage=3),
]
_K = "Javob: Vizu-Antworten A2 (1. Unterricht, Lesen)."
LESEN_HANDOUT = [  # lesson handout: 18 statements, key "Vizu-Antworten A2"
    tf("Markus wird nach der Schule eine Kochschule besuchen.", True, _K, passage=2),
    tf("Michael arbeitete viele Jahre auf einem Kreuzfahrtschiff.", True, _K, passage=3),
    tf("Frederich kocht nur am Wochenende.", False, _K, passage=1),
    tf("Markus ist faul und nicht motiviert.", False, _K, passage=2),
    tf("Frederich backt im Moment eine Pizza.", True, _K, passage=1),
    tf("Michael hat viele Länder gesehen.", True, _K, passage=3),
    tf("Markus hilft seinem Vater im Restaurant.", True, _K, passage=2),
    tf("Frederich benutzt besondere Gewürze.", True, _K, passage=1),
    tf("Michael ist heute unzufrieden mit seinem Leben.", False, _K, passage=3),
    tf("Markus geht noch zur Schule.", True, _K, passage=2),
    tf("Frederich findet Kochen immer leicht und nie stressig.", False, _K, passage=1),
    tf("Michael hat junge Köche ausgebildet.", True, _K, passage=3),
    tf("Markus wird vielleicht ein eigenes Restaurant haben.", True, _K, passage=2),
    tf("Frederich arbeitet in einem deutschen Restaurant.", False, _K, passage=1),
    tf("Michael kochte für Hunderte von Gästen.", True, _K, passage=3),
    tf("Markus lernt nichts von seinem Vater.", False, _K, passage=2),
    tf("Frederich liebt seinen Beruf.", True, _K, passage=1),
    tf("Michael hat einmal ein besonderes Menü vorbereitet.", True, _K, passage=3),
]
# one reading per text: the book's statements, then the handout's (its no. 14
# "Frederich arbeitet in einem deutschen Restaurant" = book statement 1)
LESEN = LESEN_BOOK + [q for q in LESEN_HANDOUT if q["question"] != "Frederich arbeitet in einem deutschen Restaurant."]

# ---------- Hören (pp.13-14), key: Vizu-Antworten A2 ----------
TRANSCRIPT = (
    "Journalist: Hallo, ich bin Alexis Schumann. Heute stelle ich Ihnen eine Frage: Warum haben Sie Ihren jetzigen Beruf gewählt?\n\n"
    "Johann: Hallo, mein Name ist Johann. Mein Beruf ist Architekt, weil mein Vater auch Architekt war. Als Kind habe ich oft mit ihm gearbeitet "
    "und Häuser gezeichnet. Das hat mir viel Spaß gemacht. Später habe ich Architektur studiert und mein Studium erfolgreich beendet. Jetzt plane "
    "ich moderne Gebäude und arbeite an interessanten Projekten.\n\n"
    "Julia: Hallo, mein Name ist Julia. Mein Beruf ist Ärztin, weil ich schon als Kind Menschen helfen wollte. Früher habe ich meine Puppen "
    "behandelt und kleine Verbände gemacht. In der Schule habe ich Biologie sehr gemocht. Danach habe ich Medizin studiert und viel gelernt. Jetzt "
    "arbeite ich im Krankenhaus und habe viele Patienten behandelt.\n\n"
    "Mikey: Hallo, mein Name ist Mikey. Mein Beruf ist noch Schüler, aber ich möchte Fußballspieler werden. Als Kind habe ich jeden Tag Fußball "
    "gespielt und viele Tore geschossen. Ich habe Cristiano Ronaldo immer bewundert. Letztes Jahr habe ich in einer Mannschaft trainiert. Jetzt "
    "trainiere ich hart und werde in Zukunft professionell Fußball spielen.")
HOEREN = [
    mc("Warum hat Johann seinen Beruf gewählt?", ["Weil sein Vater Architekt war", "Weil er Arzt werden wollte", "Weil er Fußball liebt"], "A"),
    mc("Wen bewundert Mikey?", ["Seinen Vater", "Cristiano Ronaldo", "Einen Lehrer"], "B"),
    mc("Wo arbeitet Julia jetzt?", ["In einem Restaurant", "In einem Krankenhaus", "In einer Schule"], "B"),
    mc("Was hat Johann als Kind oft gemacht?", ["Er hat Häuser gezeichnet", "Er hat Puppen behandelt", "Er hat im Krankenhaus gearbeitet"], "A"),
    mc("Was wollte Julia schon als Kind?", ["Menschen helfen", "Architektin werden", "Lehrerin werden"], "A"),
    mc("Was wird Mikey in Zukunft machen?", ["Er wird Arzt", "Er wird Lehrer", "Er wird professionell Fußball spielen"], "C"),
    mc("Was hat Julia in der Schule besonders gemocht?", ["Sport", "Biologie", "Geschichte"], "B"),
    mc("Was macht Johann jetzt?", ["Er plant moderne Gebäude", "Er spielt Fußball", "Er trainiert Kinder"], "A"),
    mc("Was hat Mikey letztes Jahr gemacht?", ["Er hat Medizin studiert", "Er hat in einer Mannschaft trainiert", "Er hat Architektur studiert"], "B"),
    mc("Warum wollte Julia Ärztin werden?", ["Weil sie reich werden wollte", "Weil sie schon als Kind helfen wollte", "Weil ihr Vater Arzt war"], "B"),
    mc("Was ist Johann von Beruf?", ["Arzt", "Architekt", "Fußballspieler"], "B"),
    mc("Was macht Mikey jetzt?", ["Er trainiert hart", "Er arbeitet im Krankenhaus", "Er studiert Architektur"], "A"),
]

# ---------- Musik Zeit (p.15) — shown as text of the Zusammenfassung ----------
SONG = (
    "<h4>Musik Zeit: „Glück auf dem Asphalt“ — Berge</h4><p>"
    + "<br>".join([
        "Komm wir sehen in den Himmel rauf", "Schau der Horizont malt einen feinen Strich", "Und die Sterne, sie tanzen für dich",
        "Keine Zahl ist so groß um sie alle zu zählen", "Sag, wie weit reicht das helle Licht", "Unserer Sonne, sie dreht ihren Radius",
        "Selbst das Meer ist unendlich tief", "Und die Berge vor dir ruhen so mühelos", "Steigst du bei mir ein?", "Komm, wir ziehen heut einfach los",
        "In Richtung Freiheit, wo uns keiner kennt", "Und vor uns liegt das Glück auf dem Asphalt", "Und der Blick ist weit, hier im Sonnenschein",
        "Komm wir verlaufen uns unterwegs", "Und wir halten nicht an, bis es dunkel wird", "Und die Luft ist so süß und klar",
        "Ja wir atmen den Frieden, der uns umgibt", "Bist du mit dabei?", "", "Komm, wir ziehen heut einfach los", "In Richtung Freiheit, wo uns keiner kennt",
        "Und vor uns liegt das Glück auf dem Asphalt", "Und der Blick ist weit", "Wir schauen nicht mehr zurück", "Nur in die Ferne, denn wir haben Zeit",
        "Und vor uns liegt das Glück auf dem Asphalt", "Hier im Sonnenschein, hier im Sonnenschein", "Hier im Sonnenschein",
        "Es ist so still, hier wo das Licht alles erfüllt", "Siehst du die Formen und die Farben vibrieren?",
        "Es ist so leicht, denn in der Natur können wir grenzenlos sein", "Bist du dabei? Wir haben unendlich viel Zeit, viel Zeit",
        "Komm, wir ziehen heut einfach los", "In Richtung Freiheit, wo uns keiner kennt", "Und vor uns liegt das Glück auf dem Asphalt",
        "Und der Blick ist weit", "Wir schauen nicht mehr zurück, nur in die Ferne", "Denn wir haben Zeit", "Und vor uns liegt das Glück auf dem Asphalt",
        "Hier im Sonnenschein, hier im Sonnenschein", "Hier im Sonnenschein"])
    + "</p>")

# ---------- Wortschatz (p.18) ----------
WORDS = numbered_words([
    ("der Architekt", "arxitektor"), ("die Ärztin", "shifokor (ayol)"), ("der Arzt", "shifokor"), ("der Lehrer", "o‘qituvchi"),
    ("die Lehrerin", "o‘qituvchi (ayol)"), ("der Ingenieur", "muhandis"), ("der Koch", "oshpaz"), ("die Köchin", "oshpaz (ayol)"),
    ("der Fußballspieler", "futbolchi"), ("der Polizist", "politsiyachi"), ("die Polizistin", "politsiyachi (ayol)"), ("der Journalist", "jurnalist"),
    ("die Journalistin", "jurnalist (ayol)"), ("der Fahrer", "haydovchi"), ("der Verkäufer", "sotuvchi"), ("die Verkäuferin", "sotuvchi (ayol)"),
    ("der Manager", "menejer"), ("der Student", "talaba"), ("die Studentin", "talaba (ayol)"), ("der Pilot", "uchuvchi"),
    ("der Mechaniker", "mexanik"), ("die Krankenschwester", "hamshira"), ("der Zahnarzt", "tish shifokori"), ("der Schauspieler", "aktyor"),
    ("die Schauspielerin", "aktrisa"), ("der Programmierer", "dasturchi"), ("der Bäcker", "novvoy"), ("der Friseur", "sartarosh"),
    ("der Fotograf", "fotograf"), ("der Elektriker", "elektrik")], "Berufe und Personen")
WORDS += numbered_words([
    ("die Berufswahl", "kasb tanlash"), ("die Erfahrung", "tajriba"), ("erfolgreich", "muvaffaqiyatli"), ("motiviert", "motivatsiyali"),
    ("unterstützen", "qo‘llab-quvvatlamoq"), ("planen", "rejalashtirmoq"), ("entwickeln", "rivojlantirmoq"), ("die Zukunft", "kelajak"),
    ("das Projekt", "loyiha"), ("das Studium", "oliy ta’lim"), ("abschließen", "tugatmoq"), ("teilnehmen", "qatnashmoq"), ("die Mannschaft", "jamoa"),
    ("trainieren", "mashq qilmoq"), ("bewundern", "hayratlanmoq"), ("behandeln", "davolamoq"), ("zeichnen", "chizmoq"), ("beenden", "tugatmoq"),
    ("interessant", "qiziqarli"), ("schwierig", "qiyin"), ("helfen", "yordam bermoq"), ("arbeiten", "ishlamoq"), ("lernen", "o‘rganmoq"),
    ("studieren", "o‘qimoq (oliy)"), ("verdienen", "pul topmoq"), ("empfehlen", "tavsiya qilmoq"), ("entscheiden", "qaror qilmoq"),
    ("vielleicht", "balki"), ("früher", "ilgari"), ("heutzutage", "hozirgi kunda")], "Karriere und wichtige Verben")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]

UEBUNGEN_SETS = [s for s in (
    exercise("Unterrichtsblatt: 20 Sätze im Präteritum und Perfekt", HANDOUT_20,
             "Dars varag'idagi 20 ta gap: fe'lni Präteritum (va Perfekt) shaklida yozing. Modal fe'llar faqat Präteritumda.", source="book"),
    reverse_vocab_set(WORDS),
) if s]

SCHREIBEN_PROMPT = (
    "Mein Traumberuf – Schritt für Schritt (A2 Niveau)\n\n"
    "Schritt 1: Einleitung — Was ist dein Traumberuf? (Mein Traumberuf ist … / Ich möchte … werden.)\n"
    "Schritt 2: Begründung — Warum möchtest du diesen Beruf? Benutze „weil“. (Ich möchte … werden, weil … / Dieser Beruf ist interessant, weil …)\n"
    "Schritt 3: Vergangenheit — Schreibe über deine Kindheit oder Erfahrungen im Perfekt oder Präteritum. (Als Kind habe ich … / Früher wollte ich … "
    "/ Ich habe schon …)\n"
    "Schritt 4: Zukunft — Schreibe über deine Pläne im Futur I. (Ich werde … / In Zukunft werde ich …)\n"
    "Schritt 5: Schluss — ein positiver Satz über deinen Traum. (Ich hoffe, dass ich erfolgreich werde. / Ich bin motiviert und glaube an meinen Traum.)\n\n"
    "Kompletter Beispieltext (A2): Mein Traumberuf ist Arzt. Ich möchte Arzt werden, weil ich Menschen helfen will. Als Kind habe ich gern mit "
    "meinen Puppen gespielt und sie behandelt. In der Schule habe ich Biologie besonders gemocht. Ich habe viel über den menschlichen Körper "
    "gelernt. In Zukunft werde ich Medizin studieren und hart arbeiten. Ich hoffe, dass ich ein guter Arzt werde.")


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 1. Unterricht", source="vizu", page=3, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie ist die Berufswahl in Deutschland?", page=4,
             prompt="Wie ist die Berufswahl in Deutschland? Sprechen Sie über die drei Fragen.",
             questions=["Warum ist die Berufswahl wichtig?", "Welche Faktoren beeinflussen die Berufswahl?", "Welche Möglichkeiten gibt es in Deutschland?"],
             min_duration=10, max_duration=120,
             metadata={"book_answers": [
                 "Die Berufswahl ist wichtig, weil sie unsere Zukunft beeinflusst und über unseren Erfolg und unsere Zufriedenheit entscheidet.",
                 "Interessen, Fähigkeiten, Schulbildung, Erfahrungen, Arbeitsmarkt und persönliche Ziele beeinflussen die Berufswahl.",
                 "In Deutschland gibt es Ausbildung, Studium, duale Ausbildung, Weiterbildung und viele Karrierechancen in verschiedenen Branchen."]}),
        base(L, "grammatik", 1, "Grammatik: Präsens, Präteritum und Perfekt", page="5-9", rules=RULES,
             exercises=[exercise("Aufgabe 1: Präteritum und Perfekt", AUFGABE_1, "Schreiben Sie die Sätze im Präteritum und Perfekt (kitob, 8-bet)."),
                        exercise("Aufgabe 2: Präteritum und Perfekt", AUFGABE_2, "Schreiben Sie die Sätze im Präteritum und Perfekt (kitob, 9-bet).")]),
        base(L, "lesen", 1, "Lesen: Mein Beruf — Mein Leben (Aufgabe 1-3)", page="10-12",
             instruction="Lesen Sie die Texte und entscheiden Sie: Richtig oder Falsch?",
             metadata={"note": "Kitobdagi savollar (javob matndan iqtibos bilan) + dars varag'idagi gaplar (javob: Vizu-Antworten A2). "
                               "Takroriy gap (Frederich … deutschen Restaurant) bir marta."},
             passages=PASSAGES, questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Warum haben Sie Ihren Beruf gewählt?", page="13-14", audio_file="A2 1.Unterricht Hören.m4a",
             instruction="Hören Sie den Dialog. Wählen Sie die richtige Antwort (a, b oder c).", transcript=TRANSCRIPT,
             questions=HOEREN, max_score=len(HOEREN)),
        base(L, "schreiben", 1, "Schreiben: Mein Traumberuf", page=16, prompt=SCHREIBEN_PROMPT, task_type="description", min_words=50, max_words=150,
             time_limit=25, support_phrases=["Mein Traumberuf ist …", "Ich möchte … werden, weil …", "Als Kind habe ich …", "Früher wollte ich …",
                                             "In Zukunft werde ich …", "Ich hoffe, dass …"]),
        base(L, "sprechen", 1, "Sprechen: Ich möchte … werden", page=17, topic="Mein Zukunftsberuf",
             prompt="Sprich über deinen Zukunftsberuf. Benutze den Satz: Ich möchte … werden. Tipp: Benutze den Satzanfang „Ich möchte … werden, weil …“",
             questions=["Was möchtest du werden? Warum?", "Welche Ausbildung oder welches Studium brauchst du?",
                        "Was musst du dafür lernen? Welche Fächer sind wichtig?", "Was möchtest du in der Zukunft machen? Welche Pläne hast du?"],
             response_type="monolog", min_duration=30, max_duration=150,
             speech_goal="Über den Zukunftsberuf sprechen: Beruf + Grund (weil), Ausbildung/Studium, wichtige Fächer, Zukunftspläne.",
             keywords=["Ich möchte", "werden", "weil", "studieren", "Ausbildung", "in der Zukunft"],
             sample_answer="Ich möchte Arzt werden, weil ich Menschen helfen möchte. Ich muss Medizin studieren. Das Studium dauert viele Jahre. "
                           "Ich muss viel lernen. Biologie, Chemie und Deutsch sind wichtig. In der Zukunft möchte ich in einem Krankenhaus arbeiten "
                           "und vielen Menschen helfen."),
        base(L, "wortschatz", 1, "Wortschatz: Berufe, Personen und wichtige Verben", page=18, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen: A2 1. Unterricht", exercises=UEBUNGEN_SETS),
        base(L, "yakuniy", 1, "Abschlusstest: A2 1. Unterricht", source="vizu",
             instruction="Präsens, Präteritum, Perfekt va kasblar bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Ich ___ gestern einen Film gesehen.", ["habe", "bin", "hatte"], "A"),
                 mc("Sie ___ letztes Jahr nach Berlin gefahren.", ["hat", "ist", "war"], "B", "fahren → Perfekt mit sein."),
                 mc("Präteritum von „Ich muss arbeiten.“", ["Ich musste arbeiten.", "Ich muss gearbeitet.", "Ich habe arbeiten."], "A"),
                 mc("Perfekt von „Er schreibt eine E-Mail.“", ["Er hat eine E-Mail geschrieben.", "Er ist eine E-Mail geschrieben.", "Er schrieb eine E-Mail."], "A"),
                 mc("Welcher Satz ist ein Fragesatz mit Fragewort?", ["Lernst du Deutsch?", "Warum lernst du Deutsch?", "Ich lerne Deutsch."], "B"),
                 mc("Präteritum von „Wir gehen ins Kino.“", ["Wir gingen ins Kino.", "Wir gehten ins Kino.", "Wir sind ins Kino."], "A"),
                 tf("Frederich Schuman arbeitet in einem italienischen Restaurant.", True, "Lesen, Aufgabe 1."),
                 tf("Julia ist Architektin.", False, "Hören: Julia ist Ärztin."),
                 mc("„die Erfahrung“ — o'zbekchasi?", ["tajriba", "kelajak", "loyiha"], "A"),
                 mc("„verdienen“ — o'zbekchasi?", ["pul topmoq", "davolamoq", "chizmoq"], "A"),
                 mc("Ich möchte Ärztin werden, ___ ich Menschen helfen will.", ["weil", "aber", "und"], "A"),
                 mc("In Zukunft ___ ich Medizin studieren.", ["werde", "wurde", "habe"], "A", "Futur I: werden + Infinitiv."),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 1. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML + SONG),
    ]
