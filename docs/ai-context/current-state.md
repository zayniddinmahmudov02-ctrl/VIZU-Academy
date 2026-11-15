# Current state

Updated 2026-11-15.

## Revisions

| Where | Revision | Note |
| --- | --- | --- |
| `origin/main` | `0cb7b165` (owner push 2026-11-15 04:08 = overlays 1–4: packages, lesson gating, audio trim / Multilevel Audio, Medienwelt) | local machine still has no git; overlays 5 "Student navigation" and 6 "Film player" (below) are NOT pushed yet |
| Server checkout | `0cb7b165` + **LF overlay 5 "Student navigation"** (22 files, `dashboard-courses.tsx` removed) + **LF overlay 6 "Film player"** (36 files; list = `overlay-replaced.txt` / `film_overlay.tar` in the backup dir, originals `overlay-originals.tar`). Once the owner pushes: `git checkout -- <modified>`, remove the new untracked files, `git pull --ff-only` (script pattern: `px4_sync`; every dirty file must first be byte-identical to origin) | leftovers `package-lock.json` (root), `"hlarni xavfsiz saqlash"` — pre-existing, not ours |
| DB (production + local test) | Alembic `b6e2d9f4a1c8` (film player: subtitle analysis columns, `film_renditions`, `media_player_prefs`, `media_progress.player_state`; applied 2026-11-15; before: `f4c8a1e6b9d2` Medienwelt, `e8b4d2f6a1c3`, `c7e1f3a9b2d5`) | SQL preview `migration-b6e2d9f4a1c8.sql` in the backup dir |
| Frontend production slot | `.next-b`, deployment `0cb7b165-20261115031347` (overlay 6; build passed first time) | `.next-a` = previous (rollback: `docs/deploy-frontend.md`) |
| Last backup | `/var/backups/vizu/pre-film-player-20261115-031221` (DB dump with restore list check, 21 originals of overlay 6) | before: `pre-nav-20261115-010539`, `pre-medien-20261114-233902`, `pre-audio-trim-…`, `pre-lesson-gating-…`, `pre-course-packages-…` |
| Overlay 6 | "Film player + subtitles" 2026-11-15: backend (new `services/medien/{subtitles,player,lookup}.py`, routers, migration, restart) + frontend; smoke: 14 pages 200 (local + public), 13 new endpoints refuse anonymous calls (401 / 422), new strings in the build, DB at `b6e2d9f4a1c8`, services + bots active, logs clean. Production had 0 films / 0 subtitles at deploy (nothing existing touched); `ffmpeg` + `ffprobe` exist on the server | local: backend suite 1078 passed / 17 skipped, unit 55 passed, E2E `film-player.spec.ts` 9 desktop + 1 phone passed, `medien.spec.ts` desktop 8 passed (one Musik-favorite flake in one run, passed on rerun) |
| Overlay 5 | "Student navigation" 2026-11-15, frontend only (no backend restart, no migration): dashboard hub of five cards, `/kurse` level status chips, language switcher on top of sidebar + mobile drawer, certificates Print, `hub` texts; smoke: 15 pages 200 (local + public), old URLs `/courses`, `/courses/a1`, `/lessons` redirect, new strings in the build, old frame strings 0, services + bots active | local E2E: 135 passed; 6 failures not from this work (Battle: 3 stale scoring expectations in `battle.spec.ts`, profile-photo leaderboard state in `battle-dashboard.spec.ts`) |

## Packages (production, 2026-11-14)

Table `course_packages`, edited in Admin → Angebote (no prices in the frontend). A1 49 000 (was the admin override; kept) /
A2 99 000, 30 days; B1 100 000, 60 days; A1–B1 200 000, 180 days; A1–C1 400 000, 365 days (opens B2/C1 when released);
B2, C1, B2–C1 COMING_SOON (not buyable). The old `app_settings.angebote.offers` overrides (incl. B2/C1 149 000 and the
bundle strike-through prices) are no longer read. 33 orders, 2 promo codes, 0 approval requests at deploy.

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

