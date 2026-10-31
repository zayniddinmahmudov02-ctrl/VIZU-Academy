# Security rules (always)

- Secrets: never read `.env` values into the conversation, logs, docs or reports. Refer to settings by
  name (`DATABASE_PASSWORD`, `SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`, `R2_SECRET_ACCESS_KEY`, `SUPER_ADMIN_VERIFICATION_PASSWORD`, …). On the server read DB
  settings inside a script into env vars, never echo them.
- Personal data: no user names, emails, phones, payment receipts or recordings in docs, commits or chat.
- Authorization: every new endpoint states its dependency: `get_current_user`, `require_lesson_access`,
  `require_admin_panel_access` (staff read), `require_content_editor` (SUPER_ADMIN/ADMIN/CONTENT_MANAGER
  write), `require_super_admin`, `require_teacher_panel_access`. Add a 401/403 test for it.
- IDOR: students only ever read/write their own attempts/submissions (see
  `tests/test_homework_grading_rbac_and_idor.py`, `test_writing_speaking_submission_rbac_and_idor.py`).
- Answer keys (`is_correct`, `config.accepted`, `config.pairs`) never reach a student before grading.
- Uploads: validate extension + declared MIME + file content; size limits; random storage names
  (`services/a2_audio/assets.py`, `services/lesson_skills/admin.py:_store_audio`, `test_upload_path_safety`).
- Payments: prices only from `services/vizu_pay/offers.py`; manual gateway; never create orders,
  approvals or "test" payments on production.
- HTML from editors goes through the sanitizer (`test_safe_html`).
- Production: no test users, forged tokens or synthetic audio. Telegram bots are off-limits.
