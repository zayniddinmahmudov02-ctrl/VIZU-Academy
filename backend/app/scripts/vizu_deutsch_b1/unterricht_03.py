"""B1 3. Unterricht — Ernährung und Essgewohnheiten — Grammatik: Infinitiv mit zu (book pp. 42-60).

Book: title p.42, Frage des Themas (Wie ist Ihre Essgewohnheit?) p.43,
Infinitiv mit zu p.44, Infinitiv-Gruppen (ohne zu, statt zu, um zu) p.45,
Grammatik Aufgabe 1-4 (word banks) pp.46-49, Lesen Aufgabe 1 (Einladung,
zuordnen) p.50, Lesen Aufgabe 2 (Leserbrief, Wörter) p.51, Lesen Aufgabe 3
(Abendessen mit Freunden: um / ohne / statt … zu) p.52, Hören Teil 1-3
(Ulrich und Ella, gap text) pp.53-55, Schreiben Teil 1 (E-Mail neues Auto,
Musterlösung) p.56, Schreiben Teil 2 (Urlaub am Strand, Musterlösung) p.57,
Sprechen Teil 1 (Büro neu einrichten, Muster-Dialog) p.58, Sprechen Teil 2
(Wie viel Fernsehen ist gesund, Musterpräsentation) p.59, Wichtige
Redewendungen für Modul 3 p.60.

Book defects (kept visible, never "repaired" by guessing):
* Grammatik Aufgabe 1: the word bank (lernen, reisen, machen, lesen, helfen,
  anrufen, sparen, essen) does not fit the 8 sentences (reisen is needed
  twice, Satz 7 needs "kaufen") -> all four Grammatik tasks are open writing
  tasks (teacher review), the word bank is shown as help.
* Lesen Aufgabe 1: item 2 and option c) are missing in the book; "Termin für
  Antwort" has no printed option (text: "die nächsten Tage"). Imported: the 5
  items with a printed answer (VIZU key, held) + the Termin question as short
  answer from the text.
* Lesen Aufgabe 2 says "Lücken (1-6)" but the page prints 4 gaps; the two
  extra words (trinken, Gast) stay as distractors.
* Hören Teil 1-3: 37 blanks without numbers, word bank or key; only the audio
  ("3.Unterricht Teil 1-2-3.mp3") can decide them -> key_pending; the blanks
  are numbered per Teil in reading order (multi-word blanks = one gap)."""

from . import (
    base, completion, example_gap, exercise, gap, intro_html, key_meta, match, meaning_sets, mc, redewendungen, short, summary_html,
)

L = 3
LESSON_TITLE = "Ernährung und Essgewohnheiten"
LESSON_DESCRIPTION = "Thema: Ernährung und Essgewohnheiten · Grammatik: Infinitiv mit zu (um … zu, ohne … zu, statt … zu)"
AUDIO = {"vizu-b1-l03-hoeren-01": "3.Unterricht Teil 1-2-3.mp3"}

EINFUEHRUNG_HTML = intro_html(
    3, "Ernährung und Essgewohnheiten", "Infinitiv mit zu (um … zu, ohne … zu, statt … zu)",
    ["Infinitiv mit „zu“ — niyat, reja, istak va maqsadni ifodalash (hoffen, planen, versuchen … + zu + Infinitiv);",
     "Infinitiv-Gruppen: zu-siz (Modalverben), statt … zu (muqobil), um … zu (maqsad), ohne … zu;",
     "ovqatlanish odatlari va mehmondorchilik haqida so'zlar."],
    ["ovqatlanish odatlaringiz haqida gapirasiz;",
     "taklifnoma va o'quvchi xatini o'qib tushunasiz;",
     "aka-singilning suhbatini tinglab, bo'sh joylarni to'ldirasiz;",
     "yangi mashinangiz haqida e-mail va dengiz bo'yidagi ta'til haqida fikringizni yozasiz;",
     "ofisni jihozlash rejasini muhokama qilasiz va televizor haqida taqdimot qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(3, [
    "<strong>Infinitiv mit zu</strong>: Subjekt + Verb/Adjektiv/Nomen + zu + Infinitiv — Ich hoffe, Deutsch zu lernen. „zu“ steht direkt vor dem Infinitiv.",
    "Typische Verben: hoffen, planen, versuchen, vergessen, beginnen, lernen, wünschen, entscheiden, versprechen, vorhaben.",
    "<strong>ohne zu</strong> nach Modalverben: Ich kann Deutsch lernen. · <strong>statt zu</strong> = anstatt zu (Alternative): Ich lerne Deutsch statt zu schlafen.",
    "<strong>um zu</strong> (Zweck / Ziel): Ich lerne Deutsch, um besser zu kommunizieren. · <strong>ohne … zu</strong>: Ich übersetze den Text, ohne Wörterbuch zu benutzen.",
    "<strong>Redewendungen:</strong> in Betracht ziehen, zu dem Schluss kommen, einen Einfluss haben auf, voneinander abhängen, eine Lösung finden, "
    "Prioritäten setzen, Verantwortung übernehmen, im Voraus planen, sich bemühen um, eine Herausforderung meistern.",
])

