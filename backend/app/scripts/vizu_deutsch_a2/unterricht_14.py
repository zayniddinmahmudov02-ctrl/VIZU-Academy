"""A2 14. Unterricht — Zukunft, Träume und Lebensplanung — Gemeinsame Wiederholung A2 (lesson PDF "A2 14.Unterricht", 9 pages).

Lesson 14 is not part of the book "VIZU-Deutsch A2" (it ends with lesson 13
on p.183); the lesson PDF has no text layer — taken from its page images
(page numbers below refer to that PDF). Content: Frage p.2, grammar review
(13 topics) p.3, review exercises p.4, learning resources for Lesen, Hören,
Schreiben, Sprechen and Wortschatz pp.5-9 (tips and links, no texts or
tasks). There is no Hören audio and no Lesen text for this lesson — the
skill competencies show the resource pages as text, nothing is invented.

Review exercises: open gaps (dass-Sätze: "Ich hoffe, dass du bald ___.") are
not imported; gaps with several correct words accept every correct one
(Futur I / Modalverben, Präpositionen). The booklet's topic 5 / 12 / 13
repeat earlier topics (printing) — the review lists each topic once."""

from . import base, exercise, gap, intro_html, mc, summary_html, tf, ul

L = 14
LESSON_TITLE = "Zukunft, Träume und Lebensplanung"
LESSON_DESCRIPTION = "Thema: Zukunft, Träume und Lebensplanung · Gemeinsame Wiederholung A2 Grammatik"

EINFUEHRUNG_HTML = intro_html(
    14, "Zukunft, Träume und Lebensplanung", "Gemeinsame Wiederholung A2 Grammatik",
    ["A2 grammatikasining 13 mavzusini takrorlash;",
     "kelajak rejalari va orzular haqida gapirish;",
     "A2 darajasida mustaqil o'qish, tinglash, yozish va gapirish uchun manbalarni bilish."],
    ["keyingi 5 yilda nimaga erishmoqchi ekaningizni aytasiz;",
     "har bir grammatik mavzu bo'yicha qisqa mashqlarni bajarasiz;",
     "A2 imtihoniga mustaqil tayyorlanish rejasini tuzasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(14, [
    "<strong>A2 Grammatik:</strong> Satzbau, Perfekt / Präteritum, wenn-Sätze, Imperativ, Infinitiv mit zu, weil / denn / deshalb, dass-Sätze, "
    "Präpositionen, trotzdem / aber, damit / um … zu, Futur I, Passiv, Konjunktiv II.",
    "<strong>Strategie:</strong> jeden Tag ein bisschen — lesen, hören, schreiben und sprechen.",
    "„Heute ein Leser – morgen ein Gewinner.“",
])

REVIEW_HTML = (
    "<h3>Gemeinsame Wiederholung A2 Grammatik</h3><ol>"
    "<li><strong>Satzbau + Perfekt vs. Präteritum:</strong> Subjekt + Verb + … — Ich lerne Deutsch.</li>"
    "<li><strong>wenn-Sätze (Konditionalsätze):</strong> Wenn + Verb am Ende, Hauptsatz — Wenn ich Zeit habe, gehe ich ins Kino.</li>"
    "<li><strong>Imperativ (du, ihr, Sie):</strong> Geht ins Bett! · Seien Sie ruhig, Herr Müller!</li>"
    "<li><strong>Infinitiv mit zu + um … zu / ohne … zu:</strong> Ich beginne, Deutsch zu lernen. · Er lernt, um die Prüfung zu bestehen.</li>"
    "<li><strong>Kausalsätze (weil, denn, deshalb):</strong> …, weil + Satz (Verb am Ende) · …, denn + Hauptsatz · …, deshalb + Hauptsatz (Verb 2).</li>"
    "<li><strong>dass-Sätze + Satzklammer:</strong> …, dass + Subjekt + … + Verb (am Ende) — Ich hoffe, dass du bald kommst.</li>"
    "<li><strong>Lokale Präpositionen + Wechselpräpositionen:</strong> auf, an, in, über, vor, unter … — Der Laptop liegt auf dem Tisch.</li>"
    "<li><strong>trotzdem (Gegensatz) + aber:</strong> …, trotzdem + Verb + Subjekt · …, aber + Hauptsatz.</li>"
    "<li><strong>Finalsätze (damit / um … zu):</strong> Ich spare Geld, damit ich reisen kann. · Ich spare Geld, um zu reisen.</li>"
    "<li><strong>Futur I + Modalverben:</strong> Ich werde Urlaub machen. · Du willst mehr lernen.</li>"
    "<li><strong>Passiv Präsens + man-Strukturen:</strong> werden + Partizip II — Das Auto wird repariert.</li>"
    "<li><strong>Konjunktiv II (höfliche Bitten):</strong> würde + Infinitiv; starke Verben: hätte, wäre, könnte … — Könnten Sie mir helfen?</li></ol>"
)


