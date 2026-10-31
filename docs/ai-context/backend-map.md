# Backend map

Updated 2026-10-31 · source: directory listing of `backend/`. Module details: `module-registry.md`.

| Path | Contents |
|---|---|
| `app/main.py` | FastAPI app, CORS, request id, `_ALL_ROUTERS` (bare + `/api/v1` mounts), `/uploads` static mount (needs `uploads/` dir) |
| `app/core/` | `config.py` (Settings), `security/roles.py` (UserRole), `audit.py` (`write_audit`), `exceptions.py`, `cors.py`, `request_id.py`, `logging/`, `storage/protected_local.py` |
| `app/api/<module>/` | routers; `dependencies/` = auth, db, pagination, progress (`require_lesson_access`), section_gate |
| `app/api/admin/` | admin routers (users, media_management, hoeren_a1, loesung, vizu_pay, videos, books, zertifikate, notifications, page_management, teacher_assignments, vizu_multilevel) |
| `app/services/<module>/` | business logic; biggest: `lesson_skills/` (admin, skill_tests, results, loesung, exercises, question_types, ai_evaluation, hoeren_pdf_import, levels), `lms/`, `a2_audio/`, `vizu_pay/`, `vizu_multilevel/`, `mock_exam/`, `assessment_engine/`, `global_chat/`, `study_groups/` |
| `app/services/ai/` | AI clients (chat, client, feedback, speaking, translation, writing); providers by setting `AI_PROVIDER`, `GEMINI_*`, `OPENAI_*`, `ANTHROPIC_*` |
| `app/models/` | SQLAlchemy models, all imported in `models/__init__.py` |
| `app/schemas/` | Pydantic schemas (mostly the older CRUD modules; newer modules define inputs in the router) |
| `app/scripts/` | data scripts (`python -m app.scripts.<name>`): book editions + importers, key audits (`a1_hoeren_keys`, `a2_keys`), A2 audio (`a2_audio_processing`, `a2_lesson4_hoeren`, `a2_audio_cleanup`, `a2_audio_manifest`, `a2_audio_inventory`), `ensure_lms_structure`, `course_content_audit`, `legacy_content_cleanup`, `create_super_admin`, seeds |
| `app/data/` | generated book JSON (`vizu_deutsch_a1`, `vizu_deutsch_a2`, `vizu_deutsch_a2_buch`, `vizu_deutsch_b1`), `a2_audio_transcripts.json` |
| `app/protected_storage/` | private files (gitignored): `lesson-listening/` (Hören audio, `a2-audio/` subfolder), videos, quarantine |
| `alembic/versions/` | migrations (see `database-map.md`) |
| `tests/` | 82 test modules; DB integration tests need `VIZU_WB_TEST_DB_URL` |
| `scripts/` | `backup-course-content.sh`, `import_vocabulary.py`, `update_vocabulary.py`, `reset_password.py` |
| `requirements.txt` | pinned deps (reportlab, qrcode, boto3 added 2026-10-29; `openpyxl` missing, see known-issues) |