GRAMMAR_ZU = (
    "<h3>Infinitiv mit zu</h3><p>Der Infinitiv mit „zu“ drückt Absichten, Pläne, Wünsche, Hoffnungen oder Ziele aus.</p>"
    "<h4>Regeln</h4><ul><li>Der Infinitiv mit „zu“ wird nach bestimmten Verben, Adjektiven und Nomen verwendet.</li>"
    "<li>„zu“ steht immer direkt vor dem Infinitiv.</li><li>Zwischen „zu“ und Infinitiv stehen keine weiteren Wörter.</li></ul>"
    "<h4>Struktur</h4><p><strong>Subjekt + Verb/Adjektiv/Nomen + zu + Infinitiv</strong></p>"
    "<h4>Typische Verben</h4><p>hoffen · planen · versuchen · vergessen · beginnen · lernen · wünschen · entscheiden · versprechen · vorhaben</p>"
    "<h4>Beispiele</h4><ul><li>Ich hoffe, Deutsch zu lernen.</li><li>Wir planen, im Sommer nach Deutschland zu reisen.</li>"
    "<li>Er versucht, jeden Tag Sport zu machen.</li><li>Ich habe vergessen, dich anzurufen.</li><li>Sie beginnt, ein neues Buch zu lesen.</li></ul>"
    "<p><strong>Merke:</strong> Der Infinitiv mit „zu“ steht nach bestimmten Verben, Adjektiven und Nomen und zeigt eine Absicht, einen Plan, Wunsch "
    "oder ein Ziel.</p>"
)
GRAMMAR_GRUPPEN = (
    "<h3>Infinitiv-Gruppen: ohne zu, statt zu, um zu …</h3>"
    "<p>Der Infinitiv kann mit oder ohne „zu“ stehen. Manchmal wird „zu“ weggelassen oder durch andere Wörter ersetzt.</p>"
    "<table><thead><tr><th>1. Infinitiv-Gruppen ohne „zu“</th><th>2. Infinitiv mit „statt zu“</th><th>3. Infinitiv mit „um zu …“</th></tr></thead><tbody>"
    "<tr><td><strong>Regeln:</strong> Nach Modalverben und bestimmten Verben steht der Infinitiv ohne „zu“.</td>"
    "<td><strong>Regeln:</strong> „Statt zu“ bedeutet „anstatt zu“. Es wird benutzt, um eine Alternative auszudrücken.</td>"
    "<td><strong>Regeln:</strong> „Um zu“ drückt den Zweck oder das Ziel einer Handlung aus.</td></tr>"
    "<tr><td><strong>Struktur:</strong> Subjekt + Modalverb/Verb + Infinitiv (ohne zu)</td><td><strong>Struktur:</strong> Subjekt + Verb + statt zu + Infinitiv</td>"
    "<td><strong>Struktur:</strong> Subjekt + Verb + um zu + Infinitiv</td></tr>"
    "<tr><td>Ich kann Deutsch lernen.<br>Wir wollen nach Berlin fahren.<br>Er muss früh aufstehen.<br>Sie lässt die Kinder spielen.<br>"
    "<em>Wichtige Verben:</em> können, wollen, müssen, sollen, dürfen, lassen, sehen, hören, fühlen, helfen, machen …</td>"
    "<td>Ich lerne Deutsch statt zu schlafen.<br>Wir gehen ins Kino statt zu Hause zu bleiben.<br>Er arbeitet hart statt zu faulenzen.<br>"
    "<em>„Statt zu“ = anstatt zu. Es zeigt eine bessere Alternative.</em></td>"
    "<td>Ich lerne Deutsch, um besser zu kommunizieren.<br>Wir sparen Geld, um eine Reise zu machen.<br>Sie geht zum Arzt, um gesund zu bleiben.<br>"
    "<em>„Um zu“ = mit dem Ziel, um den Zweck etwas zu erreichen.</em></td></tr></tbody></table>"
    "<p><strong>ohne … zu</strong> (Buch S. 49): Ich übersetze den Text, ohne Wörterbuch zu benutzen.</p>"
)

# ---------- Lesen ----------
EINLADUNG = (
    "Hallo Anita und Klaus,\nnächstes Wochenende steigt bei uns eine riesige Geburtstagsparty – wie ihr wisst, wird Oliver, der arme alte Mann, 30 Jahre "
    "alt!\nKommt doch am Samstag so um 20 Uhr bei uns vorbei und bringt gutes Wetter mit, wir würden gern im Garten feiern …!\nSupernett wäre es, wenn "
    "ihr auch etwas zum Essen machen würdet. Meldet euch doch die nächsten Tage mal bei mir, ob ihr kommen könnt und was ihr mitbringt.\nIch freu "
    "mich!\nLiebe Grüße\nHanna\nP.S.: Nehmt euch einen warmen Pulli mit, falls es nachts im Garten kalt wird!")
