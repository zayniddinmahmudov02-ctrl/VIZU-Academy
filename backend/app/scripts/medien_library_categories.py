"""Bibliothek: put every book into one of the six categories (Literatur, Historisch, Beruflich, Sonstige, Prüfungsvorbereitung,
Wortschatz) by its real content. The categories themselves come from migration c8d3f5a1e7b2.

The assignment of the production books was decided by reading each book (title, author, description and the PDF's own text,
2026-11-23) — see ASSIGNMENTS (matched by exact title, with the reason). A book that is not listed keeps its category when that
category is one of the six; a book without one (or in an inactive old category) goes to Sonstige. Only `media_books.category_id`
changes: ids, files, URLs, progress and purchases stay untouched; nothing is deleted.

    python -m app.scripts.medien_library_categories plan
    python -m app.scripts.medien_library_categories apply --confirm <plan id> --backup-dir /var/backups/vizu/<dir>

`apply` re-checks the plan id, writes a JSON copy of every changed book's old category first, then commits and writes one
audit_logs row (action medien_library_categories).
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.medien import MediaBook, MediaCategory

SIX = ("literatur", "historisch", "beruflich", "sonstige-buecher", "pruefungsvorbereitung", "wortschatz")
FALLBACK = "sonstige-buecher"
ASSIGNMENTS = {
    "VIZU-Deutsch A1": ("sonstige-buecher", "Lehrbuch (Grammatik, Wortschatz, Übungen) — kein Roman, keine Prüfungs- oder Wortliste"),
    "VIZU-Deutsch A2": ("sonstige-buecher", "Lehrbuch (Grammatik, Wortschatz, Übungen) — kein Roman, keine Prüfungs- oder Wortliste"),
    "VIZU-Deutsch B1": ("sonstige-buecher", "Lehrbuch (Grammatik, Wortschatz, Übungen) — kein Roman, keine Prüfungs- oder Wortliste"),
    "Alchemist": ("literatur", "Roman (Paulo Coelho, Der Alchimist)"),
    "Ein Hund namens Money": ("literatur", "Erzählung / Kinderroman (Bodo Schäfer): die Geschichte von Kira und dem Hund Money"),
    "Erster Tag in der Schule": ("literatur", "kurze Geschichte (\"Erster Schultag von Fix\")"),
    "Starke Verben - Kuchli Fe`llar": ("wortschatz", "Tabelle der starken / unregelmäßigen Verben A1–C2 mit Präteritum, Perfekt und "
                                                     "Übersetzungsspalte — Wortschatz, kein Prüfungsmaterial"),
    "A1 Wortliste Goethe": ("wortschatz", "Goethe-Wortliste A1"),
    "A2 Wortliste - Goethe": ("wortschatz", "Goethe-Wortliste A2"),
    "B1 Wortliste Goethe": ("wortschatz", "Goethe-Wortliste B1"),
}


def _categories(db: Session) -> dict:
    return {c.slug: c for c in db.scalars(select(MediaCategory).where(MediaCategory.kind == "BOOK"))}


def build_plan(db: Session) -> dict:
    cats = _categories(db)
    missing = [s for s in SIX if s not in cats or not cats[s].is_active]
    if missing:
        raise RuntimeError(f"categories missing or inactive (run the migration first): {missing}")
    by_id = {c.id: c for c in cats.values()}
    items = []
    for book in db.scalars(select(MediaBook).order_by(MediaBook.created_at)):
        current = by_id.get(book.category_id)
        if book.title in ASSIGNMENTS:
            slug, reason = ASSIGNMENTS[book.title]
        elif current is not None and current.slug in SIX:
            slug, reason = current.slug, "bleibt (Kategorie passt)"
        else:
            slug, reason = FALLBACK, "keine eindeutige Kategorie -> Sonstige"
        target = cats[slug]
        items.append({"book_id": str(book.id), "title": book.title, "from": current.name if current else None, "to": target.name,
                      "to_id": str(target.id), "change": book.category_id != target.id, "reason": reason})
    changes = [(i["book_id"], i["to_id"]) for i in items if i["change"]]
    return {"plan_id": hashlib.sha256(json.dumps(changes, sort_keys=True).encode()).hexdigest()[:12], "items": items}


def apply_plan(db: Session, confirm: str, backup_dir: Path) -> dict:
    plan = build_plan(db)
    if plan["plan_id"] != confirm:
        raise RuntimeError(f"plan id is {plan['plan_id']}, not {confirm} — run `plan` again")
    changes = [i for i in plan["items"] if i["change"]]
    backup_dir.mkdir(parents=True, exist_ok=True)
    books = {str(b.id): b for b in db.scalars(select(MediaBook).where(MediaBook.id.in_([i["book_id"] for i in changes])).with_for_update())}
    snap = backup_dir / f"library-categories-before-{plan['plan_id']}.json"
    snap.write_text(json.dumps({"taken_at": datetime.now(timezone.utc).isoformat(),
                                "books": [{"id": k, "category_id": str(b.category_id) if b.category_id else None} for k, b in books.items()]},
                               indent=1), encoding="utf-8")
    for item in changes:
        books[item["book_id"]].category_id = item["to_id"]
    db.add(AuditLog(actor_id=None, action="medien_library_categories",
                    details=f"plan={plan['plan_id']}; changed={len(changes)}; " + "; ".join(f"{i['title']}: {i['from']} -> {i['to']}" for i in changes)[:900]))
    db.commit()
    return {"plan_id": plan["plan_id"], "changed": len(changes), "backup": str(snap)}


def _print_plan(plan: dict) -> None:
    changed = [i for i in plan["items"] if i["change"]]
    print(f"Bibliothek categories — plan id {plan['plan_id']} — {len(plan['items'])} book(s), {len(changed)} change(s)")
    for i in plan["items"]:
        mark = "CHANGE" if i["change"] else "keep  "
        print(f"  {mark} {i['title']!r}: {i['from']} -> {i['to']} ({i['reason']})")


def main(argv=None) -> int:
    from app.db.session import SessionLocal

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    ap = sub.add_parser("apply")
    ap.add_argument("--confirm", required=True)
    ap.add_argument("--backup-dir", required=True)
    args = parser.parse_args(argv)
    db = SessionLocal()
    try:
        if args.cmd == "plan":
            _print_plan(build_plan(db))
            print("READ-ONLY: nothing was changed.")
        else:
            print(json.dumps(apply_plan(db, args.confirm, Path(args.backup_dir)), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    finally:
        db.rollback()
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
