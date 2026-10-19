"""B1 1. Unterricht — Meine Freizeitaktivitäten — Grammatik: Kausale Angaben (book pp. 3-24).

Book: title p.3, Frage des Themas p.4, Grammatik weil / da p.5, denn / deshalb
p.6, deswegen / aufgrund + Genitiv p.7, Grammatik-Aufgaben 1-4 ("Vervollständige
die Sätze sinnvoll", open) pp.8-11, Lesen Aufgabe 1 (Alltagszufriedenheit,
richtig / falsch) p.12, Lesen Aufgabe 2 (kausale Konnektoren, LÖSUNG printed)
p.13, Lesen Aufgabe 3 (Am Wochenende, richtig / falsch) p.14, Hören Aufgabe 1
(Interview mit einem Fußballspieler, richtig / falsch) p.15, Hören Aufgabe 2
(Dialog Katrin / Ralf, Teil 1-2, the 12 missing words are printed under the
text) pp.16-17, Schreiben Aufgabe 1 (E-Mail, Musterlösung) p.18, Schreiben
Teil 2 (Meinung, Musterlösung) p.19, Sprechen Teil 1 (gemeinsam planen,
Musterlösung Dialog) pp.20-21, Sprechen Teil 2 (Präsentation, Musterlösung)
pp.22-23, Wichtige Redewendungen für Modul 1 p.24.

Keys: Lesen 2 and Hören 2 from the book; Lesen 1 and 3 decided by VIZU from
the text (held for verification in Lösung); Hören 1 only from the audio
(pending). Audio: "1.Unterricht Aufgabe 1.m4a" = Hören 1, "1.Unterricht
Aufgabe 2-3.m4a" = the Katrin / Ralf dialog (Hören Aufgabe 2, Teil 1 + 2).
Book p.6 says "Denn leitet einen Nebensatz ein" — kept as printed; the
examples show denn + Hauptsatz (verb in 2nd position)."""

from . import (
    base, completion, example_gap, exercise, gap, intro_html, key_meta, meaning_sets, mc, redewendungen, summary_html, tf,
)

L = 1
LESSON_TITLE = "Meine Freizeitaktivitäten"
LESSON_DESCRIPTION = "Thema: Meine Freizeitaktivitäten · Grammatik: Kausale Angaben (weil, da, denn, deshalb, deswegen, aufgrund + Genitiv)"
AUDIO = {"vizu-b1-l01-hoeren-01": "1.Unterricht Aufgabe 1.m4a", "vizu-b1-l01-hoeren-02": "1.Unterricht Aufgabe 2-3.m4a"}

EINFUEHRUNG_HTML = intro_html(
    1, "Meine Freizeitaktivitäten", "Kausale Angaben (weil, da, denn, deshalb, deswegen, aufgrund + Genitiv)",
    ["sababni turli bog'lovchilar bilan aytish: weil / da (ergash gap), denn, deshalb / deswegen, aufgrund + Genitiv;",
     "bo'sh vaqt mashg'ulotlari haqida gapirish va yozish;",
     "muhim iboralar: sich interessieren für, Angst haben vor, sich kümmern um …"],
    ["bo'sh vaqtingizni qanday o'tkazishingizni sababi bilan aytasiz;",
     "Germaniyadagi kundalik hayotdan qoniqish haqidagi matnni tushunasiz;",
     "futbolchi bilan intervyu va do'stlar dialogini tinglab tushunasiz;",
     "do'stingizga e-mail va forumga o'z fikringizni yozasiz;",
     "sherigingiz bilan taqdimot rejalashtirasiz va mavzu bo'yicha taqdimot qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(1, [
    "<strong>weil</strong>: Hauptsatz + weil + Nebensatz (Verb am Ende) — Ich gehe ins Fitnessstudio, weil ich gesund bleiben möchte.",
    "<strong>da</strong>: Da + Nebensatz, Hauptsatz — Da es regnet, bleiben wir heute zu Hause.",
    "<strong>denn</strong>: Hauptsatz + denn + Hauptsatz — Ich gehe heute früher schlafen, denn ich bin sehr müde.",
    "<strong>deshalb / deswegen</strong>: die Folge — Es hat stark geregnet, deshalb ist das Spiel ausgefallen.",
    "<strong>aufgrund + Genitiv</strong>: Aufgrund des schlechten Wetters bleiben wir zu Hause.",
    "<strong>Redewendungen:</strong> einen Wunsch haben, in Anspruch nehmen, zur Verfügung stehen, Rücksicht nehmen auf, sich interessieren für, "
    "sich kümmern um, Angst haben vor, sich vorbereiten auf, verantwortlich sein für, die Möglichkeit haben.",
])

