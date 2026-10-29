# Test natijalari (2026-10-29)

Har bir raqam haqiqiy buyruq chiqishidan olingan. Loglar: `D:\vz_tmp\audit_*.log`.

## Muhit

| | |
|---|---|
| OS | Windows 11. Lokal git yo‘q, shuning uchun daraxt `origin/main` bilan blob-hash orqali solishtirildi. |
| Python / Node | Backend `.venv`, Node `D:\node.exe` |
| Test DB | PostgreSQL 18, `127.0.0.1:54329`. Bazalar: `vizu_audit` (unit/integratsiya/migratsiya) va `vizu_audit_e2e` (Playwright). Ikkalasi ham saqlab qolindi. |
| TEMP | C: diskda 1.27 GB bo‘sh joy bo‘lgani uchun `D:\vz_tmp\audit_tmp` ga yo‘naltirildi |
| Prod | Faqat read-only. Prod’da test bajarilmadi (oldingi Global Chat deploy smoke testidan tashqari). |

## Backend (`python -m unittest discover -s tests`)

| Bosqich | Ran | O‘tdi | Fail | Error | Skip |
|---|---|---|---|---|---|
| Prod serverda, audit boshida (`gc_tests.log`) | 854 | 784 | 2 | 1 | 67 |
| Lokal baseline (integratsiya yoqilgan, tuzatishlardan oldin) | 853 | 835 | 1 | 0 | 17 |
| **Lokal yakuniy** | **888** | **871** | **0** | **0** | **17** |

- **Prod’dagi 3 ta muammo:**
  - `test_course_access_terms` — pytest yo‘q (B-6);
  - `test_no_email_modules` — serverda eski katalog qolgan (O-3);
  - `test_page_management` — `/admin/groups` (B-4) va `/admin/media` (B-2).
- **Prod’dagi 67 ta skip** — integratsiya testlari, chunki serverda test DB URL berilmagan.
- **Lokal baseline’dagi 1 ta fail** — `test_page_management` (`/admin/groups`).
- **888 = 853 + 25 yangi test + 10 ta qayta yozilgan test.** Qayta yozilganlar avval umuman yig‘ilmagan.
- **17 ta skip** — `test_auth_session_flow`. U ishlab turgan backend’ni talab qiladi va alohida ishga tushirildi (pastda).
- **`ERROR: could not find an existing A1 Lesson 1 …` qatorlari** test xatosi emas. Bu tekshirilayotgan skriptlarning kutilgan chiqishi.

### Yangi va o‘zgartirilgan testlar

| Fayl | Testlar | Tuzatishdan oldin | Keyin |
|---|---|---|---|
| `test_lms_visit_race.py` | 2 | 2 FAIL (`UniqueViolation`, prod xatosi takrorlandi) | OK (3/3 ketma-ket yugurish) |
| `test_student_quiz_permissions.py` | 5 | 4 FAIL + 1 ERROR | OK |
| `test_upload_path_safety.py` | 6 | Import xatosi; reproduksiya skripti fayl `uploads/` dan tashqariga yozilganini ko‘rsatdi | OK |
| `test_client_ip.py` | 7 | — (yangi helper) | OK |
| `test_api_docs_setting.py` | 3 | — | OK |
| `test_certificate_verify_public.py` | 2 | — | OK |
| `test_course_access_terms.py` | 10 | 0 ta yig‘ilgan (lokal); import xatosi (prod) | OK |

## Backend HTTP oqimi (`tests.test_auth_session_flow`, real uvicorn + `vizu_audit_e2e`)

- **Natija:** 17 tadan 16 tasi o‘tdi.
- **1 ta NOT RUN:** `test_telegram_login_session_is_revocable`. U haqiqiy `TELEGRAM_BOT_TOKEN` ni talab qiladi, Telegram botga tegilmadi.

## Migratsiyalar (`vizu_audit`)

