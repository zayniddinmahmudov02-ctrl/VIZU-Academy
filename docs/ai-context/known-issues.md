# Known issues

Updated 2026-11-05. Remove an entry when it is fixed (and note it in `recent-changes.md`).

| # | Area | Issue | Since | Next step |
|---|---|---|---|---|
| 1 | A2 Hören | 13. Unterricht audio files are byte-identical copies of 12. Unterricht (also in the owner's source folder); 4 tasks stay drafts (MISMATCH) | 2026-10-21 | owner uploads the real files → rerun `a2_audio_processing` |
| 2 | A2 Hören | 6. Unterricht: 12 open (free-text) questions, keys written but NEEDS_REVIEW (literal comparison) | 2026-10-21 | admin confirms variants in LMS → Lösung or converts to MC |
| 3 | A2 Hören | 4. Unterricht Text 1–3 have no questions (book "Familie Mannsberg" questions in backup `/var/backups/vizu/pre-a2l4-20261030-011331/legacy/`) | 2026-10-30 | owner decision |
| 4 | A2 transcripts | 7 spots marked `[unverständlich]` (`docs/a2-transcription-report.md`) | 2026-10-30 | listen and correct |
| 5 | A2 archive | old `[Archiv]` audio cleanup waiting: plan id `552c5c27371e` (5 files), quarantine not run | 2026-10-29 | separate approval |
| 6 | A2 sales | sales enabled on production while readiness = NEEDS_CONTENT | 2026-10-28 | owner decision |
| 7 | Config | `SUPER_ADMIN_VERIFICATION_PASSWORD` not set on production (logged at every start) | ≤ 2026-10-20 | owner sets it in `.env` |
| 8 | Deps | `openpyxl` not installed on production → `/admin/users/export.xlsx` fails | ≤ 2026-10-29 | add to requirements + install (approval) |
| 9 | Frontend lint | full `npx eslint .`: 9 errors / 10 warnings in untouched files | — | separate cleanup |
| 11 | Docs | some docstrings say "first 3 lessons free"; code: only lesson 1 (`offers.free_lessons()`) | — | fix when touching those files |
| 12 | Groups | `docs/groups-classroom.md` (2026-10-28) said not on production; current production state not re-checked | — | verify on next groups task |
| 13 | A2 Wortschatz | words without a Wörterbuch entry have grammar (`vizu-grammatik`, 2026-11-01) but no example sentence; tests do not include the newly filled forms | 2026-11-01 | examples by admin / separate task if wanted |
| 14 | E2E env | `a2-audio-manager.spec.ts` expects the seed task "E2E Hören Lektion 1"; `vizu_gcr_e2e` holds the real A2 edition since the 2026-10-30 rehearsal | 2026-11-01 | reseed a fresh e2e DB for that spec |
| 15 | Battle content | only A1 has picture words (89); A2…C1 stages play with A1 words until their own words + checked pictures are published; C1+ has no word source | 2026-11-05 | add words via /admin/battle (Wörterbuch ID + Commons / upload) or a new words.json batch |
| 16 | Battle admin | avatars, rank badges and achievement icons are code-defined (SVG / config), not admin-uploadable; themes, backgrounds, overlay, accent, word pictures are | 2026-11-05 | owner decision whether uploads are needed |
| 17 | Battle prod check | no authenticated match was played on production (no test users there by rule); verified locally (E2E) + anonymous / read-only on production | 2026-11-05 | owner plays one ranked or bot match |
