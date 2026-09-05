"""Bootstrap script: imports the full A1 Lesson 1 ("Herzlich Willkommen")
content — Grammatik (Deutsches Alphabet), Wortschatz, Lesen, Hören,
Schreiben, Sprechen and the Grammatik Quiz — into the *existing* A1
Lesson 1 row. Mirrors seed_courses.py's pattern: never creates a new
Course/Module/Lesson, only tops up content on what's already there.

Idempotent and additive only:
  - Lesson 1 is looked up by (course.level == "A1", module == the
    course's one module, lesson.number == 1) and must already exist —
    the script aborts if it doesn't (no Lesson is ever created here).
  - Every content row is matched by a natural key (title, or
    german_word+translation for Vocabulary, or question text for
    QuizQuestion) before insert — re-running this script never
    duplicates a row, it only creates what's missing.
  - No other lesson, in A1 or any other level, is ever touched.
  - No migration, no schema change: only inserts through the exact
    models/columns that already exist.

Hören (Listening) rows are created with audio_url="" and
is_published=False — Listening.audio_url is NOT NULL at the DB level
and no real audio recording exists yet for this lesson's source text,
so a fake URL is deliberately never invented. The transcripts are
saved and ready; an admin uploads the real audio file and publishes
each row from the CMS once it's recorded (same manual-URL pattern
already used for Vocabulary audio).

Video is not touched at all: no video URL/file was given in the
source material for this lesson, and the existing Lesson 1 video (if
any) is left exactly as it is.

Homework is not touched: no distinct Hausaufgabe content was given in
the source material for this lesson (see the module 12 note in the
import brief) — inventing one would violate the "don't fabricate
content" rule this script otherwise follows for audio.

Run from the `backend/` directory:

    python -m app.scripts.seed_lesson_1
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.grammar import Grammar
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.module import Module
from app.models.quiz import QUIZ_TYPE_GRAMMAR, Quiz
from app.models.quiz_option import QuizOption
from app.models.quiz_question import QuizQuestion
from app.models.reading import Reading
from app.models.speaking import Speaking
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing

LEVEL = "A1"
LESSON_NUMBER = 1

# ==========================
# Grammatik — Deutsches Alphabet
# ==========================

GRAMMAR_TITLE = "Das deutsche Alphabet"

GRAMMAR_CONTENT = """NEMIS TILI ALIFBOSI

Aa — A [ah]
Bb — Be [bay]
Cc — Ce [tsay]
Dd — De [day]
Ee — E [ay]
Ff — Ef [eff]
Gg — Ge [gay]
Hh — Ha [hah]
Ii — I [eeh]
Jj — Jott / Je [yot]
Kk — Ka [kah]
Ll — El [ell]
Mm — Em [em]
Nn — En [en]
Oo — O [oh]
Pp — Pe [pay]
Qq — Qu / Que [koo]
Rr — Er [err]
Ss — Es [es]
Tt — Te [tay]
Uu — U [oh]
Vv — Vau [fow]
Ww — We [vay]
Xx — Ix [iks]
Yy — Ypsilon [oopsoilohn]
Zz — Zett [tset]
Ää — Ä [eh]
Üü — Ü [uuh]
Öö — Ö [ouh]
ß — Eszett [ess-set]

MUHIM HARFLAR VA O'QILISHI

C c:
- a, o, u undoshlardan oldin: [k] — Misollar: Café, Clown
- e, i, ä undoshlardan oldin: [ts] — Misollar: Cent, Cinema

H h:
- So'z boshida yoki unli oldida: [h] — Misollar: Haus, heute
- Ikki unli orasida kelib, talaffuz qilinmaydi — Misollar: gehen, Uhr, Zahn

J j:
- Asli nemischa so'zlarda: [y] — Misollar: Jahr, Junge
- Xorijiy so'zlarda: [zh] — Misollar: Job, Joggen, Jeans

Q q:
- Har doim: [kv] — Misollar: Qualität, Quelle

R r:
- So'z boshida yoki undoshdan keyin: [r] — Misollar: Rot, Brief, Lehrer, Mutter

