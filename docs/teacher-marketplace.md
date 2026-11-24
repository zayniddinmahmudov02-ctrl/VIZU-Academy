# My Teacher (Lehrer-Marktplatz) — arxitektura, qoidalar, ishlatish

Sana: 2026-11-24 · Migratsiya `d9e4a1c7b3f5` (oldingi `c8d3f5a1e7b2`). Barcha qoidalar backend'da; frontend faqat ko‘rsatadi.

## 1. Nima qilindi

- Talaba menyusida **"Hilfe Anfragen" o‘rniga "My Teacher"** (`/my-teacher`). Eski yordam so‘rovlari o‘chirilmagan: `/support` ishlaydi,
  sidebar'dagi "Hilfe benötigt?" kartasi va admin `/admin/support` joyida.
- Katalog: 9:16 portret kartalar (faqat rasm + ism), qidiruv (ism / familiya), filtrlar (til, daraja, kurs bor, hozir dars beradi), sahifalash.
- O‘qituvchi profili: rasm, ism, mutaxassislik, tillar, darajalar, Verified Teacher, Berufserfahrung, o‘quvchilar soni (hozirgi / jami, har biri bir marta),
  tasdiqlangan sertifikatlar, reyting (★ 4.8/5, N baho), sharhlar, kurslar.
- O‘qituvchi paneli: Mein Profil (9:16 crop, preview), Meine Kurse (yaratish, tahrirlash, tasdiqqa yuborish, ro‘yxat, to‘lov holati, davomat),
  Spezialstunden (bepul dars so‘rovi, xonani ochish), Bewertungen (faqat o‘qish + shikoyat).
- Admin: `/admin/lehrer-marktplatz` (Übersicht, Lehrer, Zertifikate, Kurse, Spezialstunden, Bewertungen, Einstellungen).
- Bepul maxsus dars Global Chat'da e'lon qilinadi (xabar + chat oynasidagi "Jonli darslar" qatori, Join) va VIZU video xonasida (LiveKit) o‘tadi.

## 2. Ma'lumotlar (yangi jadval faqat kerak bo‘lganda)

| Jadval | Nima |
| --- | --- |
| `teacher_profiles` (+ustunlar) | ommaviy profil (rasm, headline, bio, tajriba, tillar, darajalar…), admin bayroqlari (`catalog_hidden`, `profile_disabled`, `verified`), saqlangan reyting (`rating_avg`, `rating_count`) |
| `teacher_certificates` | sertifikat + fayl (private), holat pending / verified / rejected |
| `teacher_courses` | o‘qituvchi kursi: tur PAID / FREE / UPCOMING, narx, joylar, jadval, holat, tasdiq holati, `group_id` (tasdiqlanganda yaratilgan guruh = sinfxona) |
| `teacher_course_enrollments` | yozilish: PENDING_PAYMENT / ACTIVE / COMPLETED / CANCELLED / REJECTED / REFUNDED; bitta "tirik" yozilish (partial unique) |
| `teacher_course_interests` | "Bald verfügbar" kurslarga qiziqish ro‘yxati (yozilish emas) |
| `teacher_reviews`, `teacher_review_reports` | baho (talaba + kurs bo‘yicha bitta, 1–5), shikoyatlar |
| `special_lessons`, `special_lesson_signups` | bepul maxsus dars (15–90 daqiqa), qatnashishga yozilish |
| `video_rooms` (+ustunlar) | `group_id` endi NULL bo‘lishi mumkin, `special_lesson_id`, `hard_end_at`, `students_camera_allowed`; ishtirokchida `can_video` |
| `subscription_orders.teacher_course_id` | pullik kurs buyurtmasi (plan `TEACHER_COURSE`) |

Video dars, guruh chat, to‘lov, bildirishnoma, audit — mavjud tizimlar qayta ishlatilgan (ikkinchi video / to‘lov / progress tizimi yo‘q).

## 3. Qoidalar

