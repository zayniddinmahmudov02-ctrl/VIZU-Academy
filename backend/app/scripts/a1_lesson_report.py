"""Read-only report of what students see in an A1 book lesson: Grammatik
images (resources, images in the competency text and in grammar rules),
Lesen texts with their question counts, Hören tasks (questions, audio,
published). Writes nothing — safe to run on production before and after
`import_vizu_deutsch_a1 --replace`.

    python -m app.scripts.a1_lesson_report --lesson 1
"""

import argparse

from sqlalchemy import text

from app.db.session import SessionLocal

LESSON_SQL = ("SELECT le.id, le.title FROM lessons le JOIN modules m ON m.id = le.module_id JOIN courses c ON c.id = m.course_id "
              "JOIN languages lg ON lg.id = c.language_id WHERE lg.code = 'de' AND c.level = 'A1' AND m.number = 1 AND le.number = :n")


def report(db, n: int) -> dict:
    row = db.execute(text(LESSON_SQL), {"n": n}).first()
    if row is None:
        raise SystemExit(f"A1 lesson {n} not found")
    lesson_id = row.id
    one = lambda sql: db.execute(text(sql), {"l": lesson_id}).scalar()  # noqa: E731
    rows = lambda sql: db.execute(text(sql), {"l": lesson_id}).all()  # noqa: E731
    return {
        "lesson": f"{row.title} ({lesson_id})",
        "grammatik_image_resources": one("SELECT count(*) FROM learning_resources WHERE lesson_id = :l AND competency = 'GRAMMATIK' AND resource_type = 'IMAGE'"),
        "grammatik_text_images": one("SELECT count(*) FROM lesson_competencies WHERE lesson_id = :l AND kind = 'GRAMMATIK' AND body ILIKE '%<img%'"),
        "grammar_rules_with_images": one("SELECT count(*) FROM grammars WHERE lesson_id = :l AND is_published AND content::text ILIKE '%<img%'"),
        "image_resources": [f"{r.competency or '-'}: {r.title} (published={r.is_published})" for r in rows(
            "SELECT competency, title, is_published FROM learning_resources WHERE lesson_id = :l AND resource_type = 'IMAGE' ORDER BY competency, title")],
        "lesen": [f"{r.title}: {r.n} question(s)" for r in rows(
            "SELECT r.title, (SELECT count(*) FROM reading_questions q WHERE q.reading_id = r.id) AS n FROM readings r "
            "WHERE r.lesson_id = :l AND r.is_published ORDER BY r.order_index, r.title")],
        "hoeren": [f"{r.title}: {r.n} question(s), audio={'yes' if r.audio else 'NOT UPLOADED'}, published={r.is_published}" for r in rows(
            "SELECT l.title, l.is_published, (l.audio_storage_path IS NOT NULL OR l.audio_url IS NOT NULL) AS audio, "
            "(SELECT count(*) FROM listening_questions q WHERE q.listening_id = l.id) AS n FROM listenings l "
            "WHERE l.lesson_id = :l AND l.title NOT LIKE '[Archiv]%' ORDER BY l.order_index, l.title")],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lesson", type=int, default=1, help="A1 lesson number (book Modul)")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        r = report(db, args.lesson)
    finally:
        db.close()
    print(f"A1 lesson {args.lesson}: {r['lesson']}")
    ok = not (r["grammatik_image_resources"] or r["grammatik_text_images"] or r["grammar_rules_with_images"])
    print(f"Grammatik images: resources={r['grammatik_image_resources']} in text={r['grammatik_text_images']} "
          f"in rules={r['grammar_rules_with_images']}  -> {'OK (0)' if ok else 'OLD IMAGES PRESENT'}")
    for key in ("image_resources", "lesen", "hoeren"):
        print(f"{key}:")
        for line in r[key] or ["(none)"]:
            print(f"  {line}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
