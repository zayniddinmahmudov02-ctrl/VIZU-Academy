# VIZU-DEUTSCH — to‘liq tizim auditi (2026-10-29)

Bog‘liq hujjatlar: [bug-fixes.md](bug-fixes.md) · [security-findings.md](security-findings.md) · [test-results.md](test-results.md)

## Qamrov va qoidalar

- **Kod bazasi:** `origin/main` = `491a453` (Global Chat deploy). Lokal daraxt audit boshida shu commit bilan bayt-bayt bir xil edi; CRLF farqi hisobga olinmadi.
- **Production:** faqat o‘qildi. Konfiguratsiya, journal, header va portlar tekshirildi.
  - Prod’da deploy, migratsiya va servis restarti **bajarilmadi**.
  - Prod ma’lumotlari o‘zgartirilmadi.
  - Telegram bot (kod, baza, servislar) ga tegilmadi.
- **Testlar:** lokal test klasteri (PostgreSQL 18, `:54329`) ishlatildi:
  - `vizu_audit` — unit va integratsiya testlari, migratsiya round-trip;
  - `vizu_audit_e2e` — Playwright.
- **Barcha tuzatishlar lokal va commit qilinmagan.** Ro‘yxat [bug-fixes.md](bug-fixes.md) da.

## Arxitektura (tekshirilgan holat)

| Qatlam | Haqiqiy holat |
|---|---|
| Backend | FastAPI 0.139, SQLAlchemy 2 + psycopg 3, Alembic. Har bir router ikki joyga ulangan (bare va `/api/v1`), jami 1324 ta route. |
| Frontend | Next.js 16.2.10, React 19.2, TanStack Query, Zustand, Tailwind 4. 95 ta sahifa. |
| Baza | PostgreSQL. 102 ta migratsiya, yagona head `e9b4c2f7a3d1`. Prod’da 133 ta jadval. |
| Deploy | systemd: `vizu-backend` (uvicorn `0.0.0.0:8000`, root) va `vizu-frontend` (`next start`, `:3000`). Frontend `.next-a` / `.next-b` slotlari orqali chiqariladi (hozir `.next-a`). nginx → Cloudflare. |
| Media | `uploads/` → nginx `alias` orqali ochiq. Himoyalangan fayllar `app/protected_storage/` da va faqat imzolangan token orqali beriladi. |
| Auth | Bearer JWT + refresh rotation, `sid` orqali bekor qilish. Login e-mail yoki telefon bilan. Login va registratsiyada rate limit bor. |

## Tekshirilgan modullar

| Modul | Nima tekshirildi | Natija |
|---|---|---|
| Auth / RBAC | 1324 ta route’ning dependency daraxti avtomatik sanaldi. Auth’siz 27 ta route qo‘lda ko‘rib chiqildi. | 27 tasi ham ataylab ochiq: login, register, health, katalog yoki imzolangan token. IP spoofing tuzatildi (S-2). |
| Kurslar / LMS / progress | Prod journal tahlili, parallel visit testi | **P1 race tuzatildi** (B-1) |
| Quiz / baholash | Generic `student-quizzes` CRUD | **Talaba o‘z bahosini yoza olardi — tuzatildi** (S-3) |
| To‘lovlar (VIZU Pay) | Chek yuklash (kengaytma, magic-byte, 10 MB), egalik, admin amallari | Muammo topilmadi |
| Fayl yuklash | `/upload/{folder}`, `/media-library/upload` | **Path traversal va stored XSS tuzatildi** (S-1) |
| Sertifikatlar | Barcha endpointlar SUPER_ADMIN; public `verify` | Public javobdagi ortiqcha maydonlar olib tashlandi (S-6) |
| Global Chat | Integratsiya va E2E (desktop + mobile), prod smoke | Muammo topilmadi, 16/16 E2E o‘tdi |
| Groups & Classroom | Integratsiya testlari | Muammo topilmadi. IP helper umumiy helper’ga o‘tkazildi. |
| Wörterbuch | Integratsiya testlari | Muammo topilmadi |
| Page management | Katalog testi | `/admin/groups` qo‘shildi (B-4) |
| Baza / migratsiyalar | `upgrade head`, `downgrade base`, `alembic check` | 3 ta buzilgan downgrade va 9 ta model farqi tuzatildi (B-3, B-5) |
| Frontend | `tsc`, ESLint, production build, xavfsizlik header’lari | Header’lar qo‘shildi (S-5). ESLint’dagi eski 9 ta error ochiq qoldi (O-6). |
| Infra (prod, read-only) | Firewall, portlar, nginx, `.env` ruxsatlari, journal | Firewall o‘chiq (S-4, ochiq), `/docs` hammaga ochiq (S-7) |