def _g(title: str, text: str, gaps: dict, explanation: str | None = None) -> dict:
    return gap(f"Ergänzen Sie die Sätze. ({title})", text, gaps, points=len(gaps), explanation=explanation)


REVIEW_SETS = [
    exercise("1–4: Satzbau, wenn-Sätze, Imperativ, Infinitiv mit zu", [
        _g("Satzbau + Perfekt", "Gestern [[1]] ich Deutsch gelernt.", {"1": ["habe"]}),
        _g("Satzbau + Perfekt", "Ich [[1]] heute Deutsch.", {"1": ["lerne"]}),
        _g("Satzbau + Perfekt", "Letzte Woche [[1]] ich viel gelernt.", {"1": ["habe"]}),
        _g("wenn-Sätze", "Wenn ich Zeit habe, [[1]] ich ins Kino.", {"1": ["gehe"]}),
        _g("wenn-Sätze", "Wenn es regnet, [[1]] ich zu Hause.", {"1": ["bleibe"]}),
        _g("wenn-Sätze", "Wenn ich reich wäre, [[1]] ich ein Haus kaufen.", {"1": ["würde"]}),
        _g("Imperativ", "[[1]] (lernen) Sie jeden Tag!", {"1": ["Lernen"]}),
        _g("Imperativ", "[[1]] (gehen) ihr bitte leise!", {"1": ["Geht"]}),
        _g("Imperativ", "[[1]] (sein) Sie pünktlich, bitte!", {"1": ["Seien"]}),
        _g("Infinitiv mit zu", "Ich gehe in die Bibliothek, [[1]] lernen.", {"1": ["um zu"]}),
        _g("Infinitiv mit zu", "Er geht früh los, [[1]] den Bus zu bekommen.", {"1": ["um"]}),
        _g("Infinitiv mit zu", "Ich habe keine Zeit, [[1]] kochen.", {"1": ["zu"]}),
    ], "Gemeinsame Wiederholung A2 — Ergänzen Sie die Sätze."),
    exercise("5–9: Kausalsätze, Präpositionen, trotzdem / aber, Finalsätze", [
        _g("Kausalsätze", "Ich lerne Deutsch, [[1]] ich in Deutschland leben möchte.", {"1": ["weil", "da"]}),
        _g("Kausalsätze", "Er ist müde, [[1]] er lange gearbeitet hat.", {"1": ["weil", "da"]}),
        _g("Kausalsätze", "Es regnet, [[1]] bleiben wir zu Hause.", {"1": ["deshalb", "darum", "deswegen"]}),
        _g("Präpositionen", "Das Buch liegt [[1]] dem Tisch.", {"1": ["auf", "unter", "neben", "vor", "hinter", "an"]}, "Wo? → Dativ: auf dem Tisch."),
        _g("Präpositionen", "Ich gehe [[1]] die Schule.", {"1": ["in", "an", "vor", "hinter"]}, "Wohin? → Akkusativ: in die Schule."),
        _g("Präpositionen", "Wir wohnen [[1]] Berlin.", {"1": ["in"]}),
        _g("trotzdem / aber", "Es regnet, [[1]] ich gehe spazieren.", {"1": ["aber"]}, "„ich gehe“ — Subjekt vor dem Verb → aber (nach trotzdem: gehe ich)."),
        _g("trotzdem / aber", "Ich bin müde, [[1]] ich lerne weiter.", {"1": ["aber"]}),
        _g("trotzdem / aber", "Er hat wenig Geld, [[1]] er kauft ein Auto.", {"1": ["aber"]}),
        _g("Finalsätze", "Ich lerne Deutsch, [[1]] ich besser sprechen kann.", {"1": ["damit"]}),
        _g("Finalsätze", "Sie spart Geld, [[1]] sie reisen kann.", {"1": ["damit"]}),
        _g("Finalsätze", "Er übt jeden Tag, [[1]] die Prüfung zu bestehen.", {"1": ["um"]}),
    ], "Gemeinsame Wiederholung A2 — Ergänzen Sie die Sätze."),
    exercise("10–13: Futur I + Modalverben, Passiv, Finalsätze, Konjunktiv II", [
        _g("Futur I + Modalverben", "Ich [[1]] morgen kommen.", {"1": ["werde", "will", "kann", "muss", "möchte", "soll", "darf"]}),
        _g("Futur I + Modalverben", "Du [[1]] mehr lernen.", {"1": ["wirst", "willst", "kannst", "musst", "möchtest", "sollst", "solltest", "darfst"]}),
        _g("Futur I + Modalverben", "Wir [[1]] ins Kino gehen.", {"1": ["werden", "wollen", "können", "müssen", "möchten", "sollen", "dürfen"]}),
        _g("Passiv Präsens", "Das Auto [[1]] in der Werkstatt repariert.", {"1": ["wird"]}),
        _g("Passiv Präsens", "Hier [[1]] nicht geraucht.", {"1": ["wird"]}),
        _g("Passiv Präsens", "In Deutschland [[1]] Deutsch gesprochen.", {"1": ["wird"]}),
        _g("Finalsätze", "Wir üben viel, [[1]] wir besser spielen.", {"1": ["damit"]}),
        _g("Finalsätze", "Er steht früh auf, [[1]] pünktlich zu sein.", {"1": ["um"]}),
        _g("Finalsätze", "Sie liest Bücher, [[1]] mehr zu lernen.", {"1": ["um"]}),
        _g("Konjunktiv II", "[[1]] Sie mir bitte helfen?", {"1": ["Könnten", "Würden"]}),
        _g("Konjunktiv II", "[[1]] du mir das Buch geben?", {"1": ["Könntest", "Würdest"]}),
        _g("Konjunktiv II", "[[1]] Sie bitte langsamer sprechen?", {"1": ["Könnten", "Würden"]}),
    ], "Gemeinsame Wiederholung A2 — Ergänzen Sie die Sätze."),
]


