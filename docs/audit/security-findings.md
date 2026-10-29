# Xavfsizlik topilmalari (2026-10-29)

Barcha reproduksiyalar lokal test muhitida yoki temp katalogda bajarildi. Prod’da faqat read-only so‘rovlar yuborildi: header’lar, ochiq portga bitta `GET /health`, journal tahlili. Hech qanday ekspluatatsiya qilinmadi. Tuzatishlar lokal, deploy qilinmagan.

## S-1 · High · Fayl yuklashda path traversal va stored XSS — tuzatildi

- **Kim:** `ADMIN_PANEL_ROLES` dagi istalgan rol: SUPER_ADMIN, ADMIN, CONTENT_MANAGER, PAYMENT_MANAGER, SUPPORT, **TEACHER**.
- **Qayerda:** `POST /upload/{folder}`, `POST /media-library/upload`.
- **Muammo.** `folder` allowlist bilan tekshiriladi, lekin multipart `filename` o‘zgarishsiz `uploads/<folder>/<filename>` ga yozilardi. Starlette `../../evil.py` ni tozalamaydi (tekshirildi). Servis root sifatida ishlaydi.
- **Reproduksiya** (temp katalogda, eski kod bilan): `filename="../../evil.py"` → fayl `uploads/` dan **tashqariga** yozildi.
- **Ta'sir.**
  - Istalgan faylni ustidan yozish, masalan `app/*.py`, va keyingi restartda kod bajarilishi.
  - nginx `/uploads/` ni `alias` bilan bir xil domenda beradi, shuning uchun yuklangan `.html` yoki `.svg` fayl `vizu-deutsch.com` nomidan script ishga tushiradi (stored XSS) va admin tokenlarini o‘g‘irlashi mumkin.
- **Tuzatish.**
  1. `safe_filename()`: faqat oxirgi path segmenti va `[\w.-]` belgilari, boshidagi nuqtalar olib tashlanadi, uzunligi ≤150.
  2. `LocalStorage._inside_root()`: `upload()` va `delete()` `ROOT` dan tashqariga chiqadigan yo‘lni rad etadi (defense in depth).
  3. `BLOCKED_EXTENSIONS` (`.html`, `.htm`, `.svg`, `.js`, `.xml`, `.php` va boshqalar) → 400. Media turlari (mp3/m4a/mp4/png/pdf/docx …) avvalgidek qabul qilinadi.
- **Test:** `tests/test_upload_path_safety.py` (6). Reproduksiya skripti tuzatishdan keyin faylni `uploads/images/evil.py` ga yozadi, ya'ni ichkariga.

## S-2 · Medium · IP bo‘yicha rate limitni chetlab o‘tish — tuzatildi (infra qismi ochiq)

- **Muammo.** Uchta joyda forwarding header’larga **har qanday mijozdan** ishonilardi:
  - `auth/router._client_ip` (login va registratsiya limiti);
  - `study_groups._ip`;
  - `advertisements._client` (`X-Forwarded-For[0]` ni Cloudflare orqali ham soxtalashtirish mumkin).