S s:
- So'z boshida unli oldidan: [z] — Misollar: Sonne, sieben
- So'z oxiri yoki undosh oldidan: [s] — Misollar: Haus, ist
- sp: [shp] — Misollar: Sport, Sprache
- st: [sht] — Misollar: Student, Stadt

V v:
- Ko'p nemis so'zlarida: [f] — Misollar: Vater, Volk
- Ba'zi xorijiy so'zlarda: [v] — Misollar: Video, Virus

W w:
- Har doim: [v] — Misollar: Wasser, Winter

Y y:
- Ko'p hollarda [ü] yoki [i] tovushiga yaqin — Misollar: Physik, Psychologie
- Ba'zi xorijiy so'zlarda [y] kabi — Misol: Yoga

Z z:
- Har doim: [ts] — Misollar: Zeit, Zimmer

Ä ä: "ä" va "e" oralig'idagi tovush — Misol: Mädchen
Ö ö: "ö" va "e" oralig'idagi tovush — Misol: schön
Ü ü: "ü" va "i" oralig'idagi tovush — Misol: Tür

ß: "Eszett", "scharfes S" — Har doim: [s] — Misollar: Straße, Fußball

HARF BIRIKMALARI

ch → [ç] — Misollar: ich, Küche (Ba'zi xorijiy so'zlarda [k] — Misollar: Bach, Buch, Charakter)
sch → [sh] — Misollar: Schule, Schnee
sp → [shp] — Misollar: Sport, Sprache
st → [sht] — Misollar: Student, Stadt
ph → [f] — Misollar: Philosophie, Physik
th → [t] — Misollar: Theater, Thema
ck → [k] — Misollar: Jacke, Zucker
ng → [ŋ] — Misollar: singen, Finger

DIFTONG / IKKI UNLI TOVUSH BIRIKMALARI

