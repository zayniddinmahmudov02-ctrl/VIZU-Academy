# Test natijalari

## 2026-10-30 — A2 4. Unterricht Hören: Text 1–3 (lokal + production)

Batafsil: `docs/a2-lesson-4-hoeren-update.md` 7-bo‘lim.

- **Lokal backend:** to‘liq to‘plam **907 passed, 17 skipped**; yangi `test_a2_lesson4_hoeren` 5/5; migratsiya testlari 2/2 (`b8e3d1a7c5f2` upgrade → downgrade → upgrade).
- **Lokal frontend:** `tsc` 0 xato; ESLint — yangi/o‘zgargan fayllarda 0, butun frontendda 9 error / 10 warning, hammasi o‘zgartirilmagan fayllarda; unit 19/19; build OK.
- **E2E** `a2-lesson4-hoeren.spec.ts` (desktop + Pixel 7): 7 passed, 1 skipped (upload faqat desktop’da).
- **Server:** tegishli modullar — Ran 124, OK (skipped 61).
- **Production smoke:** sahifalar 200; anonim 401 (8/8); backend va frontend xato 0.
- **NOT RUN:** production’da tizimga kirgan brauzer testi — parollar yo‘q; sun’iy audio yuklanmadi.

## 2026-10-29 (server vaqti) — production deploy va smoke testlar

Batafsil: `docs/audit/production-deploy-2026-10-29.md`. Serverda: o‘zgargan backend modullari 122 test OK (56 DB-integratsiya skip), frontend `tsc` OK, unit 19/19, build OK (2-urinishda), smoke testlar — HTTP 200, anonim 401 (11/11), READ ONLY servis tekshiruvlari OK. Brauzer orqali login qilingan smoke test bajarilmadi (production parollari yo‘q).

## 2026-10-30 — Global Chat reply + A2 Audio Manager (lokal)

Har bir raqam haqiqiy buyruq chiqishidan olingan. Loglar: `D:\vz_tmp\gcr_*.log`. Production’da hech qanday test bajarilmadi.

**Muhit:** lokal Windows, git yo‘q. Python 3.13, yangi venv (scratchpad, `requirements.txt` + `pytest`; `reportlab`, `qrcode[pil]`, `httpx` qo‘shimcha o‘rnatildi — 1-izoh). Node 24.18. Test PostgreSQL 18 (`127.0.0.1:54329`, `D:\vz_tmp\pgtest2`), yangi bazalar: `vizu_gcr_test` (unit/integratsiya), `vizu_gcr_mig` (migratsiya), `vizu_gcr_e2e` (Playwright). Bazalar saqlab qolindi, klaster ish oxirida to‘xtatildi.

### Backend (`python -m unittest discover -s tests`, `VIZU_WB_TEST_DB_URL` + `VIZU_MIGRATION_TEST_DB_URL`)

| Bosqich | Ran | Fail | Error | Skip |
|---|---|---|---|---|
| Baseline, o‘zgarishlardan oldin | 836 | 0 | 11 | 17 |
| **Yakuniy** | **917** | **0** | **0** | **17** |

- Baseline’dagi 11 error — hammasi `ModuleNotFoundError: reportlab` (keyin `qrcode`): paketlar kod ishlatadi, lekin `requirements.txt` da yo‘q. O‘rnatilgandan keyin bu modullar yuklandi — yakuniy sondagi farqning bir qismi shu.
- 17 skip — `test_auth_session_flow` (ishlab turgan backend talab qiladi), avvalgidek.
- Yangi testlar: `test_global_chat` +8 (2 kontrakt/unit, 6 integratsiya), `test_global_chat_reply_migration` 1, `test_a2_audio_manager` 19, `test_a2_audio_management` +1, `test_angebote` (narx qoidasi subtestlari).
- Ish davomida yiqilgan va tuzatilganlar: karantin papka nomi to‘qnashuvi (kod), migration testi Alembic’ni umumiy test bazasiga yo‘naltirib, `fileConfig` bilan logger’larni o‘chirgani (`test_request_id` yiqildi — test kodi). Tuzatishdan keyin to‘liq yugurish OK.

### Migratsiyalar (`vizu_gcr_mig`)

