"""Fill the grammar of the A2 lesson words that the Wörterbuch does not cover, from
app/scripts/a2_wortschatz_grammar_data.py (source "vizu-grammatik"). Only EMPTY fields are
filled; the book's word / article / translation and every admin or Wörterbuch value stay.
Default is the read-only plan.

    python -m app.scripts.a2_wortschatz_grammar plan
    python -m app.scripts.a2_wortschatz_grammar apply --backup-dir DIR --confirm <plan id>"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.vocabulary import Vocabulary
from app.scripts import a2_wortschatz_grammar_data as data
from app.services.lms.a2_module_separation import _lessons, _row

SOURCE = "vizu-grammatik"


def fills(v: Vocabulary) -> dict[str, str]:
    out = {}
    word = v.german_word
    if not v.word_type and word in data.WORD_TYPE:
        out["word_type"] = data.WORD_TYPE[word]
    word_type = out.get("word_type") or v.word_type
    if word_type == "Nomen" and not v.plural and word in data.PLURAL:
        out["plural"] = data.PLURAL[word]
    if word_type == "Verb" and word in data.VERBS:
        for column, value in zip(("verb_praeteritum", "verb_partizip_ii", "verb_auxiliary"), data.VERBS[word], strict=True):
            if not getattr(v, column):
                out[column] = value
    return out


def plan(db) -> dict:
    lessons = _lessons(db)
    rows = db.scalars(select(Vocabulary).where(Vocabulary.lesson_id.in_([lsn.id for lsn in lessons])).order_by(Vocabulary.id))
    items = [{"id": str(v.id), "word": v.german_word, "fill": f} for v in rows if (f := fills(v))]
    digest = hashlib.sha256(json.dumps(items, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    counts: dict[str, int] = {}
    for i in items:
        for k in i["fill"]:
            counts[k] = counts.get(k, 0) + 1
    return {"plan_id": digest, "words": len(items), "fields": counts, "items": items}


def apply(db, backup_root: Path, confirm: str) -> dict:
    current = plan(db)
    if confirm != current["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {current['plan_id']} — nothing was changed")
    folder = backup_root / f"a2-wortschatz-grammar-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{current['plan_id']}"
    folder.mkdir(parents=True, exist_ok=False)
    words = {str(v.id): v for v in db.scalars(select(Vocabulary).where(Vocabulary.id.in_([i["id"] for i in current["items"]])))}
    (folder / "backup.json").write_text(json.dumps([_row(v) for v in words.values()], default=str, ensure_ascii=False, indent=1), encoding="utf-8")
    for item in current["items"]:
        v = words[item["id"]]
        sources = dict(v.data_sources or {})
        for column, value in item["fill"].items():
            setattr(v, column, value)
            sources[column] = SOURCE
        v.data_sources = sources
    write_audit(db, actor_id=None, action="a2_vocabulary_grammar_filled",
                details=f"plan={current['plan_id']}; words={current['words']}; fields={current['fields']}; source={SOURCE}; backup={folder}")
    return {k: current[k] for k in ("plan_id", "words", "fields")} | {"backup": str(folder)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    sub.add_parser("plan")
    a = sub.add_parser("apply")
    a.add_argument("--backup-dir", required=True)
    a.add_argument("--confirm", required=True)
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                result = plan(db)
                print(json.dumps({k: result[k] for k in ("plan_id", "words", "fields")}, ensure_ascii=False, indent=1))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply(db, Path(args.backup_dir), args.confirm), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