| Tekshiruv | Natija |
|---|---|
| Bo‘sh bazada `alembic upgrade head` | OK (exit 0). Head `e9b4c2f7a3d1`, yagona head. |
| `alembic downgrade base` | **Oldin:** 3 joyda FAIL. **Keyin:** OK, faqat `alembic_version` jadvali qoladi. |
| Qayta `alembic upgrade head` | OK |
| `alembic check` | **Oldin:** 10 ta farq. **Keyin:** 1 ta farq (`student_speakings.user_id` nullable, ataylab qoldirilgan). Exit kodi shu sabab -1. |

## Frontend

| Tekshiruv | Natija |
|---|---|
| `tsc --noEmit` | exit 0, 0 ta xato |
| `eslint src next.config.ts` | exit 1: **9 error, 8 warning** — hammasi audit’dan oldin ham bor edi (O-6) |
| `next build` (alohida `.next-audit` katalogida) | exit 0, `Compiled successfully`, `/admin/media` ro‘yxatda bor |
| Komponent testlari | Loyihada yo‘q (NOT AVAILABLE) |

ESLint’dagi 9 ta error:

- `react-hooks/set-state-in-effect` qoidasi bo‘yicha `video-player.tsx`, `receipt-viewer.tsx`, `use-calendar-events.ts`, `use-information.ts`, `use-lesson-access.ts`, `use-lesson.ts`, `use-video-progress.ts`, `use-install-prompt.ts` va `use-vizu-pay.ts` da.
- Production build ESLint’ni ishga tushirmaydi, shuning uchun ular deploy’ni to‘xtatmaydi.

## E2E (Playwright, Chrome; desktop + Pixel 7)

Stack: lokal uvicorn `:8000` (`vizu_audit_e2e`) va `next start` `:3000`.

| Yugurish | Passed | Failed | Skipped |
|---|---|---|---|
| 1-yugurish | 51 | 5 | 10 |
| Seed tuzatilgandan keyin, faqat `global-chat.spec.ts` | 16 | 0 | 0 |
| **Yakuniy to‘liq yugurish** | **56** | **0** | **10** |

- **1-yugurishdagi 5 ta fail** mening seed'imdagi xato tufayli bo‘lgan, kod xatosi emas.
  - Seed'imda test foydalanuvchisining ismi asl `gc_seed.py` dagidan farq qilgan ("Sami" o‘rniga "Gc Student1").
  - Natijada mute bekor qilinmadi va keyingi testlar 403 olishda davom etdi.
- **10 ta skip ataylab qilingan:**
  - 6 ta screenshot testi (`E2E_SHOTS` talab qiladi);
  - 2 ta admin testi mobile’da;
  - 2 ta logout testi o‘zining loyihasidan tashqarida.

**Qamrov:**

- login, logout va remember-me;
- welcome, register va yordam dialoglari;
- student panel va sozlamalar;
- admin sidebar;
- Global Chat: XSS, live xabarlar, unread, pin, mute, edit/delete va mobil layout.

**E2E qamrovida yo‘q (NOT COVERED):**

- Groups & Classroom UI;
- Wörterbuch (qidiruv, Random 5, saqlangan so‘zlar);
- kurs va dars UI;
- to‘lov UI.

Bular faqat backend integratsiya testlari bilan tekshirildi: `test_study_groups`, `test_woerterbuch`, `test_course_access_terms` va boshqalar.

## Bajarilmagan (NOT RUN)

- Prod’da regression yoki E2E — qoida bo‘yicha taqiqlangan.
- Telegram login HTTP testi — bot tokeni kerak.
- Yuklama va performance testlari.
- Qo‘lda brauzer, accessibility va ekran o‘quvchi auditi.
- Tashqi xizmatlar (Gemini AI baholash, Cloudflare R2).

## Tozalash

- Audit uchun ishga tushirilgan uvicorn (PID 16528) va `next start` (PID 2820) bola jarayonlari bilan birga to‘xtatildi. `:8000` va `:3000` portlari bo‘sh.
- `frontend/.next-audit` build katalogi o‘chirildi.
- `frontend/tsconfig.json` (build uni o‘zgartirgan) asl holatiga qaytarildi.
- Serverdagi `/root/cc_*` read-only skriptlari va loglari qoldi. `/tmp/cc_gi` klon o‘chirildi.
