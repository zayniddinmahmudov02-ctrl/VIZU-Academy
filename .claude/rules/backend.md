---
paths:
  - "backend/**/*.py"
---
# Backend rules

Map: `docs/ai-context/backend-map.md`, endpoints: `docs/ai-context/api-registry.md`.

- Style: match the surrounding module (docstring at the top explaining the rules, few comments, long lines
  are fine up to ~150). Services take `db: Session` first; they raise `HTTPException` with UPPER_SNAKE codes.
- New router: `APIRouter(prefix="/...")` in `app/api/<module>/`, import it in `app/main.py` and add it to
  `_ALL_ROUTERS`. New admin pages must also be registered in `app/services/page_management.py`
  (`tests/test_page_management.py` checks that every `frontend/src/app/**/page.tsx` is listed).
- New model: own file in `app/models/`, import it in `app/models/__init__.py`, write an Alembic migration
  (see `database.md`). Never rely on `create_all`.
- Settings: `app/core/config.py` (`settings.X`); add new ones with a safe default, document the name only.
- Scripts in `app/scripts/`: read-only by default, `--apply`/`apply --confirm <id>` to write, print a plan,
  write an audit log entry (`app.core.audit.write_audit`). Never delete rows that carry learner history
  (attempts cascade from tasks — archive instead).
- AI: `app/services/ai/` + `lesson_skills/ai_evaluation.py`; providers by setting name, never a key in code.
- Audio checks reuse `services/a2_audio/assets.py:detect_format` / `lesson_skills/admin.py:_detect_audio`.
- Python on Windows: `D:\vz_tmp\venv\Scripts\python.exe` (scratch venv with reportlab, qrcode, httpx);
  there is no `backend/.venv` locally. `app.main` needs an existing `backend/uploads/` dir to import.
