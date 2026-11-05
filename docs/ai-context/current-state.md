# Current state

Updated 2026-11-05.

## Revisions

| Where | Revision | Note |
| --- | --- | --- |
| Local `main` = `origin/main` | `d00a67a` (dashboard redesign) | uncommitted: dashboard-deploy docs, the whole mobile-app work, dashboard pass 2 (banner/courses frame), Battle audio + Wortschatz completion — no git on this machine since 2026-11-05 |
| Server checkout | `d00a67a` via `git pull --ff-only` (2026-11-05) | untracked leftovers `frontend/package-lock.json` (M), `package-lock.json`, `"hlarni xavfsiz saqlash"` — pre-existing, not ours |
| DB | production Alembic `e5a9c3f1b7d2`; local test DBs `f2b6d8a4c1e9` (`app_releases`) | |
| Frontend production slot | `.next-a`, deployment `d00a67a-20261105044618` | `.next-b` = previous (`99390cd`, rollback) |
| Last backup | `/var/backups/vizu/pre-dashboard-20261105-044137` (144 tables, 0 differing) | before: `pre-battle-20261105-010814` |

## Content (production)

- Battle (2026-11-05): 89 published A1 picture words + 89 published pictures, 6 published themes; all stages playable (A2+ use A1 words).
- A2: lessons 1–13 published (14 "Wiederholung" draft); Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 written tasks: Schreiben 25 · Grammatik 5 · Wortschatz 9 · Lesen 1 (`writings.competency`).
- A2 Wortschatz: 216 words, 32 published test sets. A2 readiness `NEEDS_CONTENT`; sales enabled.

## Last verification (2026-11-05)

- Dashboard pass 2 (local, not deployed): tsc/eslint OK, unit 37/37; E2E `dashboard-layout` 8/8 (+ viewport sweep 1920,
  1440, 1366, 820, 390, 360: no overflow, banner on top, toggle ≥ 44 px, no clipped CTA), `student-panel`, `admin`,
  `mobile-app` all passed; `battle-dashboard` only the known leaderboard-photo data failure (`mobile-known-issues.md` #8).
- Mobile app (local, not deployed): backend 1007 passed / 17 skipped; frontend tsc/eslint OK, unit 37/37; E2E
  `mobile-app` 8 passed (+2 skipped by design); regression `auth/admin/student-panel/battle-dashboard/battle` 55 passed,
  6 skipped, 1 failed (`battle-dashboard` leaderboard photo: E2E-data issue, `mobile-known-issues.md` #8). APK: debug +
  test-signed release built, `apksigner` OK, installed and run on the Android 15 emulator. Status: `mobile-app-overview.md`.
- Dashboard deploy (`d00a67a`): frontend tsc/eslint OK, unit 32/32; E2E `battle-dashboard` + `student-panel` 16/16
  (desktop + Pixel 7). Server unittest (battle, profile_photo, route protection) 41 OK (13 DB skips). Production smoke:
  11 pages 200, anonymous APIs 401 (battle/summary, lms/levels, learning-activity, users/me/photo), new strings in
  `.next-a`, users/certificates/achievements/dictionary/lessons/battle counts equal to backup, errors 0, bots active.
- Earlier (Battle deploy): local backend 980 passed / 17 skipped; E2E `battle`, `admin`, `auth`, `student-panel` passed.

## Open decisions for the owner

See `known-issues.md` #1–#8, #13, #15–#17.