GRAMMAR_WEIL_DA = (
    "<h3>Grammatik: Kausale Angaben — weil / da</h3>"
    "<table><thead><tr><th>WEIL</th><th>DA</th></tr></thead><tbody>"
    "<tr><td>Weil leitet einen Nebensatz ein. Der Grund kommt NACH dem Hauptsatz.</td>"
    "<td>Da leitet einen Nebensatz ein. Der Grund kommt VOR dem Hauptsatz.</td></tr>"
    "<tr><td><strong>Hauptsatz + weil + Nebensatz</strong></td><td><strong>Da + Nebensatz + Hauptsatz</strong></td></tr>"
    "<tr><td>01 Ich gehe ins Fitnessstudio, weil ich gesund bleiben möchte.<br>"
    "02 Ich lerne Deutsch, weil ich später in Deutschland studieren möchte.<br>"
    "03 Ich bin mit dem Fahrrad zur Arbeit gefahren, weil das Wetter schön war.</td>"
    "<td>01 Da ich morgen früh aufstehe, gehe ich heute früher schlafen.<br>02 Da es regnet, bleiben wir heute zu Hause.<br>"
    "03 Da ich viel zu tun habe, kann ich heute nicht mitkommen.</td></tr></tbody></table>"
)
GRAMMAR_DENN_DESHALB = (
    "<h3>Grammatik: Kausale Angaben — denn / deshalb</h3>"
    "<table><thead><tr><th>DENN</th><th>DESHALB</th></tr></thead><tbody>"
    "<tr><td>Denn leitet einen Nebensatz ein. Der Grund kommt NACH dem Hauptsatz.</td>"
    "<td>Deshalb leitet einen Hauptsatz ein. Die Folge (Ergebnis) kommt NACH dem Grund.</td></tr>"
    "<tr><td><strong>Struktur:</strong> Hauptsatz + denn + Nebensatz</td><td><strong>Struktur:</strong> Deshalb + Hauptsatz + Begründung</td></tr>"
    "<tr><td>01 Ich gehe heute früher schlafen, denn ich bin sehr müde.<br>02 Wir nehmen den Zug, denn es gibt heute Streik.<br>"
    "03 Er lernt jeden Tag Deutsch, denn er möchte in Deutschland studieren.</td>"
    "<td>01 Ich habe viel gearbeitet, deshalb habe ich gute Noten.<br>02 Es hat stark geregnet, deshalb ist das Spiel ausgefallen.<br>"
    "03 Ich habe mein Handy zu Hause vergessen, deshalb bin ich ohne Handy zur Schule gegangen.</td></tr></tbody></table>"
    "<p><em>Hinweis:</em> Nach <strong>denn</strong> steht das Verb auf Position 2 (wie im Hauptsatz): … denn ich <strong>bin</strong> sehr müde. "
    "Nach <strong>deshalb</strong> folgt direkt das Verb: deshalb <strong>habe</strong> ich gute Noten.</p>"
)
GRAMMAR_DESWEGEN_AUFGRUND = (
    "<h3>Grammatik: Kausale Angaben — deswegen / aufgrund + Genitiv</h3>"
    "<table><thead><tr><th>DESWEGEN</th><th>AUFGRUND + GENITIV</th></tr></thead><tbody>"
    "<tr><td>Deswegen leitet einen Hauptsatz ein. Die Folge (Ergebnis) kommt daraus.</td>"
    "<td>Aufgrund + Genitiv leitet einen Nebensatz ein. Der Grund steht im Vordergrund.</td></tr>"
    "<tr><td><strong>Struktur:</strong> Deswegen + Hauptsatz</td><td><strong>Struktur:</strong> Aufgrund + Genitiv + Nebensatz</td></tr>"
    "<tr><td>01 Es hat geregnet, deswegen bleibt das Spiel aus.<br>02 Ich habe viel zu tun, deswegen kann ich heute nicht mitkommen.<br>"
    "03 Die Straßen sind voll, deswegen komme ich später nach Hause.</td>"
    "<td>01 Aufgrund des schlechten Wetters bleiben wir zu Hause.<br>02 Aufgrund der hohen Preise kaufen viele Menschen weniger ein.<br>"
    "03 Aufgrund meines vollen Terminkalenders habe ich wenig Zeit für Hobbys.</td></tr></tbody></table>"
)

# ---------- Lesen ----------
TEXT_ALLTAG = (
    "Eine Umfrage zur Alltagszufriedenheit in Deutschland ergab, dass 76 Prozent der Deutschen mit ihrem Alltag zufrieden sind. Besonders wichtig "
    "fanden die Befragten, dass der Alltag abwechslungsreich ist. Außerdem spielt das Gefühl, sein Leben selbst bestimmen zu können, eine wichtige "
    "Rolle. Einen großen Einfluss auf die Zufriedenheit haben auch eine sinnvolle Tätigkeit und die Anerkennung von anderen Menschen. "
    "Überraschenderweise liegen materielle Aspekte wie die finanzielle Situation der Umfrageteilnehmer nicht auf den vorderen Plätzen, sie kamen nur "
    "auf Platz neun.\n\nZu den Dingen, die die Deutschen im Alltag nerven, gehören ungeliebte Tätigkeiten im Haushalt, Verspätungen bei öffentlichen "
    "Verkehrsmitteln und Staus.")
LESEN_1 = [
    tf("Etwa drei Viertel der Deutschen sind mit ihrem Alltag zufrieden.", True, "„… dass 76 Prozent der Deutschen mit ihrem Alltag zufrieden sind.“"),
    tf("Abwechslung und Selbstbestimmung spielen bei der Zufriedenheit der Menschen eine große Rolle.", True,
       "„Besonders wichtig fanden die Befragten, dass der Alltag abwechslungsreich ist. Außerdem spielt das Gefühl, sein Leben selbst bestimmen zu "
       "können, eine wichtige Rolle.“"),
    tf("Nur wenn man viel Geld verdient, ist man glücklich.", False,
       "„… materielle Aspekte wie die finanzielle Situation … liegen nicht auf den vorderen Plätzen, sie kamen nur auf Platz neun.“"),
    tf("Hausarbeit ist für viele Befragte wichtig.", False, "„Zu den Dingen, die die Deutschen im Alltag nerven, gehören ungeliebte Tätigkeiten im Haushalt …“"),
    tf("Über Staus und Verspätungen ärgern sich viele.", True, "„… nerven … Verspätungen bei öffentlichen Verkehrsmitteln und Staus.“"),
]