LESEN_1 = [
    match("Ordnen Sie zu: Was steht in der Einladung?", ["Anlass", "Zeit", "Art der Veranstaltung", "Gastgeber", "Kleiderordnung"],
          ["nächster Samstag, 20 Uhr", "Gartenparty", "30. Geburtstag", "keine, warmen Pulli mitnehmen", "Garten von Hanna und Oliver", "Hanna und Oliver"],
          {"1": "C", "2": "A", "3": "B", "4": "F", "5": "D"}, points=5,
          explanation="Anlass = 30. Geburtstag („wird Oliver … 30 Jahre alt“); Zeit = Samstag 20 Uhr; Art = Gartenparty („im Garten feiern“); "
                      "Gastgeber = Hanna und Oliver; Kleiderordnung = keine, warmen Pulli mitnehmen („Nehmt euch einen warmen Pulli mit“). "
                      "„Garten von Hanna und Oliver“ (= Ort, im Buch fehlt Punkt 2) bleibt übrig."),
    short("Termin für Antwort: Bis wann sollen sich Anita und Klaus melden?", ["die nächsten Tage", "in den nächsten Tagen", "nächste Tage"],
          explanation="„Meldet euch doch die nächsten Tage mal bei mir …“ (im Buch fehlt die passende Option c)."),
]
WOERTER_2 = ["Kühlschrank", "anderen", "trinken", "Gast", "zu Hause", "Essen"]
LESERBRIEF = (
    "Letzten Samstag war ich auf meiner ersten Party in Deutschland. Ich war ziemlich spät dran. Viele Leute waren schon da. Maria hat die Tür "
    "aufgemacht und mich sehr nett begrüßt. Sie hat gesagt: „Fühl dich wie zu [[1]]! Wenn du was trinken willst – die Getränke stehen im [[2]] und "
    "das Essen ist auf dem Tisch im Wohnzimmer.“ Dann hat sie mir zwei Freundinnen vorgestellt und ist weggegangen. Maria hat mir kein Getränk "
    "angeboten und auch nichts zum [[3]]. Das war nicht besonders höflich, oder? Ich habe mir dann selbst etwas genommen – so wie die [[4]].")
LESEN_2 = [gap("Lesen Sie den Text und ergänzen Sie die Lücken mit den passenden Wörtern.", LESERBRIEF,
               {"1": {"accepted": ["Hause"], "options": ["Hause", "Gast", "Essen", "trinken"]},
                "2": {"accepted": ["Kühlschrank"], "options": WOERTER_2},
                "3": {"accepted": ["Essen"], "options": WOERTER_2},
                "4": {"accepted": ["anderen"], "options": WOERTER_2}}, points=4,
               explanation="Fühl dich wie zu Hause · im Kühlschrank · nichts zum Essen · so wie die anderen.")]
ABEND = (
    "Am Freitag habe ich meine Freunde zum Abendessen eingeladen. Wir haben uns getroffen, [[1]] zusammen zu kochen und einen schönen Abend zu "
    "verbringen. [[2]] in ein Restaurant [[3]] gehen, haben wir Pizza und Salat selbst gemacht. Niemand hat sein Handy benutzt, [[4]] vorher ein Foto "
    "vom Essen [[5]] machen. Während des Essens haben wir viel gelacht und über unsere Zukunft gesprochen. Am Ende waren alle glücklich, [[6]] sich "
    "zu beeilen nach Hause [[7]] gehen.")
_UOS = ["um", "ohne", "statt", "zu"]
LESEN_3 = [gap("Ergänzen Sie die Lücken mit: um … zu, ohne … zu oder statt … zu.", ABEND,
               {"1": {"accepted": ["um"], "options": _UOS}, "2": {"accepted": ["Statt"], "options": ["Statt", "Um", "Ohne", "Zu"]},
                "3": {"accepted": ["zu"], "options": _UOS}, "4": {"accepted": ["um"], "options": _UOS}, "5": {"accepted": ["zu"], "options": _UOS},
                "6": {"accepted": ["ohne"], "options": _UOS}, "7": {"accepted": ["zu"], "options": _UOS}}, points=7,
               explanation="um zusammen zu kochen · Statt in ein Restaurant zu gehen · um vorher ein Foto vom Essen zu machen · "
                           "ohne sich zu beeilen, nach Hause zu gehen.")]

# ---------- Hören (key only from the audio) ----------
TEIL_1 = (
    "Ulrich hat von seiner Firma ein gutes Angebot bekommen. Er kann Abteilungsleiter werden, muss aber in einer anderen Stadt arbeiten. Seine Frau "
    "Gabi möchte nicht [[1]], weil sie gerade ein Haus gekauft haben und Lilli, ihre Tochter, in die Schule gekommen ist. Außerdem hat Gabi eine gute "
    "[[2]] in einer Apotheke. Ulrich weiß nicht, was er tun soll, und trifft sich mit seiner Schwester in einem Café, um vielleicht von ihr einen guten "
    "Rat zu [[3]].\n"
    "Ulrich: Hallo Schwesterchen! Schön, dass du dir Zeit für mich [[4]] hast.\n"
    "Ella: Ist doch klar, Uli! Da komme ich doch gleich, wenn mein kleiner Bruder ein Problem hat! Trinkst du auch einen Cappuccino?\n"
    "Ulrich: Ja, einen großen!\n"
    "Ella: (zur Kellnerin) Zwei große Cappuccini, bitte! (zu Ulrich) So, und jetzt noch mal von vorne, vorhin am Telefon habe ich nicht alles ganz "
    "richtig verstanden. [[5]] genau?\n"
    "Ulrich: Also, mein Chef hat mir letzten Freitag angeboten, die neue Abteilung in Frankfurt als Leiter zu [[6]]. Das wäre genial für meinen [[7]], "
    "auch die Aufgabe wäre eine wirklich interessante [[8]]. Und es wird gut bezahlt!\n"
    "Ella: Super! Gratulation!\n"
    "Ulrich: (lacht geschmeichelt) Danke! Ich habe mich auch wirklich gefreut. (sorgenvoll) Aber Gabi möchte [[9]] umziehen. Sie liebt ihre Arbeit in "
    "der Apotheke und Lilli ist doch auch gerade erst [[10]].\n"
    "Ella: Das heißt, dass du dir unter der Woche ein Zimmer in Frankfurt [[11]] müsstest.")
