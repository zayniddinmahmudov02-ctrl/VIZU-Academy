---
paths:
  - "frontend/**"
  - "e2e/**"
---
# Frontend rules

Map: `docs/ai-context/frontend-map.md`. Read `frontend/AGENTS.md` (Next.js 16 differs from older versions;
docs in `frontend/node_modules/next/dist/docs/`).

- Data: API calls only in `src/features/<feature>/services/*.ts` (or `features/admin/services/`) through
  `src/services/api.ts` (axios, `/api/v1/...`). Components use TanStack Query (`useQuery`, query keys like
  `["a2-audio-processing"]`).
- UI: admin uses `@/components/admin/admin-ui` (`AdminButton`, `AdminPageHeader`, …) and CSS vars
  `var(--admin-*)`; student pages use the theme tokens (`text-text-primary`, `bg-surface-card`, …).
  Admin copy is German, student copy comes from `src/lib/i18n` translations (uz/de).
- Errors: `apiErrorMessage(err, fallback)` from `features/admin/services/lesson-skills-admin-service.ts`.
- Tests: `data-testid` on interactive elements; unit tests in `tests/unit/*.test.mjs` (node --test, pure TS
  helpers); E2E specs in `e2e/tests/`.
- Mobile: every page must work at phone width without horizontal scroll (E2E checks it).
- Some files carry a UTF-8 BOM (e.g. `media-management-service.ts`): keep it. Line endings CRLF.
- Never build into `.next-a`/`.next-b` locally; `next build` rewrites `tsconfig.json` — restore it.
