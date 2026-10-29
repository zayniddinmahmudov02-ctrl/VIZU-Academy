# A2 kursi — audit va implementatsiya hisoboti

Sana: 2026-10-30. Muhit: lokal Windows nusxasi (`D:\Projects\VIZU-Academy`), lokal git yo‘q, production’ga ulanish yo‘q. **Production deploy, production migration va eski arxivni o‘chirish bajarilmagan.** Telegram botlar, ularning kodi, bazasi va servislari tegilmagan.

## 1. Audit (ish boshlanishidan oldin)

| Savol | Topilgan |
|---|---|
| A2 kursi, modul, darslar | `courses` (level A2, til `de`) → asosiy modul → `lessons` 1–14 (`services/lms/structure.py`, `LEVEL_LESSON_COUNTS["A2"] = 14`). Kontent: kitobga sodiq nashr `app/scripts/vizu_deutsch_a2_buch` (2026-10-27), birinchi raqamlashtirish `[Archiv] …` sifatida qolgan. 14-dars “Wiederholung”, bo‘sh, nashrsiz |
| Tartib va unlock | `lessons.number`, admin reorder; `services/lms/access.py` (draft → 404, LOCKED, Premium/Angebote, ixtiyoriy sequential) |
| Media Management | `/admin/media-management` — barcha darajalar video/audio sharhi, faqat o‘qiydi; A2 uchun `GET /a2-audio` va vazifa-kartochkalari (`a2-listening-management.tsx`) |
| Audio qayerda | Disk, shaxsiy: `app/protected_storage/lesson-listening/` (`ProtectedLessonListeningStorage`). Object storage (R2) faqat video uchun |
| Audio ↔ DB | `listenings.audio_storage_path` (+ `audio_original_name`, hajm, tur), qo‘shimcha treklar `listening_audio_tracks`, eski versiyalar `listening_audio_archives` |
| Eski A2 audio arxivi | `[Archiv]` vazifalari, `listenings.a2_material_key` (`a2-l01-audio-01` …), A2 vazifalarining `listening_audio_archives` qatorlari — batafsil `docs/a2-media-cleanup-plan.md` |
| Umumiy media | `file_references` bir faylga ishora qiluvchi barcha vazifa/treklarni sanaydi; `media_assets` va `uploads/` alohida tizim |
| Narx, sotuv, promo | `vizu_pay/offers.py` — A2 99 000 UZS (200 000 dan), sotuv yopiq; promo kodlar mavjud — `docs/a2-sales-readiness.md` |
| Sotib olishdan keyin | SUPER_ADMIN buyurtmani tasdiqlaydi → `access_start/end_date` (A2: 1 oy) → `owned_levels` |
| Audio pleer, progress | `listening-section.tsx` (blob orqali, ommaviy URL yo‘q), urinishlar `lesson_skill_attempts`; audio’siz vazifa ko‘rsatilmasdi (bo‘lim “mashqlar yo‘q” derdi) |
| Admin upload | Har bir vazifaga alohida (`POST /admin/lesson-skills/listenings/{id}/audio`: MP3/WAV/M4A, 100 MB, mazmun bo‘yicha tekshiruv). Batch, dublikat, kutubxona yo‘q edi |
| Hören holati (oldingi audit) | 25 joriy vazifa, hammasi qoralama, audio yo‘q; 4–7, 10–13-darslarda kitobda kalit yo‘q |

## 2. Qilingan ishlar