KONNEKTOREN = ["weil", "da", "denn", "deshalb", "deswegen", "aus diesem Grund", "aufgrund"]
LESEN_2_ROWS = [
    ("Ich verbringe meine Freizeit oft draußen. [[1]] ich nach der Arbeit Entspannung brauche, gehe ich im Park spazieren.", "weil"),
    ("Meine Freunde spielen jedes Wochenende Fußball. Ich spiele auch mit, [[1]] Sport gesund ist und viel Spaß macht.", "denn"),
    ("Am Samstag hat es den ganzen Tag geregnet. [[1]] konnten wir nicht wandern.", "deshalb"),
    ("[[1]] des schlechten Wetters blieben wir zu Hause und spielten Brettspiele.", "aufgrund"),
    ("Meine Schwester liest jeden Abend Romane, [[1]] sie spannende Geschichten liebt.", "da"),
    ("Ich wollte gestern schwimmen gehen. Das Schwimmbad war jedoch geschlossen. [[1]] bin ich ins Fitnessstudio gegangen.", "deswegen"),
    ("Viele Menschen verbringen ihre Freizeit aktiv. [[1]] sie regelmäßig Sport treiben, fühlen sie sich gesünder und haben mehr Energie.", "aus diesem Grund"),
    ("Ich lerne jeden Tag Deutsch, [[1]] ich später in Deutschland studieren möchte.", "weil"),
    ("[[1]] meines vollen Terminkalenders finde ich am Wochenende trotzdem Zeit für meine Hobbys.", "aufgrund"),
    ("Am Sonntag hatten wir schönes Wetter. [[1]] machten wir ein Picknick am See.", "deshalb"),
]
LESEN_2 = [gap(f"{n}. Ergänzen Sie den passenden Konnektor.", s, {"1": {"accepted": [a], "options": KONNEKTOREN}},
               explanation=f"LÖSUNG (Buch): {a}")
           for n, (s, a) in enumerate(LESEN_2_ROWS, start=1)]

TEXT_WOCHENENDE = (
    "Am Wochenende versuche ich, mich von der stressigen Woche zu erholen. Normalerweise stehe ich nicht so früh auf, weil ich etwas länger schlafen "
    "möchte. Nach dem Frühstück räume ich mein Zimmer auf und helfe meinen Eltern im Haushalt.\n\nAm Samstagnachmittag treffe ich mich oft mit "
    "meinen Freunden. Manchmal gehen wir ins Kino oder spielen Fußball im Park. Wenn das Wetter schlecht ist, bleiben wir zu Hause und schauen einen "
    "Film oder spielen Gesellschaftsspiele.\n\nDer Sonntag ist für mich etwas ruhiger. Ich lese gern Bücher oder lerne Deutsch, weil ich meine "
    "Sprachkenntnisse verbessern möchte. Außerdem bereite ich mich auf die neue Woche vor und plane meine wichtigsten Aufgaben. Am Abend verbringe ich "
    "noch etwas Zeit mit meiner Familie, bevor ich früh ins Bett gehe.")
LESEN_3 = [
    tf("Der Autor steht am Wochenende immer sehr früh auf.", False, "„Normalerweise stehe ich nicht so früh auf …“"),
    tf("Am Samstag trifft sich der Autor oft mit seinen Freunden.", True, "„Am Samstagnachmittag treffe ich mich oft mit meinen Freunden.“"),
    tf("Bei schlechtem Wetter spielen sie Fußball im Park.", False,
       "„Wenn das Wetter schlecht ist, bleiben wir zu Hause und schauen einen Film oder spielen Gesellschaftsspiele.“"),
    tf("Am Sonntag lernt der Autor Deutsch, um seine Sprachkenntnisse zu verbessern.", True,
       "„Ich lese gern Bücher oder lerne Deutsch, weil ich meine Sprachkenntnisse verbessern möchte.“"),
    tf("Der Autor plant am Sonntag die Aufgaben für die neue Woche.", True, "„… bereite ich mich auf die neue Woche vor und plane meine wichtigsten Aufgaben.“"),
    tf("Am Sonntagabend arbeitet der Autor bis spät in die Nacht.", False,
       "„Am Abend verbringe ich noch etwas Zeit mit meiner Familie, bevor ich früh ins Bett gehe.“"),
]

# ---------- Hören ----------
HOEREN_1 = [
    tf("Die Mannschaft von Franz hat heute drei Punkte gewonnen.", None),
    tf("Franz hat ein kaputtes Bein.", None),
    tf("Franz war mit der Leistung des Schiedsrichters nicht zufrieden.", None),
    tf("Franz möchte gern für einen englischen Verein spielen, hat aber noch kein Angebot bekommen.", None),
    tf("Borussia Dortmund wird in diesem Jahr deutscher Meister.", None),
    tf("Franz tut etwas für die Jugendarbeit in seiner Heimatstadt.", None),
]

