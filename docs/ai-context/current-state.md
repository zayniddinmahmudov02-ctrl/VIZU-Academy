# Current state

Updated 2026-11-05.

## Revisions

| Where | Revision | Note |
| --- | --- | --- |
| Local `main` = `origin/main` | `99390cd` (VIZU DEUTSCH BATTLE) + docs | |
| Server checkout | `99390cd` via `git pull --ff-only` (2026-11-05) | untracked leftovers `frontend/package-lock.json` (M), `package-lock.json`, `"hlarni xavfsiz saqlash"` — pre-existing, not ours |
| DB (local test + production) | Alembic `e5a9c3f1b7d2` | |
| Frontend production slot | `.next-b`, deployment `99390cd-20261105011349` | `.next-a` = previous (rollback) |
| Last backup | `/var/backups/vizu/pre-battle-20261105-010814` (137 tables, 0 differing; migration SQL + seed plan/apply JSON inside) | before: `pre-a2gram-20261101-045927` |

## Content (production)

- Battle (2026-11-05): 89 published A1 picture words + 89 published pictures, 6 published themes; all stages playable (A2+ use A1 words).
- A2: lessons 1–13 published (14 "Wiederholung" draft); Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 written tasks: Schreiben 25 · Grammatik 5 · Wortschatz 9 · Lesen 1 (`writings.competency`).
- A2 Wortschatz: 216 words, 32 published test sets. A2 readiness `NEEDS_CONTENT`; sales enabled.

## Last verification (2026-11-05)

- Local backend 980 passed / 17 skipped; frontend unit 28/28; E2E `battle` 8 passed (+2 skipped by design), `admin`,
  `auth`, `student-panel` 40 passed.
- Server unittest (battle, migration, route protection, page management) 43 OK (13 DB skips). Production smoke: pages 200,
  Battle APIs anonymous 401, forged media token 404, other tables unchanged vs backup, backend errors 0, bots active.

## Open decisions for the owner

See `known-issues.md` #1–#8, #13, #15–#17.