ei / ai → [ay] — Misollar: mein, Kaiser
eu / äu → [oy] — Misollar: neu, Häuser
au → [au] — Misollar: Haus, Auto
ie → [ii] — Misollar: Liebe, vier
eu (xorijiy so'zlarda) → [oy] yoki [ey] — Misollar: Europa, Eule"""

# ==========================
# Wortschatz
# ==========================

# (german_word, article, translation)
VOCABULARY_ITEMS = [
    # Personen
    ("ich", None, "men"),
    ("du", None, "sen"),
    ("er", None, "u"),
    ("sie", None, "u"),
    ("wir", None, "biz"),
    ("ihr", None, "siz"),
    ("sie", None, "ular"),
    # Schule und Lernen
    ("Schule", "die", "maktab"),
    ("lernen", None, "o'rganmoq"),
    ("Deutschunterricht", "der", "nemis tili darsi"),
    ("Buch", "das", "kitob"),
    ("Heft", "das", "daftar"),
    ("Stift", "der", "ruchka"),
    # Familie
    ("Mutter", "die", "ona"),
    ("Vater", "der", "ota"),
    ("Bruder", "der", "aka / uka"),
    ("Schwester", "die", "opa / singil"),
    ("Familie", "die", "oila"),
    ("Freund", "der", "do'st (o'g'il)"),
    ("Freundin", "die", "do'st (qiz)"),
    # Hobbys und Freizeit
    ("Fußball spielen", None, "futbol o'ynamoq"),
    ("malen", None, "rasm chizmoq"),
    ("Musik hören", None, "musiqa tinglamoq"),
    ("lesen", None, "o'qimoq"),
    ("schwimmen", None, "suzmoq"),
    ("Rad fahren", None, "velosiped haydamoq"),
    # Tageszeiten und Tage
    ("Morgen", "der", "tong"),
    ("Tag", "der", "kun"),
    ("Abend", "der", "kechqurun"),
    ("Nacht", "die", "tun"),
    ("Montag", None, "dushanba"),
    ("Dienstag", None, "seshanba"),
    ("Mittwoch", None, "chorshanba"),
    ("Donnerstag", None, "payshanba"),
    ("Freitag", None, "juma"),
    ("Samstag", None, "shanba"),
    ("Sonntag", None, "yakshanba"),
    # Wetter und Jahreszeiten
    ("sonnig", None, "quyoshli"),
    ("warm", None, "iliq"),
    ("kalt", None, "sovuq"),
    ("regnerisch", None, "yomg'irli"),
    ("windig", None, "shamolli"),
    ("Frühling", "der", "bahor"),
    ("Sommer", "der", "yoz"),
    ("Herbst", "der", "kuz"),
    ("Winter", "der", "qish"),
    # Wichtige Wörter
    ("kommen", None, "kelmoq"),
    ("wohnen", None, "yashamoq"),
    ("gehen", None, "bormoq"),
    ("mögen", None, "yoqtirmoq"),
    ("danke", None, "rahmat"),
    ("bitte", None, "iltimos"),
    ("ja", None, "ha"),
    ("nein", None, "yo'q"),
]

# ==========================
# Lesen — A1 Modul 1 matnlari
# ==========================

READING_TEXTS = [
    (
        "Text 1",
        "Hallo! Ich heiße Tom und ich bin 10 Jahre alt.\n"
        "Ich komme aus Usbekistan und wohne in Taschkent.\n"
        "Ich gehe in die Schule und lerne Deutsch.\n"
        "Ich mag Fußball. Danke!",
        "Salom! Mening ismim Tom va men 10 yoshdaman.\n"
        "Men O'zbekistondan va Toshkentda yashayman.\n"
        "Men maktabga boraman va nemis tilini o'rganaman.\n"
        "Menga futbol yoqadi. Rahmat!",
    ),
    (
        "Text 2",
        "Hallo! Ich heiße Anna und ich bin 9 Jahre alt.\n"
        "Ich komme aus Usbekistan und wohne in Taschkent.\n"
        "Ich gehe in die Schule und lerne Deutsch.\n"
        "Ich mag Malen und Musik. Danke!",
        "Salom! Mening ismim Anna va men 9 yoshdaman.\n"
        "Men O'zbekistondan va Toshkentda yashayman.\n"
        "Men maktabga boraman va nemis tilini o'rganaman.\n"
        "Menga rasm chizish va musiqa yoqadi. Rahmat!",
    ),
    (
        "Text 3",
        "Hallo! Wir heißen Tom und Anna.\n"
        "Wir sind 10 und 9 Jahre alt.\n"
        "Wir kommen aus Usbekistan und wohnen in Taschkent.\n"
        "Wir gehen in die Schule und lernen Deutsch.\n"
        "Wir mögen Fußball, Malen und Musik. Danke!",
        "Salom! Bizning ismimiz Tom va Anna.\n"
        "Biz 10 va 9 yoshdamiz.\n"
        "Biz O'zbekistondan va Toshkentda yashaymiz.\n"
        "Biz maktabga boramiz va nemis tilini o'rganamiz.\n"
        "Bizga futbol, rasm chizish va musiqa yoqadi. Rahmat!",
    ),
]


def _reading_content(german: str, uzbek: str) -> str:
    return f"{german}\n\n---\nO'zbekcha tarjima:\n{uzbek}"


# ==========================
# Hören
# ==========================

_HOEREN_DE = (
    "Es ist Samstag. Tom und Anna gehen in den Park.\n"
    "Es ist sonnig und warm.\n"
    "Tom spielt Fußball und Anna liest ein Buch.\n"
    "Ein Hund kommt und läuft zu ihnen.\n"
    "Sie lachen und spielen mit dem Hund.\n"
    "Nach zwei Stunden gehen sie nach Hause.\n"
    "Sie sind müde, aber glücklich."
)

_HOEREN_UZ = (
    "Shanba kuni. Tom va Anna parkka borishadi.\n"
    "Quyoshli va iliq kun.\n"
    "Tom futbol o'ynaydi, Anna esa kitob o'qiydi.\n"
    "Bir it kelib, ular tomon yuguradi.\n"
    "Ular kulib, it bilan o'ynashadi.\n"
    "Ikki soatdan so'ng uyga ketishadi.\n"
    "Ular charchagan, lekin baxtli."
)

# (title, transcript)
LISTENING_TEXTS = [
    ("Text 1", _reading_content(_HOEREN_DE, _HOEREN_UZ)),
    ("Text 2", _HOEREN_UZ),
    ("Text 3", _reading_content(_HOEREN_DE, _HOEREN_UZ)),
]

# ==========================
# Schreiben
# ==========================

WRITING_TASKS = [
    (
        "Topshiriq 1",
        "Hallo! Ich heiße ________, ich bin ________ Jahre alt,\n"
        "ich komme aus ________ und wohne in ________.\n"
        "Ich gehe in die Schule und lerne ________.\n"
        "Ich mag ________.\n\n"
        "So'zlar: 10, Fußball, Usbekistan, Tom, Taschkent, Deutsch",
    ),
    (
        "Topshiriq 2",
        "Salom! Mening ismim ________,\n"
        "men ________ yoshdaman,\n"
        "men ________dan va ________da yashayman.\n"
        "Men maktabga boraman va ________ tilini o'rganaman.\n"
        "Menga ________ yoqadi.\n\n"
        "So'zlar: 10, futbol, O'zbekiston, Tom, Toshkent, nemis",
    ),
    (
        "Topshiriq 3",
        "Das ist mein Freund ________.\n\n"
        "Er/Sie ist ________ Jahre alt,\n"
        "er/sie kommt aus ________ und wohnt in ________.\n"
        "Er/Sie geht in die Schule und lernt ________.\n"
        "Er/Sie mag ________.\n\n"
        "So'zlar: Usbekistan, Anna, Malen und Musik, Taschkent, 9, Deutsch",
    ),
    (
        "Topshiriq 4",
        "Bu mening do'stim ________.\n"
        "U ________ yoshda,\n"
        "u ________dan va ________da yashaydi.\n"
        "U maktabga boradi va ________ tilini o'rganadi.\n"
        "Unga ________ yoqadi.\n\n"
        "So'zlar: Anna, 9, O'zbekistondan, Toshkentda, nemis, Malen va musiqa",
    ),
]

# ==========================
# Sprechen
# ==========================

SPEAKING_TITLE = "Stellen Sie sich vor!"
SPEAKING_TOPIC = "Sich vorstellen – Erzählen Sie über sich!"
SPEAKING_INSTRUCTION = (
    "Hallo! Ich heiße __________________,\n"
    "ich bin __________ Jahre alt,\n\n"
    "ich komme aus __________________\n"
    "und wohne in __________________.\n\n"
    "Ich gehe in die Schule und lerne __________________.\n\n"
    "Ich mag __________________\n"
    "(z. B. Fußball, Musik, Bücher).\n\n"
    "Meine Hobbys sind __________________.\n\n"
    "Mein Lieblingsfach ist __________________.\n\n"
    "Ich habe ________ Bruder /\n"
    "________ Schwester.\n\n"
    "Meine Familie ist __________________.\n\n"
    "Ich freue mich, Deutsch zu lernen!\n\n"
    "Tipp: Sprich über dich selbst! Sei mutig und lächle!"
)

# ==========================
# Grammatik Quiz — Deutsche Alphabet
# ==========================

QUIZ_TITLE = "1. Unterricht Grammatik Quiz"
QUIZ_DESCRIPTION = "Deutsche Alphabet"

# (question, [4 options], correct_index 0-based)
QUIZ_QUESTIONS = [
    ("Nemis alifbosida nechta asosiy harf bor?", ["24", "26", "28", "30"], 1),
    ("Nemis tilida nechta Umlaut harfi bor?", ["2", "3", "4", "5"], 1),
    ("\"sch\" harf birikmasi o'zbekchaga yaqin qanday o'qiladi?", ["ch", "sh", "s", "k"], 1),
    ("\"sp\" so'z boshida qanday o'qiladi?", ["sp", "shp", "sht", "sh"], 1),
    ("\"st\" so'z boshida qanday o'qiladi?", ["st", "sht", "shp", "ts"], 1),
    ("\"ch\" odatda \"ich\" so'zida qanday tovush beradi?", ["[k]", "[ç]", "[sh]", "[t]"], 1),
    ("Nemis tilida \"ß\" qanday ataladi?", ["Umlaut", "Eszett", "Zett", "Ypsilon"], 1),
    ("\"z\" harfi nemis tilida qanday o'qiladi?", ["z", "ts", "s", "sh"], 1),
    ("\"w\" harfi nemis tilida qanday o'qiladi?", ["w", "v", "f", "y"], 1),
    ("\"v\" ko'p nemis so'zlarida qanday o'qiladi?", ["v", "f", "b", "w"], 1),
    ("\"j\" nemischa so'zlarda ko'pincha qanday o'qiladi?", ["j", "y", "sh", "ts"], 1),
    ("\"qu\" qanday o'qiladi?", ["ku", "kv", "shu", "tsu"], 1),
    ("\"ei\" qanday o'qiladi?", ["ey", "ay", "iy", "oy"], 1),
    ("\"eu\" qanday o'qiladi?", ["ay", "oy", "au", "iy"], 1),
    ("\"au\" qanday o'qiladi?", ["ay", "oy", "au", "u"], 2),
    ("\"ie\" qanday o'qiladi?", ["ii", "ay", "oy", "e"], 0),
    ("\"ph\" qanday o'qiladi?", ["p", "f", "h", "v"], 1),
    ("\"th\" qanday o'qiladi?", ["t", "th", "f", "s"], 0),
    ("\"ck\" qanday o'qiladi?", ["k", "ts", "sh", "g"], 0),
    ("\"ng\" qanday tovush beradi?", ["n", "ng / [ŋ]", "g", "nk"], 1),
]

OPTION_LETTERS = ["A", "B", "C", "D"]


def get_lesson_1(db) -> Lesson | None:
    language = db.scalar(select(Language).where(Language.code == "de", Language.deleted_at.is_(None)))
    if language is None:
        return None

    course = db.scalar(select(Course).where(Course.language_id == language.id, Course.level == LEVEL))
    if course is None:
        return None

    module = db.scalar(select(Module).where(Module.course_id == course.id))
    if module is None:
        return None

    return db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.number == LESSON_NUMBER))


