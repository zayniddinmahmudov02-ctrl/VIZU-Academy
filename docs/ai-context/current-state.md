# Current state

Updated 2026-11-05.

## Revisions

| Where | Revision | Note |
| --- | --- | --- |
| `origin/main` | `392c2a9f` (owner pushed the local work from GitHub Desktop: mobile app, dashboard pass 2, Battle audio, Wortschatz rule) | local machine still has no git |
| Server checkout | `392c2a9f` via `git pull --ff-only` (2026-11-05) + **LF overlays** (no local git), all identical to the local files: (1) Wortschatz UI — `wortschatz-section.tsx`, `translations.ts`, `globals.css`, `lms-flashcards.tsx` deleted (originals `/var/backups/vizu/pre-wortschatz-ui-20261105-084616`); (2) Battle points — `services/battle/{config,engine,questions,home}.py`, `tests/test_battle.py`, `battle/components/{result,battle-home}.tsx`, `battle-service.ts`, `battle-translations.ts` (originals `/var/backups/vizu/pre-battle-points-20261105-085529/files`). Once the owner pushes them: `git checkout -- <these files>` (+ `git checkout -- frontend/src/components/lms/lms-flashcards.tsx`) on the server, then `git pull --ff-only` | untracked leftovers `frontend/package-lock.json` (M), `package-lock.json`, `"hlarni xavfsiz saqlash"` — pre-existing, not ours |
| DB (production + local test) | Alembic `f2b6d8a4c1e9` (`app_releases`, empty) | |
| Frontend production slot | `.next-b`, deployment `392c2a9f-20261105085729` (with both overlays) | `.next-a` = previous (Wortschatz overlay only, rollback) |
| Last backup | `/var/backups/vizu/pre-mobile-dash2-20261105-081839` (144 tables, 0 differing; migration SQL inside) | before: `pre-dashboard-20261105-044137` |

## Content (production)

- Battle (2026-11-05): 89 published A1 picture words + 89 published pictures, 6 published themes; all stages playable (A2+ use A1 words).
- A2: lessons 1–13 published (14 "Wiederholung" draft); Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 written tasks: Schreiben 25 · Grammatik 5 · Wortschatz 9 · Lesen 1 (`writings.competency`).
- A2 Wortschatz: 216 words, 32 published test sets. A2 readiness `NEEDS_CONTENT`; sales enabled.

## Last verification (2026-11-05)

- Deploy `392c2a9f`: server unittest 95 OK (36 DB skips); migration preview 1 CREATE TABLE + 1 unique index, 0 drop; health
  200; 14 pages 200 (incl. `/download`, `/admin/app-management`); anonymous APIs 401, `app/releases/latest` 404 (no APK
  yet); new dashboard markers in `.next-b` (course toggle/panel, compact banner, Lernwerkzeuge, "Letzte Aktivität"), no
  Erfolge/Zertifikate cards; counts vs backup only grew (+1 user, +2 Battle profiles = live use); errors 0; bots active.
  Not checked: logged-in production dashboard screenshot (no test accounts on production).
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
