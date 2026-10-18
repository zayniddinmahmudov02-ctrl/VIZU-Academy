"""A2 6. Unterricht — Beziehungen und Kommunikation — Grammatik: dass-Sätze (book pp. 63-72).

Book: Frage p.64, dass-Sätze p.65, Aufgaben 1-4 p.66, Lesen (Lukas und Jonas /
Paul und Leon, ten Richtig/Falsch each) pp.67-68, Hören (two conflicts,
twelve open questions, no transcript) p.69, Schreiben (Thema + E-Mail) p.70,
Sprechen p.71, Wichtige Wörter worksheet (30 words) p.72; the handout lists
60 words with translations (used for the word list).

Keys: "Vizu-Antworten A2" has none. dass-Aufgaben: one correct sentence each
(dass + verb at the end). Lesen: decided by the quoted sentence — book
statement Paul 9 ("Paul bekommt gute Noten in der Schule") is NOT imported:
the text only says "in der Schule alles gut läuft", grades are not mentioned.
The handout's four extra statements (Lukas 10/11, Paul 10/11) are added.
Hören has open questions: imported as answer fields whose accepted answers
an admin sets after listening (key_pending, stays a draft)."""

from . import (
    article_set, base, exercise, forward_vocab_set, gap, intro_html, mc, numbered_words, reverse_vocab_set, short, summary_html, tf,
    vocab_match_sets,
)

L = 6
LESSON_TITLE = "Beziehungen und Kommunikation"
LESSON_DESCRIPTION = "Thema: Beziehungen und Kommunikation · Grammatik: dass-Sätze"
AUDIO = {"vizu-a2-l06-hoeren-01": "A2 6.Unterricht.mp3"}

EINFUEHRUNG_HTML = intro_html(
    6, "Beziehungen und Kommunikation", "dass-Sätze",
    ["dass bilan ergash gap tuzish: Ich glaube, dass er heute kommt.;",
     "ergash gapda fe'lni oxiriga qo'yish va tipik xatolarni tuzatish;",
     "munosabatlar, do'stlik va muloqot so'zlarini o'rganish."],
    ["muloqotda tushunmovchiliklar nima uchun paydo bo'lishini aytasiz;",
     "do'stlik va oilaviy munosabatlar haqidagi matnlarni tushunasiz;",
     "do'stlaringiz haqida matn va Parijdagi singlingizga e-mail yozasiz;",
     "do'stlar va oila siz uchun nima uchun muhimligini gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(6, [
    "<strong>dass-Satz:</strong> ein Nebensatz — er erklärt, was jemand denkt, sagt, fühlt oder meint.",
    "<strong>Struktur:</strong> Hauptsatz (Verb 2) + dass + Nebensatz (Verb Ende) — Ich glaube, dass er heute kommt.",
    "<strong>Typischer Fehler:</strong> Ich denke, dass er kommt heute. ✗ → Ich denke, dass er heute kommt. ✓",
    "<strong>Wortschatz:</strong> die Beziehung, das Missverständnis, vermissen, vertrauen, die Entfernung, sich gewöhnen, sich entschuldigen.",
])

GRAMMAR_HTML = (
    "<h3>dass-Sätze (A2)</h3>"
    "<h4>1. Was ist ein „dass-Satz“?</h4><ul><li>Ein dass-Satz ist ein <strong>Nebensatz</strong>.</li>"
    "<li>Er erklärt, was jemand <strong>denkt, sagt, fühlt</strong> oder <strong>meint</strong>.</li></ul>"
    "<h4>2. Struktur</h4><p><strong>Hauptsatz + dass + Nebensatz</strong> (Verb 2 → Verb Ende)</p>"
    "<ul><li>Ich glaube, dass er heute <strong>kommt</strong>.</li><li>Sie sagt, dass sie krank <strong>ist</strong>.</li></ul>"
    "<h4>3. Satzbau (ganz wichtig!)</h4><p>Subjekt + Verb + …, dass + Subjekt + …, Verb</p>"
    "<h4>4. Wann benutzt man „dass“?</h4><ul><li>Ich hoffe, dass du die Prüfung bestehst.</li><li>Er denkt, dass das Wetter gut ist.</li>"
    "<li>Wir wissen, dass Deutsch wichtig ist.</li><li>Sie sagt, dass sie morgen arbeitet.</li></ul>"
    "<h4>5. Unterschied: Hauptsatz vs. dass-Satz</h4>"
    + "<table><tbody><tr><td>Ohne dass:</td><td>Er kommt.</td></tr><tr><td>Mit dass:</td><td>Ich glaube, dass er kommt.</td></tr></tbody></table>"
    "<h4>6. Beispiele</h4><ul><li>Ich denke, dass Deutsch interessant ist.</li><li>Er sagt, dass er keine Zeit hat.</li><li>Wir hoffen, dass du kommst.</li>"
    "<li>Sie weiß, dass ich müde bin.</li></ul>"
    "<h4>7. Typische Fehler</h4><p>Ich denke, ____ er heute kommt. a) das · <strong>b) dass</strong> · c) des</p>"
    "<h4>8. Mini-Übung</h4><ul><li>dass leitet Nebensätze ein. ✓</li><li>Das Verb steht am Ende. ✓</li></ul>"
)