def seed_grammar(db, lesson: Lesson) -> int:
    existing = db.scalar(
        select(Grammar).where(Grammar.lesson_id == str(lesson.id), Grammar.title == GRAMMAR_TITLE)
    )
    if existing is not None:
        print(f"  Grammatik '{GRAMMAR_TITLE}' already exists - skipping.")
        return 0

    db.add(
        Grammar(
            lesson_id=str(lesson.id),
            title=GRAMMAR_TITLE,
            content=GRAMMAR_CONTENT,
            order_index=1,
            is_published=True,
        )
    )
    print(f"  Created Grammatik '{GRAMMAR_TITLE}'.")
    return 1


def seed_vocabulary(db, lesson: Lesson) -> int:
    created = 0
    for order_index, (word, article, translation) in enumerate(VOCABULARY_ITEMS, start=1):
        existing = db.scalar(
            select(Vocabulary).where(
                Vocabulary.lesson_id == lesson.id,
                Vocabulary.german_word == word,
                Vocabulary.translation == translation,
            )
        )
        if existing is not None:
            continue
        db.add(
            Vocabulary(
                lesson_id=lesson.id,
                german_word=word,
                article=article,
                translation=translation,
                order_index=order_index,
                is_published=True,
            )
        )
        created += 1
    print(f"  Created {created} Wortschatz item(s) (of {len(VOCABULARY_ITEMS)} total).")
    return created


