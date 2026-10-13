"""Create the missing VIZU LMS structure (course, main module, lessons 1..N as
drafts, competency rows) for one or all levels. Same function as POST
/admin/lms/levels/{level}/ensure-structure. Idempotent; never deletes or
renumbers anything.

    python -m app.scripts.ensure_lms_structure            # A1 A2 B1 B2 C1
    python -m app.scripts.ensure_lms_structure --levels A2 B1
"""

import argparse

from app.db.session import SessionLocal
from app.services.lms import structure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--levels", nargs="+", default=list(structure.LEVELS), choices=structure.LEVELS)
    args = parser.parse_args()
    db = SessionLocal()
    try:
        for level in args.levels:
            r = structure.ensure_structure(db, level)
            c = r["created"]
            print(
                f"{level}: course {'created' if c['course'] else 'ok'}, module {'created' if c['module'] else 'ok'}, "
                f"new draft lessons {c['lessons'] or '-'}, competency rows +{c['competencies']}"
                + (f", lesson numbers outside 1..{structure.LEVEL_LESSON_COUNTS[level]}: {r['numbers_outside_range']}" if r["numbers_outside_range"] else "")
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