def _resources(title: str, why: list[str], items_: list[tuple[str, list[str]]], strategy: list[str], tips: list[str], links: list[str],
               remember: str) -> str:
    return (f"<h3>A2 darajada {title} uchun eng yaxshi manbalar</h3>"
            + "<h4>Nima uchun muhim?</h4>" + ul(why)
            + "".join(f"<h4>{name}</h4>" + ul(points) for name, points in items_)
            + "<h4>A2 uchun strategiya (tez progress)</h4>" + "<ol>" + "".join(f"<li>{s}</li>" for s in strategy) + "</ol>"
            + "<h4>Qo'shimcha maslahatlar</h4>" + ul(tips)
            + "<h4>Foydali linklar</h4>" + ul(links)
            + f"<p><strong>Esda tuting:</strong> {remember}</p>")


LESEN_HTML = _resources(
    "Lesen (o'qish tushunish)",
    ["So'z boyligini oshiradi", "Grammatikani tushunishga yordam beradi", "Imtihonlarga tayyorlaydi", "Fikrni tez tushunish ko'nikmasini rivojlantiradi"],
    [("Jurnallar (A2 uchun mos)", ["Deutsch perfekt — A1–B2 darajalar uchun, har maqolada lug'at izohi, matn + izoh + audio",
                                   "Deutsch üben – Lesen & Schreiben (Hueber) — maxsus mashq kitobi, imtihon formatiga yaqin",
                                   "Schubert Verlag – Online material — bepul online mashqlar, test formatida"]),
     ("Onlayn saytlar (kunlik mashq uchun)", ["DW Deutsch Lernen (Nicos Weg) — video + matn + mashq", "Lingolia Deutsch — qisqa matnlar, grammatikaga bog'langan",
                                              "Nachrichtenleicht.de — juda oddiy tilda real yangiliklar"]),
     ("Kitoblar (bosqichma-bosqich)", ["Graded Readers (A2 daraja): „Ein neues Leben in Berlin“, „Die verlorene Tasche“, „Ferien am Meer“ — kuniga 10–15 daqiqa"])],
    ["Kuniga 1 matn o'qi (Deutsch perfekt yoki DW)", "Noma'lum so'zlarni yozib bor", "5–6 gapni qayta yoz (paraphrase)", "Oxirida qisqa xulosa qil (3–4 gap)"],
    ["O'qishdan zavq olish uchun qiziq mavzuni tanlang", "Noma'lum so'zlarni kontekst orqali aniqlashga harakat qiling",
     "O'qigan matningizni yuqori ovozda o'qib chiqing", "Kichik yutuqlarni nishonlang"],
    ["www.deutsch-perfekt.com", "www.hueber.de", "www.schubert-verlag.de", "www.dw.com/deutsch-lernen", "www.lingolia.com", "www.nachrichtenleicht.de"],
    "Doimiy o'qish — tilni tushunishning eng kuchli kaliti! Kuniga 15 daqiqa o'qish — katta natijalarga olib keladi.")
