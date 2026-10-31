# Project overview

Updated 2026-10-31.

**VIZU-DEUTSCH / VIZU Academy** — online German school for Uzbek speakers, https://vizu-deutsch.com.

- **Products:** A1–C1 courses (LMS, lesson 1 free, levels sold through VIZU Pay), VIZU-Multilevel level test
  with certificate, Vorbereitung (Goethe-style mock exams), Wörterbuch, groups/classroom with teachers,
  Global Chat, notifications, support, achievements, PWA.
- **Users:** STUDENT; staff roles SUPER_ADMIN, ADMIN, CONTENT_MANAGER, PAYMENT_MANAGER, SUPPORT, TEACHER.
- **Languages:** student UI uz/de, admin UI German, course content German with Uzbek explanations, docs Uzbek.
- **Content state (2026-10-30):** A1 built and published; A2 book edition imported, lessons 1–13 published,
  Hören 22/27 published (see `current-state.md`); B1 sources exist; B2/C1 structure only (?).
- **Repo:** `backend/` (FastAPI), `frontend/` (Next.js), `e2e/` (Playwright), `docs/` (audits, runbooks,
  `ai-context/` maps). Telegram bots live elsewhere and are out of scope (`docs/telegram-bot-inventory.md`,
  `docs/bot-site-*.md` describe the planned migration).
- **Owner workflow:** the owner commits with GitHub Desktop; Claude works locally on Windows and deploys over SSH.
