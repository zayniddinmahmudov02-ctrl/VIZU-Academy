# Known issues

Updated 2026-10-31. Remove an entry when it is fixed (and note it in `recent-changes.md`).

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
| 10 | Local env | C: drive is full; Claude's temp dir is on C: (outputs may be cut) | 2026-10-31 | free space or set `CLAUDE_CODE_TMPDIR` to D: |
| 11 | Docs | some docstrings say "first 3 lessons free"; code: only lesson 1 (`offers.free_lessons()`) | — | fix when touching those files |
| 12 | Groups | `docs/groups-classroom.md` (2026-10-28) said not on production; current production state not re-checked | — | verify on next groups task |