## Topilmalar xulosasi

| ID | Daraja | Qisqacha | Holat |
|---|---|---|---|
| S-1 | **High** | Yuklashda path traversal (`filename="../../x"`), `/uploads/` orqali stored XSS. TEACHER va SUPPORT ham bajara oladi. | Tuzatildi (lokal) |
| S-3 | **High** | Talaba `POST/PUT /student-quizzes` orqali o‘ziga `score=100, passed=true` yozib, bo‘limlarni ochishi va ball olishi mumkin | Tuzatildi (lokal) |
| B-1 | **P1** | `…/competencies/{kind}/visit` da race: 48 soatda 53 ta HTTP 500 | Tuzatildi (lokal) |
| S-4 | **High** (infra) | Firewall o‘chiq: `:8000` va `:3000` internetdan ochiq, nginx va Cloudflare chetlab o‘tiladi | **Ochiq** — egasining infra qarori kerak |
| S-2 | Medium | `CF-Connecting-IP` / `X-Forwarded-For` har qanday mijozdan qabul qilinardi, IP bo‘yicha login limitini chetlab o‘tish mumkin edi | Tuzatildi (lokal) |
| B-2 | P2 | `.gitignore` dagi `media/` qoidasi `frontend/src/app/admin/media/page.tsx` ni yashirgan, natijada prod’da `/admin/media` 404 | Tuzatildi (lokal) |
| S-7 | Medium | `/docs` va `/openapi.json` hammaga ochiq (1041 ta yo‘l) | Tuzatildi (lokal; prod’da standart holatda o‘chadi) |
| S-5 | Low | Saytda xavfsizlik header’lari yo‘q edi | Tuzatildi (lokal) |
| B-3 | P2 | Migratsiyalarni `downgrade base` qilib bo‘lmasdi (3 ta revision) | Tuzatildi (lokal) |
| B-5 | P2 | Model va sxema o‘rtasida 10 ta farq: autogenerate indekslarni jimgina o‘chirib yuborardi | 9 tasi tuzatildi, 1 tasi atayin |
| B-6 | P2 | Kirish muddati va to‘lov testlari (10 ta) hech qachon ishlamagan: lokalda yig‘ilmagan, serverda import xatosi | Tuzatildi (lokal) |
| B-4 | P3 | Page catalog’da `/admin/groups` yo‘q edi, test yiqilardi | Tuzatildi (lokal) |
| S-6 | Low | Public sertifikat tekshiruvi `user_id` va fayl yo‘llarini qaytarardi | Tuzatildi (lokal) |
| O-1…O-9 | — | Ochiq qolgan masalalar | Pastda |

## Ochiq qolgan masalalar