DIALOG_1 = (
    "Katrin und Ralf haben sich auf einer Geburtstagsparty bei gemeinsamen Freunden kennengelernt. Sie waren sich sehr sympathisch und haben sich für "
    "Samstagabend in einer Kneipe verabredet. Ralf sitzt schon an einem Tisch, als Katrin mit kleiner [[1]] eintrifft.\n"
    "Ralf: Katrin, hier! Hey, da bist du ja! Schön, dich zu sehen!\n"
    "Katrin: Oh, tut mir so leid, Ralf! Ich habe ganz knapp meine Trambahn verpasst! Und die nächste kam erst zehn Minuten später.\n"
    "Ralf: Ach, kein Problem, ich war auch nicht ganz [[2]]. Jetzt entspann dich erst einmal. Möchtest du auch ein Glas Rotwein?\n"
    "Katrin: Ja, gerne. Ist deiner gut? Schön trocken?\nRalf: Ja, mir schmeckt er. Da, probier doch mal!\n"
    "Katrin: Wenn ich darf? Mmh, lecker. Den nehme ich auch.\n"
    "Ralf: Noch einen [[3]] von dem Rotwein, bitte! Super, dass es heute Abend geklappt hat! Letztes Mal hatten wir ja nicht viel Zeit zum Reden.\n"
    "Katrin: Klar, das war ja auch [[4]]. Aber jetzt erzähl mir doch noch mal, was du beruflich machst. Das habe ich auf der Party nicht so richtig "
    "verstanden.\n"
    "Ralf: Ach, das ist nicht so schwierig. Ich bin selbstständig und arbeite als Übersetzer für verschiedene [[5]]. Gerade übersetze ich ein "
    "Jugendbuch aus dem Englischen.\nKatrin: Du sprichst dann sicher fließend Englisch, oder?\n"
    "Ralf: Ja, sonst wär's schwierig! Aber Sprachen waren schon immer mein [[6]]. Ich kann auch Französisch, Spanisch und Italienisch. Und du?")
DIALOG_2 = (
    "Katrin: Oh nein, da bin ich nicht gut. Englisch geht gerade so, aber mein Schulfranzösisch versteht in Frankreich keiner. Meine Leidenschaft ist "
    "mehr der Sport!\nRalf: Stimmt, du hast ja erzählt, dass du [[7]] bist. Was machst du denn am liebsten?\n"
    "Katrin: Reiten ist mein [[8]]. Wenn das nur nicht so teuer wäre! Aber ich fahre auch gern Rad, schwimme und [[9]] gern und gehe oft zum Joggen. "
    "Und im Winter natürlich Skifahren und Langlaufen!\nRalf: Wann hast du denn noch Zeit zum Arbeiten?\n"
    "Katrin: Tja, da habe ich wirklich Glück. Ich arbeite in der Praxis meiner Mutter und bin deshalb ein wenig [[10]] in meinen Arbeitszeiten. Aber "
    "das ist bei dir doch sicher auch so? Du bist doch selbstständig!\n"
    "Ralf: Na ja schon, aber ich muss rechtzeitig fertig sein, damit ich wieder neue [[11]] bekomme.\n"
    "Katrin: Klar, das verstehe ich. Man muss sicherlich sehr diszipliniert sein, wenn man allein zu Hause arbeitet. Du lebst doch allein, oder?\n"
    "Ralf: Nicht ganz, ich wohne mit meiner kleinen Schwester in einer WG. Sie ist gerade bei meinen Eltern ausgezogen und wollte nicht allein in "
    "einer fremden Stadt leben. Ich mag sie sehr – du wirst sie ja bald kennenlernen!\nKatrin: Ach, ja?\n"
    "Ralf: Äh ja, ich meine, wenn du willst! Du könntest mich ja mal besuchen – ich kann wirklich gut [[12]]!\n"
    "Katrin: Na, das ist doch ein Angebot! Wie wär's mit Samstag in acht Tagen?\n"
    "Ralf: (etwas überrascht) Okay! Das müsste passen! Was isst du denn gerne? …")
DIALOG_KEY = {"1": "Verspätung", "2": "pünktlich", "3": "Viertelliter", "4": "Werners Geburtstag", "5": "Verlage", "6": "Hobby",
              "7": "Physiotherapeutin", "8": "Lieblingssport", "9": "segle", "10": "flexibel", "11": "Aufträge", "12": "kochen"}


def _filled(text: str) -> str:
    for k, v in DIALOG_KEY.items():
        text = text.replace(f"[[{k}]]", v)
    return text


HOEREN_2 = [
    gap("Teil 1: Hören Sie den Dialog und ergänzen Sie den Text. Schreiben Sie die fehlenden Wörter in die Lücken.", DIALOG_1,
        {k: [DIALOG_KEY[k]] for k in "123456"}, points=6, explanation="Lösung (Buch, S. 16): " + ", ".join(f"{k}. {DIALOG_KEY[k]}" for k in "123456")),
    gap("Teil 2: Hören Sie den Dialog und ergänzen Sie den Text. Schreiben Sie die fehlenden Wörter in die Lücken.", DIALOG_2,
        {k: [DIALOG_KEY[k]] for k in ("7", "8", "9", "10", "11", "12")}, points=6,
        explanation="Lösung (Buch, S. 17): " + ", ".join(f"{k}. {DIALOG_KEY[k]}" for k in ("7", "8", "9", "10", "11", "12"))),
]

# ---------- Schreiben / Sprechen ----------
MUSTER_EMAIL = (
    "Betreff: Mein neuer Laptop\n\nLiebe Anna,\nwie geht es dir? Ich hoffe, dir geht es gut. Mir geht es sehr gut.\nIch möchte dir eine schöne "
    "Nachricht erzählen. Ich habe mir einen neuen Laptop gekauft, weil ich ihn für mein Studium und meine Arbeit brauche.\nMein Laptop ist von der "
    "Marke HP. Er ist silberfarben, hat einen 15-Zoll-Bildschirm und 500 GB Speicherplatz. Ich finde ihn sehr modern und praktisch. Er wird mir bei "
    "meiner Arbeit wirklich helfen und meine Aufgaben schneller und professioneller machen.\nHast du am Freitagabend Zeit? Wir können uns treffen und "
    "den neuen Laptop gemeinsam ausprobieren. Ich freue mich schon sehr auf unser Treffen.\nLiebe Grüße\nDein Freund")
