# Telegram bot inventari (1-bosqich audit)

Audit sanasi: 2026-10-28. Rejim: faqat o'qish. Production kodi, bazasi va servislari o'zgartirilmagan, hech narsa restart qilinmagan.
Secret, token, parol, karta raqami, taklif havolalari va foydalanuvchi ma'lumotlari bu hujjatga kiritilmagan. Faqat nomlar, sonlar va bog'lanishlar keltirilgan.

## 1. Joylashuv va ishga tushirish

| Narsa | Qiymat (dalil) |
|---|---|
| Ishchi katalog | `/opt/vizu/bots/telegram-cours2026` (`/etc/systemd/system/telegram-cours2026.service`, `WorkingDirectory`) |
| Git | branch `main`, HEAD `ee83faf`, origin `github.com/zayniddinmahmudov02-ctrl/telegram-cours2026`, origin bilan farq 0/0 |
| Working tree | faqat ` M .env` (tracked `.env` lokal o'zgartirilgan) |
| Servis | `telegram-cours2026.service`, `User=root`, `Restart=always`, `EnvironmentFile=.env`, `ExecStart=venv/bin/python main.py`; 2026-10-24 dan beri ishlab turibdi |
| Rejim | long polling (`main.py`: `delete_webhook(drop_pending_updates=True)` + `dp.start_polling`) |
| Freymvork | aiogram ≥ 3.13, psycopg2 `ThreadedConnectionPool` (2–20 ulanish, thread executor) — `database/connection.py` |
| FSM xotirasi | `MemoryStorage` (`loader.py`), ya'ni restartda barcha FSM holatlari va o'yin sessiyalari yo'qoladi |
| Qo'shimcha | Flask `GET /` → "Bot is running", `0.0.0.0:10000` da (`main.py`), internetga ochiq (`ss -ltnp`; `ufw` o'chiq, nginx proxy yo'q) |
| Hajm | ~17 200 qator Python, 14 router, 26 DB jadval |
| Env kalitlari (faqat nomlar) | `TOKEN`, `DATABASE_URL`, `ADMIN_ID`, `ADMIN_PASSWORD`, `ADMIN_CHANNEL_ID`, `CHANNEL_ID`. Ixtiyoriy: `ADMIN_IDS`, `APP_TIMEZONE` (default `Asia/Tashkent`), `PORT` |

**Sayt bilan bitta serverda.** Sayt `/opt/vizu/VIZU-Academy` da ishlaydi (`vizu-backend` uvicorn :8000, `vizu-frontend` Next.js slotlari). Bot va saytning PostgreSQL 16 instansiyasi bitta, lekin bazalari alohida: bot `telegram_course2026` da, sayt `vizu` da.

### 1.1 Serverdagi boshqa bot va xizmatlar

| Xizmat | Holat | Izoh |
|---|---|---|
| `vizu-bot.service` → `/opt/vizu/academy` | disabled, inactive | Aynan shu repoching **eski nusxasi** (HEAD `aad6b37`, joriydan 6 commit orqada). `.env` dagi token jonli bot bilan bir xil va `DATABASE_URL` ham `telegram_course2026` ga qaraydi. Yoqilsa, bitta token bilan ikkita polling jarayoni bir-biri bilan to'qnashadi. |
| `nano_bot.service` (`/opt/nano_bot`) | active | Boshqa loyiha (o'z bazasi `nano_bot`), auditga kirmaydi |
| `vizu-ig-agent.service` | active | Instagram agenti (:8010), auditga kirmaydi |
| `vizu-db-backup.timer` | har kuni ~03:00 | `/opt/vizu/scripts/backup_db.sh` **faqat sayt bazasi `vizu` ni** zaxiralaydi (14 kun saqlanadi). Bot bazasi `telegram_course2026` zaxiralanmaydi. |
| cron | faqat tizimniki (certbot, e2scrub, sysstat) | Botga tegishli cron yo'q |
| `vizu_academy_bot` bazasi | 16 jadval | Avvalgi bot sxemasi (`lesson_progress`, `vizu_*_results`, `w_certificates`…). Joriy kodda ishlatilmaydi. |

### 1.2 Fon vazifalari (bot ichida, `main.py` → `services/runtime.py`)

| Vazifa | Davr | Nima qiladi |
|---|---|---|
| `cleanup_quiz_memory` | 1 soat | xotiradagi o'yin lug'atlarini va `generated/*.png` ni tozalash. **Xato:** `runtime.py` oxirida `quiz_sessions` va boshqalar qayta e'lon qilingan, shuning uchun tozalash boshqa (bo'sh) obyektlar ustida ishlaydi. |
| `daily_champion_scheduler` | har kuni 00:00:05 (APP_TIMEZONE) | kecha eng ko'p XP olgan foydalanuvchini `daily_champions` ga yozadi; xabar yuborilmaydi |
| `weekly_champion_scheduler` | dushanba 00:00:05 | `weekly_champions` + **barcha foydalanuvchilarga xabar** |
| `monthly_champion_scheduler` | oyning 1-kuni | `monthly_champions` + barchaga xabar |

Uchala champion vazifasi ham idempotent (unique indeks + `*_exists`) va restartdan keyin o'tkazib yuborilgan davrni to'ldiradi. Ular bot jarayoni ichida ishlaydi; alohida scheduler yo'q.

## 2. Funksiyalar

"Saytda" ustuni qisqa izoh beradi; to'liq tasnif `bot-to-site-feature-matrix.md` da.

### F01. Start va majburiy kanal obunasi
- **Foydalanuvchi:** `/start` bosadi. Kanalga a'zo bo'lmasa, "a'zo bo'ling" xabari va tekshirish tugmasi chiqadi.
- **Kod:** `handlers/start.py`, `middlewares/subscription.py` (`get_chat_member`, adminlar va `/start`, `check_sub` istisno).
- **DB:** yo'q.
- **Bog'liqlik:** Telegram kanali (`CHANNEL_ID`/`@vizu_deutsch`).
- **Saytda:** yo'q, Telegram'ga xos.
- **Murakkablik/xavf:** past.
- **Qaror:** botda qoladi.

### F02. Foydalanuvchini avtomatik ro'yxatga olish
- **Foydalanuvchi:** har qanday update'da profili upsert qilinadi.
- **Kod:** `middlewares/user_tracking.py` → `database/users.py:upsert_user`.
- **DB:** `users` (PK `user_id` = Telegram ID).
- **Saytda:** sayt hisobi alohida (email yoki telefon). Mini App kirish `users.telegram_id` ni to'ldiradi, lekin hozir 0 ta foydalanuvchida to'ldirilgan.
- **Xavf:** o'rtacha — ID mapping kerak.
- **Qaror:** botda qoladi va bog'lash (linking) qo'shiladi.

### F03. Asosiy menyu va "🇩🇪 VIZU-De" Mini App tugmasi
- **Foydalanuvchi:** menyudan bo'lim tanlaydi. VIZU-De tugmasi saytni Telegram WebApp sifatida ochadi.
- **Kod:** `keyboards/main.py` (`WebAppInfo(url="https://vizu-deutsch.com")`).
- **Saytda:** sayt `POST /auth/telegram` (initData HMAC) va `telegram-auto-login.tsx` bilan buni qabul qiladi. Oxirgi 30 kunda 1 ta so'rov bo'lgan, javob 401.
- **Qaror:** botda qoladi; saytga kirish nuqtasi.

### F04. So'z o'yini (WortSpiel) — botda qoladi
To'liq mexanika 3-bo'limda.
- **Kod:** `handlers/wordgame.py`, `handlers/quiz_callback.py`, `handlers/quiz_retry.py`, `services/quiz.py`, `services/loader.py`.
- **DB:** `quiz_progress`, `users.unlocked_level`, `user_scores`, `xp_events`.
- **Ma'lumot:** `A1/A2/B1/B2/C1-words.csv`.
- **Saytda:** yo'q. Sayt `Wörterbuch` sahifasi faqat interfeys: `use-woerterbuch.ts` da "BACKEND TODO".
- **Qaror:** **botda qoladi** (talab).

### F05. Reyting (Leaderboard)
- **Foydalanuvchi:** "🏆 Reytinglar" yoki `/leaderboard` → kunlik, haftalik, oylik, overall top-100 va o'z o'rni.
- **Kod:** `handlers/leaderboard.py`, `database/leaderboard.py`.
- **DB:** `xp_events` (vaqt bo'yicha filtr, hech narsa reset qilinmaydi), `user_scores.global_score`, `quiz_progress` (aniqlik).
- **Saytda:** sayt XP hisoblaydi (`StudentProgress.total_score`, `services/learning/experience/service.py`), lekin reyting sahifasi yoki API yo'q.
- **Qaror:** botda qoladi; saytga faqat o'qish uchun ko'rinish keyinroq.

### F06. Champions (kunlik, haftalik, oylik tarix)
- **Foydalanuvchi:** "Champions" bo'limida tarixni ko'radi; haftalik va oylik g'olib barchaga e'lon qilinadi.
- **Kod:** `handlers/leaderboard.py`, `services/ranking.py`, `services/runtime.py`.
- **DB:** `daily_champions` (89), `weekly_champions` (13), `monthly_champions` (3). `hall_of_fame` (0) ishlatilmaydi.
- **Saytda:** yo'q.
- **Qaror:** botda qoladi.

### F07. W-Zertifikat (So'z o'yini sertifikati)
- **Foydalanuvchi:** darajaning barcha bloklari ≥ 60% bo'lsa, PDF sertifikat oladi (Gold ≥ 90, Silver ≥ 80, aks holda Bronze).
- **Kod:** `services/certificate.py`, `services/certificate_generator.py` (Jinja2 + WeasyPrint), `templates/certificate.html`, `database/certificates.py`.
- **DB va fayllar:**
  - `certificates` (35 ta; unique `(user_id, certificate_type, level)`);
  - PDF fayllar: `certificates/generated/*.pdf` (35 fayl, ~115 MB).
- **Saytda:** sayt `Zertifikate` — kurs va multilevel sertifikati, boshqa qoida (0 ta). W-Zertifikat yo'q.
- **Qaror:** botda qoladi (o'yin bilan bog'liq). Saytda ko'rsatish ixtiyoriy.

### F08. Mening profilim
- **Foydalanuvchi:** ism, telefon, XP (bugun/hafta/oy/umumiy), aniqlik va darajani ko'radi; ismini o'zgartiradi; sertifikatlarini ko'radi.
- **Kod:** `handlers/profile.py`.
- **DB:** `users`, `xp_events`, `user_scores`, `quiz_progress`, `certificates`.
- **Saytda:** qisman (`/settings`, `/dashboard`, `/certificates`), lekin o'yin XP'si yo'q.
- **Qaror:** botda qoladi. Saytda bog'langan profil ko'rinishi qo'shilishi mumkin.

### F09. Video kurslar katalogi
- **Foydalanuvchi:** A1, A2, B1, A1–B1, A1–C1 kurslarining narxi va dars soni; B2, C1, B2–C1 "Tez orada"; bepul namuna dars havolasi.
- **Kod:** `handlers/video.py`, `keyboards/video.py`.
- **Ma'lumot:** narxlar kod ichida `config/settings.py: COURSE_INFO`. Kurs tanlanganda `users.course` ga yoziladi.
- **Saytda:** qisman. Saytda `Angebote` va VIZU Pay bor, narxlar `app_settings.angebote` da. **Mahsulotlar har xil:** bot Telegram video kanallariga kirishni sotadi; sayt saytdagi darslarga kirishni sotadi va hozir faqat A1.
- **Xavf:** yuqori (biznes qoidasi farq qiladi).
- **Qaror:** qo'shimcha tekshiruv kerak.

### F10. To'lov (chek orqali qo'lda tasdiqlash)
- **Foydalanuvchi:**
  1. kartaga pul o'tkazadi;
  2. chek yuboradi (rasm yoki PDF);
  3. ism va telefonini kiritadi;
  4. ariza admin kanaliga tushadi;
  5. admin "Tasdiqlash" yoki "Rad etish" ni bosadi;
  6. foydalanuvchi kurs kanali va guruh taklif havolasini oladi.
- **Kod:** `handlers/payment.py`, `database/payments.py`, `keyboards/payment.py`, `states/payment.py`.
- **DB:** `payments` — 78 ta: approved 69, pending 3, rejected 6 (2026-07 … 2026-10).
- **Saytda:** qisman. VIZU Pay: `subscription_orders`, chek yuklash, `require_super_admin` bilan tasdiqlash, promo kodlar.
- **Xavf:** yuqori (pul + kirish huquqi).
- **Qaror:** qo'shimcha tekshiruv. Tarixiy to'lovlar botda saqlanadi.

### F11. Medien (Bücher, Filme, Musik)
- **Foydalanuvchi:**
  - kitoblarni daraja va kategoriya bo'yicha, filmlarni, musiqani ko'radi;
  - qidiradi;
  - musiqani sevimlilarga qo'shadi;
  - fayl xususiy Telegram kanalidan `copy_message` bilan yuboriladi.
- **Kod:** `handlers/media.py`, `services/media.py`, `services/loader.py`, `keyboards/media.py`, `database/favorites.py`.
- **Ma'lumot:**
  - katalog CSV'da: `Bucher.csv` 147, `Filme.csv` 11, `Musik.csv` 451;
  - fayllar serverda emas, Telegram kanallarida;
  - DB'da faqat `favorite_music` (10).
- **Saytda:** qisman. Sayt `admin/books` da PDF kitoblar bor (3 ta). Film va musiqa yo'q.
- **Xavf:** o'rtacha. Fayllar Telegram'da va mualliflik huquqi masalasi bor.
- **Qaror:** qo'shimcha tekshiruv.

### F12. Ma'lumotlar
- **Foydalanuvchi:** VIZU, muallif, ijtimoiy tarmoqlar va admin kontakti haqida matnlar.
- **Kod:** `handlers/info.py`, `texts/info.py`, `keyboards/info.py`.
- **DB:** yo'q.
- **Saytda:** qisman (`/informationen`).
- **Qaror:** botda qoladi (statik). Matnlar bir manbadan boshqarilishi mumkin.

### F13. Hausaufgaben (uy vazifasi)
- **Foydalanuvchi:**
  1. kategoriyani tanlaydi: "Sprechen guruh", "Video darslar", "Online guruhlar";
  2. birinchi marta parol kiritadi;
  3. ism va familiyasini kiritadi;
  4. daraja va dars raqamini tanlaydi;
  5. audio, voice, rasm, hujjat yoki matnni istalgan tartibda yuklaydi;
  6. tasdiqlaydi — vazifa kategoriya kanaliga yuboriladi.
  
  Shuningdek tarix va umumiy ballni ko'radi.
- **Kod:** `handlers/homework/{access,profile,menu,submission,history}.py`, `services/homework.py`, `database/homework*.py`, `utils/security.py` (PBKDF2, 200k).
- **DB:**
  - `homework_categories` (3, hammasida parol bor);
  - `homework_memberships` (144);
  - `homework_submissions` (239);
  - `homework_submission_files` (736);
  - `homework_evaluations` (154).
- **Fayllar:** faqat Telegram `file_id`. Fayl serverga yuklab olinmaydi.
- **Saytda:** qisman. Saytda dars ichidagi Schreiben/Sprechen topshiriqlari va o'qituvchi paneli bor (`student_writings` 6, `student_speakings` 10), `homework_submissions` 0. Biznes modeli boshqa: bot kanal, parol va guruh asosida ishlaydi.
- **Xavf:** yuqori.
- **Qaror:** qo'shimcha tekshiruv.

### F14. Sprechen guruh (Hausaufgaben ichida)
- **Foydalanuvchi:**
  1. jins va daraja guruhini tanlaydi (0–A1, A2–B1, B2–C1);
  2. parol kiritadi;
  3. tegishli Telegram guruh havolasini oladi;
  4. 20 darslik jadvalda vazifa yuboradi.
  
  Admin parolni almashtirsa, barcha a'zolikning kirish huquqi bekor bo'ladi (`access_password_hash` snapshot).
- **Kod:** `handlers/homework/sprechen.py`, `services/homework.py:is_sprechen_access_valid`, `config/settings.py: SPRECHEN_GROUP_LINKS`.
- **DB:** `homework_memberships.gender/level_group/access_password_hash`.
- **Saytda:** yo'q.
- **Qaror:** botda qoladi (Telegram guruhlariga bog'liq).

### F15. Uy vazifasini baholash (admin)
- **Foydalanuvchi (admin):** kanal postidagi yoki admin paneldagi 1–5 tugmasini bosadi. Natija statusi `revision_required`, `accepted` yoki `excellent` bo'ladi, talabaga xabar yuboriladi, kanal posti yangilanadi.
- **Kod:** `handlers/homework/evaluation.py` (`is_admin` tekshiriladi), `keyboards/homework_admin.py`.
- **DB:** `homework_evaluations` (UPSERT, `UNIQUE(submission_id)`), `homework_submissions.status`.
- **Saytda:** qisman (`/teacher/schreiben`, `/teacher/sprechen`).
- **Qaror:** qo'shimcha tekshiruv.

### F16. Hausaufgaben Admin
- **Foydalanuvchi (admin):**
  - kategoriyani yoqish/o'chirish;
  - parol o'rnatish;
  - kategoriya a'zolari ro'yxati;
  - topshiriqlar ro'yxati, dars yoki foydalanuvchi bo'yicha filtr;
  - statistika va Sprechen guruh statistikasi.
- **Kod:** `handlers/homework/admin.py` (har handlerda `is_admin`).
- **DB:** homework jadvallari.
- **Saytda:** qisman (sayt admin paneli boshqa modelga qurilgan).
- **Qaror:** F13 bilan birga hal qilinadi.

### F17. Admin panel
- **Foydalanuvchi (admin):**
  - statistika: yangi va faol foydalanuvchilar, premium, bloklangan, o'chirilgan;
  - xaridorlar va oxirgi 30 to'lov;
  - W-Zertifikatlar soni, oxirgi 20 tasi, PDF ochish.
- **Kod:** `handlers/admin.py`, `keyboards/admin.py`, `database/{users,payments,certificates,statistics}.py`.
- **Ruxsat:** `ADMIN_IDS` (`services/auth.py:is_admin`). Hozir 1 ta admin ID sozlangan.
- **Saytda:** qisman (sayt admin paneli, `admin/payments`, `admin/users`).
- **Qaror:** botda qoladi (bot ma'lumotlari uchun). Bog'langandan keyin saytda yig'ma ko'rinish.

### F18. Reklama (broadcast)
- **Foydalanuvchi (admin):** xabar yuboradi, `/send` bilan tasdiqlaydi. Bot uni `copy_message` bilan barcha bloklanmagan foydalanuvchilarga yuboradi; tezlik cheklangan va `RetryAfter` hurmat qilinadi. Botni bloklaganlar `is_blocked`, o'chirilgan akkauntlar `is_deleted` deb belgilanadi.
- **Kod:** `handlers/broadcast.py`, `services/broadcast.py`.
- **DB:** `users`.
- **Saytda:** qisman. Sayt bildirishnomalari (`broadcast_notifications`) faqat sayt ichida ko'rinadi, Telegram'ga yetmaydi.
- **Qaror:** botda qoladi. Kelajakda sayt bildirishnomasini Telegram orqali yetkazish kanali bo'lishi mumkin.

### F19. Shaxsiy xabar (admin → foydalanuvchi)
- **Kod:** `handlers/private_message.py`.
- **Saytda:** qisman (`support` tiketlari, ikki tomonlama).
- **Qaror:** botda qoladi.

### F20. Health endpoint
- `main.py` Flask `GET /` (port 10000). Hosting'dan qolgan keep-alive; hozir faqat skanerlar murojaat qilyapti (loglarda `Bad request version`).
- **Qaror:** keyingi bosqichda localhost'ga yopish tavsiya etiladi.

## 3. So'z o'yini mexanikasi (botda qolishi shart)

| Jihat | Kod bo'yicha holat |
|---|---|
| Boshlanishi | "🎮 So'z O'yini" → darajalar (A1–C1) → daraja → blok tugmalari. Tugma matni regexp bilan tahlil qilinadi: `^(🏆\|✅\|📖\|🔒)\s*LEVEL-N-Blok` (`handlers/wordgame.py`). |
| So'zlar | Ishga tushganda CSV'dan xotiraga yuklanadi (`services/loader.py`). Ustunlar: `id, german, correct, wrong1, wrong2`. Blok = 100 ta ketma-ket qator (`services/quiz.py`: `start_index=(block-1)*100`; C1 11-blok istisno). |
| Bloklar soni | A1/A2/B1: 10, B2: 15, C1: 11 (`LEVEL_CONFIG`) |
| Savol | Nemischa so'z va 3 ta o'zbekcha variant (aralashtiriladi). Har javob — inline callback `quiz:{user}_{wordId}:a{i}`. "⛔ Yakunlash" tugmasi bor. |
| Sessiya | Faqat xotirada (`config.quiz_sessions`, `active_questions`, `answered_users`). Restartda yarim qolgan test yo'qoladi. |
| Ochilish qoidasi | Keyingi blok oldingi blok `best_score ≥ 60` bo'lsa ochiladi. Daraja yig'indisi `required` (A1: 600) ga yetganda `users.unlocked_level` keyingi darajaga o'tadi. **Lekin** `start_quiz_block` `unlocked_level` ni faqat o'qiydi, darajaga kirishni cheklamaydi — barcha darajalar har kimga ochiq. |
| Ball | To'g'ri javob = +1. Natija `quiz_progress(user_id, level, block_number)` ga `GREATEST(best_score)` bilan yoziladi (faqat rekord saqlanadi). |
| XP | Birinchi o'tishda XP = ball. Qayta o'tishda faqat rekorddan oshgan farq beriladi (`finish_quiz`). `add_score` bitta tranzaksiyada `user_scores.global_score` ni oshiradi va `xp_events` ga yozadi. |
| Urinish | Har bir urinish alohida saqlanmaydi; faqat blok rekordi va XP hodisasi qoladi. Noto'g'ri javob `user_scores.wrong_answers` ni oshiradi. `correct_answers` esa har yakunlangan blokda +1 bo'ladi (javob soni emas). |
| Leaderboard | `xp_events` dan kun, hafta yoki oy boshidan beri (APP_TIMEZONE) hisoblanadi; overall = `global_score`. Bloklangan (`is_blocked`) foydalanuvchilar chiqarib tashlanadi. |
| Identifikatsiya | Faqat Telegram `from_user.id` (`users.user_id` BIGINT PK). Boshqa akkaunt tushunchasi yo'q. |
| Hajm (prod) | `quiz_progress` 1385 qator: A1 314 foydalanuvchi, A2 103, B1 79, B2 30, C1 13. `xp_events` 1623 (2026-07-30 … 2026-10-28). `user_scores` 517. |

**Topilgan nuqsonlar (bu bosqichda o'zgartirilmaydi):**
1. So'z CSV fayllarida sarlavha qatori yo'q: birinchi qator `1,der Apfel,…`. Loader esa `next(reader)` bilan birinchi qatorni tashlab yuboradi. Natijada har darajaning 1-so'zi o'yinga hech qachon tushmaydi va oxirgi blokda 99 ta savol bo'ladi. Yuklangan qatorlar: A1, A2, B1 999 tadan, B2 1499, C1 1099.
2. `unlocked_level` darajaga kirishni cheklamaydi (yuqorida).
3. `cleanup_quiz_memory` noto'g'ri obyektlar ustida ishlaydi (1.2-bo'lim).

**Integratsiyadan keyin buzilmasligi uchun:**
- `quiz_progress`, `user_scores`, `xp_events` sxemasi, `LEVEL_CONFIG`, CSV tartibi (blok = qator indeksi) va callback formatlari o'zgarmasin.
- Saytga eksport faqat **o'qish** (read-only view yoki API) orqali bo'lsin.
- Sayt lug'ati (`vocabularies`, 1280 so'z, darsga bog'langan) bilan bot so'zlari (5600, CSV) alohida ma'lumotlar to'plami. Ularni birlashtirish bloklarni siljitadi, shuning uchun bu alohida qaror.

## 4. Ishlatilmaydigan yoki eskirgan kod va jadvallar

| Element | Dalil |
|---|---|
| `handlers/certificate.py`, `handlers/search.py` | `handlers/__init__.py` va `bot.py` routerlar ro'yxatida yo'q |
| `handlers/xp.py` ("🔥 XP Reytingi") | Bunday tugma hech bir klaviaturada yo'q. SQL `approved = 1` (boolean = integer) PostgreSQL'da xato beradi. |
| `handlers/payment.py:start_payment` | `payment:` callback'ini avval `handlers/video.py:payment_info` ushlaydi, chunki `video` routeri oldin ulangan |
| `promotions` jadvali va `COURSE_PROMOTIONS` | Jadval yaratiladi, lekin hech bir handler foydalanmaydi (joriy HEAD) |
| `films`, `books`, `music`, `videos` jadvallari, `database/media.py` | 0 qator; katalog CSV'dan o'qiladi |
| `homework`, `homework_files`, `homework_submissions_legacy`, `teacher_messages`, `teacher_message_files`, `hall_of_fame` | Kodda havola yo'q (2, 1 va 0 qatorlar) |
| `users.approved`, `users.total_score`, `users.daily_score`, `users.phone` | Joriy oqimda yozilmaydi (`phone` 0 ta foydalanuvchida) |

## 5. Xavfsizlik topilmalari

| # | Daraja | Topilma | Dalil |
|---|---|---|---|
| S0 | **Kritik** | Bot repositorysi GitHub'da **ochiq**: autentifikatsiyasiz `api.github.com/repos/...` 200 qaytaradi. `.env` Git'da kuzatiladi; HEAD'dagi `TOKEN` **hozir ishlab turgan bot tokeni bilan bir xil**. Xuddi shu token saytda `TELEGRAM_BOT_TOKEN` sifatida Mini App `initData` HMAC'ini tekshirish uchun ishlatiladi. Demak tokenni bilgan har kim botni boshqara oladi (xabar yuborish, update o'qish) va saytga soxta Telegram kirishini yasay oladi. Hozir saytda `telegram_id` bog'langan akkaunt 0 ta, shuning uchun soxta kirish faqat yangi akkaunt yaratadi. Bog'lash (linking) yoqilgach esa bu **akkauntni egallab olishga** aylanadi. `ADMIN_PASSWORD` (kodda ishlatilmaydi), `ADMIN_ID`, `ADMIN_CHANNEL_ID` ham ochiq; `DATABASE_URL` ishlab turgan qiymatdan farq qiladi. Tarixda 13 ta commit `.env` ni o'zgartirgan. | `git ls-files .env`, `git show HEAD:.env` (faqat solishtirish, qiymat chiqarilmagan) |
| S0b | O'rta | Bot va sayt bitta PostgreSQL roliga ega (rol superuser emas), bot roli sayt bazasi `vizu` ga ulana oladi. PostgreSQL faqat localhost'da tinglaydi. | `pg_roles`, `has_database_privilege` |
| S0c | Ma'lumot (sayt) | `vizu-backend` `0.0.0.0:8000` va `vizu-frontend` `*:3000` da nginx'ni chetlab ochiq tinglaydi (`ufw` o'chiq) | `ss -ltn` |
| S1 | **Yuqori** | `approve_payment:` va `reject_payment:` callback'larida admin tekshiruvi yo'q. Status tekshiruvi ham yo'q (allaqachon tasdiqlangan to'lov qayta tasdiqlanadi va havola qayta yuboriladi). Callback ma'lumotini mijoz soxtalashtirishi mumkin, shuning uchun admin bo'lmagan foydalanuvchi o'z to'lov ID'si bilan kurs havolasini olishi mumkin. | `handlers/payment.py:567-676`, `database/payments.py:264` |
| S2 | Ma'lumot | Haqiqiy suiiste'mol izi topilmadi: 69 ta tasdiqning hammasini sozlangan admin qilgan, 6 ta rad etishning ham hammasini. Ekspluatatsiya sinab ko'rilmagan. | faqat sonlar, `payments.approved_by` |
| S3 | O'rta | Bot bazasi avtomatik zaxiralanmaydi | `backup_db.sh` |
| S4 | O'rta | Flask `0.0.0.0:10000` internetga ochiq, `ufw` o'chiq | `ss -ltnp`, `ufw status` |
| S5 | O'rta | Eski `/opt/vizu/academy` nusxasida xuddi shu token va DB bor. Xizmat yoqilsa, ikki bot to'qnashadi. | 1.1-bo'lim |
| S6 | Past | Hausaufgaben parolini tanlashda urinishlar soni cheklanmagan | `handlers/homework/access.py:181`, `sprechen.py:146` |
| S7 | Past | Standart `parse_mode=HTML`; reyting va kanal postlarida foydalanuvchi ismi escape qilinmaydi. `<` belgili ism xabarni buzadi. | `loader.py`, `handlers/leaderboard.py` |
| S8 | Ma'lumot | Kurs va guruh taklif havolalari hamda kanal ID'lari kod ichida (`config/settings.py`) va Git'da turibdi | — |
| S9 | Ma'lumot | Tracked `.env` lokal o'zgartirilgan (` M .env`); tarixdagi secretlar — S0 ga qarang | `git status`, `git log -- .env` |

S0 va S1 bu bosqichda tuzatilmadi (faqat audit). Ular har qanday integratsiyadan **oldin** hal qilinishi kerak (roadmap 0-bosqich).
- S0 uchun: BotFather'da tokenni almashtirish (bot va sayt `.env` ga bir vaqtda), repositoryni yopish yoki `.env` ni olib tashlab tarixdan tozalash, `ADMIN_PASSWORD` boshqa joyda ishlatilgan bo'lsa almashtirish.
- Tokenni almashtirish ikkala servisni restart qilishni talab qiladi — buning uchun alohida tasdiq kerak.