TEIL_2 = (
    "Ulrich: Genau. Die einfache [[1]] von 200 km jeden Tag zu machen, ist unmöglich, das geht [[2]] zeitlich [[3]] finanziell.\n"
    "Ella: Könntest du denn nicht auch [[4]] arbeiten?\n"
    "Ulrich: Das hatte ich auch schon [[5]]. Mein Chef war von der Idee nicht begeistert, aber er meinte, den Freitag müsste ich nicht unbedingt im "
    "Büro verbringen, wenn nicht gerade wichtige [[6]] stattfinden.\n"
    "Ella: Aber das wäre doch eine gute [[7]]! Dann bist du immerhin von Donnerstagabend bis Sonntagabend zu Hause!\n"
    "Ulrich: (unsicher) Na ja, schon, aber ich bekomme nichts mehr vom [[8]] mit. Und Gabi müsste alles alleine machen.\n"
    "Ella: Aber [[9]], wenn du [[10]] hast, gehst du morgens um halb acht aus dem Haus und kommst auch nicht vor acht Uhr abends nach Hause. Und Lilli "
    "muss um die Zeit ins Bett – mehr als ein [[11]] [[12]] ist da nicht drin! (leicht ironisch) Und ich glaube auch nicht, dass du dann noch den "
    "Rasen mähst oder den Wasserhahn im Bad reparierst!\n"
    "Ulrich: (zögernd) Na ja, natürlich nicht. Das macht eigentlich Gabi sowieso alles allein …\n"
    "Ella: Siehst du? Und wenn du dich mal länger mit Lilli über Skype [[13]], ist das vielleicht mehr wert als ein müdes „Gute Nacht, mein Schatz!“")
TEIL_3 = (
    "Ulrich: Aber die [[1]]! Ich [[2]] eine ganze Menge [[3]] und müsste die Miete für ein Zimmer in Frankfurt zahlen!\n"
    "Ella: Tja, das müsstest du natürlich genau durchrechnen, ob es [[4]]. Aber denkst du nicht, dass du auch einen [[5]] von der Firma bekommen "
    "könntest, wenn du ihnen die Situation erklärst? Sie wollen dich doch gern auf der Position haben!\n"
    "Ulrich: Hm, ja, das könnte ich versuchen. Aber wirklich glücklich bin ich bei dem Gedanken nicht …\n"
    "Ella: Ach, Uli, du solltest es einfach mal [[6]]. Schau dir das Ganze mal ein Jahr lang an. Dann könnt ihr sehen, was es für [[7]] oder [[8]] hat "
    "und wie ihr damit zurechtgekommen seid. Und wer weiß, vielleicht [[9]] ihr euch dann wirklich umzuziehen, oder vielleicht gibt es eine "
    "Möglichkeit für dich, wieder hier einen Job zu finden. Aber du bist um eine interessante [[10]] reicher!\n"
    "Ulrich: Und mein [[11]] auch … Ach, ich glaube, Ella, du hast recht. Ich muss ja nicht mein ganzes Leben in dieser Situation verbringen. "
    "Manchmal hat man einfach [[12]] vor etwas Neuem!\n"
    "Ella: Das denke ich auch. Zahlen wir?\n"
    "Ulrich: Ja, aber das übernehme ich! Für so einen guten [[13]] sind zwei Cappuccino wirklich nicht zu viel … (lacht)\n"
    "Ella: (lacht auch) Oh, wie großzügig, Bruderherz!")


def _pending(text: str, n: int) -> dict:
    return {str(i): [] for i in range(1, n + 1)}


HOEREN = [
    gap("Teil 1: Hören Sie den Dialog und ergänzen Sie die Lücken (1–11).", TEIL_1, _pending(TEIL_1, 11), points=11),
    gap("Teil 2: Hören Sie den Dialog und ergänzen Sie die Lücken (1–13).", TEIL_2, _pending(TEIL_2, 13), points=13),
    gap("Teil 3: Hören Sie den Dialog und ergänzen Sie die Lücken (1–13).", TEIL_3, _pending(TEIL_3, 13), points=13),
]

# ---------- Schreiben / Sprechen ----------
MUSTER_AUTO = (
    "Lieber Haytam,\nwie geht's dir? Hoffentlich ist alles gut. Mir geht es zurzeit super und ich habe heute einen tollen Grund, dir zu schreiben: Ich "
    "habe mir meinen Traum erfüllt und ein neues Auto gekauft!\nEs ist ein Mercedes C63 in der Farbe Weiß. Das Auto ist einfach fantastisch! Es hat "
    "einen starken Motor (620 km pro Stunde), ist sehr bequem und sieht dazu noch richtig elegant aus. Besonders mag ich die Ledersitze, die große "
    "Sitzplatz und das moderne Display. Außerdem hat es viele Sicherheitsfunktionen und eine Klimaanlage, die bei jedem Wetter perfekt funktioniert.\n"
    "Ich habe das Auto gekauft, weil mein altes Auto kaputt war und ich jeden Tag zur Arbeit fahren muss. Außerdem wollte ich schon lange etwas "
    "Modernes und Sicheres, auf das ich mich verlassen kann.\nIch würde mich sehr freuen, wenn du Zeit hättest, mit mir mein neues Auto "
    "auszuprobieren. Lass uns am Wochenende einen Ausflug machen – zum Beispiel an den See oder in die Berge. Dann kannst du das Auto selbst fahren "
    "und wir verbringen eine schöne Zeit zusammen.\nLass von dir hören, wann es dir passt!\nLiebe Grüße\nDein Freund")