LAURA = ("(12.10. 18:30) Laura: Ich finde es sehr sinnvoll, dass Kinder schon im Kindergarten Fremdsprachen lernen. In diesem Alter lernen sie besonders "
         "schnell und haben keine Angst davor, Fehler zu machen. So können sie später leichter weitere Sprachen lernen und bessere Chancen im Beruf "
         "haben. Natürlich sollte aber auch genügend Zeit für die Muttersprache bleiben.")
MUSTER_MEINUNG = (
    "Ich stimme Laura größtenteils zu. Fremdsprachen im Kindergarten können Kindern viele Vorteile bringen. In jungen Jahren sind Kinder sehr offen und "
    "lernen neue Wörter und Ausdrücke fast spielerisch. Besonders durch Lieder, Spiele und Geschichten macht das Lernen Spaß und bleibt lange im "
    "Gedächtnis. Außerdem haben die Kinder später in der Schule weniger Schwierigkeiten und bessere Chancen im Beruf, weil sie mehrsprachig sind.\n"
    "Trotzdem sollten wir nicht vergessen, wie wichtig die Muttersprache ist. Kinder müssen ihre eigene Sprache gut beherrschen, um richtig denken, "
    "fühlen und sich ausdrücken zu können. Deshalb sollte im Kindergarten ein gutes Gleichgewicht zwischen der Fremdsprache und der Muttersprache "
    "gefunden werden.\nZusammenfassend finde ich, dass Fremdsprachen im Kindergarten eine sehr gute Idee sind, wenn sie kindgerecht und in Maßen "
    "vermittelt werden.")
MUSTER_PLANEN = (
    "1. Welche Stadt? — Kandidat 1: Ich würde gern Berlin präsentieren. Berlin ist die Hauptstadt Deutschlands und eine sehr große und interessante "
    "Stadt. Dort gibt es viele Sehenswürdigkeiten, Parks, Museen und kulturelle Veranstaltungen. — Kandidat 2: Ich finde Berlin auch eine gute Wahl. "
    "Über Berlin haben wir viel zu berichten. Die Stadt hat eine spannende Geschichte und ist heute ein wichtiges Zentrum für Politik, Kultur, "
    "Wissenschaft und Wirtschaft.\n"
    "2. Welche Informationen? — Kandidat 1: Ich kenne einen Bekannten, der in Berlin lebt. Er kann uns bestimmt viele Tipps und Informationen geben. "
    "Wir können ihn über das Leben in Berlin, die Arbeitsmöglichkeiten und die Freizeitangebote fragen. — Kandidat 2: Außerdem können wir im Internet "
    "recherchieren. Dort finden wir viele Informationen über die Bevölkerung, die Wirtschaft, die Geschichte, das Wetter, das Verkehrssystem und vieles "
    "mehr.\n"
    "3. Wer macht was? — Kandidat 1: Ich glaube, ich kann die Hauptinformationen sammeln und den Text schreiben. Ich kümmere mich um die Fakten über "
    "Bevölkerung, Wirtschaft und Sehenswürdigkeiten. — Kandidat 2: Ich kümmere mich um die Bilder. Ich suche schöne Fotos von Berlin herunter, "
    "bearbeite sie und füge sie in die Präsentation ein. Außerdem kann ich die Informationen über Geschichte und Kultur vorbereiten.\n"
    "4. Welche Materialien? — Kandidat 1: Für unsere Präsentation brauchen wir einen Beamer, einen Lautsprecher, einen Laptop und natürlich eine "
    "stabile Internetverbindung. — Kandidat 2: Ja, und wir sollten auch Stifte, Papier und eventuell Karten oder Diagramme vorbereiten. So wird "
    "unsere Präsentation anschaulich und interessant.")
MUSTER_PRAESENTATION = (
    "Erfahrung: Ich fahre jeden Tag mit öffentlichen Verkehrsmitteln zur Schule, aber manchmal fährt mich mein Vater mit dem Auto. Mit dem Bus oder der "
    "Straßenbahn bin ich meistens schneller im Stadtzentrum, besonders wenn viel Verkehr ist.\n"
    "Situation: In meiner Stadt nutzen die meisten Menschen öffentliche Verkehrsmittel wie Bus, Straßenbahn und U-Bahn. Sie sind günstig und "
    "praktisch. Trotzdem gibt es auch viele Autos auf den Straßen, besonders zu den Stoßzeiten. Dann gibt es oft Staus und die Luft ist nicht mehr so "
    "sauber.\n"
    "Vorteile: Mit dem Auto kann man die Überfüllung im öffentlichen Verkehr vermeiden. Man ist flexibler und kann sein Ziel schnell erreichen. Im "
    "Auto fühlt man sich auch ungestört, man kann Musik hören oder telefonieren. Öffentliche Verkehrsmittel sind dagegen günstiger, "
    "umweltfreundlicher und man muss sich keine Sorgen um Parkplätze machen.\n"
    "Nachteile: Mit dem Auto muss man für Benzin, Reparaturen und Versicherung viel Geld ausgeben. Außerdem stoßen Autos Abgase aus und verursachen "
    "Staus. Öffentliche Verkehrsmittel sind manchmal überfüllt, besonders zu den Stoßzeiten, und wenn es Verspätungen gibt, kommt man nicht pünktlich "
    "an.\n"
    "Meinung: Meiner Meinung nach sind öffentliche Verkehrsmittel in einer Stadt die bessere Wahl, weil sie bequem, sicher und umweltfreundlich sind. "
    "Natürlich braucht man manchmal ein Auto, aber man sollte es nur dann benutzen, wenn es wirklich nötig ist.")