| ID | Daraja | Masala | Tavsiya |
|---|---|---|---|
| S-4 / O-1 | High | `ufw inactive`. uvicorn `0.0.0.0:8000` da va `next start` `*:3000` da internetdan ochiq (o‘z kompyuterimdan tasdiqlandi). Bundan tashqari origin nginx IP orqali ham ochiq, shuning uchun soxta `CF-Connecting-IP` u orqali hali ham o‘tadi. | 1) uvicorn’ni `--host 127.0.0.1` ga o‘tkazish. 2) `next start -H 127.0.0.1`. 3) `ufw allow 22,80,443` va `ufw enable` (oldin SSH’ni tekshirish!). Yoki 80/443 ni faqat Cloudflare IP oralig‘iga ochish, nginx’da `set_real_ip_from` + `real_ip_header CF-Connecting-IP`. Prod o‘zgarishi bo‘lgani uchun bajarilmadi. |
| O-2 | Ops | Prod’da `SUPER_ADMIN_VERIFICATION_PASSWORD` sozlanmagan, 7 kunda `verify-admin-password` 3 marta 503 qaytargan | Egasi `docs/super-admin-verification-secret.md` bo‘yicha o‘rnatadi |
| O-3 | Low | Prod’da eski `backend/app/services/email/` katalogi qolgan (faqat `__pycache__`), shu sabab `test_no_email_modules` yiqiladi | Serverda shu katalogni qo‘lda o‘chirish |
| O-4 | Low | Prod venv’da `pytest` yo‘q. Testlar `unittest` bilan ishlaydi; B-6 dan keyin pytest’ga bog‘liq test qolmadi. | Hech narsa qilish shart emas |
| O-5 | Low | `student_speakings.user_id`: model nullable, toza bazada NOT NULL (initial migratsiyadan). Prod’da ustun keyinroq nullable qo‘shilgan. | Ataylab qoldirildi; yangi muhitlar uchun hujjatlashtirildi |
| O-6 | P3 | ESLint: 9 ta `react-hooks/set-state-in-effect` (video player, hooks), 5 ta `<img>`, 2 ta ishlatilmagan prop | Funksional xato emas. Video player’ni qayta yozish regressiya xavfi bilan keladi, shuning uchun alohida vazifa sifatida qilish kerak. |
| O-7 | Low | `productionBrowserSourceMaps: true` — frontend manba kodi hammaga ochiq | Ataylab yoqilgan (#310 diagnostikasi uchun). Kerak bo‘lmasa o‘chirish. |
| O-8 | Low | Sertifikat QR kodi `https://verify.vizu.uz/certificate/…` ga yo‘naltiradi. Bu joriy domen emas va frontend’da verify sahifasi yo‘q. | QR URL’ni joriy domenga va haqiqiy sahifaga moslash |
| O-9 | Low | Mock-exam (Vorbereitung) HTML’i serverda sanitize qilinmaydi. Yozish faqat SUPER_ADMIN’da, shuning uchun risk past. | Defense-in-depth sifatida `app/core/utils/safe_html.py` ni qo‘llash |
| O-10 | Ops | Lokal C: diskda 1.27 GB bo‘sh joy qolgan. Eng kattalari: npm-cache 4.2 GB, INetCache 2.0 GB, Chrome profili 1.2 GB, Temp 1.15 GB. | `npm config set cache D:\npm-cache`, keyin `npm cache clean --force` (foydalanuvchi qarori). Audit davomida TEMP D: ga yo‘naltirildi, hech narsa o‘chirilmadi. |
| O-11 | Info | Prod frontend logida 114 ta `Failed to find Server Action "x"` | Tashqi skanerlar (ilovada Server Action yo‘q). Avval ham shunday aniqlangan. |

## Tekshirilmagan yoki qisman tekshirilgan qismlar

- **Telegram login (`test_telegram_login_session_is_revocable`)** — NOT RUN. Haqiqiy bot tokeni kerak, botga tegilmadi.
- **Groups, Wörterbuch, to‘lov UI** uchun Playwright spec’lar yo‘q. Ular faqat backend integratsiya testlari bilan tekshirildi.
- **Haqiqiy brauzerda qo‘lda vizual tekshiruv**, ekran o‘quvchi va to‘liq accessibility auditi bajarilmadi. Avtomatik E2E faqat desktop Chrome va Pixel 7 emulyatsiyasida ishladi.
- **AI baholash (Gemini)** va **R2 storage** — tashqi xizmatlar chaqirilmadi.
- **Ishlash (performance):** yuklama testi o‘tkazilmadi. N+1 so‘rovlar tizimli qidirilmadi, faqat prod journal’dagi 5xx tahlil qilindi.

## Prod’ga chiqarish uchun eslatma (bajarilmagan)

1. **Yangi migratsiya yo‘q.** Model o‘zgarishlari faqat metadata, eski migratsiya fayllarida esa faqat `downgrade()` o‘zgargan.
2. **Xulq o‘zgarishlari:**
   - `/docs`, `/redoc`, `/openapi.json` `APP_ENV=production` da 404 qaytaradi. Kerak bo‘lsa `.env` ga `API_DOCS_ENABLED=true` qo‘shiladi.
   - `POST/PUT/DELETE /student-quizzes` endi faqat admin panel rollariga ruxsat beradi. Frontend bu endpointlardan foydalanmaydi.
   - Generic uploader `.html`, `.svg`, `.js` va boshqa faol fayllarni 400 bilan rad etadi.
3. **Commit:** `frontend/src/app/admin/media/page.tsx` ni git’ga qo‘shish kerak. `.gitignore` tuzatilgani uchun endi u ko‘rinadi.
