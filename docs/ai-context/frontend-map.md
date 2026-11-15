# Frontend map

Updated 2026-11-15 · source: listing of `frontend/src/`, `frontend/package.json`. Rules: `.claude/rules/frontend.md`.
Next.js 16.2.10 App Router, React 19.2.4, TanStack Query 5, zustand 5, axios, Tailwind 4, zod, tiptap.
Scripts: `dev`, `build`, `start`, `lint`, `test:unit` (node --test `tests/unit/*.test.mjs`), `verify:pwa`.

## Routes (`src/app/`)
- `(auth)/`: login, register, forgot-password, reset-password
- `(dashboard)/` (student): dashboard, kurse (`/kurse/[level]`), lektion (`/lektion/[lessonId]/[kompetenz]`),
  courses/lessons (old player), angebote, vizu-pay, vizu-multilevel, vorbereitung, woerterbuch, groups,
  calendar, certificates, notifications, informationen, support, settings
- `admin/`: achievements, analytics, angebote, books, certificates, global-chat, groups, kurse, languages, lessons,
  levels, listening, lms, media, media-management (`hoeren-a1`, `a2/lesson-4/hoeren`), mock-exams, modules,
  notifications, page-management, payments, premium-users, settings, speaking, support, teacher-assignments, team,
  users, vizu-multilevel, werbung-banner, writing
- `teacher/`: groups, schreiben, sprechen, students · `api/admin` (route handlers) · `offline/` (PWA)

## Code
| Path | Contents |
|---|---|
| `src/services/api.ts` | axios instance (auth header, refresh) |
| `src/features/<f>/` | `services/` (API), `hooks/`, `components/`, `types/`: auth, profile, lessons, lms, courses, dashboard, vizu-pay, vizu-multilevel, vorbereitung, assessment, global-chat, groups, teacher, notifications, calendar, information, woerterbuch, books, certificates, achievements, support, pwa |
| `src/features/admin/` | admin `components/` (certificates, dashboard, language, lesson-results, lesson-skills, lms, lms-course, loesung, managers, media-management, mock-exam, page-management, payments), `services/` (one per area), `constants/endpoints.ts` |
| `src/components/lesson-player/` | student player per skill: common, grammar, listening, navigation, quiz, reading, results, skill-test, speaking, video, vocabulary, writing |
| `src/components/lms/` | LMS cards, competency nav/content, audio player, lock, purchase modal |
| `src/components/dashboard/` | student shell: `sidebar.tsx` (language switcher on top), `mobile-nav.tsx` (drawer, switcher on top), `languages/language-switcher.tsx` (variants default / sidebar / drawer / compact / segmented), `home/dashboard-hub.tsx` (five main cards), `home/learning-tools.tsx` |
| `src/features/medien/` | Medienwelt student side: `components/` (film-player, subtitle-overlay, subtitle-menu, word-popup, global-audio-player, pdf-reader …), `hooks/use-film-subtitles.ts`, `lib/subtitles.ts` (pure helpers, `tests/unit/medien-subtitles.test.mjs`), `services/medien-service.ts`, `store/` |
| `src/components/admin/` | `admin-ui` (AdminButton, AdminPageHeader, AdminInput, …), `confirm-dialog` |
| `src/lib/i18n/` | `translations.ts` (uz/de), `translations-extra.ts` + `extra/part1–10.ts` (en/ru as `[en, ru]` per key, German fallback), `use-translation.ts`; languages list `src/constants/languages.ts` (uz, de, en, ru) |
| `src/providers`, `src/store`, `src/hooks`, `src/types`, `src/constants` | app-wide |
| `tests/unit/` | `a2-audio-import`, `reply-preview`, `reply-swipe`, `i18n-extra` (en/ru parity, one namespace per part file) |
| `scripts/deploy-frontend.sh` | production slot deploy (see deployment-map) |

E2E (`e2e/tests/`): admin, auth, student-panel, global-chat, global-chat-reply, a2-audio-manager,
a2-lesson4-hoeren, a2-audio-processing, screenshots; helpers in `helpers.ts`.
