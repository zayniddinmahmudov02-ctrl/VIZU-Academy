# Architecture rules (always)

Verified 2026-10-31 against `backend/app/main.py`, `backend/app/core/security/roles.py`,
`backend/app/services/lms/structure.py`. Map: `docs/ai-context/architecture-map.md`.

- **Build on what exists.** The LMS sits on the existing tables (lessons, videos, readings, listenings,
  skill exercises, attempts). Do not add a second progress system, lesson model or media library.
- **One router, two mounts.** Every router in `main.py:_ALL_ROUTERS` is served at its bare prefix and
  under `/api/v1`. The frontend calls `/api/v1/...` only. A new router must be added to `_ALL_ROUTERS`.
- **Thin routers.** Routers validate input (Pydantic, `extra="forbid"` where the module does) and call a
  service; business rules live in `app/services/<module>/`.
- **Errors.** `HTTPException(detail=...)` is returned to the client as `{"message": detail}`. Error codes are
  UPPER_SNAKE strings, optionally `"CODE: human text"`.
- **Content structure.** Course (level A1..C1) → main module → lessons 1..N
  (`LEVEL_LESSON_COUNTS`: A1 14, A2 14, B1 20, B2 30, C1 22) → 10 competencies in fixed order
  (`models/lms.py:COMPETENCY_ORDER`). Content items carry a stable `content_id`; first-edition copies are
  titled `[Archiv] …` and are never shown to students.
- **Access.** `require_lesson_access` (free preview / purchase / staff, plus LMS lock rules) guards every
  student lesson endpoint. Roles: SUPER_ADMIN, ADMIN, CONTENT_MANAGER, PAYMENT_MANAGER, SUPPORT, TEACHER,
  STUDENT (`UserRole`). Use the existing dependencies; never check roles ad hoc in a new way.
- **Files.** Hören/A2 audio lives in private storage (`app/protected_storage/lesson-listening`), streamed
  only through access-checked endpoints with `Cache-Control: private, no-store`. Never return storage paths.
- **Data changes on production** go through a script with a read-only `plan` and an
  `apply --confirm <plan id>` step, a backup first, and an audit log entry (pattern:
  `app/scripts/a2_audio_processing.py`, `a2_lesson4_hoeren.py`, `a2_audio_cleanup.py`).