## Last verification (2026-11-15 · Medienwelt)

- Local: backend 1047 passed / 17 skipped (`test_medien` 10 over HTTP with real PDF / PNG / MP3 / MP4 + Range + chunked upload,
  `test_medien_migration`), frontend tsc + eslint clean, unit 45/45, E2E `medien.spec.ts` 9 passed (desktop + Pixel 7: admin
  CRUD + uploads, bulk 10 songs with one bad file, student shelves / filters / PDF reader resume / purchase grant, global player
  keeps playing across pages + reload restore, playlists / favorites, film player speed + de/uz subtitles + continue watching,
  security) and 69 regression E2E passed. Production: server unittest 66 OK (30 DB/ffmpeg skips), migration additive,
  `/medien*` + `/admin/medien*` pages 200, new APIs anonymous 401, 15 + 8 seeded categories, 0 content rows, orders / users
  unchanged, bots active. Not done on production: real uploads / playback (no test content or users allowed there).
- Found by the tests and fixed: reader overlay hidden under the dashboard header (portal to body), film length filter sent
  wrong query keys, film resume threshold, progress lost on page close (keepalive save), player bar covering the sidebar,
  unreadable text on two gradients. Known, not mine: the shared `PageTransition` remounts a page once after a client-side
  navigation (state typed in the first second is lost).

## Earlier verification (2026-11-15 · audio)

- Audio trim + Multilevel Audio deploy: local backend 1036 passed / 17 skipped (new `test_multilevel_audio` 5 with real
  ffmpeg WAV/MP3/M4A trims, migration up/down/up, 401/403), frontend tsc + eslint OK, unit 45/45, E2E `multilevel-audio`
  7 passed (desktop + Pixel 7) and regression specs (multilevel-exam, a2 audio manager, a2 lesson 4, admin, purchase,
  lesson-gating) green. Production: server unittest 55 OK (19 DB/ffmpeg skips), migration c7e1f3a9b2d5 → e8b4d2f6a1c3
  (additive), health 200, new endpoints anonymous 401, Multilevel Audio overview 26 slots (MT1 6, MT2–6 4, MT7–10 none),
  ffmpeg + ffprobe present (existing file probed, a 2 s cut of it made in /tmp and deleted), orders / users unchanged, bots
  active. Not done on production: a real upload / trim (no test audio allowed there) — owner's first upload is the live test.
  Local A2 specs (`a2-audio-manager`, `a2-lesson4-hoeren`) need their seeds + `a2_lesson4_hoeren apply --confirm <id> --backup-dir`
  before each run (stateful); `a2-audio-manager` now expects A2 purchasable (packages).

## Earlier verification (2026-11-14)

- Lesson gating deploy: local backend 1029 passed / 17 skipped (new `test_lesson_purchase_gating` 8), frontend tsc + eslint
  OK, unit 40/40, E2E `lesson-gating` + `purchase` 11 passed (desktop + Pixel 7: Bepul badge, sheet text, Ortga qaytish,
  Xarid qilish → /angebote, API 403, real checkout + admin approval opens the level). Production: server unittest 85 OK,
  health 200, A1/A2/B1 lesson 1 open / 2+ `PREMIUM_REQUIRED`, B2 `LEVEL_COMING_SOON`, anonymous quiz list 603 → 72
  questions (one free lesson only), strings in `.next-b`, bots active.

- Course packages deploy: local backend full suite 1021 passed / 17 skipped, package + migration DB tests 31 passed after
  the migration fix, frontend tsc OK, unit 40/40, E2E purchase + admin + multilevel-exam 11 passed (desktop + Pixel 7).
  Production: server unittest 93 OK (21 DB skips), migration a3c9e7b5d1f4 → c7e1f3a9b2d5 (additive only), health 200,
  `/vizu-pay/offers` as in "Packages", 6 new/changed APIs anonymous 401, 11 pages 200, strings in `.next-a`, orders /
  promo codes / users unchanged, bots active. Not done on production: a real purchase (no test users / payments there).

## Earlier verification (2026-11-06)

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