# ---------- Wortschatz ----------
WORDS = redewendungen([
    ("einen Wunsch haben", "eine Sehnsucht oder einen Herzenswunsch haben", "Ich habe den Wunsch, einmal die Welt zu bereisen."),
    ("in Anspruch nehmen", "etwas nutzen oder verwenden", "Viele Menschen nehmen diese Möglichkeit in Anspruch."),
    ("zur Verfügung stehen", "bereit sein, genutzt zu werden", "Mein Bruder steht mir immer mit Rat und Tat zur Verfügung."),
    ("Rücksicht nehmen auf + Akk.", "jemanden oder etwas berücksichtigen", "Wir sollten mehr Rücksicht auf ältere Menschen nehmen."),
    ("sich interessieren für + Akk.", "Interesse an etwas haben", "Ich interessiere mich sehr für andere Kulturen."),
    ("sich kümmern um + Akk.", "sich um jemanden oder etwas sorgen", "Meine Mutter kümmert sich immer um unsere Familie."),
    ("Angst haben vor + Dat.", "Furcht oder Besorgnis haben", "Ich habe Angst vor Prüfungen."),
    ("sich vorbereiten auf + Akk.", "sich im Voraus auf etwas einstellen", "Ich bereite mich auf die Prüfung gut vor."),
    ("verantwortlich sein für + Akk.", "die Verantwortung für etwas haben", "Er ist verantwortlich für das Projekt."),
    ("die Möglichkeit haben", "eine Gelegenheit oder Chance besitzen", "Wir haben die Möglichkeit, an einem Austauschprogramm teilzunehmen."),
], "Wichtige Redewendungen für Modul 1")

_K = ["weil", "deshalb", "denn"]
UEBUNGEN = [
    exercise("Welcher Konnektor passt? (Beispielsätze aus dem Buch)", [
        example_gap("Ich gehe ins Fitnessstudio, ___ ich gesund bleiben möchte.", "weil", _K, "Verb am Ende (möchte) → weil."),
        example_gap("Es hat stark geregnet, ___ ist das Spiel ausgefallen.", "deshalb", _K, "Verb direkt danach (ist) → deshalb."),
        example_gap("Wir nehmen den Zug, ___ es gibt heute Streik.", "denn", _K, "Verb auf Position 2 nach dem Subjekt (es gibt) → denn."),
        example_gap("___ es regnet, bleiben wir heute zu Hause.", "Da", ["Da", "Deshalb", "Denn"], "Da + Nebensatz, Hauptsatz."),
        example_gap("___ des schlechten Wetters bleiben wir zu Hause.", "Aufgrund", ["Aufgrund", "Weil", "Deswegen"], "aufgrund + Genitiv (des Wetters)."),
        example_gap("Die Straßen sind voll, ___ komme ich später nach Hause.", "deswegen", ["deswegen", "weil", "aufgrund"], "deswegen + Verb (komme)."),
        example_gap("Ich lerne Deutsch, ___ ich später in Deutschland studieren möchte.", "weil", _K),
        example_gap("Ich gehe heute früher schlafen, ___ ich bin sehr müde.", "denn", _K),
        example_gap("Aufgrund ___ hohen Preise kaufen viele Menschen weniger ein.", "der", ["der", "die", "den"], "aufgrund + Genitiv Plural: der Preise."),
        example_gap("Aufgrund ___ vollen Terminkalenders habe ich wenig Zeit für Hobbys.", "meines", ["meines", "meinem", "meinen"],
                    "Genitiv maskulin: meines Terminkalenders."),
    ], "Wählen Sie den passenden Konnektor. Alle Sätze stammen aus der Grammatik des Buches (S. 5-7).", source="vizu"),
]