def _acc(*sentences: str) -> list[str]:
    out = []
    for s in sentences:
        out += [s, s.replace(",", "")]
    return out


A1 = [gap("Ergänzen Sie die Sätze mit dass.", f"{i}. {s.replace('___', '[[1]]')}", {"1": ["dass"]}, explanation=s.replace("___", "dass"))
      for i, s in enumerate(["Ich denke, ___ du heute kommst.", "Er sagt, ___ er keine Zeit hat.", "Wir wissen, ___ Deutsch wichtig ist.",
                             "Sie hofft, ___ sie die Prüfung besteht.", "Ich finde, ___ der Film interessant ist.", "Er glaubt, ___ alles gut wird."],
                            start=1)]
A2 = [short(f"{i}. {q} → mit „dass“", _acc(a), explanation=a, max_length=200) for i, (q, a) in enumerate([
    ("Ich weiß. Du bist müde.", "Ich weiß, dass du müde bist."), ("Er sagt. Er lernt jeden Tag Deutsch.", "Er sagt, dass er jeden Tag Deutsch lernt."),
    ("Wir hoffen. Wir fahren nach Deutschland.", "Wir hoffen, dass wir nach Deutschland fahren."), ("Sie denkt. Der Test ist schwer.", "Sie denkt, dass der Test schwer ist."),
    ("Ich glaube. Er kommt morgen.", "Ich glaube, dass er morgen kommt."), ("Sie sagt. Sie hat viel Arbeit.", "Sie sagt, dass sie viel Arbeit hat.")], start=1)]
A3 = [short(f"{i}. {q} → dass-Satz", _acc(a), explanation=a, max_length=200) for i, (q, a) in enumerate([
    ("Ich glaube: Er ist zu Hause.", "Ich glaube, dass er zu Hause ist."), ("Sie sagt: Ich habe keine Zeit.", "Sie sagt, dass sie keine Zeit hat."),
    ("Wir wissen: Das ist richtig.", "Wir wissen, dass das richtig ist."), ("Er denkt: Deutsch ist schwer.", "Er denkt, dass Deutsch schwer ist."),
    ("Ich hoffe: Alles klappt gut.", "Ich hoffe, dass alles gut klappt."), ("Sie weiß: Der Kurs ist interessant.", "Sie weiß, dass der Kurs interessant ist.")],
    start=1)]
A4 = [short(f"{i}. {q} → richtig:", _acc(*a), explanation=a[0], max_length=200) for i, (q, a) in enumerate([
    ("Ich denke, dass er kommt heute.", ["Ich denke, dass er heute kommt."]), ("Sie sagt, dass sie hat keine Zeit.", ["Sie sagt, dass sie keine Zeit hat."]),
    ("Wir glauben, dass ist das gut.", ["Wir glauben, dass das gut ist."]),
    ("Er sagt, dass er keine Zeit hat gestern.", ["Er sagt, dass er gestern keine Zeit hatte.", "Er sagt, dass er gestern keine Zeit hat."]),
    ("Ich weiß, dass du bist müde.", ["Ich weiß, dass du müde bist."]),
    ("Sie hofft, dass sie bestehen wird die Prüfung.", ["Sie hofft, dass sie die Prüfung bestehen wird."])], start=1)]

