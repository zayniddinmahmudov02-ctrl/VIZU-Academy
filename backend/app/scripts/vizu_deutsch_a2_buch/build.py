"""Writes the book-faithful A2 edition as import documents:
app/data/vizu_deutsch_a2_buch/unterricht_01.json … unterricht_13.json
(lesson 14 "Wiederholung" has no pages in the book, so no document).

    python -m app.scripts.vizu_deutsch_a2_buch.build
"""

import json
from pathlib import Path

from app.services.content_import.schema import SCHEMA_VERSION, ContentDocument

from . import items

LESSONS = range(1, 14)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "vizu_deutsch_a2_buch"


def document(n: int) -> dict:
    return {"schema_version": SCHEMA_VERSION, "language": "de", "source": "vizu-deutsch-a2-buch", "items": items(n)}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for n in LESSONS:
        doc = document(n)
        ContentDocument.model_validate(doc)
        path = OUT_DIR / f"unterricht_{n:02d}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(doc['items'])} items")


if __name__ == "__main__":
    main()
