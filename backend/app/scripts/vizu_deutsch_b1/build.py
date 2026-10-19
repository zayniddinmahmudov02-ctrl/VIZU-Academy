"""Writes the VIZU-DEUTSCH B1 book content as import documents:
app/data/vizu_deutsch_b1/unterricht_01.json … unterricht_16.json.

    python -m app.scripts.vizu_deutsch_b1.build
    python -m app.scripts.vizu_deutsch_b1.build --modules 1
"""

import importlib
import json
from pathlib import Path

from app.services.content_import.schema import SCHEMA_VERSION, ContentDocument

MODULES = range(1, 17)  # the book has lessons 1-16 (the table of contents lists 20)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "vizu_deutsch_b1"


def document(n: int) -> dict:
    mod = importlib.import_module(f"app.scripts.vizu_deutsch_b1.unterricht_{n:02d}")
    return {"schema_version": SCHEMA_VERSION, "language": "de", "source": "vizu-deutsch-b1-book", "items": mod.items()}


def available_modules() -> list[int]:
    out = []
    for n in MODULES:
        try:
            importlib.import_module(f"app.scripts.vizu_deutsch_b1.unterricht_{n:02d}")
        except ModuleNotFoundError:
            continue
        out.append(n)
    return out


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Write the B1 book lessons as import documents.")
    parser.add_argument("--modules", type=int, nargs="*", help="book lessons (default: all available)")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for n in args.modules or available_modules():
        doc = document(n)
        ContentDocument.model_validate(doc)
        path = OUT_DIR / f"unterricht_{n:02d}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(doc['items'])} items")


if __name__ == "__main__":
    main()