MUSTER_STRAND = (
    "Das Thema Urlaub im Strand halte ich für äußerst interessant daher mochte ich meine Meinung zum Ausdruck bringen.\nNatürlich kann man die frische "
    "Luft genießen und im Strand schwimmen aber das ist nicht genug denn man kann viele neuer Dinge verpassen, außerdem entscheiden sich viele für den "
    "Strand als Urlaubsort, was den Strand überfüllt macht man soll nicht vergessen, dass die Strack Sonnenlicht der haut schadet und man sich am "
    "Strand anstecken kann\nAus dem schon genannten Gründen kann ich sagen, dass man verschiedene urlauborte ausprobieren sollte damit kann man etwas "
    "neuer entdecken und neuer Erlebnisse genießen")
MUSTER_BUERO = (
    "Kandidat 1: Also, beginnen wir mit den Möbeln. Ich finde, wir brauchen neue Schreibtische und bequeme Drehstühle.\n"
    "Kandidat 2: Stimmt, die alten Stühle sind nicht mehr bequem. Was hältst du von höhenverstellbaren Tischen?\n"
    "Kandidat 1: Gute Idee! Außerdem brauchen wir Regale und Aktenschränke für mehr Stauraum.\n"
    "Kandidat 2: Einverstanden. Und die Sofas für die Pause-Ecke wären auch schön.\n"
    "Kandidat 1: Wohin mit den alten Möbeln? Sollen wir sie verkaufen?\n"
    "Kandidat 2: Ja, auf dem Flohmarkt oder online. Den Erlös können wir für etwas anderes nutzen. Den Rest können wir spenden.\n"
    "Kandidat 1: Was brauchen wir sonst noch? Eine Kaffeemaschine ist wichtig.\n"
    "Kandidat 2: Ja, und ein neuer Drucker, ein Projektor für Präsentationen und ein paar Pflanzen für ein besseres Raumklima.\n"
    "Kandidat 1: Gute Liste! Wann präsentieren wir den Plan unserem Chef?\n"
    "Kandidat 2: Ich schlage vor, nächsten Montagmorgen. Dann haben wir bis dahin genug Zeit, alles vorzubereiten.\n"
    "Kandidat 1: Perfekt! Dann machen wir uns an die Arbeit.\n\n"
    "(Variante 2) Kandidat 2: Lass uns zuerst überlegen, welche Möbel wir brauchen. — Kandidat 1: Wir brauchen auf jeden Fall neue Schreibtische, "
    "bequeme Stühle und Regale. — Kandidat 2: Ich denke auch, ein großer Besprechungstisch wäre sinnvoll. — Kandidat 1: Ja, für Meetings und "
    "Teamarbeit. Und vielleicht ein Sofa für die Pause? — Kandidat 2: Gute Idee! Wohin mit den alten Möbeln? — Kandidat 1: Wir können sie verkaufen "
    "oder an eine gemeinnützige Organisation spenden. — Kandidat 2: 100% richtig. Was fehlt uns noch? Oh, eine Kaffeemaschine! — Kandidat 1: Und "
    "ein neuer Computer für das Büro, ein Drucker und ein Beamer für Präsentationen. — Kandidat 2: Vergiss nicht die Bilder und Pflanzen. Sie machen "
    "das Büro gemütlicher. — Kandidat 1: Stimmt! Wann sollen wir unseren Plan präsentieren? — Kandidat 2: Wie wäre es nächsten Montag um 10 Uhr? — "
    "Kandidat 1: Passt gut. Dann bereiten wir bis dahin alles vor.")
MUSTER_FERNSEHEN = (
    "Guten Tag! Heute spreche ich über das Thema „Wie viel fernsehen ist gesund“. Für mich schaue ich selten Fernsehen, weil es mir zu langweilig "
    "ist, und ich mache das mit Telefonen und Computern wett.\nHier in Marokko gibt es zwei Kategorien. Die erste Kategorie verbringt Stundenlang vor "
    "dem Fernseher, besonders Kinder und ältere Frauen, und die zweite Kategorie sieht kein Fernsehen.\nEs gibt viele Vorteile vom Fernsehen. Man kann "
    "viel Informationen von fern bekommen. Man kann viel Spaß haben und den Alltag entkommen. Außerdem kann man von fern Fremdsprachen lernen.\nAber "
    "es gibt auch Nachteile. Zu viel Fernsehen ist schlecht für unsere Augen. Man kann viel Zeit verlieren. Für Kinder ist Fernsehen eine Ablenkung "
    "von den Hausaufgaben.\nMeiner Meinung nach spielt Fernsehen in unserem Leben eine große Rolle, daher muss es richtig genutzt werden.\nDanke für "
    "Ihre Aufmerksamkeit!")