HOEREN_HTML = _resources(
    "Hörverstehen",
    ["Tinglab tushunish tezligini oshiradi", "Talaffuzni yaxshilaydi", "Real suhbatga tayyorlaydi", "Imtihonda yuqori ball beradi"],
    [("Audio / video platformalar", ["DW Deutsch Lernen (Nicos Weg) — to'liq kurs + subtitr", "Easy German (YouTube) — real nemischa eshitish",
                                     "Deutsch lernen durch Hören (YouTube / Podcast) — boshlovchilar uchun ideal"]),
     ("Online saytlar (kunlik mashq)", ["Lingolia Deutsch (Hören) — tizimli mashq", "Goethe Institut Übungen — imtihonga tayyorlaydi",
                                        "Deutsch Perfekt Audio — real hayot + audio"]),
     ("Podcast va audio kitoblar", ["Slow German (Podcast) — tushunish oson", "Coffee Break German — o'qituvchi bilan o'rganish hissi"])],
    ["Kuniga 10–15 daqiqa audio tingla", "Bir audioga kamida 2 marta qayt", "Noma'lum so'zlarni yozib bor", "Eshitganingni 2–3 gap bilan qayta ayt",
     "Subtitles bilan tekshir"],
    ["Avval subtitles bilan, keyin subtitlesiz tingla", "Qisqa audiolardan boshlang", "Bir xil audiolarni takror tinglang", "Passiv emas — faol tinglang (yozib boring)"],
    ["dw.com/deutsch-lernen", "easygerman.org", "lingolia.com/deutsch", "goethe.de", "deutsch-perfekt.com"],
    "Har kuni ozgina, lekin doimiy tinglash — katta natija beradi!")
SCHREIBEN_HTML = _resources(
    "Schreiben",
    ["Grammatikani mustahkamlaydi", "Fikrni aniq ifodalashni o'rgatadi", "Imtihon uchun asosiy skill", "Gap tuzishni tezlashtiradi"],
    [("Asosiy platformalar", ["Deutsch üben – Schreiben (Hueber) — Schreiben uchun TOP kitob", "Goethe Institut Übungen — imtihonga tayyorlaydi",
                              "DW Deutsch Lernen — tushunarli va bosqichli"]),
     ("Online saytlar (kunlik mashq)", ["Lingolia Deutsch (Schreiben) — xatolarni kamaytiradi", "Mein-Deutschbuch.de — bepul va boy resurs",
                                        "Deutsch Perfekt — real yozish uslubi"]),
     ("Yozish uchun foydali shablonlar", ["E-Mail (A2): Anrede: Liebe/Lieber … · Einleitung: Ich schreibe dir, weil … · Hauptteil: Ich möchte … / Ich habe … · "
                                          "Schluss: Viele Grüße", "Meinung: Ich denke, dass … · Meiner Meinung nach … · Ich finde das gut/schlecht, weil …"])],
    ["Har kuni 5–6 gap yoz", "Tayyor shablonlardan foydalan", "Xatolarni tekshir (Grammatik)", "Yozganingni qayta yoz (improve)", "O'qib chiq (self-check)"],
    ["Qisqa gaplardan boshlang", "Murakkab gap shart emas", "Ko'proq yoz — tezroq rivojlan", "Xatodan qo'rqma (practice = progress)"],
    ["hueber.de", "goethe.de", "dw.com/deutsch-lernen", "lingolia.com", "mein-deutschbuch.de"],
    "Yozish ko'nikmasi faqat amaliyot bilan yaxshilanadi. Bugun yoz, ertaga mukammal bo'l!")
