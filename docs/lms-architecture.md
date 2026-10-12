# VIZU LMS (A1–C1) — arxitektura

Asosiy tamoyil: bu yangi kurs tizimi, lekin **mavjud jadvallar ustiga quriladi**. Daraja, dars, video upload/stream, video progress, mashq va topshiriq jadvallari, baholash va AI baholash allaqachon ishlab turibdi; ular qayta yozilmaydi. Yangi jadvallar faqat yo'q narsalar uchun qo'shiladi: kompetenz konfiguratsiyasi, resurslar (audio/PDF/fayl/link) va kompetenz progressi. Ikkinchi progress tizimi ham, parallel dars modeli ham yaratilmaydi.

## 1. Tuzilma

| Daraja | Darslar | Saqlanishi |
|---|---:|---|
| A1 | 14 | `courses.level = 'A1'` → bitta `modules` → `lessons.number` 1..14 |
| A2 | 14 | … 1..14 |
| B1 | 20 | … 1..20 |
| B2 | 30 | … 1..30 |
| C1 | 22 | … 1..22 |

- Darslar soni backendda bitta joyda saqlanadi: `app/services/lms/structure.py` → `LEVEL_LESSON_COUNTS`.
- `ensure_structure` (admin endpoint + CLI) yetishmayotgan modul va darslarni **draft** holatida yaratadi. U hech narsani o'chirmaydi va mavjud darslarni qayta raqamlamaydi.
- Dars raqami 1..N oralig'ida bo'lishi shart va daraja ichida takrorlanmaydi. Bu service'da tekshiriladi, DB'da esa `UNIQUE(module_id, number)` bilan ta'minlanadi.
- Tartibni o'zgartirish faqat admin reorder endpointi orqali, bitta tranzaksiyada bajariladi.
- `courses` va `modules` o'chirilmaydi: ular to'lovlar, sertifikatlar va yozilishlar bilan kaskad orqali bog'langan.

## 2. Dars

`lessons` jadvaliga qo'shiladigan ustunlar (additive):

- `description`;
- `is_published` (mavjud darslar uchun `true`, yangi yaratilganlar uchun `false`);
- `access_override` (`NULL` / `OPEN` / `LOCKED`).

Mavjud ustunlar: `number`, `title`, `duration`.

`courses` jadvaliga `sequential_unlock` qo'shiladi (standart qiymat `false`, ya'ni hozirgi xatti-harakat saqlanadi).

## 3. Kompetenzlar

Har bir darsda 10 ta kompetenz, qat'iy tartibda:

| # | Kalit | Kontent manbai (mavjud jadvallar) | Tugallanishi (server) |
|---|---|---|---|
| 1 | EINFUEHRUNG | matn (`lesson_competencies.body`), `videos` (competency = EINFUEHRUNG yoki NULL), Frage des Themas (`speakings.task_kind = FRAGE`), resurslar | barcha videolar ko'rib bo'lingan + Frage yuborilgan |
| 2 | WORTSCHATZ | `vocabularies`, `skill_exercises` (WORTSCHATZ), resurslar | barcha mashq to'plamlari bajarilgan |
| 3 | GRAMMATIK | `grammars`, `skill_exercises` (GRAMMATIK) | barcha to'plamlar bajarilgan |
| 4 | LESEN | `readings` + savollar | barcha savollar topshirilgan (mavjud qoida) |
| 5 | HOEREN | `listenings` + audio + savollar | har bir audio topshirig'i bajarilgan |
| 6 | SPRECHEN | `speakings` (SPRECHEN) | o'qituvchi yoki AI tomonidan baholangan (GRADED) |
| 7 | SCHREIBEN | `writings` | baholangan (GRADED) |
| 8 | UEBUNGEN | `skill_exercises` (yangi qiymat: UEBUNGEN) | barcha to'plamlar bajarilgan |
| 9 | ABSCHLUSSTEST | `skill_exercises` (YAKUNIY), avtomatik baholanadi | yakuniy test topshirilgan |
| 10 | ZUSAMMENFASSUNG | matn + dars natijasi (`results.py`) | hisobga olinmaydi (xulosa) |