TEXT_LUKAS = (
    "Lukas und Jonas haben sich vor drei Jahren in einem Sommerlager kennengelernt, und obwohl sie am Anfang völlig fremd waren, haben sie sehr "
    "schnell gemerkt, dass sie viele gemeinsame Interessen und ähnliche Charaktereigenschaften haben. Beide spielen gern Fußball, hören moderne Musik "
    "und lieben es, neue Dinge auszuprobieren und Abenteuer zu erleben, deshalb haben sie schon in den ersten Tagen viel Zeit miteinander verbracht "
    "und eine enge Verbindung aufgebaut. Im Lager haben sie zusammen Sport gemacht, an Wettbewerben teilgenommen, am Abend am Lagerfeuer gesessen und "
    "lange, persönliche Gespräche geführt, in denen sie über ihre Träume, Ziele und ihr Leben gesprochen haben. Lukas denkt, dass Jonas ein sehr "
    "ehrlicher, zuverlässiger und hilfsbereiter Mensch ist, auf den man sich immer verlassen kann, während Jonas sagt, dass Lukas immer positive "
    "Energie bringt, kreative Ideen hat und andere motivieren kann. Nach dem Lager haben sie den Kontakt nicht verloren, sondern schreiben sich "
    "regelmäßig Nachrichten, telefonieren oft und erzählen sich alles, was in ihrem Alltag passiert, sodass ihre Freundschaft weiter gewachsen ist. "
    "Lukas hofft, dass sie sich bald wiedersehen können, vielleicht im nächsten Sommer, während Jonas glaubt, dass ihre Freundschaft stark genug ist, "
    "um auch über große Entfernungen hinweg zu bestehen. Für beide ist diese Freundschaft besonders wichtig, weil sie einander vertrauen, sich "
    "gegenseitig unterstützen und wissen, dass sie immer füreinander da sind, egal was passiert.")
TEXT_PAUL = (
    "Paul und Leon sind Brüder, die sich sehr nahestehen, obwohl sie im Moment nicht zusammenleben, denn Leon ist der ältere Bruder und studiert seit "
    "einem Jahr im Ausland in Deutschland, während Paul noch mit den Eltern in ihrer Heimatstadt lebt und zur Schule geht. Am Anfang war es für beide "
    "nicht einfach, diese Veränderung zu akzeptieren, weil sie früher viel Zeit miteinander verbracht haben, zusammen gespielt, gelernt und sich "
    "gegenseitig geholfen haben, doch jetzt müssen sie sich an die Distanz gewöhnen. Paul sagt oft, dass er seinen Bruder sehr vermisst und dass es zu "
    "Hause manchmal ruhiger und langweiliger ist ohne ihn, während Leon schreibt, dass das Leben im Ausland zwar spannend und voller neuer Erfahrungen "
    "ist, aber auch Herausforderungen mit sich bringt, zum Beispiel eine neue Sprache, neue Menschen und ein anderes Studiumssystem. Die Brüder "
    "schreiben sich regelmäßig E-Mails und Nachrichten, in denen sie über ihren Alltag berichten: Leon erzählt, dass er viele neue Freunde gefunden hat, "
    "viel lernt und selbstständiger geworden ist, während Paul berichtet, dass in der Schule alles gut läuft und dass er versucht, genauso fleißig zu "
    "sein wie sein Bruder. Paul denkt, dass Leon sehr mutig ist, weil er allein in einem fremden Land lebt und seinen eigenen Weg geht, und Leon sagt, "
    "dass Paul immer sein bester Freund und eine wichtige Unterstützung bleibt. Beide hoffen, dass sie sich bald wiedersehen, vielleicht in den "
    "Ferien, und dann viel Zeit miteinander verbringen können, um ihre Beziehung noch stärker zu machen. Ihre familiäre Beziehung ist sehr stark, weil "
    "sie auf Liebe, Respekt und Vertrauen basiert und weil sie trotz der Entfernung immer in Kontakt bleiben und sich gegenseitig motivieren.")