ABSCHLUSSTEST = [
    example_gap("Ich bin mit dem Fahrrad zur Arbeit gefahren, ___ das Wetter schön war.", "weil", _K),
    example_gap("___ ich viel zu tun habe, kann ich heute nicht mitkommen.", "Da", ["Da", "Deshalb", "Denn"]),
    example_gap("Er lernt jeden Tag Deutsch, ___ er möchte in Deutschland studieren.", "denn", _K),
    example_gap("Ich habe viel gearbeitet, ___ habe ich gute Noten.", "deshalb", _K),
    example_gap("Ich habe Angst ___ Prüfungen.", "vor", ["vor", "für", "auf"], "Angst haben vor + Dativ."),
    example_gap("Ich interessiere mich sehr ___ andere Kulturen.", "für", ["für", "um", "auf"], "sich interessieren für + Akkusativ."),
    example_gap("Meine Mutter kümmert sich immer ___ unsere Familie.", "um", ["um", "für", "vor"], "sich kümmern um + Akkusativ."),
    example_gap("Ich bereite mich ___ die Prüfung gut vor.", "auf", ["auf", "für", "um"], "sich vorbereiten auf + Akkusativ."),
    example_gap("Wir sollten mehr Rücksicht ___ ältere Menschen nehmen.", "auf", ["auf", "für", "vor"], "Rücksicht nehmen auf + Akkusativ."),
    mc("Wie viel Prozent der Deutschen sind laut Umfrage mit ihrem Alltag zufrieden?", ["76 Prozent", "56 Prozent", "96 Prozent"], "A",
       "Lesen Aufgabe 1: „… dass 76 Prozent der Deutschen mit ihrem Alltag zufrieden sind.“"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 1. Unterricht", source="vizu", page=3, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Meine Freizeitaktivitäten", page=4,
             prompt="Das Thema: Meine Freizeitaktivitäten. Denke nach, diskutiere und teile deine Meinung!",
             questions=["Welche Freizeitaktivitäten machst du am liebsten?", "Wie verbringst du deine Freizeit meistens?",
                        "Warum ist Freizeit für dich wichtig?"], min_duration=20, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Kausale Angaben", page="5-7",
             rules=[{"title": "Kausale Angaben: weil / da", "html": GRAMMAR_WEIL_DA},
                    {"title": "Kausale Angaben: denn / deshalb", "html": GRAMMAR_DENN_DESHALB},
                    {"title": "Kausale Angaben: deswegen / aufgrund + Genitiv", "html": GRAMMAR_DESWEGEN_AUFGRUND}],
             metadata={"note": "S. 6 druckt „Denn leitet einen Nebensatz ein“ — so übernommen; die Beispiele zeigen denn + Hauptsatz."}),
        completion(L, 3, "Grammatik Aufgabe 1: denn / deshalb", 8, "Vervollständige die Sätze sinnvoll (denn / deshalb).", [
            "Ich lerne jeden Tag Deutsch, denn", "Es regnet heute stark, deshalb", "Meine Freundin ist krank, denn",
            "Ich habe morgen eine wichtige Prüfung, deshalb", "Wir fahren mit dem Bus, denn", "Mein Handy funktioniert nicht mehr, deshalb",
            "Ich gehe heute früh schlafen, denn", "Die Straßen sind sehr voll, deshalb", "Sara macht regelmäßig Sport, denn",
            "Ich habe viel gearbeitet, deshalb"]),
        completion(L, 4, "Grammatik Aufgabe 2: weil / da", 9, "Vervollständige die Sätze sinnvoll (weil / da).", [
            "Ich bin heute glücklich, weil", "Da das Wetter schön ist,", "Wir können heute nicht schwimmen gehen, weil",
            "Da ich morgen früh aufstehen muss,", "Viele Menschen lernen Englisch, weil", "Ich bleibe heute zu Hause, weil",
            "Da meine Eltern Besuch bekommen,", "Er kauft ein neues Fahrrad, weil", "Da ich keine Zeit habe,", "Wir trinken heute viel Wasser, weil"]),
        completion(L, 5, "Grammatik Aufgabe 3: deswegen / aufgrund + Genitiv", 10, "Vervollständige die Sätze sinnvoll (deswegen / aufgrund + Genitiv).", [
            "Ich habe starke Kopfschmerzen, deswegen", "Aufgrund des schlechten Wetters", "Mein Zug hatte Verspätung, deswegen",
            "Aufgrund der hohen Preise", "Ich habe gestern wenig geschlafen, deswegen", "Aufgrund eines technischen Problems",
            "Die Prüfung war sehr schwer, deswegen", "Aufgrund des starken Verkehrs", "Mein Laptop ist kaputt, deswegen",
            "Aufgrund meiner wichtigen Termine"]),
        completion(L, 6, "Grammatik Aufgabe 4: Kausale Konnektoren gemischt", 11, "Vervollständige die Sätze sinnvoll (kausale Konnektoren gemischt).", [
            "Ich lerne intensiv Deutsch, weil", "Es regnet heute stark, deshalb", "Aufgrund des vielen Schnees", "Da meine Freundin Geburtstag hat,",
            "Wir bleiben heute zu Hause, denn", "Ich habe morgen frei, deswegen", "Aufgrund der Prüfung nächste Woche", "Ich trinke viel Wasser, weil",
            "Die Bahn hatte Verspätung, deshalb", "Da ich am Wochenende Zeit habe,"]),
        base(L, "lesen", 1, "Lesen Aufgabe 1: Alltagszufriedenheit in Deutschland", page=12,
             instruction="a) Lesen Sie den Text und machen Sie Aufgabe b. b) Was steht im Text? Sind die Aussagen richtig oder falsch? Kreuzen Sie an.",
             passages=[{"title": "Alltagszufriedenheit in Deutschland", "text": TEXT_ALLTAG}], questions=LESEN_1, max_score=len(LESEN_1),
             metadata=key_meta("vizu")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: Kausale Konnektoren", page=13,
             instruction="Ergänzen Sie die Sätze mit: weil • da • denn • deshalb • deswegen • aus diesem Grund • aufgrund (+ Genitiv).",
             passages=[{"title": "Lesen Aufgabe 2 — Kausale Konnektoren",
                        "text": "weil • da • denn • deshalb • deswegen • aus diesem Grund • aufgrund (+ Genitiv)\n\n"
                                "Lesen Sie die Sätze und ergänzen Sie den passenden Konnektor."}],
             questions=LESEN_2, max_score=len(LESEN_2), metadata=key_meta("book", "Lösung im Buch gedruckt (S. 13).")),
        base(L, "lesen", 3, "Lesen Aufgabe 3: Am Wochenende", page=14, instruction="Lesen Sie den Text. Richtig oder Falsch?",
             passages=[{"title": "Am Wochenende", "text": TEXT_WOCHENENDE}], questions=LESEN_3, max_score=len(LESEN_3), metadata=key_meta("vizu")),
        base(L, "hoeren", 1, "Hören Aufgabe 1: Ein Interview mit einem Fußballspieler", page=15, audio_file=AUDIO["vizu-b1-l01-hoeren-01"],
             key_pending=True,
             instruction="Hören Sie ein Interview mit dem Fußballspieler Franz Bauer. Stimmen die Aussagen mit dem Text überein? Kreuzen Sie an.",
             questions=HOEREN_1, max_score=len(HOEREN_1),
             metadata=key_meta("pending", "Kein Lösungsschlüssel im Buch — Antworten nach dem Anhören in Lösung festlegen.")),
        base(L, "hoeren", 2, "Hören Aufgabe 2: Katrin und Ralf in der Kneipe", page="16-17", audio_file=AUDIO["vizu-b1-l01-hoeren-02"],
             instruction="Hören Sie den Dialog und ergänzen Sie den Text. Schreiben Sie die fehlenden Wörter in die Lücken.",
             transcript=_filled(DIALOG_1) + "\n" + _filled(DIALOG_2), questions=HOEREN_2, max_score=12,
             metadata=key_meta("book", "Die 12 Lösungswörter stehen im Buch unter dem Text (S. 16-17). Audio-Datei „Aufgabe 2-3“ = Teil 1 + Teil 2.")),
        base(L, "schreiben", 1, "Schreiben Aufgabe 1: E-Mail an Anna — mein neuer Laptop", page=18, task_type="email",
             prompt="Sie haben einen neuen Laptop gekauft. Schreiben Sie eine E-Mail an Ihre Freundin Anna.\n\nSchreiben Sie etwas zu den folgenden "
                    "Punkten:\n1. Warum haben Sie einen neuen Laptop gekauft?\n2. Beschreiben Sie den Laptop.\n3. Laden Sie Anna ein, den Laptop "
                    "gemeinsam anzuschauen.\n\nSchreiben Sie ca. 80–100 Wörter. Vergessen Sie nicht Anrede und Gruß!",
             audience="Ihre Freundin Anna (informell)", min_words=80, max_words=110, time_limit=20,
             ai_instructions="Musterlösung aus dem Buch (Referenz, nicht wörtlich verlangen):\n" + MUSTER_EMAIL,
             metadata={"musterloesung": MUSTER_EMAIL}),
        base(L, "schreiben", 2, "Schreiben Teil 2: Fremdsprachen im Kindergarten", page=19, task_type="opinion",
             prompt="Sie haben im Fernsehen eine Diskussionssendung zum Thema „Fremdsprachen im Kindergarten“ gesehen. Im Online-Gästebuch der "
                    "Sendung finden Sie folgende Meinung:\n\n" + LAURA + "\n\nSchreiben Sie nun Ihre Meinung (circa 80 Wörter).",
             audience="Online-Gästebuch einer Fernsehsendung", min_words=70, max_words=120, time_limit=25,
             ai_instructions="Musterlösung aus dem Buch (Referenz):\n" + MUSTER_MEINUNG, metadata={"musterloesung": MUSTER_MEINUNG}),
        base(L, "sprechen", 1, "Sprechen Teil 1: Eine Stadt vorstellen — gemeinsam planen", page="20-21", topic="Eine Stadt in Deutschland oder Österreich vorstellen",
             prompt="Sie sollen in Ihrem Sprachkurs eine Stadt in Deutschland oder in Österreich vorstellen. Planen Sie gemeinsam eine Präsentation "
                    "und besprechen Sie folgende Punkte.",
             questions=["Welche Stadt? — Entscheiden Sie sich für eine Stadt und nennen Sie ihren Namen.",
                        "Welche Informationen? (Bevölkerung, Wirtschaft …) — Sprechen Sie über wichtige Informationen wie z. B. Einwohnerzahl, "
                        "Wirtschaft, Arbeitsplätze, Industrie, Tourismus usw.",
                        "Wer macht was? — Sprechen Sie darüber, wer in der Stadt lebt und arbeitet, welche Berufe es gibt und was die Menschen dort machen.",
                        "Materialien? — Überlegen Sie, welche Materialien Sie für Ihre Präsentation verwenden möchten (Bilder, Karten, Diagramme, Texte usw.)."],
             response_type="dialog", min_duration=60, max_duration=240, sample_answer=MUSTER_PLANEN,
             speech_goal="Gemeinsam eine Präsentation planen: Vorschläge machen, auf den Partner reagieren, Aufgaben verteilen.",
             keywords=["Ich würde gern", "Ich finde", "Außerdem", "Ich kümmere mich um", "Wir brauchen"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Präsentation — Mit dem Auto oder mit dem öffentlichen Verkehr", page="22-23",
             topic="Mit dem Auto oder mit dem öffentlichen Verkehr",
             prompt="Sie sollen eine Präsentation zu einem Thema halten. Planen Sie Ihre Präsentation und sprechen Sie dann. Ihre Präsentation "
                    "sollte klar strukturiert sein. Vorbereitungszeit: 5 Minuten · Sprechzeit: ca. 2–3 Minuten.",
             questions=["Erfahrung — Erzählen Sie von Ihren Erfahrungen mit dem Auto und mit öffentlichen Verkehrsmitteln.",
                        "Situation — Beschreiben Sie die Situation in Ihrer Stadt bezüglich der Verkehrsmittel.",
                        "Vorteile — Nennen Sie die Vorteile vom Auto und vom öffentlichen Verkehr.",
                        "Nachteile — Nennen Sie die Nachteile vom Auto und vom öffentlichen Verkehr.",
                        "Meinung — Sagen Sie Ihre Meinung und geben Sie eine Empfehlung."],
             response_type="monolog", preparation_time=300, min_duration=120, max_duration=180, sample_answer=MUSTER_PRAESENTATION,
             speech_goal="Strukturierte Präsentation: Erfahrung, Situation im Heimatland, Vor- und Nachteile, Meinung mit Begründung.",
             keywords=["Erfahrung", "Vorteile", "Nachteile", "Meiner Meinung nach", "weil", "deshalb"]),
        base(L, "wortschatz", 1, "Wortschatz: Wichtige Redewendungen für Modul 1", page=24, words=WORDS, exercises=meaning_sets(WORDS),
             auto_practice=False, metadata={"note": "Das Buch erklärt die Ausdrücke auf Deutsch (keine Übersetzung) — die Erklärung steht als Bedeutung."}),
        base(L, "uebungen", 1, "Übungen: B1 1. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 1. Unterricht", source="vizu",
             instruction="Abschlusstest zu Kausale Angaben und Redewendungen (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 1. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
