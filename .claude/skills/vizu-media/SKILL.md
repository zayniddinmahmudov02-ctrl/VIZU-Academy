---
name: vizu-media
description: VIZU media work — Hören audio upload and storage, A2 Audio Manager library, A2 4. Unterricht Text 1–3 slots, audio transcription (offline faster-whisper) and the A2 processing pipeline, video upload/stream, Media Management admin page. Use for audio/video files, uploads, transcripts or media cleanup.
---
# VIZU Media

## Context to load
1. `docs/ai-context/module-registry.md` → "Media Management" (+ "Hören" if keys/questions are involved).
2. Current A2 state: `docs/a2-audio-processing-manifest.md`, `docs/a2-publishing-report.md`.
3. Source by topic:
   - per-task Hören audio + tracks: `backend/app/services/lesson_skills/admin.py`
   - A2 library (validation, SHA-256 duplicates, link/unlink, removal): `backend/app/services/a2_audio/assets.py`
   - Text 1–3 slots: `a2_audio/lesson4_hoeren.py`; transcripts/pipeline: `a2_audio/processing.py`
     + `app/scripts/a2_audio_processing.py` (+ `_data.py`, `app/data/a2_audio_transcripts.json`)
   - old archive cleanup: `a2_audio/cleanup.py`; readiness: `a2_audio/readiness.py`
   - endpoints: `backend/app/api/admin/media_management_router.py`; student stream: `api/lesson_skills/router.py`
   - UI: `frontend/src/features/admin/components/media-management/`

## Rules
- Storage is private (`app/protected_storage/lesson-listening`), random file names; never a public URL.
- Accept MP3/M4A (A2 library) by extension + MIME + content; reject duplicates by SHA-256.
- A file is deleted only when nothing references it (`file_references`) and after a backup; the old A2
  archive goes plan → quarantine → (approval) → purge.
- Transcription runs offline: `D:\vz_tmp\whisper_venv` + `D:\vz_tmp\work\a2h_transcribe.py`
  (large-v3 + medium, CPU), transcripts in `D:\vz_tmp\a2h_tr`; build records with
  `D:\vz_tmp\work\a2p_build_transcripts.py`. Same content = same transcript (SHA-256), never re-transcribe.
- Unclear words → `[unverständlich]`, never guessed. A wrong audio (e.g. 13. Unterricht = 12. copies) is
  MISMATCH: no keys, no publishing.
- Production audio comes from the user's book folder only; no synthetic audio on production.

## Tests
`tests/test_a2_audio_manager.py`, `test_a2_audio_management.py`, `test_a2_lesson4_hoeren.py`,
`test_a2_audio_processing.py`, `test_video*.py`; E2E `e2e/tests/a2-*.spec.ts`.