LESEN = [
    tf("Lukas und Jonas haben sich in der Schule kennengelernt.", False, "„… haben sich vor drei Jahren in einem Sommerlager kennengelernt …“", passage=1),
    tf("Sie haben schnell gemerkt, dass sie ähnliche Interessen haben.", True, "„… haben sie sehr schnell gemerkt, dass sie viele gemeinsame Interessen … haben.“",
       passage=1),
    tf("Beide mögen keine Musik.", False, "„Beide spielen gern Fußball, hören moderne Musik …“", passage=1),
    tf("Sie haben im Lager viel Zeit zusammen verbracht.", True, "„… haben sie schon in den ersten Tagen viel Zeit miteinander verbracht …“", passage=1),
    tf("Sie haben nie miteinander gesprochen.", False, "„… lange, persönliche Gespräche geführt …“", passage=1),
    tf("Lukas denkt, dass Jonas ehrlich und hilfsbereit ist.", True, "„Lukas denkt, dass Jonas ein sehr ehrlicher, zuverlässiger und hilfsbereiter Mensch ist …“",
       passage=1),
    tf("Jonas findet, dass Lukas negativ ist.", False, "„… Jonas sagt, dass Lukas immer positive Energie bringt …“", passage=1),
    tf("Nach dem Lager haben sie den Kontakt verloren.", False, "„Nach dem Lager haben sie den Kontakt nicht verloren …“", passage=1),
    tf("Sie schreiben sich regelmäßig Nachrichten.", True, "„… schreiben sich regelmäßig Nachrichten …“", passage=1),
    tf("Lukas möchte Jonas bald wiedersehen.", True, "„Lukas hofft, dass sie sich bald wiedersehen können …“ (Unterrichtsblatt)", passage=1),
    tf("Jonas glaubt, dass ihre Freundschaft schwach ist.", False, "„… Jonas glaubt, dass ihre Freundschaft stark genug ist …“ (Unterrichtsblatt)", passage=1),
    tf("Ihre Freundschaft basiert auf Vertrauen und Unterstützung.", True, "„… weil sie einander vertrauen, sich gegenseitig unterstützen …“", passage=1),
    tf("Paul und Leon sind Cousins.", False, "„Paul und Leon sind Brüder …“", passage=2),
    tf("Leon studiert im Ausland in Deutschland.", True, "„… studiert seit einem Jahr im Ausland in Deutschland …“", passage=2),
    tf("Paul lebt allein in einer anderen Stadt.", False, "„… während Paul noch mit den Eltern in ihrer Heimatstadt lebt …“", passage=2),
    tf("Am Anfang war die Situation für beide einfach.", False, "„Am Anfang war es für beide nicht einfach …“", passage=2),
    tf("Paul vermisst seinen Bruder sehr.", True, "„Paul sagt oft, dass er seinen Bruder sehr vermisst …“", passage=2),
    tf("Leon schreibt, dass das Leben im Ausland immer leicht ist.", False, "„… zwar spannend … aber auch Herausforderungen mit sich bringt …“", passage=2),
    tf("Die Brüder schreiben sich regelmäßig E-Mails.", True, "„Die Brüder schreiben sich regelmäßig E-Mails und Nachrichten …“", passage=2),
    tf("Leon hat im Ausland keine neuen Freunde.", False, "„Leon erzählt, dass er viele neue Freunde gefunden hat …“", passage=2),
    tf("Paul denkt, dass Leon mutig ist.", True, "„Paul denkt, dass Leon sehr mutig ist …“ (Unterrichtsblatt)", passage=2),
    tf("Leon sagt, dass Paul ihm nicht wichtig ist.", False, "„… Leon sagt, dass Paul immer sein bester Freund und eine wichtige Unterstützung bleibt.“ "
       "(Unterrichtsblatt)", passage=2),
    tf("Ihre Beziehung ist stark trotz der Entfernung.", True, "„Ihre familiäre Beziehung ist sehr stark … trotz der Entfernung …“", passage=2),
]


def _open(q: str) -> dict:
    return gap(q, "Antwort: [[1]]", {"1": []})