### 2.1 A2 Audio Manager (Media Management → A2)
- Yangi jadval `a2_audio_assets` (migration `a6d2f9c4e8b1`, additive): Unterricht, tur (HOEREN/TEXT/UNTERRICHT/OTHER), qism, nom, original fayl nomi, parser natijasi, xavfsiz saqlash nomi (`a2-audio/<uuid>.<format>`), format, MIME, hajm, **SHA-256 (unique)**, davomiylik, tartib, tekshiruv holati + izoh + kim/qachon, bog‘langan vazifa + kim/qachon, kim yuklagan.
- Fayl mavjud shaxsiy Hören storage’da saqlanadi — storage almashtirilmadi; o‘quvchiga faqat mavjud Hören endpointi orqali (`require_lesson_access` + nashr qilingan vazifa) yetib boradi.
- Upload tekshiruvlari (serverda): nomda boshqa daraja → 422; kengaytma, e’lon qilingan MIME va fayl baytlari bir xil formatni ko‘rsatishi shart (MP3: ID3/MPEG frame, AAC ADTS rad; M4A: `ftyp` + audio brand, M4V rad); bo‘sh fayl; `A2_AUDIO_MAX_BYTES` (config, 100 MB) → 413; formatlar `A2_AUDIO_FORMATS` (config); dublikat → `409 DUPLICATE` (mavjud yozuv bilan), yangi nusxa o‘chiriladi.
- Fayl nomidan Unterricht/tur/qism (`filename.py`, NFC normalizatsiya, `Teil_1`, “UNTERICHT”); admin qiymatlari ustun; admin keyin tuzatadi (`PATCH`).
- Batch upload (frontend): fayllar ketma-ket, har biriga progress; hisobot: muvaffaqiyatli / dublikat / xato (sababi bilan) / bog‘lanmagan.
- Preview/play (admin blob), “Geprüft” / “Problem” (izoh majburiy).
- **Bog‘lash faqat admin tasdig‘i bilan**; taklif faqat bitta vazifa aniq mos kelganda; “Text” fayllari taxmin qilinmaydi. Faqat joriy A2 Hören vazifalari; vazifaning eski audiosi arxivga o‘tadi; vazifa qoralamaga o‘tadi. Qayta bog‘lash, ajratish (`unlink`), boshqa fayl bilan almashtirish.
- O‘chirish ikki alohida qaror: yozuvni o‘chirish (fayl qoladi) va faylni o‘chirish (faqat hech narsa ishlatmasa; bog‘langan yozuv o‘chirilmaydi; avval fayl, keyin yozuv). Har bir amal `audit_logs` ga yoziladi.
- Mavjud per-vazifa Hören endpointlari endi kutubxona fayllarini hisobga oladi: vazifa audiosini o‘chirish/almashtirish kutubxona faylini **o‘chirmaydi**, faqat bog‘lanishni bo‘shatadi. `unreferenced_files` va `a2_audio_inventory` kutubxona fayllarini “egasiz” deb ko‘rsatmaydi.
- Manifest: `GET /a2-audio/manifest`, `python -m app.scripts.a2_audio_manifest` — `docs/a2-media-manifest.md`.

### 2.2 Eski arxiv
- `python -m app.scripts.a2_audio_cleanup plan | quarantine | restore | purge` — reja, karantin (SHA-256, manifest), qaytarish, alohida tasdiqli purge. DB qatorlari hech qachon o‘zgartirilmaydi. Production’da **ishga tushirilmagan** — `docs/a2-media-cleanup-plan.md`.

### 2.3 Kurs, darslar, sotuv
- Mavjud LMS (darslar ro‘yxati, tartib, unlock, kompetensiyalar) qayta yozilmadi — ishlaydi va testlangan. Kontent uydirilmadi (tavsif, matn, test, audio yaratilmadi).
- O‘quvchi: audio yo‘q nashr qilingan vazifa uchun “Audio hali yuklanmagan” (`audio_pending`), player ko‘rsatilmaydi.
- Sotuv: narxsiz darajani sotuvga ochish rad etiladi; tayyorlik indikatori — `docs/a2-sales-readiness.md`.

## 3. O‘zgartirilgan va yangi fayllar (A2)

