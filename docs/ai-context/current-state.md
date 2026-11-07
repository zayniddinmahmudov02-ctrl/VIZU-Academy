# Current state

Updated 2026-11-06.

## Revisions

| Where | Revision | Note |
| --- | --- | --- |
| `origin/main` | `0c5b9b45` (owner push: Multilevel import, keys editor, PDF view) | local machine still has no git; the exam mode (below) is NOT pushed yet |
| Server checkout | `0c5b9b45` via `git pull --ff-only` (2026-11-06, the previous overlay was identical to it) + **LF overlay "Multilevel exam"** (51 files incl. docs: migration `a3c9e7b5d1f4`, `models/mock_attempt_section.py` + 4 mock models, `services/mock_exam/{multilevel_exam_service,multilevel_service,attempt_service}.py`, `api/mock_exam/{multilevel_exam_router,attempt_router}.py`, `main.py`, `page_management.py`, `protected_local.py`, tests, student `vorbereitung/multilevel/**` + components/service/types, `settings/page.tsx`, `translations.ts`, admin `mock-exams/multilevel`, preview page, nav, label rename files, E2E specs; originals `/var/backups/vizu/pre-multilevel-exam-20261105-220413/files`). Once the owner pushes: `git checkout -- <modified>`, remove the new untracked files, `git pull --ff-only` | untracked leftovers `frontend/package-lock.json` (M), `package-lock.json`, `"hlarni xavfsiz saqlash"` — pre-existing, not ours |
| DB (production + local test) | Alembic `a3c9e7b5d1f4` (Multilevel exam mode, applied 2026-11-06) | SQL preview in the backup dir |
| Frontend production slot | `.next-b`, deployment `0c5b9b45-20261105220723` (with the exam overlay) | `.next-a` = previous (rollback) |
| Last backup | `/var/backups/vizu/pre-multilevel-exam-20261105-220413` (145 tables, 0 differing) | before: `pre-multilevel-20261105-170946` |

## Content (production)

- Vorbereitung Multilevel (2026-11-05): level "Multilevel B1–C1" (NATIONAL) with Modelltest 1–10, all **DRAFT**. 1–6: 535
  questions in total incl. 7–10; 1–6 keys 0 (PDFs have none) + Hören audio missing (26 Teile) → admin enters keys/audio,
  then publishes; 7–10: 35/35 keys, Hören "Noch nicht verfügbar", Sprechen 1.2 pictures missing. Check-list per test
  (`docs/multilevel-modelltests.md`). Since 2026-11-06 a timed exam mode exists (`/vorbereitung/multilevel`), but **no test
  is publishable yet**: 1–6 need keys + Hören audio, 7–10 need Hören tasks (guard: all four sections). Scoring settings at
  defaults (50 = Ungeklärt, overall rule unconfirmed). 0 attempts.

- Battle (2026-11-05): 89 published A1 picture words + 89 published pictures, 6 published themes; all stages playable (A2+ use A1 words).
- A2: lessons 1–13 published (14 "Wiederholung" draft); Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 written tasks: Schreiben 25 · Grammatik 5 · Wortschatz 9 · Lesen 1 (`writings.competency`).
- A2 Wortschatz: 216 words, 32 published test sets. A2 readiness `NEEDS_CONTENT`; sales enabled.

## Last verification (2026-11-06)

- Multilevel exam deploy: local backend 1022 passed / 17 skipped (incl. exam flow + migration up/down/up), frontend tsc +
  eslint OK, unit 37/37, E2E `multilevel-exam` 3 passed (student desktop + Pixel 7: no level choice, autosave + reload,
  submit, finish, result /75 /300, history, profile; admin desktop: hub, grading, preview) on a local seed. Production:
  server unittest 27 OK (5 DB skips), migration f2b6d8a4c1e9 → a3c9e7b5d1f4 (1 table, 2 columns, 3 unique), health 200,
  11 pages 200, 11 new APIs anonymous 401, strings in `.next-b`, 145 tables counts unchanged vs backup, errors 0, bots
  active. Not done on production: a real exam run (no published test; no test users allowed there).

- Multilevel deploy: local backend 1010 passed / 23 skipped, frontend tsc + eslint OK; server unittest 9 OK (2 DB skips);
  no migration; health 200; 7 pages 200; new admin APIs anonymous 401; public list of the new level `[]`, draft test /
  Kompetenz 404; strings in `.next-a`; counts vs backup only grew in mock-exam tables (+1 level, +10 tests, +535 questions,
  +2188 options) and audit +1; importer re-plan = 10× SKIP; errors 0; bots active. Not checked: logged-in admin UI on
  production (no test accounts there) — verified only in tsc/lint and locally by API.

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