def seed_reading(db, lesson: Lesson) -> int:
    created = 0
    for order_index, (title, german, uzbek) in enumerate(READING_TEXTS, start=1):
        existing = db.scalar(select(Reading).where(Reading.lesson_id == lesson.id, Reading.title == title))
        if existing is not None:
            continue
        db.add(
            Reading(
                lesson_id=lesson.id,
                title=title,
                content=_reading_content(german, uzbek),
                order_index=order_index,
                is_published=True,
            )
        )
        created += 1
    print(f"  Created {created} Lesen text(s) (of {len(READING_TEXTS)} total).")
    return created


def seed_listening(db, lesson: Lesson) -> int:
    created = 0
    for order_index, (title, transcript) in enumerate(LISTENING_TEXTS, start=1):
        existing = db.scalar(
            select(Listening).where(Listening.lesson_id == str(lesson.id), Listening.title == title)
        )
        if existing is not None:
            continue
        db.add(
            Listening(
                lesson_id=str(lesson.id),
                title=title,
                # No real audio recording exists yet for this text — see
                # module docstring. Left unpublished on purpose.
                audio_url="",
                transcript=transcript,
                order_index=order_index,
                is_published=False,
            )
        )
        created += 1
    print(f"  Created {created} Hoeren text(s) (of {len(LISTENING_TEXTS)} total) - unpublished, audio pending.")
    return created


