"""Loads VIZU-Multilevel Lesen from app/content/vizu_multilevel/lesen.json
(20 Aufgaben, 1 question each, 5 points -> 100). Replaces existing Lesen
content in one transaction; a no-op when the content is already identical.

Run from backend/:  python -m app.scripts.seed_vizu_multilevel_lesen
"""

from app.db.session import SessionLocal
from app.services.vizu_multilevel import lesen_json_import_service


def main() -> None:
    db = SessionLocal()
    try:
        print(lesen_json_import_service.import_default(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