| Fayl | |
|---|---|
| `backend/app/models/a2_audio_asset.py`, `models/__init__.py` | yangi model |
| `backend/alembic/versions/a6d2f9c4e8b1_a2_audio_assets.py` | yangi migration |
| `backend/app/services/a2_audio/` (`filename.py`, `assets.py`, `readiness.py`, `cleanup.py`) | yangi servislar |
| `backend/app/api/admin/media_management_router.py` | 12 ta yangi endpoint (`/a2-audio/assets…`, `/a2-audio/manifest`, `/a2-audio/targets`, `/a2-readiness…`), `unreferenced_files` |
| `backend/app/services/lesson_skills/admin.py` | `file_references` kutubxonani sanaydi; bog‘lanishni bo‘shatish |
| `backend/app/api/lesson_skills/router.py` | `audio_pending` |
| `backend/app/services/vizu_pay/offers.py` | narxsiz sotuv rad |
| `backend/app/core/config.py` | `A2_AUDIO_MAX_BYTES`, `A2_AUDIO_FORMATS` |
| `backend/app/scripts/a2_audio_cleanup.py`, `a2_audio_manifest.py`, `a2_audio_inventory.py` | CLI |
| `backend/tests/test_a2_audio_manager.py` (yangi, 19 test), `test_a2_audio_management.py` (stub’lar 4-manbaga moslandi + 1 test), `test_angebote.py` (+ narx qoidasi) | testlar |
| `frontend/src/features/admin/components/media-management/a2-audio-manager.tsx`, `a2-audio-import.ts`, `media-management-client.tsx` | UI |
| `frontend/src/features/admin/services/media-management-service.ts` | API client |
| `frontend/src/components/lesson-player/listening/listening-section.tsx`, `features/lessons/services/lesson-skills-service.ts`, `lib/i18n/translations.ts` | “Audio hali yuklanmagan” |
| `frontend/tests/unit/a2-audio-import.test.mjs`, `e2e/tests/a2-audio-manager.spec.ts` | testlar |

## 4. Migratsiyalar

| Revision | Oldingi | Mazmun | Downgrade |
|---|---|---|---|
| `f3a8c1d5e7b2` | `e9b4c2f7a3d1` | `global_chat_messages.reply_to_id` + FK + partial index | ustun va index o‘chadi |
| `a6d2f9c4e8b1` | `f3a8c1d5e7b2` | `a2_audio_assets` jadvali | jadval o‘chadi, **fayllar qoladi** (Media Management’da “DB yozuvisiz” bo‘lib ko‘rinadi) |

Ikkalasi bo‘sh bazada `upgrade head → downgrade base → upgrade head` va reply uchun ma’lumotli round-trip bilan sinaldi. `alembic check`: faqat avvaldan ma’lum 1 farq (`student_speakings.user_id`).

## 5. Ish davomida aniqlangan muammolar

| # | Muammo | Holat |
|---|---|---|
| 1 | `backend/requirements.txt` da `reportlab`, `qrcode` yo‘q, lekin kod import qiladi (sertifikat PDF); toza o‘rnatishda 11 ta test import xatosi beradi. `boto3`/`botocore` (R2), `openpyxl` ham ro‘yxatda yo‘q (lazy import) | **Ochiq** — requirements o‘zgartirilmadi (server muhitini ko‘rmasdan); tasdiqlansa qo‘shish kerak |
| 2 | `httpx` yo‘q — FastAPI `TestClient` ishlamaydi | HTTP testlari `httpx` bo‘lmasa skip bo‘ladigan qilib yozildi |
| 3 | Swipe: `setPointerCapture` faol bo‘lmagan pointer uchun exception tashlab, swipe’ni to‘xtatardi | Tuzatildi (try/catch), E2E bilan topilgan |
| 4 | Karantin: bir soniyada qayta karantin bir xil papka nomini berardi | Tuzatildi (mikrosekund), test bilan topilgan |
| 5 | In-process Alembic (`Config("alembic.ini")`) `fileConfig` orqali ilova logger’larini o‘chirib, keyingi testni yiqitardi; `env.py` URL’ni `settings` dan oladi | Mening migration testimda tuzatildi; `env.py` o‘zgartirilmadi |
| 6 | Avval audio’siz nashr qilingan vazifa jimgina yo‘qolar, bo‘lim “mashqlar yo‘q” derdi | Tuzatildi (`audio_pending`) |

## 6. Qolgan vazifalar (alohida tasdiq bilan)

1. Production deploy (backup → migratsiya → backend → frontend slot).
2. Haqiqiy A2 audio fayllarini yuklash va bog‘lash; manifestni serverda chiqarish.
3. Serverda cleanup `plan` → ko‘rib chiqish → `quarantine` → kuzatish → (yozma tasdiq) `purge`.
4. Kurs tavsifi, yetishmayotgan Hören kalitlari (admin audio tinglab).
5. Sandbox to‘lov testi, mobil/desktop tekshiruvi, keyin A2 sotuvini yoqish (biznes qarori).
6. `requirements.txt` ga yetishmayotgan paketlar (5-bo‘lim, 1-band).