| Tekshiruv | Natija |
|---|---|
| `alembic upgrade head` | OK, head `a6d2f9c4e8b1` (yagona) |
| `alembic downgrade base` | OK, faqat `alembic_version` qoladi |
| qayta `upgrade head` | OK |
| Reply: ma’lumotli `upgrade → downgrade e9b4c2f7a3d1 → upgrade` | OK (xabarlar saqlanadi, FK va partial index bor) |
| `alembic check` | 1 farq — avvaldan ma’lum `student_speakings.user_id`; yangi modellar migratsiyalarga mos |

### Frontend

| Tekshiruv | Natija |
|---|---|
| `tsc --noEmit` | exit 0 |
| `eslint src next.config.ts tests` | 9 error, 8 warning — avvalgi audit bilan bir xil, hammasi o‘zgartirilmagan fayllarda; yangi/o‘zgargan fayllarda 0 |
| `npm run test:unit` (yangi, `node --test`, dependency qo‘shilmagan) | 19/19 (swipe 9, iqtibos 6, A2 import 4) |
| `next build` (`NEXT_DIST_DIR=.next-e2e`, `.next-a`/`.next-b` tegilmadi) | exit 0, “Compiled successfully”; `tsconfig.json` build’dan keyin tiklandi, `.next-e2e` o‘chirildi |

### E2E (Playwright, Chrome; desktop + Pixel 7; lokal uvicorn `:8000` + `next start` `:3000`)

| Yugurish | Passed | Failed | Skipped |
|---|---|---|---|
| Yangi spec’lar, 1-yugurish | 5 | 5 | 4 |
| Yangi spec’lar, tuzatishdan keyin | 10 | 0 | 4 |
| **To‘liq suite (yangi + eski)** | **66** | **0** | **14** |

- 1-yugurishdagi 5 fail: 3 tasi test kodi (iqtibos matni asl xabar lokatoriga ham mos kelgan; mobil yugurishda bir xil matn 60 s ichida qayta yuborilib server to‘g‘ri `429 duplicate_message` qaytargan), 1 tasi mening seed’im (A2 kompetensiyalari qoralama qolgan), 1 tasi **haqiqiy xato** — swipe’da `setPointerCapture` exception (tuzatildi).
- 14 skip: avvalgi 10 ta + yangi 4 ta ataylab (swipe testi faqat mobile, A2 admin oqimi faqat desktop).
- Qamrov: reply (tugma, klaviatura, Escape/X, iqtibos → asl xabarga scroll, o‘chirilgan asl xabar fallback’i, API: 422/forged maydon), mobil swipe (chapga — javob; vertikal, o‘ngga, qisqa — javob emas; `touch-action: pan-y`; gorizontal scroll yo‘q; tugma hover’siz ko‘rinadi), A2 (o‘quvchi/anonim 401/403, batch upload hisobot bilan, WAV va kengaytma/mazmun nomuvofiqligi xatolari, dublikat, taklif + tasdiqli bog‘lash, tekshiruv, nashrdan keyin 1-darsda o‘quvchi pleeri, 2-dars 403, `private, no-store`, sotuv yopiq — narx backend’dan, `purchasable: false`).
- To‘lov oqimi (buyurtma → rad → yangi buyurtma → tasdiq → takroriy tasdiq rad → `OFFER_ALREADY_OWNED` → refund) **faqat backend integratsiya testida**, servis funksiyalari orqali (`test_a2_purchase_flow_and_access`). UI orqali to‘lov va real to‘lov tizimi sinalmadi — ManualGateway, avtomatik gateway yo‘q.

### Bajarilmagan (NOT RUN)

- Production’da har qanday test, deploy, migratsiya.
- Haqiqiy A2 audio fayllari bilan test (fayllar mavjud emas; testlarda kichik generatsiya qilingan MP3/M4A sarlavhalari ishlatildi).
- Haqiqiy brauzerda haqiqiy barmoq bilan swipe (E2E pointer hodisalarini emulyatsiya qiladi).
- Qo‘lda accessibility / screen reader auditi, yuklama testlari.

### Tozalash

- uvicorn va `next start` to‘xtatildi; `:8000`, `:3000` bo‘sh. Test PostgreSQL klasteri to‘xtatildi (ish boshida ham to‘xtagan edi).
- E2E backend yaratgan `backend/app/protected_storage/` (faqat 2 ta generatsiya qilingan test fayli; papka avval yo‘q edi) va bo‘sh `backend/uploads/` o‘chirildi. `frontend/.next-e2e` o‘chirildi.
- `frontend/node_modules`, `e2e/node_modules` (gitignore’da) qoldirildi.

---

## 2026-10-29

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