HOEREN = [_open(q) for q in [
    "1. Konflikt (Lukas und Jonas): Wo haben sich Lukas und Jonas kennengelernt?", "1. Konflikt: Was haben sie gern zusammen gemacht?",
    "1. Konflikt: Was ist beim Fußballspiel passiert?", "1. Konflikt: Wie hat sich Jonas gefühlt?", "1. Konflikt: Was hat Lukas später gemacht?",
    "1. Konflikt: Was haben sie aus dem Problem gelernt?", "2. Konflikt (Paul und Leon): Wer sind Paul und Leon?", "2. Konflikt: Wo lebt Leon?",
    "2. Konflikt: Warum hatte Leon oft keine Zeit?", "2. Konflikt: Wie hat sich Paul gefühlt?", "2. Konflikt: Was hat Leon erklärt?",
    "2. Konflikt: Was haben sie gelernt?"]]

WORDS = numbered_words([
    ("die Beziehung", "munosabat"), ("die Kommunikation", "muloqot"), ("das Missverständnis", "tushunmovchilik"), ("der Freund", "do‘st"),
    ("die Freundschaft", "do‘stlik"), ("der Bruder", "aka-uka"), ("die Familie", "oila"), ("zusammenleben", "birga yashamoq"), ("sich verstehen", "tushunish"),
    ("sprechen", "gaplashmoq"), ("erklären", "tushuntirmoq"), ("erzählen", "hikoya qilmoq"), ("denken", "o‘ylamoq"), ("glauben", "ishonmoq"),
    ("hoffen", "umid qilmoq"), ("fühlen", "his qilmoq"), ("vermissen", "sog‘inmoq"), ("helfen", "yordam bermoq"), ("unterstützen", "qo‘llab-quvvatlamoq"),
    ("vertrauen", "ishonch bildirmoq"), ("respektieren", "hurmat qilmoq"), ("wichtig", "muhim"), ("ehrlich", "halol"), ("freundlich", "mehribon"),
    ("traurig", "xafa"), ("glücklich", "baxtli"), ("wütend", "jahli chiqqan"), ("der Streit", "janjal"), ("die Lösung", "yechim"), ("akzeptieren", "qabul qilmoq"),
    ("die Entfernung", "masofa"), ("im Ausland", "chet elda"), ("das Studium", "o‘qish"), ("lernen", "o‘rganmoq"), ("arbeiten", "ishlamoq"), ("leben", "yashamoq"),
    ("der Alltag", "kundalik hayot"), ("die Nachricht", "xabar"), ("die E-Mail", "elektron xat"), ("telefonieren", "telefon qilmoq"), ("schreiben", "yozmoq"),
    ("antworten", "javob bermoq"), ("sich treffen", "uchrashmoq"), ("verbringen", "vaqt o‘tkazmoq"), ("erleben", "boshdan kechirmoq"), ("die Erfahrung", "tajriba"),
    ("die Veränderung", "o‘zgarish"), ("sich gewöhnen", "ko‘nikmoq"), ("allein", "yolg‘iz"), ("zusammen", "birga"), ("oft", "tez-tez"), ("selten", "kamdan-kam"),
    ("immer", "har doim"), ("manchmal", "ba’zida"), ("stark", "kuchli"), ("schwach", "kuchsiz"), ("ruhig", "tinch"), ("das Problem", "muammo"),
    ("sich entschuldigen", "uzr so‘ramoq"), ("verstehen", "tushunmoq")], "Beziehungen und Kommunikation")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]
