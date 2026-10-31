# Current state

Updated 2026-11-01.

## Revisions
| Where | Revision | Note |
|---|---|---|
| Local `main` = `origin/main` | `7749ea4` (A2 module separation) + doc update | |
| Server checkout | `7749ea4` via `git pull --ff-only` (2026-11-01) | untracked leftovers `frontend/package-lock.json` (M), `package-lock.json`, `"hlarni xavfsiz saqlash"` — pre-existing, not ours |
| DB (local test + production) | Alembic `d7e2b4f8a1c6` | |
| Frontend production slot | `.next-a`, deployment `7749ea4-20261031214051` | `.next-b` = previous (rollback) |
| Last backup | `/var/backups/vizu/pre-a2modsep-20261031-213415` (restore check 135 tables, 0 differing) | also `…-213514` (second copy) |

## Content (production, 2026-11-01)
- A2: lessons 1–13 published (14 "Wiederholung" draft); Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 written tasks: Schreiben 25 · Grammatik 5 · Wortschatz 9 · Lesen 1 (`writings.competency`).
- A2 Wortschatz: 216 words (130 enriched from verified Wörterbuch entries), 32 published test sets (L1–4: 7 each, L9: 4).
- A2 readiness: `NEEDS_CONTENT` (only `hoeren_published` + the 4 manual checks open); sales enabled.

## Last verification
- Local backend 949 passed / 17 skipped; frontend unit 23/23; E2E `a2-module-separation` 11 passed, 1 skipped.
- Server unittest 109 OK (15 skipped). Production smoke 2026-11-01: pages 200, new APIs anonymous 401, Schreiben counts only
  Schreiben tasks, other levels unchanged, backend errors 0, bots active.

## Open decisions for the owner
See `known-issues.md` #1–#8, #13.