Har bir kompetenzga istalgancha video va resurs biriktirish mumkin.

Yangi `lesson_competencies` jadvali: `lesson_id`, `kind`, `position`, `body`, `is_published`.

- `UNIQUE(lesson_id, kind)`, `UNIQUE(lesson_id, position)`.
- `CHECK` cheklovi `position` har doim kalitning standart o'rniga teng bo'lishini ta'minlaydi, ya'ni tartibni DB darajasida buzib bo'lmaydi.
- Admin kompetenzni yashirishi mumkin (`is_published = false`). Bunda tartib o'zgarmaydi.

**Student uchun holatlar:**

- `not_started` — Nicht begonnen
- `in_progress` — In Bearbeitung (javob yuborilgan, lekin hali baholanmagan holat ham shu yerga kiradi; batafsil holat alohida maydonda qaytadi)
- `completed` — Abgeschlossen
- `locked` — Gesperrt: dars yopiq bo'lsa
- `not_available` — Nicht verfügbar: kompetenz nashr qilingan, lekin kontenti yo'q

**Hisoblanadigan va hisoblanmaydigan kompetenzlar:**

- Baholanadigan yoki kuzatiladigan elementi (video, savollar, topshiriqlar) bor kompetenz dars tugallanishiga hisoblanadi.
- Faqat matn yoki resursdan iborat kompetenz hisoblanmaydi. Ochilganda "ko'rildi" deb belgilanadi, lekin darsni tugallashga ta'sir qilmaydi, chunki oddiy tugma bosish tugallash hisoblanmasligi kerak.

## 4. Resurslar (audio, PDF, rasm, hujjat, link)

Yangi `learning_resources` jadvali:

- bog'lanish: `lesson_id`, `competency` (NULL bo'lsa, butun darsga tegishli);
- `resource_type`: AUDIO / PDF / IMAGE / DOCUMENT / LINK;
- `title`, `description`, `order_index`, `is_published` (standart: draft);
- fayl ma'lumotlari: `storage_key` yoki `external_url` (`CHECK` bilan aynan bittasi), `mime_type`, `size_bytes`, `duration_seconds`, `original_filename`;
- `created_by`.

Fayllar `app/protected_storage/lms-resources/<lesson_id>/` da saqlanadi:

- ochiq `/uploads` ga tushmaydi;
- `GET /api/v1/lms/resources/{id}/file` orqali beriladi: dars ruxsati tekshiriladi, Range qo'llab-quvvatlanadi (audio seek uchun);
- fayl almashtirilganda eski fayl faqat boshqa hech bir qator undan foydalanmasa o'chiriladi.

**Video:** `videos` jadvaliga `competency` va `subtitle_key` (WebVTT) qo'shiladi. Yuklash, imzolangan stream va progress mavjud tizimdan foydalanadi.

## 5. Progress — bitta markaziy service

`app/services/lms/progress.py`:

- **Signallar:** mavjud manbalardan o'qiladi — `video_progress`, `lesson_skill_attempts`, `student_writings`/`student_speakings` (baholar), `results.py`. Yangi parallel hisob yo'q.
- **`student_competency_progress`** (yangi jadval, `UNIQUE(user, lesson, competency)`): holat, ball, `started_at`, `completed_at`, `last_activity_at` — tarix va ro'yxatlar uchun snapshot.
- **`student_progress`** (mavjud jadval) dars darajasidagi progress bo'lib qoladi. Unga `completed_at` va `last_activity_at` qo'shiladi; `lesson_completed` shu yerda yoziladi.
- **Snapshot qachon yangilanadi:** dars ochilganda, video tugaganda, mashq yoki test topshirilganda, o'qituvchi baholaganda.
- **Daraja progressi:** nashr qilingan darslar orasida tugallanganlar ulushi.
- **"Davom etish":** oxirgi faol dars; agar u tugallangan bo'lsa, keyingi ochiq va tugallanmagan dars.
- **Eski `section_gate.is_lesson_completed`** shu service'ga yo'naltiriladi, shunda tugallanish qoidasi bitta joyda qoladi.

