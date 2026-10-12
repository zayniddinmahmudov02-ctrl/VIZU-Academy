"""Writes the VIZU-DEUTSCH A1 book content as import documents (format 1.1):
app/data/vizu_deutsch_a1/modul_01.json … modul_14.json.

    python -m app.scripts.vizu_deutsch_a1.build
"""

import importlib
import json
from pathlib import Path

from app.services.content_import.schema import SCHEMA_VERSION, ContentDocument

MODULES = range(1, 15)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "vizu_deutsch_a1"


def document(n: int) -> dict:
    mod = importlib.import_module(f"app.scripts.vizu_deutsch_a1.modul_{n:02d}")
    return {"schema_version": SCHEMA_VERSION, "language": "de", "source": "vizu-deutsch-a1-book", "items": mod.items()}


def available_modules() -> list[int]:
    out = []
    for n in MODULES:
        try:
            importlib.import_module(f"app.scripts.vizu_deutsch_a1.modul_{n:02d}")
        except ModuleNotFoundError:
            continue
        out.append(n)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for n in available_modules():
        doc = document(n)
        ContentDocument.model_validate(doc)  # format check (keys are checked by the importer)
        path = OUT_DIR / f"modul_{n:02d}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(doc['items'])} items")


if __name__ == "__main__":
    main()
