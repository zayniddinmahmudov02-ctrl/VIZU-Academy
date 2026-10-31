# Recent changes

Newest first, about 15 entries; move older ones to `recent-changes-archive.md` (create when needed).

| Date | Change | Modules | Key files / docs |
|---|---|---|---|
| 2026-10-31 | Project knowledge system: `CLAUDE.md`, `.claude/rules/*`, `.claude/skills/vizu-*`, `docs/ai-context/*`; `.gitignore` now versions `.claude/rules` + `.claude/skills` only | all | this folder |
| 2026-10-30 | A2 audio processing 1–13: transcripts per SHA-256 (`a2_audio_transcripts`, migration `c4f7a9e2d6b3`), keys verified, 22/27 Hören published, L7 "Text 2" track added, L4 Text 1–3 adopted into the A2 library, readiness check `hoeren_published`, admin panel "A2 Audio-Verarbeitung" | Hören, Media | `services/a2_audio/processing.py`, `scripts/a2_audio_processing*.py`, `docs/a2-*-report.md` |
| 2026-10-30 | A2 4. Unterricht: "Familie Mannsberg" removed (backup), tasks Text 1–3 with `listenings.task_key` (migration `b8e3d1a7c5f2`), slot page `/admin/media-management/a2/lesson-4/hoeren` | Hören, Media | `services/a2_audio/lesson4_hoeren.py`, `docs/a2-lesson-4-hoeren-update.md` |
| 2026-10-29 | Global Chat reply (`reply_to_id`, migration `f3a8c1d5e7b2`), A2 Audio Manager (`a2_audio_assets`, `a6d2f9c4e8b1`), sales readiness indicator, old A2 archive cleanup tools; production deploy | Chat, Media, Payments | `docs/audit/global-chat-reply.md`, `docs/audit/production-deploy-2026-10-29.md` |
