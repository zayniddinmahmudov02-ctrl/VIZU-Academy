# Groups & Classroom — arxitektura va hisobot

Sana: 2026-11-21 · Holat: **Groups va LiveKit integratsiyasi lokal test bazada tekshirilgan; LiveKit production'ga o‘rnatilmagan.**

## 1. Audit natijasi — nima qayta ishlatildi

| Ehtiyoj | Mavjud manba (qayta ishlatildi) |
|---|---|
| Rollar | `users.role`: STUDENT, TEACHER, SUPER_ADMIN (+ staff rollari); teacher paneli `/teacher` (TEACHER, SUPER_ADMIN) |
| Dars progressi | `student_progress`: lesson_completed, completed_at, last_activity_at, total_score (0–100), competencies_* |
| Yo‘nalishlar (Lesen, Hören …) | `student_competency_progress` + `lesson_competencies` |
| Topshiriqlar va baholar | `student_writings`, `student_speakings`, `homework_submissions`. Statuslar: DRAFT / SUBMITTED / EVALUATING / NEEDS_REVISION / GRADED; score, feedback, reviewed_at |
| Deadline | `writings.closes_at` (mavjud bo‘lsa) |
| Baholash | Mavjud `StudentWritingService` / `StudentSpeakingService` / `HomeworkSubmissionService` va `/teacher/{writing,speaking,homework}/{id}/grade` endpointlari |
| Audio tinglash | Mavjud `/speakings/submissions/{id}/audio` |
| Bildirishnomalar | Mavjud `notifications` jadvali (`link_path` bilan) |
| Rate limit | Mavjud `auth_rate_limit_events` jadvali (identifikator va IP faqat HMAC hash ko‘rinishida) |
| Real-time | WebSocket yo‘q, shuning uchun chat **polling** bilan ishlaydi: 5 soniyada `?after=`, sahifa ko‘rinmayotganda to‘xtaydi |

Ikkinchi, parallel progress yoki baholash tizimi yaratilmadi.

## 2. Yangi jadvallar (migratsiya `b7e3d9a2c5f1`, down: `d4b8e2f6a9c1`)

Faqat guruhga oid ma’lumotlar saqlanadi; mavjud jadvallar o‘zgarmaydi.

| Jadval | Mazmuni |
|---|---|
| `study_groups` | nomi, tavsifi, teacher_id, daraja, turi (online/offline/hybrid), holati (active/paused/archived/blocked), sanalar, sig‘imi, chat rejimi (open/teacher_only/closed), oxirgi faollik |
| `study_group_courses` | guruh ↔ kurs (`UNIQUE(group, course)`). Bu **enrollment emas** |
| `study_group_members` | `UNIQUE(group_id, user_id)`; rol (teacher/student), holat (active/removed/left), can_post, last_read_at (o‘qilmagan xabarlar uchun) |
| `study_group_join_codes` | faqat `code_hash` (HMAC-SHA256, unique); holat, expires_at, max_uses, use_count, revoked_at |
| `study_group_messages` | matn, pin; moderatsiyada qator saqlanadi (deleted_at/by), matn yashiriladi |
| `study_group_announcements` | sarlavha, matn, pin, arxiv |
| `study_group_tasks` | guruh uchun dars-vazifa + `due_at`. Bajarilgan-bajarilmagani LMS'dan o‘qiladi |
| `study_group_audit_logs` | kim, nima, qachon. Kod, token yoki parol yozilmaydi |
| `study_group_video_rooms` | har bir mavjud guruhga bittadan rejalashtirilgan LiveKit room |
| `study_group_video_sessions` | dars boshlanishi/yakunlanishi va davomiyligi |
| `study_group_video_events` | qo‘shilish, boshqaruv va client yuborgan aloqa hodisalari; tokenlar saqlanmaydi |

Videochat jadvallari `c1v7d3e9a5b2` migratsiyasida qo‘shilgan; mavjud guruhlar uchun room qatori backfill qilinadi. Downgrade faqat videochat jadvallarini o‘chiradi, guruhlar va a’zoliklar qoladi.

Indekslar: o‘qituvchi+holat, a’zo+holat, xabarlar (group_id, created_at), e’lonlar, audit.