WORDS = redewendungen([
    ("etwas in Betracht ziehen", "etwas als Möglichkeit ernsthaft überlegen", "Wir ziehen in Betracht, in Zukunft im Ausland zu studieren."),
    ("zu dem Schluss kommen", "nach Überlegung eine Entscheidung treffen", "Nach vielen Gesprächen sind wir zu dem Schluss gekommen, zu reisen."),
    ("einen Einfluss haben auf", "etwas bewirken oder verändern", "Unsere Umgebung hat einen großen Einfluss auf unsere Stimmung."),
    ("etwas voneinander abhängen", "zusammenhängen, sich gegenseitig beeinflussen", "Erfolg und Fleiß hängen eng miteinander zusammen."),
    ("eine Lösung finden", "ein Problem erfolgreich bewältigen", "Wir müssen gemeinsam eine Lösung für dieses Problem finden."),
    ("Prioritäten setzen", "wichtige Dinge zuerst behandeln", "Ich setze meine Prioritäten auf Gesundheit und gute Bildung."),
    ("Verantwortung übernehmen", "für etwas die Pflicht akzeptieren", "Jeder sollte Verantwortung für seine Entscheidungen übernehmen."),
    ("etwas im Voraus planen", "vorher vorbereiten und organisieren", "Eine gute Planung im Voraus spart Zeit und Stress."),
    ("sich bemühen um", "sich anstrengen, um etwas zu erreichen", "Ich bemühe mich um bessere Noten in der Universität."),
    ("eine Herausforderung meistern", "eine schwierige Aufgabe erfolgreich bewältigen", "Jede Herausforderung macht uns stärker und selbstbewusster."),
], "Wichtige Redewendungen für Modul 3")

UEBUNGEN = [
    exercise("Infinitiv mit oder ohne zu? (Beispielsätze aus dem Buch)", [
        example_gap("Ich hoffe, Deutsch ___ lernen.", "zu", ["zu", "um", "—"], "hoffen + zu + Infinitiv."),
        example_gap("Ich kann Deutsch ___.", "lernen", ["lernen", "zu lernen", "um zu lernen"], "Nach Modalverben: Infinitiv ohne zu."),
        example_gap("Wir wollen nach Berlin ___.", "fahren", ["fahren", "zu fahren", "gefahren"], "wollen + Infinitiv ohne zu."),
        example_gap("Ich habe vergessen, dich ___.", "anzurufen", ["anzurufen", "zu anrufen", "anrufen"], "Trennbares Verb: an-zu-rufen."),
        example_gap("Wir gehen ins Kino, ___ zu Hause zu bleiben.", "statt", ["statt", "um", "ohne"], "statt zu = Alternative."),
        example_gap("Sie geht zum Arzt, ___ gesund zu bleiben.", "um", ["um", "statt", "ohne"], "um zu = Ziel."),
        example_gap("Ich übersetze den Text, ___ Wörterbuch zu benutzen.", "ohne", ["ohne", "um", "statt"], "ohne … zu."),
        example_gap("Er versucht, jeden Tag Sport zu ___.", "machen", ["machen", "gemacht", "macht"]),
    ], "Wählen Sie die richtige Form (Sätze aus dem Buch, S. 44-45 und 49).", source="vizu"),
]