def seed_writing(db, lesson: Lesson) -> int:
    created = 0
    for order_index, (title, instruction) in enumerate(WRITING_TASKS, start=1):
        existing = db.scalar(select(Writing).where(Writing.lesson_id == str(lesson.id), Writing.title == title))
        if existing is not None:
            continue
        db.add(
            Writing(
                lesson_id=str(lesson.id),
                title=title,
                instruction=instruction,
                min_words=5,
                max_words=60,
                order_index=order_index,
                is_published=True,
            )
        )
        created += 1
    print(f"  Created {created} Schreiben task(s) (of {len(WRITING_TASKS)} total).")
    return created


def seed_speaking(db, lesson: Lesson) -> int:
    existing = db.scalar(
        select(Speaking).where(Speaking.lesson_id == str(lesson.id), Speaking.title == SPEAKING_TITLE)
    )
    if existing is not None:
        print(f"  Sprechen '{SPEAKING_TITLE}' already exists - skipping.")
        return 0

    db.add(
        Speaking(
            lesson_id=str(lesson.id),
            title=SPEAKING_TITLE,
            topic=SPEAKING_TOPIC,
            instruction=SPEAKING_INSTRUCTION,
            order_index=1,
            is_published=True,
        )
    )
    print(f"  Created Sprechen '{SPEAKING_TITLE}'.")
    return 1


def seed_grammar_quiz(db, lesson: Lesson) -> tuple[int, int]:
    quiz = db.scalar(
        select(Quiz).where(
            Quiz.lesson_id == str(lesson.id), Quiz.quiz_type == QUIZ_TYPE_GRAMMAR, Quiz.title == QUIZ_TITLE
        )
    )
    quizzes_created = 0
    if quiz is None:
        quiz = Quiz(
            lesson_id=str(lesson.id),
            quiz_type=QUIZ_TYPE_GRAMMAR,
            title=QUIZ_TITLE,
            description=QUIZ_DESCRIPTION,
            order_index=1,
            is_published=True,
        )
        db.add(quiz)
        db.flush()
        quizzes_created = 1
        print(f"  Created Grammatik Quiz '{QUIZ_TITLE}'.")
    else:
        print(f"  Grammatik Quiz '{QUIZ_TITLE}' already exists - checking questions.")

    questions_created = 0
    for order_index, (question_text, options, correct_index) in enumerate(QUIZ_QUESTIONS, start=1):
        existing_question = db.scalar(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id, QuizQuestion.question == question_text)
        )
        if existing_question is not None:
            continue

        question = QuizQuestion(
            quiz_id=quiz.id,
            question=question_text,
            order_index=order_index,
            is_published=True,
        )
        db.add(question)
        db.flush()

        for option_index, option_text in enumerate(options):
            db.add(
                QuizOption(
                    question_id=question.id,
                    option_text=f"{OPTION_LETTERS[option_index]}) {option_text}",
                    is_correct=(option_index == correct_index),
                    order_index=option_index + 1,
                )
            )
        questions_created += 1

    print(f"  Created {questions_created} Grammatik Quiz question(s) (of {len(QUIZ_QUESTIONS)} total).")
    return quizzes_created, questions_created


def main() -> None:
    db = SessionLocal()
    try:
        lesson = get_lesson_1(db)
        if lesson is None:
            print(
                "ERROR: could not find an existing A1 Lesson 1 "
                "(Language 'de' -> Course level='A1' -> first Module -> Lesson number=1). "
                "This script never creates a Lesson - aborting without changes."
            )
            return

        print(f"Found A1 Lesson 1: id={lesson.id} title={lesson.title!r}")

        seed_grammar(db, lesson)
        seed_vocabulary(db, lesson)
        seed_reading(db, lesson)
        seed_listening(db, lesson)
        seed_writing(db, lesson)
        seed_speaking(db, lesson)
        seed_grammar_quiz(db, lesson)

        db.commit()
        print()
        print(f"Done. Lesson 1 id={lesson.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