Guruh o‘chirilmaydi, faqat arxivlanadi. Chat va progress saqlanib qoladi.

## 3. Ruxsatlar (hammasi backend'da, `app/services/study_groups/access.py`)

- **Boshqarish:** guruh o‘qituvchisi yoki SUPER_ADMIN. Bloklangan guruhni faqat SUPER_ADMIN o‘zgartiradi.
- **Ko‘rish:** boshqaruvchilar va guruhning faol a’zolari. Qolgan hamma uchun javob **404** bo‘ladi (403 emas), toki begona guruhning mavjudligi ham bilinmasin.
- **So‘rov tanasi:** `extra="forbid"`, ya’ni `user_id`, `role` kabi maydonlar rad etiladi. `teacher_id` faqat SUPER_ADMIN uchun qabul qilinadi.
- **Baholash:** mavjud qoida (`TeacherAssignment`) o‘zgarmadi. Unga **qo‘shimcha** shart qo‘shildi (`scope.py`): talaba o‘qituvchining (bloklanmagan) guruhida faol a’zo bo‘lsa va guruh shu kursga bog‘langan bo‘lsa, ruxsat beriladi. Talaba guruhdan chiqsa, ruxsat ham yo‘qoladi.
- **Kursga kirish:** guruhga qo‘shilish pullik kursni ochmaydi. Darsga kirish mavjud `ensure_lesson_open` va enrollment qoidalari bilan boshqariladi.

## 4. Qo‘shilish kodi xavfsizligi

- Kod 8 belgidan iborat, 31 harfli alifboda (I/L/O/0/1 yo‘q), `secrets` modulida yaratiladi. Ko‘rinishi `XXXX-XXXX`, variantlar soni ≈ 8.5·10¹¹.
- Bazada faqat HMAC hash saqlanadi. Ochiq kod **faqat bir marta** — yaratilgan paytdagi javobda ko‘rsatiladi. O‘qituvchi istalgan vaqtda yangisini yarata oladi; yangi kod yaratilishi bilan eskisi bekor bo‘ladi.
- To‘xtatish/faollashtirish, amal qilish muddati, foydalanish limiti va guruh sig‘imi tekshiriladi. Qo‘shilish paytida guruh qatori qulflanadi (`SELECT … FOR UPDATE`), shuning uchun parallel so‘rovlarda ham limit buzilmaydi.
- Noto‘g‘ri kodga cheklov: 15 daqiqada foydalanuvchiga 10 ta, IP'ga 30 ta urinish; keyin 429.
- Kod log, audit yoki API javobida chiqmaydi (testlar bilan tekshirilgan).

## 5. Monitoring — hisoblash qoidalari (`progress.py`)

**Guruh vazifasining talaba bo‘yicha holati**, ustuvorlik tartibida:

1. `needs_revision` — biror topshirig‘i tuzatishga qaytarilgan;
2. `under_review` — tekshirilmoqda;
3. `completed` yoki `completed_late` — dars tugatilgan; agar tugatilgan vaqt `due_at` dan keyin bo‘lsa, `completed_late`;
4. `overdue` — muddat o‘tgan, ish topshirilmagan;
5. `in_progress` — boshlangan;
6. `not_started` — boshlanmagan.

**Dashboard ko‘rsatkichlari:**

- talabalar soni, faollar (oxirgi 7 kun ichida faollik);
- topshirilgan / bajarilmagan / kechiktirilgan / tekshirilayotgan vazifalar;
- o‘qituvchi tekshiruvini kutayotgan ishlar;
- o‘rtacha dars bali (`total_score`, faqat tugatilgan darslar bo‘yicha);
- o‘rtacha baho (faqat baholangan ishlar bo‘yicha);
- umumiy progress.