- **Ruxsat:** talaba endpointlari `get_current_user` (+ yozilish / baho uchun faqat STUDENT, 403 `STUDENT_ONLY`); o‘qituvchi `/teacher/market/*`
  `require_teacher_panel_access`; admin `/admin/teacher-market/*` o‘qish `require_admin_panel_access`, qarorlar `require_super_admin`. Yashirin /
  o‘chirilgan profil va boshqa o‘qituvchining kursi → 404.
- **Reyting:** faqat backend hisoblaydi (ko‘rinadigan baholar o‘rtachasi), o‘qituvchi o‘zgartira olmaydi (API'da maydon yo‘q). Baho berish: talabaning
  ACTIVE / COMPLETED yozilishi bor va kurs boshlangan; bir kurs uchun bitta (keyin tahrirlash); admin yashiradi / qaytaradi; har moderatsiya auditda.
  Sharhda faqat "Ism F." ko‘rinadi, email / telefon yo‘q.
- **Kurs tasdig‘i:** yangi kurs va nom / tavsif / daraja / til / tur / narx o‘zgarishi Super Admin tasdig‘idan o‘tadi (Einstellungen: "Kurse automatisch
  veröffentlichen", standart o‘chiq). Tasdiqlanganda guruh yaratiladi, o‘qituvchi guruh o‘qituvchisi bo‘ladi.
- **Joylar:** yozilish kurs qatorini qulflab (`FOR UPDATE`) tekshiriladi; PENDING_PAYMENT + ACTIVE joy egallaydi; to‘lgan kurs "Ausgebucht".
- **Holatlar:** Anmeldung läuft / Bald verfügbar / Ausgebucht (hisoblanadi) / In Vorbereitung / Laufend / Abgeschlossen / Abgesagt.
- **To‘lov:** onlayn provayder yo‘q → mavjud VIZU Pay karta o‘tkazmasi + chek (yoki chek yo‘q: sana + vaqt). Narx serverda kursdan olinadi,
  client yuborgan summa / holatga ishonilmaydi. Faqat Super Admin `Admin → Payments → Payment Requests` da tasdiqlaydi → yozilish ACTIVE, talaba guruhga
  qo‘shiladi; rad etish joyni bo‘shatadi; refund → REFUNDED, guruhdan chiqadi. Takroriy buyurtma bloklanadi (bitta ochiq buyurtma).
- **Fayllar:** profil rasmi 720×1280 WebP, kurs rasmi 1280×720 WebP (qayta kodlanadi, tasodifiy nom, `/uploads/teacher-market/…`); sertifikat
  rasm → WebP yoki PDF (`%PDF-`, ≤ 10 MB) — `app/protected_storage/teacher-certificates`, faqat tekshiruvli endpoint orqali, `private, no-store`.
  Kengaytma + MIME + mazmun tekshiriladi, eng kichik tomon 200 px.

## 4. Bepul maxsus dars va jonli xona

- O‘qituvchi so‘raydi (boshlanish ≥ 1 soat keyin, ≤ 90 kun; 15–90 daqiqa; 2 … `SPECIAL_LESSON_MAX_PARTICIPANTS` ishtirokchi; bir vaqtda ≤ 10 ochiq so‘rov).
- Super Admin tasdiqlaydi (vaqtni ko‘chirishi mumkin) yoki sabab bilan rad etadi; tasdiqda Global Chat'ga o‘qituvchi nomidan e'lon (5 tadan kam pin
  bo‘lsa pin), barcha faol talabalarga bildirishnoma.
- Xonani faqat **boshlanishdan 15 daqiqa oldin … tugashgacha** ochish mumkin (server vaqti). Xona `hard_end_at = boshlanish + davomiylik` bilan
  ochiladi; talabalar mikrofonsiz, kamerasiz, ekran ulashishsiz kiradi; o‘qituvchi har biriga mikrofon / kamera / ekran ruxsatini alohida beradi,
  hammani o‘chiradi, chiqaradi, bloklaydi; o‘qituvchi istalgan payt tugatadi.
- **Vaqt chegarasi backend'da:** `services/teacher_market/scheduler.py` har 30 s (`pg_try_advisory_lock(7302411)`, bitta worker) `tick()` chaqiradi:
  `hard_end_at` o‘tgan xonani yopadi (LiveKit xonasi o‘chiriladi → hamma uziladi), tugagan darsni ENDED qiladi, pinni oladi, o‘qituvchiga "xonani
  ochish mumkin", yozilganlarga 30 daqiqa oldin eslatma yuboradi. Qo‘shimcha: har `get_room` / `join` ham muddatni tekshiradi.
  Frontend faqat qolgan vaqtni ko‘rsatadi (server vaqti offset'i bilan) va 5 daqiqa qolganda ogohlantiradi.
- Token faqat backend'da yaratiladi (xona + foydalanuvchiga bog‘langan, 300 s); xona URL'ini bilish yetarli emas — `join` har safar ruxsatni tekshiradi.
- Tarix saqlanadi (darslar, xonalar, ishtirokchilar, hodisalar o‘chirilmaydi).

## 5. Sozlamalar (faqat nomlar)

- `SPECIAL_LESSON_MAX_PARTICIPANTS` (standart 100, 2–500), `TEACHER_MARKET_SCHEDULER_ENABLED` (standart true; `APP_ENV=test` da doim o‘chiq).
- LiveKit: mavjud `LIVEKIT_URL`, `LIVEKIT_API_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (guruh video darslari bilan bir xil).
- Admin sozlamasi `app_settings["teacher_market"].course_auto_publish`.

## 6. Onlayn to‘lov (qurilmagan — kerakli ma'lumotlar)

Click / Payme / Uzum ulash uchun egasidan kerak: merchant / service ID, maxfiy kalit, callback (webhook) URL'ini provayder kabinetida ro‘yxatdan
o‘tkazish, test rejimi ma'lumotlari. Sozlama nomlari (taklif, kodda hali yo‘q): `CLICK_MERCHANT_ID`, `CLICK_SERVICE_ID`, `CLICK_SECRET_KEY`,
`PAYME_MERCHANT_ID`, `PAYME_SECRET_KEY`. Ulanganda: imzoli webhook → idempotent tasdiq → mavjud `activate_for_order` hook. O‘qituvchiga pul o‘tkazish
(payout) ham qurilmagan.

## 7. Testlar

- Backend: `tests/test_teacher_market.py` (kontrakt, 401/403, crop, PDF, holatlar, katalog, profil, kurs + tasdiq, bepul / pullik yozilish,
  approve / reject / refund, baholar, maxsus dars oynasi va vaqt chegarasi), `tests/test_teacher_market_migration.py` (upgrade / downgrade / upgrade).
- Frontend unit: `tests/unit/teacher-market.test.mjs` (matnlar uz/de + backend xato kodlari), `tests/unit/video-rooms.test.mjs` (countdown).
- E2E: `e2e/tests/teacher-marketplace.spec.ts` (seed `D:\vz_tmp\work\tm_e2e_seed.py`; jonli qism `E2E_PYTHON` + `E2E_TM_SHIFT`, haqiqiy lokal LiveKit,
  backend scheduler yoqilgan).

## 8. Cheklovlar / ochiq ishlar

- Onlayn to‘lov provayderi va o‘qituvchiga to‘lov yo‘q (§6).
- Production'da TEACHER hisoblari yo‘q — katalog bo‘sh bo‘ladi, egasi Admin → Team orqali o‘qituvchi yaratadi (test hisobi yaratilmaydi).
- Haqiqiy qurilmalarda / mobil tarmoqlarda real jonli dars hali sinalmagan; TURN/TLS holati `docs/group-video-lessons.md` §9 da.

## 9. Rollback

Kod: overlay originallari (backup papkasi) qaytariladi. DB: `alembic downgrade c8d3f5a1e7b2` faqat qo‘lda va backup'dan keyin (maxsus dars
xonalari o‘chiriladi, yangi jadvallar tushadi) — avtomatik downgrade qilinmaydi.
