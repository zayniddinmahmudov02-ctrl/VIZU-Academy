"""Idempotent seed for VIZU-Mock -> Schreiben: exactly 5 Aufgaben, 20 points
each (100 total), each with its analytic rubric.

The content lives in app.services.vizu_multilevel.schreiben_content (shared
with the API's ensure_content safety net). Matching is by Aufgabe number
(order_index):
* first run  -> creates the 5 Aufgaben;
* later runs -> update the same 5 rows in place (texts / word limits /
  points / rubric) — never duplicates;
* unchanged content -> nothing changes.
Student submissions are never touched.

Run on the server (from backend/):
    python -m app.scripts.seed_vizu_mock_schreiben
"""

from app.db.session import SessionLocal
from app.services.vizu_multilevel.schreiben_content import POINTS_PER_TASK, TASKS, seed  # noqa: F401


def main() -> None:
    db = SessionLocal()
    try:
        print("seed:", seed(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
