# Bot va sayt bazalari auditi

Audit sanasi: 2026-10-28. Faqat o'qish: sxema, qator soni va bog'lanishlar.
Shaxsiy qiymatlar (ism, telefon, ID, chek) chiqarilmagan. Mosliklar vaqtinchalik fayllarda faqat **son** sifatida hisoblandi va fayllar darhol o'chirildi.

## 1. Umumiy holat

| | Bot | Sayt |
|---|---|---|
| Baza | `telegram_course2026` (11 MB) | `vizu` (25 MB) |
| Server / instansiya | bitta PostgreSQL 16, faqat `localhost:5432` | xuddi shu |
| DB roli | **bitta umumiy rol** (superuser emas). Bot roli `vizu` ga ham ulana oladi. | xuddi shu |
| Migratsiya | Alembic yo'q. Har ishga tushishda `database/init.py` `CREATE TABLE IF NOT EXISTS` + `ALTER … ADD COLUMN IF NOT EXISTS` bajaradi. | Alembic, joriy revision `a7c2e9f4b1d6` |
| Jadvallar | 26 | 118 |
| Foydalanuvchi ID | `users.user_id BIGINT` = Telegram ID (PK) | `users.id UUID`; `users.telegram_id BIGINT UNIQUE NULL` |
| Zaxira | **Yo'q** (avtomatik) | Har kuni `vizu_db_*.dump`, 14 kun. Fayllar `644` huquqli (hammaga o'qiladi). |

**Xulosa:** bazalar alohida. Umumiy jadval yo'q. ID'lar orasida bog'lanish (mapping) yo'q.

## 2. Bot bazasi (`telegram_course2026`)

### 2.1 Jadvallar va qator soni

| Guruh | Jadval (qatorlar) | Kodda ishlatiladimi |
|---|---|---|
| Foydalanuvchi | `users` (1232) | ha |
| So'z o'yini | `quiz_progress` (1385; PK `user_id, level, block_number`) | ha |
| XP / reyting | `user_scores` (517), `xp_events` (1623), `daily_champions` (89), `weekly_champions` (13), `monthly_champions` (3), `hall_of_fame` (0) | ha (`hall_of_fame` — yo'q) |
| Sertifikat | `certificates` (35) | ha |
| To'lov | `payments` (78), `promotions` (1) | `payments` — ha; `promotions` — yo'q |
| Hausaufgaben | `homework_categories` (3), `homework_memberships` (144), `homework_submissions` (239), `homework_submission_files` (736), `homework_evaluations` (154) | ha |
| Media | `favorite_music` (10); `films`, `books`, `music`, `videos` (0) | `favorite_music` — ha; qolganlari faqat statistikada |
| Eskirgan | `homework` (0), `homework_files` (2), `homework_submissions_legacy` (1), `teacher_messages` (0), `teacher_message_files` (0) | yo'q |

### 2.2 Foreign key'lar

- `users(user_id)` ga `ON DELETE CASCADE` bilan bog'langan: `user_scores`, `xp_events`, `homework_memberships`, `homework_submissions`.
- `homework_submissions(id)` ga: `homework_submission_files`, `homework_evaluations` (UNIQUE).
- `homework_categories(id)` ga: `homework_memberships`, `homework_submissions`.
- `monthly_champions(id)` ga: `hall_of_fame`.

**FK'siz (faqat mantiqan bog'langan):** `quiz_progress.user_id`, `certificates.user_id`, `payments.user_id`, `*_champions.user_id`, `favorite_music.telegram_id`.

Muhim: `users` qatorini o'chirish XP va uy vazifasini kaskad o'chiradi, lekin to'lov va o'yin rekordini yetim qoldiradi. Rollback va tozalashda foydalanuvchini o'chirish taqiqlanadi.

### 2.3 Asosiy entitylar (agregat)

| Ko'rsatkich | Qiymat |
|---|---|
| Foydalanuvchilar | 1232; 30 kunda faol 321; botni bloklagan (`is_blocked`) 291; o'chirilgan 21; username'i bor 747 |
| `users.phone` | 0 ta to'ldirilgan (telefon faqat `payments` da) |
| `unlocked_level` | A1 1189, A2 31, B1 7, B2 4, C1 1 |
| So'z o'yini o'yinchilari | 423 (`quiz_progress`); XP olganlar 404 |
| To'lovlar | approved 69 (7 065 000 so'm), pending 3 (hammasi 7 kundan eski), rejected 6. 62 ta alohida xaridor. 1 foydalanuvchi bitta kursni 2 marta tasdiqlatgan. |
| Kurs bo'yicha tasdiqlangan | A1 44, A2 5, B1 2, A1–B1 11, A1–C1 7 |
| W-Zertifikatlar | A1 19, A2 9, B1 4, B2 2, C1 1 |
| Uy vazifasi | 94 foydalanuvchi. Statuslar: draft 68, submitted 17, excellent 122, accepted 14, revision_required 18. |
| Uy vazifasi fayllari | photo 585, voice 121, text 24, audio 5, pdf 1. Eng kattasi 7.6 MB; > 20 MB yo'q. Hammasi Telegram `file_id`. |

### 2.4 Takrorlanishi mumkin bo'lgan yozuvlar