Ma’lumot bo‘lmasa, qiymat `null` (UI'da „—“) bo‘ladi; sun’iy foiz yoki baho ko‘rsatilmaydi.

**Samaradorlik:** guruh ma’lumoti o‘zgarmas sondagi so‘rovlar bilan yuklanadi (N+1 yo‘q). Talabalar jadvali filtr, saralash va sahifalash bilan serverda hisoblanadi.

## 6. API (`/api/v1/groups`, barchasi login talab qiladi)

| Kim | Endpointlar |
|---|---|
| Talaba | `GET /my`, `POST /join/preview`, `POST /join`, `POST /{id}/leave`, `GET /{id}/me` |
| A’zo / boshqaruvchi | `GET /{id}`, `GET /{id}/members`, `GET,POST /{id}/messages`, `POST /{id}/read`, `GET /{id}/announcements`, `GET /{id}/lessons` |
| O‘qituvchi | `GET /options`, `GET /teaching`, `POST /`, `PATCH /{id}`, `POST,PATCH /{id}/code`, `PATCH /{id}/members/{uid}`, `PATCH /{id}/messages/{mid}`, `PUT /{id}/chat`, `POST,PATCH /{id}/announcements…`, `PUT /{id}/tasks`, `DELETE /{id}/tasks/{tid}`, `GET /{id}/tasks`, `GET /{id}/dashboard`, `GET /{id}/students`, `GET /{id}/students/{sid}`, `GET /{id}/audit` |
| SUPER_ADMIN | `GET /admin/all` (filtrlar: o‘qituvchi, daraja, holat, kurs, sana, qidiruv), `GET /admin/stats`, `PATCH /{id}` bilan block/unblock |
| Videochat a’zosi / boshqaruvchisi | `GET /{id}/video`, `PUT /{id}/video/schedule`, `POST /{id}/video/{start,end,join,events,control}`. Tokenni faqat backend beradi; guruh a’zoligi va manager huquqi serverda tekshiriladi |
| Admin panel / SUPER_ADMIN | `GET /admin/video/rooms` (admin-panel ruxsati), `POST /admin/video/rooms/{id}/end` (faqat SUPER_ADMIN) |

Baholash uchun alohida endpoint yo‘q: mavjud `/teacher/{writing,speaking,homework}/{id}/grade` ishlatiladi.

## 7. Bildirishnomalar (sayt ichida; e-mail va Telegram yo‘q)

- Talaba guruhga qo‘shildi → o‘qituvchiga.
- Yangi e’lon → talabalarga.
- Yangi vazifa yoki muddat o‘zgarishi → talabalarga.
- Chatda yangi xabar → a’zolarga. Har bir guruhga bitta o‘qilmagan bildirishnoma beriladi, har bir xabar uchun alohida emas.
- Talaba ish topshirdi → guruh o‘qituvchisiga.
- Ish tekshirildi va fikr yozildi → talabaga. Bu bildirishnoma guruhdan tashqari barcha Schreiben/Sprechen/Hausaufgabe baholashlariga ham ishlaydi.

Bildirishnoma yaratishdagi xato topshirish yoki baholashni hech qachon bekor qilmaydi.

## 8. Frontend

- **Talaba:**
  - sidebar'da „Guruhlar“ bo‘limi;
  - `/groups` — guruh kartochkalari (o‘qilmagan xabarlar, oxirgi xabar, vazifalar holati) va kod bilan qo‘shilish (tasdiqlash oynasi bilan);
  - `/groups/[id]` — Umumiy, Chat, E’lonlar, Vazifalar, Mening natijalarim, A’zolar.
- **O‘qituvchi:**
  - teacher navigatsiyasida „Guruhlar“;
  - `/teacher/groups` — ro‘yxat, filtrlar, guruh yaratish, kod bir marta ko‘rsatiladi;
  - `/teacher/groups/[id]` — Umumiy (dashboard), Chat, E’lonlar, Vazifalar (dars + muddat, talabalar kesimidagi jadval), O‘quvchilar (filtr va saralash), Sozlamalar (tahrir, kod, chat rejimi, a’zolar), Audit;
  - `/teacher/groups/[id]/students/[sid]` — darslar, vazifalar, topshiriqlar (matn, audio, baholash), yo‘nalishlar, faollik.
- **Admin:** `/admin/groups` — statistika, filtrlar, bloklash/arxivlash va 15 soniyada yangilanadigan LiveKit room/participant monitoringi. Monitoringda room holati, ishtirokchilar, davomiylik hamda client yuborgan disconnect/reconnect hodisalari bor; server CPU/RAM ko‘rsatkichi hozircha mavjud emas.
- **Videochat:** student va teacher guruh sahifasidagi Videochat tabidan foydalanadi. Browser orqali LiveKit SFU'ga ulanadi; token qisqa muddatli va room-scoped. Teacher server orqali mute/kick/mikrofon va screen-share ruxsatlarini boshqaradi. Room tugaganda backend LiveKit room'ni o‘chiradi.

## 9. Testlar (lokal, 2026-11-21)

- **`tests/test_study_groups.py` — videochat bilan 14 test OK.** Tekshiriladi:
  - API kontrakti: hamma route login talab qiladi, so‘rov tanasida user/role yuborib bo‘lmaydi;
  - kod formati va hash saqlanishi;
  - rollar: student guruh yarata olmaydi, teacher boshqa teacher tayinlay olmaydi, begona guruhni boshqara olmaydi;
  - kodlar: noto‘g‘ri, muddati o‘tgan, to‘xtatilgan, bekor qilingan, limiti tugagan, sig‘im to‘lgan, o‘z guruhi, chiqarilgan talaba, rate limit;
  - chat: begona 404, teacher-only rejim, yozish huquqi olingan talaba, moderatsiya, o‘qilmaganlar;
  - e’lonlar va bildirishnomalar;
  - LMS ma’lumotidan hisoblangan dashboard va jadval;
  - guruh orqali baholash; talaba guruhdan chiqqach ruxsat yo‘qoladi;
  - blocked/archived holatlar; admin ro‘yxati va statistika.
- **`tests/test_study_group_video_chat_migration.py` — 1 test OK:** mavjud group qatori saqlanadi, migration room qo‘shadi va downgrade guruhni o‘chirmaydi.
- LiveKit test double bilan room create/delete, takroriy start, non-member 404, token identity/room/role/TTL, teacher kick/mic/screen boshqaruvi, join rate limit va admin monitoring tekshirildi.
- **Butun backend:** 810 test OK (17 skipped). Mavjud baholash servislari regressiyasiz ishlaydi.
- **HTTP end-to-end:** lokal uvicorn, haqiqiy login, 38 ta tekshiruv, hammasi PASS.
- **Frontend:** `tsc` OK, `eslint` OK, `next build` OK.
- **Migratsiya:** test bazada upgrade → downgrade → upgrade o‘tdi.

## 10. Qolgan ishlar va cheklovlar

- **Chat polling bilan ishlaydi** (5 s). Fayl va rasm yuborish keyingi bosqichga qoldirildi.
- **Guruhda bitta o‘qituvchi bor.** Ikkinchi (yordamchi) o‘qituvchi tushunchasi yo‘q. Ruxsatlar SUPER_ADMIN tomonidan rol orqali beriladi.
- **Kodni qayta ko‘rib bo‘lmaydi.** Bu xavfsizlik tanlovi: kod faqat hash ko‘rinishida saqlanadi, kerak bo‘lsa yangisi yaratiladi.
- **Mavjud „Meine Schüler“ va Schreiben/Sprechen navbatlari** hamon faqat `TeacherAssignment` kurslarini ko‘rsatadi. Guruh talabalari ishlari guruh sahifasida ko‘rinadi.
- **Deadline'lar:** LMS'ning o‘zida deadline yo‘q, shuning uchun muddat guruh vazifasi (`study_group_tasks.due_at`) va `writings.closes_at` dan olinadi.
- **Production infra yo‘q:** `meet.vizu-deutsch.com` DNS yozuvi topilmadi; LiveKit, TURN/STUN, TLS/WSS va UDP portlar sozlanmadi. Docker, firewall yoki Nginx production'da o‘zgartirilmadi.
- **Haqiqiy brauzer va ikki qurilmali sinov qilinmadi.** Chrome/Edge/Firefox/Safari, Android/iPhone, media, TURN va reconnect tekshiruvlari production LiveKit talab qiladi.
- **Admin telemetry cheklangan:** participant count LiveKit'dan, disconnect/reconnect hodisalari client eventlaridan olinadi; CPU/RAM va LiveKit server metrics endpointi yo‘q.
- Production deploy qilinmadi. Avval DNS, valid TLS, LiveKit/TURN + UDP firewall, maxfiy konfiguratsiya va backup/restore check talab qilinadi; keyin migration preview va amaldagi deploy tartibi bajariladi.
