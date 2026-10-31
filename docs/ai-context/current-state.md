# Current state

Updated 2026-10-31.

## Revisions
| Where | Revision | Note |
|---|---|---|
| Local `main` | `cf1d287` | committed by the owner (GitHub Desktop) — includes the A2 processing work |
| Server checkout | `e414b68` + overlay of the A2 processing files (same content as `cf1d287`, not yet pulled) | next deploy: compare, reset the identical files, `git pull --ff-only` |
| DB (local test + production) | Alembic `c4f7a9e2d6b3` | |
| Frontend production slot | `.next-b`, deployment `e414b68-20261030024115` | `.next-a` = previous |

## Content (production, 2026-10-30 02:50 CET)
- A2: lessons 1–13 published (14 "Wiederholung" draft); Lesen/Schreiben/Sprechen/Grammatik exercises of the
  book edition all published; Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 readiness: `NEEDS_CONTENT` (only `hoeren_published` + the 4 manual checks open); sales enabled.

## Last verification
- Local backend 917 passed / 17 skipped; E2E `a2-audio-processing` 5 passed, 1 skipped; server tests 144 OK.
- Production smoke 2026-10-30: pages 200, protected APIs 401, 0 errors in logs, bots active.

## Open decisions for the owner
See `known-issues.md` #1–#8.
