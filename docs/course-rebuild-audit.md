# A1–C1 video kurslarini qayta qurish — 1-bosqich: audit, backup, dry-run

Holat: **faqat audit.** Hech narsa o'chirilmagan, server o'zgartirilmagan. Production hajmlari pastdagi dry-run serverda ishga tushirilgandan keyin ma'lum bo'ladi: sandboxdan production bazasiga ulanish yo'q.

## 1. Kontent turlari va saqlanish joyi

Fayl yo'llari backend servisining ishchi papkasiga nisbatan, ya'ni odatda `/opt/vizu/VIZU-Academy/backend/`.

| Kontent | Jadval(lar) | Fayl | Saqlanish joyi | Kim beradi |
|---|---|---|---|---|
| Daraja (kurs) | `courses` (`level` A1..C1, `result_config`) | — | PostgreSQL | `/api/v1/courses` |
| Modul | `modules` | — | PostgreSQL | `/api/v1/modules` |
| Dars | `lessons` (`number`, `title`, `duration`, `is_free`, eski `video_url`) | — | PostgreSQL | `/api/v1/lessons` |
| Video dars | `videos`, `video_upload_sessions` | `storage_key` | `app/protected_storage/videos/<lesson_id>/…` (himoyalangan) | `/api/v1/videos/{id}/stream?token=` |
| Video muqovasi | `videos.thumbnail_key` / `thumbnail_url` | rasm | `uploads/videos/thumbnails/…` (ochiq) | `/uploads/…` |
| Chala yuklangan video | `video_upload_sessions` | chunk'lar | `app/protected_storage/video-uploads/<id>/` | — |
| Hören (dars audiosi) | `listenings`, `listening_questions/options` | `audio_storage_path` | `app/protected_storage/lesson-listening/…` | `/api/v1/lesson-skills/…/audio` |
| Lesen | `readings`, `reading_questions/options` | `image_url` (ixtiyoriy) | PostgreSQL + `uploads/` | lesson-skills API |
| Schreiben / Sprechen / Frage | `writings`, `speakings` | `image_url` | PostgreSQL + `uploads/` | lesson-skills API |
| Grammatik / Wortschatz / Yakuniy mashqlari | `grammars`, `skill_exercises`, `skill_exercise_questions/options`, `quizzes`, `quiz_questions/options` | `grammars.video_url` (tashqi URL) | PostgreSQL | lesson-skills API |
| Wortschatz so'zlari | `vocabularies` (`lesson_id` majburiy, umumiy so'z bazasi **yo'q**) | `audio_url`, `image_url` | PostgreSQL + `uploads/` | vocabularies API |
| Uyga vazifa (eski) | `homeworks`, `homework_submissions` | — | PostgreSQL | — |
| Assessment Engine (darsga bog'langani) | `assessments` (`lesson_id`), sections, tasks, `task_audio`, attempts, submissions, evaluations | `task_audio.storage_path`, `speaking_submissions.storage_path`, `feedback_audio_path` | `app/protected_storage/audio/…` | assessment-engine API |
| Student natijalari | `student_progress`, `video_progress`, `student_quizzes`, `lesson_skill_attempts`, `student_writings`, `student_speakings`, `ai_evaluations` | `student_speakings.storage_path` | `app/protected_storage/legacy-speaking/…` | — |

**Darsga biriktirilgan PDF va qo'shimcha fayllar uchun model yo'q.** `books` jadvali (Bücher, `app/protected_storage/books/`) darajaga bog'langan alohida PDF kutubxona, darslarga bog'lanmagan. Alohida "audio kitob" modeli ham yo'q: dars audiosi faqat Hören topshiriqlari (`listenings`) orqali saqlanadi.

## 2. Bog'lanishlar xaritasi (haqiqiy foreign key'lar asosida)

```
courses ──CASCADE──► modules ──CASCADE──► lessons ──CASCADE──► 19 jadval ──► jami 46 jadval
   │
   └─CASCADE──► payments, certificates, enrollments, teacher_assignments   ⚠
```

- **`courses` yoki `modules` qatorini o'chirish taqiqlanadi.** `courses` o'chirilsa, to'lovlar, sertifikatlar, yozilishlar va o'qituvchi biriktirishlari ham o'chib ketadi. Shuning uchun daraja va modul qatorlari qoladi; tozalash faqat `lessons` va undan pastdagi jadvallarga tegadi.
- **`lessons` o'chirilsa**, kaskad orqali 46 ta jadvaldagi bog'liq qatorlar o'chadi. Ular orasida student progressi, video progress, Schreiben/Sprechen javoblari va o'qituvchi baholari ham bor.
- **Foreign key'siz bog'lanish:** `ai_evaluations` (`kind` + `submission_id`). Kaskad ularni o'chirmaydi, alohida o'chirish kerak; aks holda yetim qatorlar qoladi.
- **Tegilmaydigan modullar** (darslarga foreign key orqali bog'lanmagan, dry-run har safar tekshiradi):
  - VIZU-Multilevel (`vizu_multilevel_*`, `vizu_mock_*`);
  - Vorbereitung model testlari (`model_tests`, `kompetenzen`; ularning `assessments` qatorlarida `lesson_id` NULL);
  - mock exam, sertifikatlar, foydalanuvchilar va auth;
  - to'lovlar, promo kodlar;
  - `books`, `media_assets`, reklama.

## 3. Dry-run (faqat o'qiydi)

`backend/app/scripts/course_content_audit.py` bitta READ ONLY tranzaksiyada ishlaydi. Unda yozish urinishi bloklanishi sinab ko'rilgan. Skript:

- kaskadni bazaning haqiqiy foreign key'lari bo'ylab yuradi (keyin qo'shiladigan jadvallar ham avtomatik qamraladi);
- har bir jadval bo'yicha o'chadigan qatorlar sonini, SET NULL ta'sirini va RESTRICT blokerlarini chiqaradi;
- foreign key'siz yetim qoladigan qatorlarni sanaydi;
- har bir faylning diskda bor-yo'qligini va hajmini tekshiradi;
- **umumiy fayllarni ajratadi:** o'chirish to'plamidan tashqaridagi biror qator, `media_assets` yoki reklama ishlatayotgan fayl "saqlanadi" deb belgilanadi;
- hech qanday qator ishlatmayotgan, diskdagi ortiqcha video va audio fayllarni ham ko'rsatadi;
- himoyalangan jadval o'chirish to'plamiga tushib qolsa yoki Vorbereitung assessment'i tushsa, `STOP` deb chiqadi va exit kodi 1 bo'ladi.

Serverda ishga tushirish (o'zgartirmaydi):

```bash
cd /opt/vizu/VIZU-Academy/backend
.venv/bin/python -m app.scripts.course_content_audit --json /root/course-audit-$(date +%F).json
# faqat ayrim darajalar uchun: --levels A1 A2
```

Test bazasida natija (A1, 19 dars): kaskad bo'yicha 20 jadvalda 5 824 qator, `ai_evaluations` da 6 ta yetim qator, 1 video fayl. Qo'lda yozilgan SQL bilan solishtirilganda sonlar mos keldi. Himoya tekshiruvlari: OK.

## 4. Backup

`backend/scripts/backup-course-content.sh` bazaga ham, fayllarga ham yozmaydi; faqat backup papkasiga yozadi.

1. Bo'sh joyni tekshiradi (fayllar hajmi + baza hajmi, 20 % zaxira bilan). Joy yetmasa, to'xtaydi.
2. `pg_dump -Fc` bilan to'liq baza dumpini oladi, so'ng `pg_restore --list` bilan uni o'qish mumkinligini tekshiradi.
3. `app/protected_storage` va `uploads` ning `tar` arxivini oladi; arxivdagi fayllar soni diskdagi bilan teng bo'lishi shart.
4. `sha256sum` bilan nazorat summalarini yozadi va darhol qayta tekshiradi.
5. `RESTORE_CHECK=1` bilan dumpni vaqtinchalik bazaga tiklab, jadvallar bo'yicha qator sonlarini solishtiradi, keyin vaqtinchalik bazani o'chiradi.

Parol va tokenlar hech qayerga chiqarilmaydi: ular `.env` dan olinib, `pg_dump` ga faqat muhit o'zgaruvchisi orqali beriladi. Natija `/var/backups/vizu/course-reset-<vaqt>/` ga tushadi, faqat egasi o'qiy oladi (`umask 077`). Biror tekshiruv o'tmasa, exit kodi 1 bo'ladi va tozalash boshlanmasligi kerak.

```bash
cd /opt/vizu/VIZU-Academy/backend
RESTORE_CHECK=1 bash scripts/backup-course-content.sh   # CREATEDB huquqi bo'lsa
```

Test bazasida: 101 jadval, `restore check: 101 tables restored, 0 with differing counts`.

**Tiklash:**
- baza: `pg_restore --clean --if-exists --no-owner -d <db> db.dump` (servis to'xtatilgan holda);
- fayllar: `backend/` ichida `tar -xf files.tar`.

## 5. Tasdiqlash uchun qarorlar

O'chirishni bajaradigan qism hali yozilmagan, ataylab. U quyidagi qarorlar va serverdagi dry-run natijasidan keyin, aynan shu tanlov asosida yoziladi.

1. **Qamrov:** A1–C1 ning barcha darslari, yoki faqat ayrim darajalar?
2. **Student tarixi:** darslar bilan birga quyidagilar ham o'chadi: progress, video progress, Schreiben/Sprechen javoblari, o'qituvchi baholari, AI baholari. Bunga roziligingiz kerak. Alternativa: dars qatorlari qoldiriladi, faqat ichidagi kontent tozalanadi. Bu tarixni saqlab qoladi, lekin eski progress yangi kontentga mos kelmay qoladi.
3. **Modullar:** mavjud modul qatorlari (nomlari bilan) qolsinmi yoki yangi tizimda admin ularni qayta nomlaydimi? O'chirilmaydi, chunki kurs kaskadi xavfli emas, lekin modul nomlari eski bo'lishi mumkin.
4. **`books` (Bücher PDF kutubxonasi):** bu alohida modul. Tozalashga kiritilsinmi? Hozirgi rejada kiritilmagan.
5. **VIZU-DEUTSCH A1 kitob importi:** u ham shu dars kontentining bir qismi, tozalanganda u ham o'chadi. Import skripti qolgani uchun keyin qayta import qilish mumkin.

## 6. Yangi tizim: mavjud arxitekturani kengaytirish

Parallel model yaratish shart emas. Talablarning ko'pi allaqachon mavjud jadvallar va API'larda bor:

| Talab | Holat |
|---|---|
| Daraja, modul, dars, ketma-ketlik | Bor: `courses.level`, `modules.order_index/number`, `lessons.number` va admin sahifalari |
| Video yuklash (bo'laklab), himoyalangan saqlash, nashr qilish, preview | Bor |
| Video progress, davom ettirish, completion | Bor; brauzerda sinalgan |
| Kirish sharti (bepul dars, Premium, daraja egasi) | Bor: `lessons.is_free`, `can_access_lesson` |
| Kompetenzlar tartibi | Bor; frontend va backend tartibi contract test bilan bog'langan |
| Hören audiosi | Bor (`listenings`, himoyalangan) |
| **Darsga PDF va qo'shimcha resurslar** | **Yo'q.** Kerak: yangi `lesson_resources` jadvali (PDF, AUDIO, FILE), himoyalangan saqlash, autentifikatsiyali yuklab olish endpointi, admin sahifasi |
| **Dars tavsifi, dars darajasida nashr qilish/yashirish** | **Yo'q** (`lessons` da `description` va `is_published` ustunlari yo'q). Kerak: additive migration, standart qiymat bilan |
| **Fayl holatini tekshirish** (bor/yo'q, hajm, yuklanish) | Qisman (video playback faylni tekshiradi). Kerak: admin uchun "storage health" ko'rinishi |

Barcha migrationlar additive bo'ladi, `downgrade` bilan; mavjud API kontraktlari o'zgarmaydi.