SPRECHEN_HTML = _resources(
    "Sprechen",
    ["Erkin muloqot qilishni o'rgatadi", "Ishonchni oshiradi", "Imtihonda asosiy skill", "Real hayotda eng kerakli"],
    [("Asosiy platformalar", ["DW Deutsch Lernen (Nicos Weg) — gapirish uchun tayyor dialoglar", "Tandem (App) — jonli muloqot", "HelloTalk (App) — feedback olish"]),
     ("Online va praktika manbalari", ["Easy German (YouTube) — real nutqni o'rganish", "italki (Platform) — professional practice",
                                       "Deutsch mit Marija (YouTube) — A2 uchun tushunarli"]),
     ("Sprechen uchun foydali qoliplar", ["Fikr bildirish: Ich denke, dass … · Meiner Meinung nach … · Ich finde das gut/schlecht …",
                                          "Savol berish: Was denkst du darüber? · Warum ist das wichtig? · Kannst du das erklären?",
                                          "Javob berish: Ich bin damit einverstanden … · Das stimmt, aber … · Ich glaube, dass …"])],
    ["Har kuni 5–10 daqiqa gapir", "O'zing bilan gaplash (self-talk)", "Audio eshitib takrorla (shadowing)", "Oddiy gaplardan boshla", "Xatodan qo'rqma"],
    ["Sekin gapir — to'g'ri gapir", "Qisqa gap = yaxshi gap", "Ko'proq practice = tez progress", "Har kuni oz-ozdan gapir"],
    ["dw.com/deutsch-lernen", "tandem.net", "hellotalk.com", "easygerman.org", "italki.com"],
    "Ko'proq gapirish = ko'proq ishonch = yaxshi natija!")