WORKSHEET = ["die Beziehung", "das Missverständnis", "die Freundschaft", "zusammenleben", "sich verstehen", "erklären", "hoffen", "vermissen", "unterstützen",
             "respektieren", "ehrlich", "schwierig", "die Veränderung", "sich gewöhnen", "die Erfahrungen", "im Ausland", "das Studium", "arbeiten", "der Alltag",
             "die Nachricht", "die E-Mail", "schreiben", "antworten", "sich treffen", "verbringen", "allein", "zusammen", "oft", "selten", "verstehen"]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 6. Unterricht", source="vizu", page=63, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Warum entstehen Missverständnisse in der Kommunikation?", page=64,
             prompt="Warum entstehen Missverständnisse in der Kommunikation? Sprechen Sie über die drei Gründe.",
             questions=["A: Weil wir unterschiedlich denken und fühlen", "B: Wegen schlechter Ausdrucksweise und unklarer Informationen",
                        "C: Durch Vorurteile und fehlendes Zuhören"],
             min_duration=20, max_duration=120,
             metadata={"book_points": {
                 "A": ["Jeder Mensch hat seine eigenen Gedanken und Erfahrungen.", "Unsere Gefühle beeinflussen, wie wir etwas verstehen.",
                       "Wörter können für jeden etwas anderes bedeuten.", "Wir hören oft nur das, was wir hören wollen.",
                       "Kulturelle Unterschiede spielen eine große Rolle.", "Deshalb kann die gleiche Nachricht unterschiedlich verstanden werden."],
                 "B": ["Wenn wir uns unklar ausdrücken, entstehen leicht Fehler.", "Zu viele Informationen verwirren den Gesprächspartner.",
                       "Wir erklären manchmal zu schnell und nicht genau genug.", "Wichtige Details werden oft weggelassen.",
                       "Geschriebene Nachrichten können leicht falsch verstanden werden.", "Deshalb ist es wichtig, klar und einfach zu kommunizieren."],
                 "C": ["Vorurteile beeinflussen unser Verständnis von anderen.", "Wir denken manchmal, wir wissen schon Bescheid.",
                       "Wenn wir nicht richtig zuhören, verstehen wir nur die Hälfte.", "Wir beurteilen andere, bevor wir alles gehört haben.",
                       "Unsere Annahmen verhindern echtes Verständnis.", "Respektvolles Zuhören hilft, Missverständnisse zu vermeiden."]}}),
        base(L, "grammatik", 1, "Grammatik: dass-Sätze", page="65-66", rules=[{"title": "dass-Sätze (A2)", "html": GRAMMAR_HTML}],
             exercises=[exercise("Aufgabe 1: Ergänzen Sie die Sätze mit dass", A1),
                        exercise("Aufgabe 2: Bilden Sie Sätze mit dass", A2, "Verbinden Sie die zwei Sätze mit dass (Verb am Ende)."),
                        exercise("Aufgabe 3: Formen Sie die Sätze um (dass-Sätze)", A3, "Achten Sie auf die Person: Sie sagt: Ich … → Sie sagt, dass sie …"),
                        exercise("Aufgabe 4: Korrigieren Sie die Fehler", A4, "Schreiben Sie den Satz richtig: das Verb steht im dass-Satz am Ende.")]),
        base(L, "lesen", 1, "Lesen: Freundschaft im Lager / Familiäre Beziehung", page="67-68", instruction="Lesen Sie die Texte. Richtig oder Falsch?",
             passages=[{"title": "Freundschaft im Lager – Lukas und Jonas", "text": TEXT_LUKAS}, {"title": "Familiäre Beziehung – Paul und Leon", "text": TEXT_PAUL}],
             questions=LESEN, max_score=len(LESEN),
             metadata={"note": "Javob har bir savol izohida matndan iqtibos bilan. Kitobdagi „Paul bekommt gute Noten in der Schule“ olinmadi — "
                               "matnda baholar haqida gap yo'q."}),
        base(L, "hoeren", 1, "Hören: Konflikte zwischen Lukas und Jonas / Paul und Leon", page=69, audio_file="A2 6.Unterricht.mp3", key_pending=True,
             instruction="Hören Sie die zwei Texte und beantworten Sie die Fragen kurz.", questions=HOEREN,
             metadata={"note": "Ochiq savollar, kitobda javob ham, transkript ham yo'q — admin audioni tinglab qabul qilinadigan javoblarni kiritadi."}),
        base(L, "schreiben", 1, "Schreiben: Meine Freunde", page=70, task_type="description",
             prompt="Schreiben Sie einen kurzen Text über Ihre Freunde. Schreiben Sie mindestens 80 Wörter.\n\nPunkte:\n"
                    "• Wie heißen Ihre Freunde? (z.B. Lukas und Jonas)\n• Haben Sie viele Freunde oder nur wenige?\n"
                    "• Woher kennen Sie Ihre Freunde? (Schule, Nachbarn, Sport …)\n• Was machen Sie gern zusammen? (Unsere Hobbys)\n"
                    "• Welche lustigen Erlebnisse haben Sie zusammen erlebt? (Unsere Erlebnisse)\n• Was mögen Sie an Ihren Freunden und warum?",
             min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: E-Mail an meine Schwester in Paris", page=70, task_type="email",
             prompt="Ihre Schwester lebt in Paris. Sie möchten ihr eine E-Mail schreiben. Schreiben Sie mindestens 80 Wörter.\n\nPunkte:\n"
                    "• Sagen Sie, dass Sie eine E-Mail schreiben.\n• Fragen Sie nach Paris und nach ihrem Leben dort. (Über Paris sprechen)\n"
                    "• Erzählen Sie, warum Sie Ihre Schwester bald treffen möchten und wie Sie nach Paris kommen.\n"
                    "• Sprechen Sie über das Wetter, Datum und Ihre Reise. (Mein Besuch in Paris)\n• Fragen Sie, was Sie zusammen machen können.",
             audience="Ihre Schwester (informell)", min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Wichtige Wörter — Bedeutung und Beispiel", page=72, task_type="other",
             prompt="Schreiben Sie die Bedeutung und ein Beispiel.\n\n" + "\n".join(f"{i}. {w}" for i, w in enumerate(WORKSHEET, start=1)),
             min_words=60, max_words=500, time_limit=40, metadata={"note": "Kitobdagi ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "sprechen", 1, "Sprechen: Meine Verständnisse in der Beziehungen", page=71, topic="Freunde und Familie",
             prompt="Sprechen Sie über das Thema.",
             questions=["Warum sind Freunde für dich wichtig?", "Was machst du gerne mit deinen Freunden?", "Wie löst du Probleme mit deinen Freunden?",
                        "Was ist schwierig, wenn man weit voneinander entfernt ist?", "Warum ist Familie wichtig für dich?", "Was hast du von deiner Familie gelernt?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Über Freundschaft und Familie sprechen, mit dass- und weil-Sätzen begründen.",
             keywords=["Ich denke, dass", "weil", "Freunde", "Familie", "vertrauen"]),
        base(L, "wortschatz", 1, "Wortschatz: Beziehungen und Kommunikation", page=72, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False,
             metadata={"note": "Tarjimalar dars varag'idan (60 so'z)."}),
        base(L, "uebungen", 1, "Übungen: A2 6. Unterricht", source="vizu", exercises=[s for s in (
            exercise("dass-Satz: richtig oder falsch?", [
                mc("Welcher Satz ist richtig?", ["Ich glaube, dass er heute kommt.", "Ich glaube, dass er kommt heute.", "Ich glaube, er dass heute kommt."], "A"),
                mc("Welcher Satz ist richtig?", ["Sie sagt, dass sie krank ist.", "Sie sagt, dass ist sie krank.", "Sie sagt, dass sie ist krank."], "A"),
                mc("Ich denke, ___ er heute kommt.", ["das", "dass", "des"], "B", "Kitobdagi „Typische Fehler“: b) dass."),
                mc("Was steht im dass-Satz am Ende?", ["das Verb", "das Subjekt", "dass"], "A"),
            ], "dass-gap qoidasi (kitob, 65-bet).", source="vizu"),
            reverse_vocab_set(WORDS),
        ) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 6. Unterricht", source="vizu",
             instruction="dass-Sätze va munosabatlar so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Er sagt, dass er keine Zeit ___.", ["hat", "haben", "hat er"], "A"),
                 mc("Wir hoffen, dass du ___.", ["kommst", "kommen", "du kommst"], "A"),
                 mc("Richtig ist:", ["Ich weiß, dass du müde bist.", "Ich weiß, dass du bist müde.", "Ich weiß, du dass müde bist."], "A"),
                 tf("Leon studiert im Ausland in Deutschland.", True, "Lesen, Text 2."),
                 tf("Lukas und Jonas haben sich in der Schule kennengelernt.", False, "Lesen, Text 1: im Sommerlager."),
                 mc("„vermissen“ — o'zbekchasi?", ["sog'inmoq", "ishonmoq", "hurmat qilmoq"], "A"),
                 mc("„das Missverständnis“ — o'zbekchasi?", ["tushunmovchilik", "janjal", "yechim"], "A"),
                 mc("„sich entschuldigen“ — o'zbekchasi?", ["uzr so'ramoq", "ko'nikmoq", "uchrashmoq"], "A"),
                 mc("„die Entfernung“ — o'zbekchasi?", ["masofa", "o'zgarish", "tajriba"], "A"),
                 mc("Sie sagt: „Ich habe keine Zeit.“ → Sie sagt, dass ___ keine Zeit hat.", ["sie", "ich", "er"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 6. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
