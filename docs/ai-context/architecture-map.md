# Architecture map

Updated 2026-10-31 · sources: `backend/app/main.py`, `core/`, `api/dependencies/`, `frontend/scripts/deploy-frontend.sh`,
`docs/lms-architecture.md`. Rules: `.claude/rules/architecture.md`.

```
Browser (Next.js pages, PWA) ──/api/v1/…──► nginx ──► uvicorn FastAPI (vizu-backend, :8000) ──► PostgreSQL
        │                                                │
        └── Next.js server (vizu-frontend, :3000, slot .next-a|.next-b)   └── private storage (app/protected_storage)
                                                                         └── AI providers (Gemini/OpenAI/Anthropic by setting)
```

- **Request path:** frontend → `src/services/api.ts` → `/api/v1/<prefix>` → router → dependency (auth, lesson gate)
  → service → models. Errors become `{"message": …}`; every response carries `X-Request-ID`.
- **Auth:** JWT access token + refresh token (`refresh_tokens`), optional "remember me", login by email/phone or
  Telegram (init-data validated); admin panel has a second factor. Roles → `UserRole`.
- **Lesson gate:** `require_lesson_access` → `services/lms/access.ensure_lesson_open` (draft 404, lock 403) +
  `services/vizu_pay/access.can_access_lesson` (lesson 1 free, else APPROVED order or staff).
- **Content model:** one course per level; lessons hold existing task tables (videos, readings, listenings, writings,
  speakings, skill_exercises) + 10 competency rows. Student progress = attempts + competency progress + lesson completion.
- **Grading:** server-side only (`lesson_skills/skill_tests.py`, `question_types.py`); keys never sent before grading;
  Schreiben/Sprechen by AI (`ai_evaluation.py`) with append-only history and manual override.
- **Media:** Hören audio private, streamed after the gate; videos with stream tokens (`VIDEO_STREAM_TOKEN_EXPIRE_MINUTES`);
  storage provider by setting `STORAGE_PROVIDER` (local / R2 names in config).
- **Admin CMS:** same API with role dependencies; page registry (`managed_pages`) lists every admin page.
- **Content pipeline:** book Python sources → JSON → idempotent import; data fixes via plan/apply scripts with backups.
- **Realtime:** none — Global Chat and groups poll.
- **Deploy:** backend restart in place; frontend blue/green slots (`frontend/.deploy/active.env` is the systemd
  EnvironmentFile with `NEXT_DIST_DIR`).
