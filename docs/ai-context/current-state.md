# Current state

Updated 2026-11-21.

## Revisions

| Where | Revision | Note |
| --- | --- | --- |
| `origin/main` | `3f6db0f3` (owner pushes up to 2026-11-21 05:38). **It contains the OLD group video chat code** (`c1v7d3e9a5b2_group_video_chat.py`, `video_chat.py`, `group-video-chat.tsx`) that was deleted locally and never deployed: the next owner push must send the current local tree; until then never `git pull` on the server (two Alembic heads). Earlier note: `b1999043` (owner pushes 2026-11-15 07:23 / 08:10 = overlays 5 + 6 and the unfinished work of overlay 7) | **the pushes also contain `frontend/.next-e2e/` (3 458 build files, 95 MB)**: `.next-e2e` is now in `frontend/.gitignore`; the owner should `git rm -r --cached frontend/.next-e2e` and commit BEFORE the server pulls (otherwise `git merge` writes them onto the server). Local machine still has no git |
| Server checkout | `0cb7b165` + LF overlays 5, 6, **7 "Musik fix + Bibliothek + book payments"** (44 files, `books_overlay.tar` in `pre-books-pay-…`) + `set_admin_verification` script (7b) and **8 "Multilevel Hören keys + exam times"** (38 files; list = `overlay-replaced.txt` / `ml_overlay.tar`, originals `overlay-originals.tar` in `pre-ml-keys-…`) and **9 "Modelltest 1 shared Hören audio"** (28 files, `ml_shared_overlay.tar` + originals in `pre-ml-shared-audio-…`) and **11 "Musik vinyl player"** (17 files, frontend only, `vinyl_overlay.tar` + originals in `pre-vinyl-…`) and **10 "Multilevel Premium + promo approval"** (58 files, `ml_premium_overlay.tar` + originals in `pre-ml-premium-…`; `translations-extra.ts` there was the overlay-5 / `origin/main` blob `b0c98744`, accepted) and **12 "Multilevel Modelltest 1–6 open"** (35 files `mlopen_overlay.tar` + 2-file fix `mlopen_overlay2.tar`, originals `overlay-originals.tar` / `overlay2-originals.tar` in `pre-ml-open-…`). **13 "Film AI subtitles + bookshelf + book reader"** (36 files `aisubs_overlay.tar` + 2-file retry fix `aisubs_overlay2.tar`, originals in `pre-ai-subs-…`) **14 "Musik bulk upload 500"** (26 files `bulksongs_overlay.tar`, originals in `pre-bulk-songs-…`) **15 "Film subtitle agents"** (19 files `subagents_overlay.tar` + fixes 15b–15e `subagents_overlay2…5.tar`, originals `overlay*-originals.tar` in `pre-sub-agents-20261119-091821`), **16 "Multilevel Premium for 1–10"** (15 files `mlprem_overlay.tar`, originals in `pre-ml-premium-all-20261119-113128`), **17 "Global Chat button only on the dashboards"** (10 files `chatdash_overlay.tar`, originals in `pre-chat-dashboard-20261119-135705`) and **18 "Battle text questions"** (37 files `bq_overlay.tar`, originals in `pre-battle-questions-20261119-155342`) and **20 "Student statistics"** (5 changed + 8 new files `st_overlay.tar`, originals in `pre-student-stats-20261121-154113`) and **19 "Group video lessons (LiveKit)"** (13 changed + 33 new files `vr_overlay.tar`, originals `overlay-originals.tar` in `pre-video-rooms-20261121-113114`; drift check = sha256 of the production copies fetched just before). `origin/main` is at `020cc329` (owner push after 2026-11-16); not synced with origin on purpose (see above); once the owner has pushed the final files and removed `.next-e2e`: dirty files identical to `origin/main` → `git checkout` them → `git merge --ff-only` |
| DB (production + local test) | Alembic `b7e4c2a9d6f1` (`video_rooms`, `video_room_participants`, `video_room_events`, applied 2026-11-21, SQL preview `migration-b7e4c2a9d6f1.sql` in `pre-video-rooms-20261121-113114`: CREATE TABLE + CREATE INDEX only). Before: `a6c2e8f4b9d1` (`battle_questions`, applied 2026-11-19, SQL preview `migration-a6c2e8f4b9d1.sql` in `pre-battle-questions-20261119-155342`: CREATE TABLE + CREATE INDEX only; 2961 questions seeded with `battle_questions_seed apply --confirm 967b70ff7763`). Before: `f3b9d1a6c4e8` (`film_subtitle_jobs.auto_approve`, applied 2026-11-19, SQL preview `migration-f3b9d1a6c4e8.sql` in `pre-sub-agents-20261119-091821`: one ADD COLUMN … DEFAULT false NOT NULL). Before: `e8a3c5f1b7d2` (`songs.sha256` + index, applied 2026-11-19, SQL preview `migration-e8a3c5f1b7d2.sql` in `pre-bulk-songs-…`: ADD COLUMN + CREATE INDEX only; the 51 existing songs hashed by `medien_song_hashes apply --confirm 45ea88ee8b44`, 0 identical files). Before: `d5f1b8e3a9c7` (film AI subtitles: `film_subtitles.status / source / …`, table `film_subtitle_jobs`; applied 2026-11-19, SQL preview `migration-d5f1b8e3a9c7.sql` in `pre-ai-subs-…`: ADD COLUMN / CREATE TABLE / INDEX only). Before: `a7c4e2f9b1d8` (Multilevel Premium: `user_entitlements`, promo approval / category / personal codes, course promo requests, order `paid_at` / `no_receipt` / notes; applied 2026-11-18; before: `e6d2b9a4c8f3` shared Hören audio, `d4b9e2a7c3f1` Multilevel keys) | SQL preview `migration-a7c4e2f9b1d8.sql` in the backup dir (CREATE TABLE / ADD COLUMN / CHECK / index + the promo backfill: the 2 live codes → ACTIVE + approved by their creator) |
| Frontend production slot | `.next-a`, deployment `0cb7b165-20261121154434` (overlay 20) | `.next-b` = previous (rollback: `docs/deploy-frontend.md`) |
| Overlay 20 | "Student statistics" 2026-11-21: backend (new `services/admin/student_stats.py` = one rule for every student count, `api/admin/stats_router.py` `/admin/stats/{overview,students}`, `main.py`, Languages learners via the same rule, dashboard "new accounts today" by the Tashkent day; restart, no migration, no `.env` change) + frontend (student block on `/admin`, KPI labels; slot `.next-a`) + tests / E2E / docs. Smoke (read-only, production): independent SQL COUNT = API for all 10 numbers — 282 students (284 STUDENT rows − 2 `example.com` test accounts), 185 active, 97 inactive, 0 blocked, 0 teachers, 1 admin, 7 groups, 26 students in groups, 1 new today, 134 this month; list total 282; Languages "de" learners 149 (was 0); anonymous 401; pages 200; all 7 services active; 0 new errors. Backup `pre-student-stats-20261121-154113` (169 tables, 0 differing) |
| Last backup | `/var/backups/vizu/pre-student-stats-20261121-154113` (overlay 20, see its row). Before: `/var/backups/vizu/pre-video-rooms-20261121-113114` (DB dump + scratch-DB restore check: 166 tables, 0 differing; SHA256SUMS; copies of `backend/.env` and the nginx vhost before the change; originals of overlay 19; pip freeze; migration SQL + apply log; frontend deploy log) | before: `pre-battle-questions-20261119-155342` (overlay 18), `pre-chat-dashboard-20261119-135705` (overlay 17) |
| Overlay 19 | "Group video lessons (LiveKit SFU)" 2026-11-21: old local video-chat attempt removed (never deployed); new backend module `video_rooms` (router, services, model, migration `b7e4c2a9d6f1`, `livekit-api==2.0.1` + deps in the venv, restart) + frontend (meeting route `/video-room/[roomId]`, group tabs, admin `/admin/video-rooms`; `npm ci`; slot `.next-b`) + **infrastructure**: `livekit.service` v1.13.11 (checksum-verified binary, own user, limits), `/etc/livekit/livekit.yaml`, nginx `location /livekit/`, 4 `LIVEKIT_*` lines appended to `backend/.env` (values never shown). Smoke: health 200; 7 pages 200 (local + public); `https://vizu-deutsch.com/livekit/` OK through Cloudflare; WebSocket without token 401; TCP 7881 open, 7880 closed from outside; STUN on UDP 3478 answers; LiveKit API from the backend `available`; LiveKit-signed webhooks 200, unsigned 401; new endpoints anonymous 401; groups / members / messages / users counts unchanged; all 7 services active (bots untouched); no new errors. **Not tested:** a real call on production (no test users / tokens there), real devices, UDP-blocked networks; TURN/TLS BLOCKED (`docs/group-video-lessons.md` §7–9) |
| Overlay 18 | "VIZU Battle text questions" 2026-11-19: backend (new `services/battle/{question_bank,question_seed}.py`, `scripts/battle_questions_seed.py`, `data/battle/questions/*.json`, `questions.py` / `engine.py` / `home.py` / `admin.py` / `config.py`, router, models, migration `a6c2e8f4b9d1`, restart) + frontend (text round in `arena-parts.tsx`, admin tab „Fragen“; slot `.next-a`) + tests / E2E / docs. Seed: 2961 published (A1 664, A2 632, B1 528, B2 568, C1 569; 1975 linked to Wörterbuch rows). Smoke (read-only): 0 duplicates / 0 problems per level, 30 built matches per stage: A1 4 picture rounds, A2+ 0 pictures and ≥ 3 grammar, no repeats; battle_matches unchanged (545); anonymous admin question endpoints 401; bots + nginx active |
| Overlay 17 | "Global Chat button only on the dashboards" 2026-11-19: frontend only (new `features/global-chat/chat-visibility.ts`, `global-chat-widget.tsx`, comment in `dashboard-layout.tsx`; slot `.next-b`; no backend restart, no migration) + unit / E2E / docs. Smoke: 9 pages 200 (local + public), the page list in 3 chunks, anonymous `/global-chat/messages` 401, bots + nginx active |
| Overlay 16 | "Multilevel: Premium for every Modelltest 1–10" 2026-11-19: backend only (`multilevel_service.FREE_TEST_NUMBERS` empty + `free_test`, `vizu_pay/access.py`, `multilevel_premium.tests_overview`; restart, no migration, no frontend build: the frontend change is comments only, the page follows the data) + tests / E2E / docs. Smoke (read-only, production data): a student without Premium 10 / 10 locked, Super Admin 0, overview `free` 0 / `premium_total` 10 / 6 published, anonymous `/multilevel-exam/exams` 401, bots + nginx active |
| Overlay 15 | "Film subtitle agents" 2026-11-19: backend (new `services/medien/subtitle_agents.py`, `subtitle_ai.py`, `subtitle_jobs.py`, `admin_router.py`, `models/medien.py`, `config.py` `SUBTITLE_FAST_MODEL` / `SUBTITLE_PROOFREAD`, migration `f3b9d1a6c4e8`, restart) + frontend (`subtitle-manager.tsx`, `medien-admin-service.ts`; slot `.next-a`) + tests / E2E / docs; 15b–15e backend only (busy service waits, fast model only, quiet pieces, daily vs per-minute quota, translations first, placeholder lines). Smoke: 9 pages 200 (local + public), 4 subtitle endpoints 401 anonymous, new strings in the build, bots + nginx active. Then the 3 failed jobs retried (`apply --confirm 0f2b868a91e9`) and the drafts cleaned (`apply --confirm d8bf5bfdf906`) |
| Overlay 14 | "Musik bulk upload of up to 500 songs" 2026-11-19: backend (`services/medien/{song_processing,admin,common}.py`, `core/storage/local.py`, `admin_router.py`, `models/medien.py`, `main.py`, `config.py`, migration `e8a3c5f1b7d2`, script `medien_song_hashes`, restart) + frontend slot switch. Server unittest 58 OK (DB parts skip). Smoke: 11 pages 200 (local + public), 5 song endpoints anonymous 401, new strings in the build, 51 songs / 51 hashes / 51 distinct, metadata all OK, queue empty, worker on, 51 published songs unchanged, all 5 services active (bots untouched), no new errors. Not done on production: a real 500-file upload (no test files on production) — the owner's first bulk upload is the live test |
| Overlay 13 | "Film AI subtitles + Bibliothek bookshelf + book reader" 2026-11-19: backend (`services/medien/{subtitle_ai,subtitle_jobs,admin,catalog}.py`, `admin_router.py`, `models/medien.py`, `main.py` lifespan, `config.py` settings, migration `d5f1b8e3a9c7`, restart) + frontend slot switch; 13b: rate-limit back-off 16 / 32 s. Server unittest 76 OK (DB parts skip). Smoke: 12 pages 200 (local + public), 11 new / changed endpoints anonymous 401, new strings in the build, AI status gemini (`gemini-flash-latest`) configured for speech-to-text + translation, ffmpeg + libmp3lame present, 0 jobs / 0 tracks, all 5 services active (bots untouched), no new errors. Live check (nothing stored): one 60 s piece of the real film → German, 30 segments, 2 speakers, 29 cues, 0 overlaps, 3 lines → Uzbek; the main model answered 503 / 429, the fallback model worked |
| Overlay 12 | "Multilevel Modelltest 1–6 open" 2026-11-19: backend (`services/mock_exam/{multilevel_service,multilevel_exam_service,multilevel_audio}.py`, `services/vizu_pay/{access,multilevel_premium}.py`, new `scripts/multilevel_open_tests.py`, restart, no migration) + frontend slot switch. 12b: the script matched no "Hören" in the stored file name (decomposed "o" + U+0308) → NFC before matching. Data change through the script: `plan` → `apply --confirm 7f3bafd226f2`: "Variant 1 Hören..m4a" (35:30, private storage) linked as Modelltest 1's shared audio, Modelltest 1–6 DRAFT → PUBLISHED; second plan KEEP only; audit 1 + 6. Smoke: 11 pages 200 (local + public), endpoints anonymous 401, new strings in the build, 1–6 PUBLISHED / warn_only / publishable, 7–10 DRAFT, overview free 6 / premium 4 (0 available), MT1 audio ok (file on disk, ffprobe 2130.8 s), 0 attempts, all 5 services active (bots untouched), no new errors |
| Overlay 11 | "Musik vinyl player" 2026-11-18, frontend only (no migration, no backend restart): large vinyl player, floating disc + panel, X stops for good, one sound at a time, restored song no longer skipped on the first tap. Smoke: 12 pages 200 (local + public), new strings in the build, media endpoints unchanged (anonymous 401 / 422), all 5 services active (bots untouched), logs clean. Android check on a real phone: known-issues #20 |
| Overlay 10 | "Multilevel Modelltest Premium + promo approval + Promo so'rovi" 2026-11-18: backend (`services/vizu_pay/{multilevel_premium,service,admin_service,access,offers,plans,purchases}.py`, routers, schemas, models, `multilevel_exam_service.py`, migration `a7c4e2f9b1d8`, restart) + frontend slot switch; no data change besides the migration backfill. Smoke: 11 pages 200 (local + public), 12 new / changed endpoints anonymous 401, new strings in the build, product ML_PREMIUM 99 000 ACTIVE, 10 Multilevel tests listed (0 published), nobody without the Premium opens one, the 2 live course codes still work (26 / 14 uses) and are refused for the Multilevel Premium, 0 entitlements / 0 ML orders, all 5 services active (bots untouched), logs clean. **Owner:** known-issues #19 (Premium on sale while all 10 tests are DRAFT) |
| Overlay 9 | "Modelltest 1 shared Hören audio" 2026-11-16: backend (`services/mock_exam/{multilevel_audio,multilevel_service,multilevel_exam_service}.py`, `audio_files/{router,service}.py`, `models/kompetenz.py`, migration `e6d2b9a4c8f3`, restart) + frontend slot switch; no data change. Smoke: 10 pages 200 (local + public), 6 new admin calls anonymous 401, student stream 422 without / 401 with a bad token, new strings in the build, MT1 = one shared slot (status missing, 6 Teile, 35 questions, 60 min), MT2–6 unchanged per Teil (4 each), 0 audio files / 0 attempts, all 5 services active (bots untouched), logs clean. **Owner action:** upload the Modelltest 1 audio in Admin → Vorbereitung → Multilevel Audio (no audio was created on production) |
| Overlay 8 | "Multilevel Hören keys + exam times" 2026-11-16: backend (new `services/mock_exam/multilevel_keys.py`, `scripts/multilevel_hoeren_keys.py`, `data/multilevel/hoeren-keys.json`, router, exam service, migration `d4b9e2a7c3f1`, restart) + frontend slot switch. Data change through the script: `plan` (6 × SET, 0 conflicts) → `apply --confirm a005c05d9fff`: Hören keys of Modelltest 1–6 (35 + 5 × 30 = 185, tokens as typed) and Kompetenz minutes of every Modelltest = Lesen 60 / Hören 60 / Schreiben 60 / Sprechen 15 (195); a second plan is all SKIP; 6 + 1 audit entries. Smoke: 10 pages 200 (local + public), 7 endpoints anonymous 401, new strings in the build, DB counts unchanged (180 model tests, 535 questions, 0 attempts), 325 options marked (140 of MT7–10 + 185), all 5 services active (bots untouched). **Not done / blocked:** Modelltest 1–6 stay DRAFT — Lesen keys (0 of 35 per test) and Hören audio (6 / 4 Teile per test) are missing, the publish guard is unchanged (known-issues #18) |
| Overlay 7 | "Musik fix + Bibliothek rework + book payments" 2026-11-15: backend (new `services/medien/{book_payments,pdf_tools,audio_meta}.py`, `audio_files.find_tool`, rate limit, routers, migration `c2f7a9d1e4b6`, restart) + systemd drop-in `10-path.conf` (PATH with `/usr/bin`) + frontend slot switch; smoke: 13 pages 200 (local + public), 19 new / changed endpoints refuse anonymous calls (401 / 422), new strings in the build, DB at `c2f7a9d1e4b6` with unchanged row counts (4 books, 3 PAID now have the default preview of 10 pages), the 4 existing PDFs (143 / 183 / 410 / 119 pages) build a 10-page preview in a temp folder, ffprobe found with the old and the new service PATH and read an existing MP3, all 5 services active (bots untouched), no new errors. **Not done:** `SUPER_ADMIN_VERIFICATION_PASSWORD` is still not set (owner action, known-issues #7) |
| Overlay 6 | "Film player + subtitles" 2026-11-15: backend (new `services/medien/{subtitles,player,lookup}.py`, routers, migration, restart) + frontend; smoke: 14 pages 200 (local + public), 13 new endpoints refuse anonymous calls (401 / 422), new strings in the build, DB at `b6e2d9f4a1c8`, services + bots active, logs clean. Production had 0 films / 0 subtitles at deploy (nothing existing touched); `ffmpeg` + `ffprobe` exist on the server | local: backend suite 1078 passed / 17 skipped, unit 55 passed, E2E `film-player.spec.ts` 9 desktop + 1 phone passed, `medien.spec.ts` desktop 8 passed (one Musik-favorite flake in one run, passed on rerun) |
| Overlay 5 | "Student navigation" 2026-11-15, frontend only (no backend restart, no migration): dashboard hub of five cards, `/kurse` level status chips, language switcher on top of sidebar + mobile drawer, certificates Print, `hub` texts; smoke: 15 pages 200 (local + public), old URLs `/courses`, `/courses/a1`, `/lessons` redirect, new strings in the build, old frame strings 0, services + bots active | local E2E: 135 passed; 6 failures not from this work (Battle: 3 stale scoring expectations in `battle.spec.ts`, profile-photo leaderboard state in `battle-dashboard.spec.ts`) |

## Packages (production, 2026-11-14)

Table `course_packages`, edited in Admin → Angebote (no prices in the frontend). A1 49 000 (was the admin override; kept) /
A2 99 000, 30 days; B1 100 000, 60 days; A1–B1 200 000, 180 days; A1–C1 400 000, 365 days (opens B2/C1 when released);
B2, C1, B2–C1 COMING_SOON (not buyable). The old `app_settings.angebote.offers` overrides (incl. B2/C1 149 000 and the
bundle strike-through prices) are no longer read. 33 orders, 2 promo codes, 0 approval requests at deploy.

## Content (production)

- Vorbereitung Multilevel: level "Multilevel B1–C1" (NATIONAL) with Modelltest 1–10, 535 questions in total. **1–6 PUBLISHED and free
  for every logged-in student since 2026-11-19**: Hören keys 35 / 30 (overlay 8), Lesen keys 0 (PDFs have none → Lesen "not scored", total /225),
  Modelltest 1 plays the shared "Variant 1 Hören" audio (35:30), 2–6 have no Hören audio (4 Teile each, "Audio noch nicht verfügbar").
  7–10 **DRAFT** (Premium only): 35/35 keys, Hören tasks missing, Sprechen 1.2 pictures missing. Check-list per test
  (`docs/multilevel-modelltests.md`). Scoring settings at defaults (50 = Ungeklärt, overall rule unconfirmed). 0 attempts at deploy.

- Battle (2026-11-05): 89 published A1 picture words + 89 published pictures, 6 published themes; all stages playable (A2+ use A1 words).
- A2: lessons 1–13 published (14 "Wiederholung" draft); Hören 22/27 published (L6 + L13 open, see known-issues).
- A2 written tasks: Schreiben 25 · Grammatik 5 · Wortschatz 9 · Lesen 1 (`writings.competency`).
- A2 Wortschatz: 216 words, 32 published test sets. A2 readiness `NEEDS_CONTENT`; sales enabled.

## Last verification (2026-11-19 · Battle text questions)

- Local: backend full suite 1226 passed / 18 skipped (new `test_battle_questions` 12: ≥ 500 valid questions per level, no duplicates inside /
  across levels, level-appropriate grammar topics, validator, choice for a match, HTTP 401 / 403, seed plan / apply / idempotent, mixed
  matches, text round view without answer before the reveal, admin create / edit / delete / import / stats; `test_battle_questions_migration`;
  `test_battle_migration` now expects the new table at head). Frontend tsc + eslint clean, unit 76/76. E2E `battle-questions` 2 desktop + 1 phone,
  `battle-audio` 2 + 2, `battle-dashboard` 3 + 3, `battle.spec` 3 + 2 (the practice test now accepts picture or text rounds); known old
  failures unchanged: `battle.spec` result text "keine Battle Points" and "+25 BP" (scoring of 2026-11-05), profile-photo test.
- Production: alembic `a6c2e8f4b9d1`, 2961 questions published, smoke above. Picture rounds now only at A1 (own picture words); A2–C1 / C1+
  play their own text questions (before: A1 pictures for every stage).

## Group video lessons (2026-11-21 · production, overlay 19)

- Rebuilt from zero on LiveKit; details, rules, rollback and the DONE / BLOCKED / NOT TESTED table: `docs/group-video-lessons.md`.
- Local: backend 1251 passed / 18 skipped (one route-protection failure found and fixed: the webhook joined the public allowlist with its reason);
  frontend tsc + eslint clean, unit 86/86; E2E `video-rooms.spec.ts` 4/4 desktop + Pixel 7 against a real local LiveKit server.
- Found on production during the deploy (pre-existing, known-issues #23): 11:04–11:26 server time the DB pool was exhausted and Multilevel
  exam requests answered 500; the deploy restart cleared it.

## Superseded: old Group Video Chat audit (2026-11-21 · local only, code removed the same day)

- Production remains at Alembic `a6c2e8f4b9d1`; the dedicated local test and migration databases are at `c1v7d3e9a5b2`. The migration test
  inserted a pre-existing group, verified the room backfill, and verified downgrade preserves the group. No production migration was run.
- Targeted local tests: `test_study_groups.py` + `test_study_group_video_chat_migration.py` — 15 passed. Covered member/non-member token access,
  token identity/room/TTL and no `roomAdmin`, join rate limit, idempotent start, remote room create/delete, teacher kick/mic/screen permissions,
  admin monitoring counts, role guards and migration preservation.
- Frontend `tsc` and targeted ESLint passed; unit tests 76/76. Changed backend modules compiled and `app.main` imported successfully.
- Frontend admin Groups now polls LiveKit room status and participant count every 15 seconds and shows duration plus client-reported disconnect /
  reconnect counts. Backend `livekit-api==2.0.1` contains `livekit.api`; `livekit-client` is present in the frontend manifest.
- **Local build:** `next build --webpack` passed with `NEXT_PUBLIC_API_URL` set to the public site URL. Default Turbopack `next build` failed with
  28 unresolved `@vercel/turbopack-next/internal/font/google/font` modules; the standard deployment script build was not validated.
- No real-browser or two-device call was possible. Admin monitoring does not expose LiveKit CPU/RAM.

## Superseded: production preflight of the old attempt (2026-11-21, before overlay 19)

- Read-only VPS audit: Ubuntu 24.04.4, 2 vCPU, 3.8 GiB RAM, 212 GiB free disk; Docker absent, Nginx 1.24 active, UFW inactive. Existing VIZU,
  `nano_bot`, and `telegram-cours2026` services remained active after checks.
- Public DNS has no A/AAAA/CNAME for `meet.vizu-deutsch.com`. Existing TLS certificate covers only `vizu-deutsch.com` and `www`, valid to
  2027-02-18. No LiveKit/coturn service, LiveKit API credentials/settings, or LiveKit UDP listeners exist; no ports were opened.
- Server checkout is `0cb7b165`, 18 commits behind `origin/main`, with 251 dirty paths. The deployed backend lacks `video_chat.py`, migration
  `c1v7d3e9a5b2`, and `livekit-api`; pulling/overlaying or restarting it would risk unrelated production work, so no code or migration was deployed.
- **Backup DONE:** `/var/backups/vizu/pre-group-video-chat-20261121-001608`; `pg_dump` restore-tested against a scratch DB, all 166 table row counts
  matched the consistent dump snapshot; 51 private lesson audio files and metadata were archived; SHA256 checks passed. Scratch DB and temporary
  dump copy were removed. All monitored services remained active.
- Local offline migration preview contains only video-room/session/event table/index creation and the room backfill; migration test passed. No
  production migration, `.env`, Nginx, firewall, Docker, LiveKit, TURN, or service changes were made (backup only).
- **BLOCKED:** DNS must first point `meet.vizu-deutsch.com` to `217.76.62.208`; then obtain a certificate for that hostname and configure LiveKit +
  authenticated TURN, bounded media/relay UDP ranges and firewall rules. Reconcile the dirty/stale server checkout before controlled code deploy.
  External UDP/TURN and real-device E2E remain NOT TESTED.

## Earlier verification (2026-11-19 · Global Chat button only on the dashboards)

- Local: frontend tsc + eslint clean, unit 76/76 (new `chat-visibility.test.mjs`); E2E `global-chat` 9 / 9 desktop + phone (new: button on `/dashboard`,
  `/teacher`, `/admin` only, a client-side page change closes an open chat, none on `/kurse`, `/medien`, `/vorbereitung`, `/teacher/groups`,
  `/admin/global-chat`, `/admin/users`), `global-chat-reply` 3 + 4, `medien-vinyl-player` 4 + 1 (disc above the chat button on /dashboard, no button on
  /medien). The long-lived `vizu_gcr_e2e` needs the chat tables emptied before `global-chat.spec` (fixed message text; `gc_seed.py` is outdated).

## Earlier verification (2026-11-19 · Multilevel Premium for 1–10)

- Local: backend full suite 1213 passed / 18 skipped (`test_multilevel_open_tests`: all 7 fixture tests locked without the Premium, open with it / for
  staff, overview `free` 0; `test_multilevel_premium`: 10 locked, Modelltest 1 and 7 → 403 `PREMIUM_REQUIRED`; `test_multilevel_exam` students get the
  Premium in the fixture). The local `vizu_gcr_mig` was recreated at head: after many upgrade / downgrade cycles `promo_codes` had hit Postgres' 1600-column
  limit (dropped columns keep their slots). Frontend tsc + eslint clean; E2E `multilevel-premium` 6 + 1, `multilevel-open-tests` 2 + 1, `multilevel-exam`
  2 + 1, `multilevel-keys` 4, `multilevel-shared-audio` 4.
- Production: 0 students hold the Multilevel Premium; the one Multilevel attempt so far (GRADED) belongs to a student without it: the result stays,
  a new start needs the Premium.

## Earlier verification (2026-11-19 · Film subtitle agents)

- Local: backend full suite 1213 passed / 18 skipped (new `test_medien_subtitle_agents` 15: checker, split, gaps, quiet pieces, busy / quota errors,
  proofreader, bare JSON array; `test_medien_subtitle_jobs` 8 incl. gaps + retry, auto-approve, waiting on a busy service + cancel while waiting,
  translations first; `test_medien_subtitle_auto_approve_migration`); frontend tsc + eslint clean, unit 74/74; E2E `medien-ai-subtitles-reader` 5 + 1
  (default Deutsch, agents line, one-click Freigeben, "sofort freigeben" + replace), `film-player` 9 + 1.
- Production: the 3 films' jobs finished with the agents (flash-lite): "Im Westen nichts neues" 50 pieces (5 repaired, 116 lines corrected),
  "Drei Schritte zu dir" 39 (1 repaired, 66 corrected), "Interstellar" 57 (2 repaired, 1 split, 206 corrected), 0 gaps; Uzbek for the first two
  (17 / 22 batches). All 5 tracks are DRAFT (students see nothing until "Freigeben").

## Earlier verification (2026-11-19 · Musik bulk upload 500)

- Local: backend full suite 1190 passed / 18 skipped (new `test_medien_bulk_upload` 6 incl. parallel copies of one file → exactly one stored, `test_storage_paths` 3,
  `test_medien_song_hash_migration`); stress `VIZU_STRESS_500=1`: 500 different files, 6 parallel → 500 × 200 in 6.1 s, metadata queue 14.5–16 s, each stored once
  (found and fixed: a path-check race under parallel uploads, reported as "file too large"); frontend tsc + eslint clean, unit 74/74 (new `song-upload.test.mjs`);
  E2E `medien-bulk-500` 3/3 (500 files through the UI: upload 21 s, metadata of all after 27 s; reload in the middle → only the missing files sent, 120 on the
  server exactly once; duplicates / same name / lost connection + retry / other admin page meanwhile), `medien` 8 + 1, `medien-music-formats` 2, `medien-vinyl-player`
  4 + 1 (one seek flake, green on rerun). Seen locally: 100 parallel DELETEs from a test script hung the backend (known-issues #23, pre-existing pattern).

## Earlier verification (2026-11-19 · Film AI subtitles, bookshelf, book reader)

- Local: backend full suite 1183 passed / 17 skipped (new `test_medien_subtitle_ai` 17, `test_medien_subtitle_jobs` 5 with real ffmpeg pieces, retry / cancel / conflicts / drafts
  hidden from students, `test_medien_subtitle_ai_migration`); frontend tsc + eslint clean, unit 69/69 (new `medien-reader-shelf.test.mjs`); E2E `medien-ai-subtitles-reader`
  desktop 4 + phone 2 (admin job → drafts → edit → approve → SRT; student original + translation switches + sync; shelves; reader keys / clicks / buttons / zoom / exit /
  resume; phone swipe / pinch without turning / double tap / big buttons / preview paywall), `film-player` 9 + 1, `medien` 8 + 1, `medien-library-payments` 7 + 1 green.

## Earlier verification (2026-11-19 · Multilevel Modelltest 1–6 open)

- Local: backend full suite 1161 passed / 17 skipped (new `test_multilevel_open_tests`: guard warn-only for 1–6 / full for 7, access 1–6 free + 7–10 locked + anonymous
  refused, script plan / apply / wrong id / LINK_SHARED incl. a decomposed file name / MANUAL / BLOCKED / KEEP, scoring 38 / 225 with Lesen not scored, detach keeps
  1–6 published); frontend eslint clean, unit 59/59, build OK; E2E `multilevel-open-tests` (desktop 2 + phone 1), `multilevel-premium` (desktop 6 + phone 1),
  `multilevel-exam`, `-keys`, `-shared-audio`, `-audio` (desktop 14 + phone 10) all green.

## Earlier verification (2026-11-16 · Multilevel Hören keys + exam times)

- Local: backend 1137 passed / 17 skipped (new: `test_multilevel_keys` 14 incl. the real ten Modelltests built in a throwaway DB, the script plan / apply / conflict / idempotence, editing + import rules,
  35- and 30-question scoring, exam times 60 / 60 / 60 / 15, a timer that survives a refresh and the automatic close at the deadline; `test_multilevel_keys_migration`), frontend tsc + eslint clean,
  unit 55/55, E2E `multilevel-keys.spec.ts` (desktop 4 + phone 4: six tables, edit, import check, 195 min on the cards, timer after reload, section closed by itself at the deadline),
  `multilevel-exam.spec.ts` + `multilevel-audio.spec.ts` unchanged and green.
- Production data: the owner's six key lists validated against the real Modelltest structure before the apply (every letter valid for its question type, counts 35 / 30).

## Earlier verification (2026-11-15 · Musik fix, Bibliothek rework, book payments)

- Local: backend 1116 passed / 17 skipped (new: `test_medien_audio`, `test_medien_books_reader`, `test_medien_payments` incl. two real threads deciding at once,
  `test_medien_books_payments_migration`, `test_set_admin_verification`), frontend tsc + eslint clean, unit 55/55, E2E on the real local stack: `medien-library-payments.spec.ts`
  (desktop 7 + phone 1: preview bytes without page 11, paywall texts, payment form validation, receipt, reject → reason → new request → approve, download byte-identical,
  reading position in the DB), `medien-music-formats.spec.ts` (MP3 / WAV / M4A / AAC / OGG / FLAC + broken file + player), `medien.spec.ts` 8 + phone, `film-player.spec.ts` 9 + phone,
  admin / auth / dashboard / purchase / student-panel 42 passed. Uploads with FFmpeg missing (second backend without it): all formats stored, `metadata_status = FAILED`, nothing blocked.
- Fixed on the way: payment form sent a stale transfer date with a receipt; film control bar swallowed clicks on subtitle words (pointer-events); `medien.spec` Musik favorites follows the song by title.

## Earlier verification (2026-11-15 · Medienwelt)

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

See `known-issues.md` #1–#8, #13, #15–#23.
