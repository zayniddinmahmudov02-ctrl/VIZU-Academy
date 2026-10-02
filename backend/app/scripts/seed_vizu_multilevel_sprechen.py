"""Idempotent seed for VIZU-Multilevel Sprechen: 5 Aufgaben x 5 levels = 25
variants (content in app.services.vizu_multilevel.sprechen_content).

* first run  -> creates the 25 variants;
* later runs -> update the same rows in place (matched by Aufgabe + level);
* unchanged  -> nothing changes. Student answers are never touched.

Run on the server (from backend/):
    python -m app.scripts.seed_vizu_multilevel_sprechen
"""

from app.db.session import SessionLocal
from app.services.vizu_multilevel.sprechen_content import seed


def main() -> None:
    db = SessionLocal()
    try:
        print("seed:", seed(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