- **Reproduksiya.** Backend `0.0.0.0:8000` da internetdan ochiq (S-4). Har so‘rovda boshqa `CF-Connecting-IP` yuborilsa, har so‘rov yangi IP limiti oladi. Identifier bo‘yicha limit esa qoladi.
- **Tuzatish.** `app/core/client_ip.py`: header’larga faqat TCP peer `TRUSTED_PROXY_IPS` (standart `127.0.0.1,::1`, ya'ni nginx yoki Next.js) bo‘lganda ishoniladi. Tartib: `CF-Connecting-IP` → `X-Real-IP` → XFF’ning **oxirgi** hopi.
- **Test:** `tests/test_client_ip.py` (7). E2E `createStudent` (loopback orqali XFF bilan) avvalgidek ishlaydi.
- **Ochiq qism.** Origin nginx IP orqali to‘g‘ridan-to‘g‘ri ochiq. Shu yo‘l bilan kelgan soxta `CF-Connecting-IP` nginx orqali loopback’dan keladi va hali ham qabul qilinadi. Buni faqat infra darajasida yopish mumkin (S-4).

## S-3 · High · Talaba o‘z quiz bahosini yozishi mumkin edi — tuzatildi

- **Muammo.** `POST /student-quizzes` faqat `body.user_id == current_user.id` ni tekshirardi, `PUT /student-quizzes/{id}` va `DELETE` esa egaga ruxsat berardi. `StudentQuiz` qatorlari:
  - bo‘limlarni ochishda (`lesson_progress/section_gate.py`);
  - darsning 100 balllik bahosida ("Yakuniy Test" 10 ball, `lesson_scoring/service.py`) ishlatiladi.
- **Reproduksiya.** Talaba `{"user_id": "<o‘zi>", "quiz_id": "…", "score": 100, "passed": true}` ni POST qiladi, so‘rov o‘tadi. Test bilan tasdiqlandi: tuzatishdan oldin 3 ta route `get_current_user` bilan ochiq edi.
- **Tuzatish.**
  - create, update va delete endi `require_admin_panel_access` bilan himoyalangan;
  - o‘qish ega yoki admin uchun qoladi;
  - UUID va str taqqoslash xatosi tuzatildi, endi talaba o‘z ro‘yxatini ko‘radi.
  - Haqiqiy yozuvlar avvalgidek server baholaydigan `quiz/grading_service.grade_and_submit` dan keladi. Frontend `/student-quizzes` dan foydalanmaydi.
- **Test:** `tests/test_student_quiz_permissions.py` (5). Tuzatishdan oldin 4 ta fail va 1 ta error, keyin 5/5.

## S-4 · High (infra) · Firewall o‘chiq, ichki portlar internetga ochiq — OCHIQ

- **Topilma (read-only).**
  - `ufw status: inactive`, `iptables -P INPUT ACCEPT`.
  - `uvicorn --host 0.0.0.0 --port 8000` va `next-server *:3000`.
  - O‘z kompyuterimdan tekshirildi: `http://217.76.62.208:8000/health` → 200, `http://217.76.62.208:3000/login` → 200.
- **Ta'sir.**
  - Cloudflare (WAF va DDoS himoyasi) va nginx chetlab o‘tiladi.
  - Shifrlanmagan HTTP orqali login qilish mumkin.
  - S-2 qoldig‘i ham shu yo‘l bilan ishlaydi.
- **Tavsiya.** Prod o‘zgarishi bo‘lgani uchun **bajarilmadi**, egasining ruxsati kerak:
  1. `vizu-backend`: `--host 127.0.0.1`. `vizu-frontend`: `next start -H 127.0.0.1`. Keyin ikkala servisni restart qilish.
  2. `ufw allow 22/tcp; ufw allow 80/tcp; ufw allow 443/tcp; ufw enable`. Avval SSH sessiyasini ochiq ushlab turish kerak.
  3. Yaxshiroq variant: 80/443 ni faqat Cloudflare IP oralig‘iga ochish va nginx’da `set_real_ip_from <CF ranges>; real_ip_header CF-Connecting-IP;` sozlash.
  4. `vizu-ig-agent` (`:8010`) va boshqa servislar portlarini ham shu bilan birga ko‘rib chiqish.

## S-5 · Low · Xavfsizlik header’lari yo‘q edi — tuzatildi

- **Topilma.** `curl -I https://vizu-deutsch.com/` javobida HSTS, `nosniff` va `Referrer-Policy` yo‘q.
- **Tuzatish.** `frontend/next.config.ts` `headers()`: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Strict-Transport-Security: max-age=31536000`.
- **Ataylab qo‘shilmaganlari:**
  - `X-Frame-Options` va CSP `frame-ancestors`, chunki Telegram Web Mini App’ni iframe ichida ochadi;
  - `Permissions-Policy`, chunki Sprechen mikrofondan foydalanadi.
- **Tekshiruv.** Lokal `next start` javobida uchala header bor. E2E 56/56 o‘tdi.

## S-6 · Low · Public sertifikat tekshiruvi ortiqcha ma'lumot qaytarardi — tuzatildi

- **Muammo.** `GET /certificates/verify/{code}` ORM qatorini to‘liq qaytarardi: `user_id`, `course_id`, serverdagi `pdf_url` va `qr_code_url` fayl yo‘llari. Kod 128-bit tasodifiy, shuning uchun sanab chiqib bo‘lmaydi.
- **Tuzatish.** Faqat `PUBLIC_VERIFY_FIELDS` qaytariladi: raqam, kod, provider, daraja, ballar, sana, `is_valid`.
- **Test:** `tests/test_certificate_verify_public.py` (2).

## S-7 · Medium · API hujjatlari hammaga ochiq — tuzatildi

- **Topilma.** `https://vizu-deutsch.com/docs` (Swagger UI) va `/openapi.json` 200 qaytaradi: 1041 ta yo‘l, shu jumladan barcha admin endpointlar. nginx ularni ataylab proxy qiladi.
- **Tuzatish.** `API_DOCS_ENABLED` sozlamasi: qiymat berilmasa `APP_ENV=production` da docs o‘chadi, boshqa muhitlarda yoqiq qoladi. Kerak bo‘lsa `.env` ga `API_DOCS_ENABLED=true` yoziladi.
- **Test:** `tests/test_api_docs_setting.py` (3). `APP_ENV=production` da `app.docs_url is None` ekani tekshirildi.

## Tekshirildi — muammo topilmadi

- **Auth dependency auditi.** 1324 ta route avtomatik sanaldi. Auth’siz 27 tasi qo‘lda ko‘rib chiqildi va hammasi ataylab ochiq:
  - login, register, refresh, health;
  - katalog ro‘yxatlari;
  - imzolangan token bilan himoyalangan stream endpointlari (`videos/*/stream`, `lms/resources/*/file`, admin preview). Token resurs va foydalanuvchiga bog‘langan, kirish huquqi qayta tekshiriladi.
  - Public assessment to‘g‘ri javoblarni olib tashlaydi (`to_public_schema`).
- **To‘lovlar.**
  - Admin amallari (approve, reject, refund, extend, promo) faqat `require_super_admin` bilan ochiladi.
  - Chek fayli: kengaytma, magic-byte va 10 MB limit tekshiriladi.
  - `GET /orders/{id}/proof` faqat ega yoki xodimga ochiq.
- **Generic CRUD DELETE’lar** (payment, progress, writing, speaking, homework, exam) admin rollari bilan himoyalangan.
- **Video progress.** `complete` serverda yozilgan foizni tekshiradi. Erkin seek ataylab ruxsat etilgan va hujjatlashtirilgan.
- **Global Chat.**
  - Mute, ban va moderatsiya backend’da tekshiriladi.
  - Body’da `user_id` yoki `role` bo‘lsa 422 qaytadi.
  - Matn React text sifatida ko‘rsatiladi (E2E: HTML ishga tushmaydi).
  - Rate limit advisory lock ostida ishlaydi.
- **CORS.** Begona origin’dan kelgan preflight 400 bilan rad etiladi. `localhost:*` dev uchun ruxsat etilgan, auth esa Bearer token (cookie emas), shuning uchun CSRF xavfi yo‘q.
- **`.env`** fayli `600 root:root` ruxsatlari bilan va git’da yo‘q. Prod’da `APP_ENV=production`, `DEBUG=False`, SQL echo o‘chiq.

## Past darajadagi kuzatuvlar (tuzatilmagan)

- **O-7.** Production source map’lar ochiq (`productionBrowserSourceMaps: true`), bu ataylab yoqilgan.
- **O-8.** Sertifikat QR kodi begona domenga ishora qiladi (`verify.vizu.uz`).
- **O-9.** Mock-exam HTML sanitize qilinmaydi (faqat SUPER_ADMIN yozadi).
- **O-2.** `SUPER_ADMIN_VERIFICATION_PASSWORD` prod’da sozlanmagan. Tizim fail-closed ishlaydi (503), ikkinchi bosqich hozircha ishlamaydi.