## 6. Darsni ochish qoidasi (server)

Student uchun tekshiruv tartibi:

1. Dars draft bo'lsa → 404.
2. `access_override = LOCKED` → 403 `LESSON_LOCKED`.
3. Premium yoki to'lov qoidasi (mavjud `can_access_lesson`) → 403 `PREMIUM_REQUIRED`.
4. `courses.sequential_unlock = true` bo'lsa va oldingi nashr qilingan dars tugallanmagan bo'lsa → 403 `LESSON_LOCKED`. `access_override = OPEN` ketma-ketlik qoidasini chetlab o'tadi.

Admin, teacher va staff hamma darsni ko'radi. Bu qoidalar hozir dars kontentini beradigan barcha endpointlar ishlatadigan `require_lesson_access` dependency'sida qo'llanadi. Standart qiymatlarda (nashr qilingan, override yo'q, ketma-ketlik o'chiq) hozirgi xatti-harakat o'zgarmaydi.

## 7. API (`/api/v1`)

Student:

- `GET /lms/levels` — darajalar: maqsad va nashr qilingan darslar soni, progress, "davom etish".
- `GET /lms/levels/{level}` — daraja darslari (kartalar uchun).
- `GET /lms/lessons/{id}` — dars, 10 ta kompetenz holati, videolar va resurslar.
- `POST /lms/lessons/{id}/competencies/{kind}/visit` — kompetenz ochilganini qayd etadi.
- `GET /lms/resources/{id}/file` — resurs faylini beradi.

Kontentning o'zi mavjud endpointlardan keladi: `/lesson-skills/...`, `/videos/...`, `/writings`, `/speakings`, `/vocabularies`, `/grammars`.

Admin (`require_admin_panel_access`):

- `GET /admin/lms/levels`
- `PATCH /admin/lms/levels/{course_id}`
- `POST /admin/lms/levels/{level}/ensure-structure`
- `POST /admin/lms/levels/{level}/reorder`
- `GET` / `PATCH /admin/lms/lessons/{id}`
- `PATCH /admin/lms/lessons/{id}/competencies/{kind}`
- resurslar: `POST` (yuklash), `PATCH`, `PUT .../file` (almashtirish), `DELETE`, `GET .../file` (preview)
- `GET /admin/lms/lessons/{id}/progress` (sahifalangan)
- `GET /admin/lms/storage-health`

Barcha o'zgartiruvchi admin amallari `audit_logs` ga yoziladi.

## 8. Frontend (keyingi bosqichlar)

- **Student:**
  - `/courses` — darajalar va "davom etish";
  - `/courses/[level]` — dars kartalari;
  - `/lessons/[lessonId]` — 10 ta kompetenz navigatsiyasi, video va audio player, resurslar ro'yxati, mashqlar;
  - hammasi yagona API client orqali.
- **Admin:**
  - "Kurslar (A1–C1)" sahifasi: daraja bo'yicha dars soni va maqsad;
  - dars muharriri: kompetenzlar, video, resurslar, mashqlar, draft/publish;
  - progress va fayllar holati.
- **Tillar:** UI matnlari mavjud tarjima tizimida (de, uz). Ingliz tili uchun ilovaning til tizimini kengaytirish kerak, bu alohida vazifa.

## 9. Migration

Bitta additive migration (`down_revision = d7a3c9e1f5b2`) va to'liq `downgrade`.

- **Mavjud darslar:** 10 tadan kompetenz qatori yaratiladi, `is_published = true`, shunda hozirgi kontent ko'rinib turaveradi.
- **Mavjud videolar:** `competency = NULL`, ya'ni Einführung'ga tegishli deb hisoblanadi.
- **`UNIQUE(lesson_id, number)`:** mavjud ma'lumotda takrorlanuvchi raqamlar bo'lsa, migration index yaratmaydi va ogohlantirish chiqaradi; service darajasidagi tekshiruv baribir ishlaydi. Shuning uchun prodda avval dry-run qilinadi.