WORTSCHATZ_HTML = _resources(
    "Wortschatz",
    ["Gapirish osonlashadi", "O'qish tezlashadi", "Tinglab tushunish yaxshilanadi", "Imtihonda yordam beradi"],
    [("Asosiy platformalar", ["Anki (App) — flashcard tizimi, spaced repetition", "Quizlet (App/Web) — tayyor setlar, o'yin orqali yodlash",
                              "Memrise (App) — audio bilan so'zlar, real talaffuz"]),
     ("Online saytlar (kunlik mashq)", ["Lingolia Deutsch (Wortschatz) — kontekst bilan o'rganish", "DW Deutsch Lernen — real nutqda so'zlar",
                                        "Goethe Wortliste A2 — kerakli minimum"]),
     ("So'z yodlash usullari", ["Flashcard: Wort · Wort + Tarjima · Wort + Gap · Wort + Rasm", "Spaced repetition: 1-kun → 2-kun → 4-kun → 7-kun",
                                "Amaliy ishlatish: gap tuz, dialogda ishlat, ovozing bilan ayt", "Namuna: neu — yangi · Das ist ein neues Buch. (Bu yangi kitob.)"])],
    ["Kuniga 10–15 ta so'z", "Har biriga gap tuz", "3–4 marta takrorla", "Eski so'zlarni qayta ko'r", "Gapirishda ishlat"],
    ["So'zni alohida emas — gap bilan yodla", "Sinonim va antonimlarni o'rgan", "Ko'p takrorla = tez eslab qolasan", "Passiv emas — aktiv ishlat"],
    ["ankiweb.net", "quizlet.com", "memrise.com", "dw.com/deutsch-lernen", "goethe.de"],
    "Kichik qadamlar — katta natijalar! Har kuni oz-ozdan o'rgan, so'zlaring seni maqsadingga yetaklaydi.")


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 14. Unterricht", source="vizu", page=1, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Was möchtest du in den nächsten 5 Jahren erreichen?", page=2,
             prompt="Was möchtest du in den nächsten 5 Jahren erreichen? Sprich über deine Ziele, Träume und Pläne.", min_duration=20, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Gemeinsame Wiederholung A2", page="3-4", rules=[{"title": "Gemeinsame Wiederholung A2 Grammatik", "html": REVIEW_HTML}],
             exercises=REVIEW_SETS,
             metadata={"book_page": "3-4 (A2 14.Unterricht.pdf)", "note": "dass-Sätze mashqlari ochiq (bir nechta to'g'ri javob) — kiritilmadi."}),
        base(L, "kompetenz", 3, "Wortschatz: Manbalar und Methoden (A2)", page=9, competency="WORTSCHATZ", html=WORTSCHATZ_HTML),
        base(L, "kompetenz", 4, "Lesen: Die besten Quellen für A2", page=5, competency="LESEN", html=LESEN_HTML),
        base(L, "kompetenz", 5, "Hören: Die besten Quellen für A2", page=6, competency="HOEREN", html=HOEREN_HTML),
        base(L, "kompetenz", 6, "Schreiben: Die besten Quellen für A2", page=7, competency="SCHREIBEN", html=SCHREIBEN_HTML),
        base(L, "kompetenz", 7, "Sprechen: Die besten Quellen für A2", page=8, competency="SPRECHEN", html=SPRECHEN_HTML),
        base(L, "schreiben", 1, "Schreiben: Meine Ziele für die nächsten 5 Jahre", source="vizu", task_type="description",
             prompt="Schreiben Sie einen Text über Ihre Zukunft (Thema der Lektion: Was möchtest du in den nächsten 5 Jahren erreichen?).\n"
                    "• Was möchten Sie in den nächsten 5 Jahren erreichen?\n• Welche Träume haben Sie?\n• Was müssen Sie dafür tun?\n"
                    "• Wann und wie möchten Sie Ihr Ziel erreichen?\n\nBenutzen Sie Futur I (Ich werde …), wenn-Sätze und um … zu.",
             min_words=60, max_words=150, time_limit=25,
             metadata={"note": "Darsning savoli asosida VIZU tomonidan tuzilgan yozma topshiriq (PDFda alohida Schreiben topshirig'i yo'q)."}),
        base(L, "sprechen", 1, "Sprechen: Meine Zukunft — Träume und Pläne", source="vizu", topic="Zukunft, Träume und Lebensplanung",
             prompt="Sprechen Sie über Ihre Zukunft. Benutzen Sie: Ich werde … · Ich möchte … · Wenn ich …, würde ich … · um … zu.",
             questions=["Was möchtest du in den nächsten 5 Jahren erreichen?", "Was ist dein größter Traum?", "Was musst du dafür lernen oder tun?",
                        "Wo möchtest du in 5 Jahren leben und arbeiten?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Über Ziele, Träume und Pläne sprechen — mit Futur I, Konjunktiv II und Finalsätzen.",
             keywords=["Ich werde", "Ich möchte", "würde", "um … zu", "in 5 Jahren"],
             metadata={"note": "Darsning savoli asosida VIZU tomonidan tuzilgan."}),
        base(L, "yakuniy", 1, "Abschlusstest: Wiederholung A2", source="vizu",
             instruction="A2 grammatikasi bo'yicha yakuniy test (barcha 13 mavzu).",
             questions=[
                 mc("Perfekt: Gestern ___ ich nach Berlin gefahren.", ["bin", "habe", "war"], "A"),
                 mc("Wenn ich Zeit ___, gehe ich ins Kino.", ["habe", "hätte", "hatte ich"], "A"),
                 mc("Imperativ (Sie): ___ Sie pünktlich, bitte!", ["Seien", "Sind", "Sein"], "A"),
                 mc("Ich beginne, Deutsch ___.", ["zu lernen", "lernen", "gelernt"], "A"),
                 mc("Es regnet, ___ bleiben wir zu Hause.", ["deshalb", "weil", "dass"], "A"),
                 mc("Ich hoffe, dass du bald ___.", ["kommst", "kommen", "du kommst"], "A"),
                 mc("Der Laptop liegt auf ___ Tisch.", ["dem", "den", "der"], "A"),
                 mc("Es regnet. Trotzdem ___ spazieren.", ["gehe ich", "ich gehe", "gehen"], "A"),
                 mc("Ich spare Geld, ___ ich reisen kann.", ["damit", "um", "weil"], "A"),
                 mc("Das Auto ___ repariert.", ["wird", "werden", "ist geworden"], "A"),
                 mc("___ Sie mir helfen? (höflich)", ["Könnten", "Können", "Konnten"], "A"),
                 tf("„Ich werde Urlaub machen.“ ist Futur I.", True),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 14. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