ABSCHLUSSTEST = [
    mc("Wo steht „zu“ beim Infinitiv mit zu?", ["Immer direkt vor dem Infinitiv", "Am Satzanfang", "Nach dem Infinitiv"], "A", "Buch S. 44."),
    mc("Was bedeutet „statt zu“?", ["anstatt zu — eine Alternative", "mit dem Ziel", "ohne Grund"], "A", "Buch S. 45."),
    example_gap("Wir planen, im Sommer nach Deutschland ___ reisen.", "zu", ["zu", "um", "statt"]),
    example_gap("Er muss früh ___.", "aufstehen", ["aufstehen", "aufzustehen", "zu aufstehen"], "müssen + Infinitiv ohne zu."),
    example_gap("Ich lerne Deutsch, ___ besser zu kommunizieren.", "um", ["um", "statt", "ohne"]),
    example_gap("Er arbeitet hart statt zu ___.", "faulenzen", ["faulenzen", "gefaulenzt", "faulenzt"]),
    example_gap("Jeder sollte Verantwortung für seine Entscheidungen ___.", "übernehmen", ["übernehmen", "setzen", "finden"]),
    example_gap("Ich setze meine ___ auf Gesundheit und gute Bildung.", "Prioritäten", ["Prioritäten", "Lösungen", "Einflüsse"]),
    example_gap("Ich bemühe mich ___ bessere Noten in der Universität.", "um", ["um", "für", "auf"]),
    mc("Wann soll man laut Einladung zur Party kommen?", ["Am Samstag um 20 Uhr", "Am Sonntag um 18 Uhr", "Am Freitag um 20 Uhr"], "A",
       "Lesen Aufgabe 1: „Kommt doch am Samstag so um 20 Uhr bei uns vorbei …“"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 3. Unterricht", source="vizu", page=42, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie ist Ihre Essgewohnheit?", page=43, prompt="Wie ist Ihre Essgewohnheit?",
             questions=["Was essen Sie normalerweise zum Frühstück?", "Wie oft essen Sie Obst und Gemüse?", "Achten Sie auf eine gesunde Ernährung? Warum (nicht)?"],
             min_duration=30, max_duration=120,
             metadata={"book_samples": ["Zum Frühstück esse ich meistens Haferflocken mit Obst und trinke eine Tasse Tee oder Kaffee.",
                                        "Ich esse jeden Tag Obst und Gemüse, weil sie wichtig für meine Gesundheit sind.",
                                        "Ja, ich achte auf eine gesunde Ernährung. Ich vermeide Fast Food und esse lieber frisch gekochtes Essen, weil es mir "
                                        "Energie gibt."]}),
        base(L, "grammatik", 1, "Grammatik: Infinitiv mit zu und Infinitiv-Gruppen", page="44-45",
             rules=[{"title": "Infinitiv mit zu", "html": GRAMMAR_ZU}, {"title": "Infinitiv-Gruppen: ohne zu, statt zu, um zu", "html": GRAMMAR_GRUPPEN}]),
        completion(L, 3, "Grammatik Aufgabe 1: Infinitiv mit zu", 46,
                   "Setze die Verben in der richtigen Form mit „zu“ in die Lücken ein. (Wörter im Buch: lernen | reisen | machen | lesen | helfen | "
                   "anrufen | sparen | essen)", [
                       "Ich habe vor, nächstes Jahr nach Italien", "Er versucht jeden Tag Sport", "Wir planen, im Sommer nach Spanien",
                       "Es ist wichtig, Deutsch gut", "Ich habe vergessen, dich gestern", "Meine Schwester hat versprochen, mir bei den Hausaufgaben",
                       "Ich spare Geld, um ein neues Handy", "Sie beginnt, ein interessantes Buch"],
                   ),
        completion(L, 4, "Grammatik Aufgabe 2: Infinitiv mit um zu", 47,
                   "„Um zu“ drückt den Zweck oder das Ziel einer Handlung aus. Setze die Verben in der richtigen Form mit „um zu“ in die Lücken ein. "
                   "(besser verstehen | pünktlich sein | gesund bleiben | Geld sparen | Fehler vermeiden | erfolgreich sein | Deutsch verbessern | abnehmen)", [
                       "Ich lerne jeden Tag Vokabeln,", "Ich gehe früh ins Bett,", "Er macht Sport,", "Wir fahren mit dem Bus,",
                       "Sie liest die Anweisungen sorgfältig,", "Ich übe regelmäßig Grammatik,", "Mein Bruder arbeitet nebenbei,", "Ich esse weniger Süßigkeiten,"]),
        completion(L, 5, "Grammatik Aufgabe 3: Infinitiv mit statt zu", 48,
                   "„Statt zu“ bedeutet „anstatt zu“. Setze die Verben in der richtigen Form mit „statt zu“ in die Lücken ein. Beispiel: Ich bleibe zu "
                   "Hause, statt auszugehen. (fernsehen | ausgehen | Süßigkeiten essen | zu Hause bleiben | spät schlafen | Fleisch essen | Kaffee trinken | "
                   "mit dem Auto fahren)", [
                       "Ich lerne heute Abend Deutsch,", "Er geht ins Fitnessstudio,", "Wir nehmen den Zug,", "Sie isst Salat,", "Kinder sollten Obst essen,",
                       "Ich stehe früh auf,", "Er trinkt Tee,", "Wir treffen uns im Café,"]),
        completion(L, 6, "Grammatik Aufgabe 4: Infinitiv ohne … zu", 49,
                   "Setze die Verben in der richtigen Form in die Lücken ein. Beispiel: Ich übersetze den Text, ohne Wörterbuch zu benutzen. "
                   "(übersetzen | verstehen | machen | schreiben | hören | entscheiden | verlassen | benutzen)", [
                       "Ich ___ den Text, ohne Wörterbuch zu benutzen.", "Er versteht die Regeln gut, ohne den Lehrer", "Wir machen Sport, ohne ins Fitnessstudio",
                       "Sie schreibt E-Mails, ohne lange", "Ich höre Musik, ohne andere", "Du entscheidest dich schnell, ohne lange",
                       "Wir verlassen das Haus, ohne etwas zu", "Er benutzt das Handy, ohne auf die Uhr"]),
        base(L, "lesen", 1, "Lesen Aufgabe 1: Eine Einladung zur Geburtstagsparty", page=50,
             instruction="Lesen Sie diesen sehr locker formulierten Einladungstext und ordnen Sie zu.",
             passages=[{"title": "Einladung von Hanna", "text": EINLADUNG}], questions=LESEN_1, max_score=6,
             metadata=key_meta("vizu", "Buch unvollständig: Punkt 2 und Option c) fehlen; „Termin für Antwort“ hat keine gedruckte Option — "
                                       "Lösung von VIZU aus dem Text, bitte prüfen.")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: Leserbriefe — meine erste Party in Deutschland", page=51,
             instruction="Lesen Sie den Text und ergänzen Sie die Lücken mit den passenden Wörtern. (Sora Kim, 22, aus Korea)",
             passages=[{"title": "Leserbriefe", "text": "Wörter: " + " • ".join(WOERTER_2) + "\n\n" + LESERBRIEF.replace("[[", "(").replace("]]", ")")}],
             questions=LESEN_2, max_score=4,
             metadata=key_meta("vizu", "Die Anweisung nennt Lücken 1–6, gedruckt sind 4; „trinken“ und „Gast“ bleiben übrig. Lösung von VIZU — bitte prüfen.")),
        base(L, "lesen", 3, "Lesen Aufgabe 3: Abendessen mit Freunden", page=52,
             instruction="Lesen Sie den Text und ergänzen Sie die Lücken mit: um … zu, ohne … zu oder statt … zu.",
             passages=[{"title": "Abendessen mit Freunden", "text": ABEND.replace("[[", "(").replace("]]", ")")}], questions=LESEN_3, max_score=7,
             metadata=key_meta("vizu")),
        base(L, "hoeren", 1, "Hören Teil 1–3: Ulrich und Ella im Café", page="53-55", audio_file=AUDIO["vizu-b1-l03-hoeren-01"], key_pending=True,
             instruction="Hören Sie den Dialog und ergänzen Sie die Lücken. (Teil 1–3, eine Audiodatei)", questions=HOEREN, max_score=37,
             metadata=key_meta("pending", "Lückentext ohne Wörterliste und ohne Lösung im Buch — alle 37 Lücken nach dem Anhören in Lösung festlegen.")),
        base(L, "schreiben", 1, "Schreiben Teil 1: E-Mail — mein neues Auto", page=56, task_type="email",
             prompt="Sie haben ein neues Auto gekauft. Schreiben Sie eine E-Mail an Ihren Freund / Ihre Freundin. Beschreiben Sie, wie das neue Auto "
                    "ist, warum Sie es gekauft haben, und laden Sie ihn / sie ein, das Auto mit Ihnen auszuprobieren.",
             audience="Ihr Freund / Ihre Freundin (informell)", min_words=80, max_words=150, time_limit=25,
             ai_instructions="Musterlösung aus dem Buch (Referenz):\n" + MUSTER_AUTO, metadata={"musterloesung": MUSTER_AUTO}),
        base(L, "schreiben", 2, "Schreiben Teil 2: Meinung — Urlaub am Strand", page=57, task_type="opinion",
             prompt="Schreiben Sie Ihre Meinung zum Thema „Urlaub im Strand“.\n1. Beschreiben Sie, warum der Urlaub am Strand interessant ist.\n"
                    "2. Nennen Sie Vor- und Nachteile des Strandurlaubs.\n3. Geben Sie Ihre Meinung und Empfehlung.",
             audience="Forum / Online-Magazin", min_words=80, max_words=120, time_limit=25,
             ai_instructions="Musterlösung aus dem Buch (Referenz; enthält Fehler):\n" + MUSTER_STRAND, metadata={"musterloesung": MUSTER_STRAND}),
        base(L, "sprechen", 1, "Sprechen Teil 1: Gemeinsamer Plan — die Büros neu einrichten", page=58, topic="Die Büros neu einrichten",
             prompt="Sie arbeiten zusammen in einer Firma und haben von Ihrem Chef den Auftrag bekommen, die Büros neu einzurichten. Machen Sie "
                    "gemeinsam einen Plan und sprechen Sie über die folgenden Punkte.",
             questions=["Welche Möbel? — Welche Möbel brauchen wir?", "Wohin mit den alten Möbeln? — Verkaufen, verschenken oder spenden?",
                        "Was noch brauchen? — Welche Geräte und Dinge fehlen noch?", "Termin für die Präsentation — Wann präsentieren wir unseren Plan dem Chef?"],
             response_type="dialog", min_duration=60, max_duration=240, sample_answer=MUSTER_BUERO,
             speech_goal="Gemeinsam planen: Vorschläge machen, zustimmen, einen Termin vereinbaren.",
             keywords=["Ich finde", "Was hältst du von", "Gute Idee", "Einverstanden", "Ich schlage vor"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Präsentation — Wie viel Fernsehen ist gesund?", page=59, topic="Wie viel Fernsehen ist gesund?",
             prompt="Halten Sie eine Präsentation zum Thema „Wie viel fernsehen ist gesund“. Sprechen Sie 1,5 bis 2 Minuten. Tipps: Sprechen Sie klar und "
                    "deutlich. Verwenden Sie Beispiele. Nennen Sie Ihre eigene Meinung. Achten Sie auf die Zeit.",
             questions=["Erfahrung", "Situation", "Vorteile", "Nachteile", "Meinung / Fazit"],
             response_type="monolog", preparation_time=300, min_duration=90, max_duration=120, sample_answer=MUSTER_FERNSEHEN,
             speech_goal="Präsentation mit Erfahrung, Situation, Vor- und Nachteilen und Fazit.",
             keywords=["Heute spreche ich über", "Vorteile", "Nachteile", "Meiner Meinung nach", "Danke für Ihre Aufmerksamkeit"]),
        base(L, "wortschatz", 1, "Wortschatz: Wichtige Redewendungen für Modul 3", page=60, words=WORDS, exercises=meaning_sets(WORDS),
             auto_practice=False, metadata={"note": "Das Buch erklärt die Ausdrücke auf Deutsch (keine Übersetzung)."}),
        base(L, "uebungen", 1, "Übungen: B1 3. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 3. Unterricht", source="vizu",
             instruction="Abschlusstest zu Infinitiv mit zu und Redewendungen (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 3. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