- `payments`: bir foydalanuvchi va kurs uchun bir nechta `approved` (1 holat). Admin tasdig'ida status tekshiruvi yo'q (inventar S1).
- `users.full_name` bir xil bo'lgan turli Telegram akkauntlari bo'lishi mumkin. Ism bo'yicha moslashtirish taqiqlanadi.
- `homework_submissions`: har kategoriyada bitta qoralama (`get_or_create_draft_submission`). Takrorlanish kod bilan cheklangan.

## 3. Sayt bazasi (`vizu`) — integratsiyaga tegishli qismlar

| Entity | Jadval (prod qatorlar) | Izoh |
|---|---|---|
| Foydalanuvchi | `users` (130); 41 tasida `login_phone`; 0 tasida `telegram_id` | 57 ta FK `users` ga bog'langan |
| Kirish | `refresh_tokens` (sessiya `sid`), `login_history`, `auth_rate_limit_events` | Mini App: `POST /auth/telegram` |
| Xarid | `subscription_orders` (9: 8 approved, 1 rejected), `promo_codes`, `promo_code_redemptions` (5) | `user_id → users.id` FK, `reviewed_by_id` |
| Progress | `student_progress` (111), `student_competency_progress`, `video_progress`, `student_writings` (6), `student_speakings` (10) | darsga bog'langan |
| Lug'at | `vocabularies` (1280, darsga bog'langan) | Bot so'zlari (5600, CSV) bilan aloqasi yo'q |
| Sertifikat | `certificates` (0), Zertifikate API | W-Zertifikat bilan aloqasi yo'q |
| Bildirishnoma / yordam | `broadcast_notifications` (1), `notifications` (6), `support_tickets` (2) | faqat sayt ichida |
| Media | `videos` (36), `listenings` (67), `media_assets` (21), `books` (3) | Media Management |

## 4. ID mapping ehtiyoji va imkoniyatlari

| Usul | Natija (hisoblangan) | Egalikni isbotlaydimi |
|---|---|---|
| `users.telegram_id` (sayt) ↔ `users.user_id` (bot) | **0 ta moslik** (saytda bitta ham `telegram_id` yo'q) | Ha, agar Mini App `initData` haqiqiy token bilan tekshirilgan bo'lsa. **Hozirgi token ochiq** (inventar S0), shuning uchun almashtirilmaguncha ishonchsiz. |
| Bot to'lov telefoni ↔ sayt `login_phone` (oxirgi 9 raqam) | 67 va 41 dan **4 ta moslik** | **Yo'q.** Telefon foydalanuvchi o'zi yozgan matn, tasdiqlanmagan. Faqat admin uchun taklif sifatida ishlatilishi mumkin. |
| Ism yoki username | — | Yo'q. Ishlatilmaydi. |

Xulosa: avtomatik ommaviy mapping mumkin emas va xavfli. Bog'lash har bir foydalanuvchi tomonidan, ikki tomonlama tasdiq bilan qilinishi kerak (`bot-site-target-architecture.md` 3-bo'lim). Mapping jadvali sayt bazasida bo'lishi kerak.

## 5. Ma'lumot integratsiyasining xavfsiz variantlari (hozir birlashtirilmaydi)

| Variant | Mazmuni | Afzallik | Xavf | Tavsiya |
|---|---|---|---|---|
| **A. Alohida bazalar + mapping** | Bot bazasi o'zgarmaydi. Saytga `users.telegram_id` (allaqachon mavjud) va bog'lash audit jadvali qo'shiladi. | So'z o'yini va bot jadvallari tegilmaydi; rollback oddiy | Ikki manba saqlanib qoladi | **Ha (1-qadam)** |
| **B. Sayt API orqali o'qish** | Bot kerakli sayt ma'lumotini (kirish huquqi, profil) sayt backend'ining ichki API'sidan oladi; sayt bot ma'lumotini (XP, sertifikat) bot API yoki read-only view'dan oladi | Bitta biznes mantiqi, DB'ga to'g'ridan-to'g'ri yozish yo'q | API autentifikatsiyasi va rate limit kerak | **Ha (2-qadam)** |
| C. Read-only DB view yoki replika | Sayt bot bazasidan faqat o'qish huquqli alohida rol bilan o'qiydi | Tez | Hozir rol umumiy. Avval rollarni ajratish kerak. | Faqat rollar ajratilgandan keyin |
| D. Bitta bazaga birlashtirish | Bot jadvallarini `vizu` ga ko'chirish | Bitta manba | Bot Alembic'siz o'z sxemasini o'zgartiradi; so'z o'yini sxemasi buzilishi mumkin; katta rollback | **Hozir yo'q** |

## 6. Migratsiyadan oldin bajariladigan (hozir bajarilmadi)

1. Bot bazasini zaxiralash: kunlik `telegram_course2026` dump, `600` huquq, restore testi.
2. Bot va sayt uchun alohida PostgreSQL rollari. Bot roli `vizu` ga kira olmasin.
3. Sayt dump fayllari huquqini `600` ga tushirish.
4. Bot `init.py` ning har startdagi DDL'i bilan birga yashash: bot sxemasini saytdan turib o'zgartirmaslik.
