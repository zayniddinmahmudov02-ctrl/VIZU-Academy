# Eski A2 audio arxivini tozalash rejasi

Sana: 2026-10-30. Holat: **reja va vositalar tayyor. Production’da hech narsa ko‘chirilmagan va o‘chirilmagan.** Har bir bosqich alohida tasdiq bilan bajariladi.

## 1. Eski A2 audio arxivi aniq nima va qayerda

Production bazasiga bu ishda ulanilmadi (lokal muhit, `/opt/vizu` ga kirish yo‘q). Quyidagi ta’rif kod va oldingi auditlar (`docs/a2-book-audit-2026-10-22.md`, `docs/a2-book-content-audit.md`) asosida:

| Obyekt | Qayerda | Qanday aniqlanadi |
|---|---|---|
| Fayllar | `backend/app/protected_storage/lesson-listening/` (shaxsiy, ommaviy URL yo‘q) | `listenings.audio_storage_path`, `listening_audio_tracks.storage_path`, `listening_audio_archives.storage_path` |
| Birinchi raqamlashtirishning A2 Hören vazifalari | `listenings`, A2 darslarida, sarlavhasi `[Archiv] …` (`vizu-a2-…` content id) | `title LIKE '[Archiv]%'` |
| Eski “A2 audio material” vazifalari | `listenings.a2_material_key` (masalan `a2-l01-audio-01`, sarlavha “A2 1.Unterricht Hören”, 0 savol) | `a2_material_key IS NOT NULL` |
| A2 vazifalarining avvalgi audio versiyalari | `listening_audio_archives` | `listening_id` A2 darsiga tegishli |
| Media Management | Faqat ko‘rsatadi (`GET /admin/media-management/a2-audio`), `[Archiv]` vazifalarini yashiradi | — |

Oldingi auditdan ma’lum: 2026-10-22 dagi backup `/var/backups/vizu/a2-reset-20261022-185358/`; 13-dars uchun yetkazilgan fayllar 12-darsnikiga bayt-ma-bayt teng bo‘lgan (yangi A2 Audio Manager buni SHA-256 orqali dublikat deb rad etadi).

**Necha fayl va yozuv borligi hozircha noma’lum** — bu faqat serverda `plan` ishga tushirilganda ma’lum bo‘ladi. Taxminiy son yozilmadi.

## 2. Nima “eski A2 audio” hisoblanadi, nima tegilmaydi

Fayl **faqat** quyidagi holatda tozalashga tayyor (`eligible`): unga ishora qiluvchi barcha DB qatorlari eski A2 audio (`[Archiv]` yoki `a2_material_key` vazifasi, uning treklari, yoki A2 vazifasining arxivlangan versiyasi) **va** fayl diskda mavjud.

Fayl saqlanadi (`blocked`), agar unga quyidagilardan biri ishora qilsa:

- boshqa daraja (A1, B1, B2, C1) yoki darajasi noma’lum qator;
- hozirgi (joriy nashr) A2 Hören vazifasi yoki uning treki;
- A2 Audio Manager kutubxonasidagi yozuv.

Hech bir qator ishora qilmaydigan fayllar ro‘yxatga chiqadi, lekin **A2 ga tegishli deb hisoblanmaydi va tegilmaydi** (ular boshqa daraja yoki qo‘lda qoldirilgan bo‘lishi mumkin). DB qatorlari hech bir bosqichda o‘zgartirilmaydi va o‘chirilmaydi. Video, rasm, PDF, `media_assets`, `uploads/`, Bücher, foydalanuvchi yuklagan fayllar (Sprechen yozuvlari, to‘lov cheklari) bu vositaning qamroviga umuman kirmaydi.

## 3. Bosqichlar

Vosita: `python -m app.scripts.a2_audio_cleanup` (logika `app/services/a2_audio/cleanup.py`, testlar `tests/test_a2_audio_manager.py::test_cleanup_plan_quarantine_restore_purge`).

| # | Bosqich | Nima qiladi | Qaytarib bo‘ladimi | Kim tasdiqlaydi |
|---|---|---|---|---|
| 0 | Backup | `RESTORE_CHECK=1 bash scripts/backup-course-content.sh` — DB dump + `protected_storage` tar + SHA-256 | — | operator |
| 1 | `plan` | Faqat o‘qiydi. Har bir A2 faylini, unga ishora qiluvchi qatorlarni, holatini (tayyor / saqlanadi — sababi / diskda yo‘q) va `plan id` (tayyor fayllar to‘plamining hash’i) ni chiqaradi | o‘zgarish yo‘q | — |
| 2 | Yangi A2 Audio Manager’ni tekshirish | Haqiqiy fayllar yuklanadi, darslarga bog‘lanadi, tinglab “geprüft” qilinadi; `docs/a2-sales-readiness.md` | — | admin |
| 3 | `quarantine --confirm <plan id>` | Plan o‘zgargan bo‘lsa rad etadi. Aynan rejadagi fayllarni `app/protected_storage/a2-audio-quarantine/<vaqt>-<plan id>/files/` ga nusxalaydi, SHA-256 ni tekshiradi, keyin asl faylni oladi; har fayldan keyin `manifest.json` yoziladi (to‘xtab qolsa ham holat ma’lum) | **ha** — `restore` | alohida tasdiq |
| 4 | Kuzatish | Bir necha kun: o‘quvchilar va admin panelda muammo yo‘qligi | — | admin |
| 5 | (kerak bo‘lsa) `restore --manifest …` | Fayllarni joyiga qaytaradi (mavjud faylni ustidan yozmaydi), SHA-256 tekshiradi | — | — |
| 6 | `purge --manifest … --confirm <plan id>` | **Qaytarib bo‘lmaydi.** Faqat karantindagi nusxalarni o‘chiradi; avval DB’ni qayta tekshiradi — orada biror joriy narsa faylga ishora qilsa, u saqlanadi | **yo‘q** (faqat 0-bosqich backup’i) | alohida yozma tasdiq |

Serverda (tasdiqdan keyin):

```bash
cd /opt/vizu/VIZU-Academy/backend
RESTORE_CHECK=1 bash scripts/backup-course-content.sh
.venv/bin/python -m app.scripts.a2_audio_cleanup plan --json /root/a2-cleanup-plan.json --md /root/a2-cleanup-plan.md
# natija shu hujjatning 4-bo'limiga qo'shiladi va ko'rib chiqiladi
```

## 4. Manifest (serverdagi `plan` natijasi bilan to‘ldiriladi)

| Ko‘rsatkich | Qiymat |
|---|---|
| A2 bilan bog‘liq fayllar | _server `plan` dan keyin_ |
| Tozalashga tayyor | _—_ |
| Saqlanadi (sababi bilan) | _—_ |
| DB’da bor, diskda yo‘q | _—_ |
| Eski DB qatorlari (o‘zgartirilmaydi) | _—_ |
| Hech narsa ishora qilmaydigan fayllar (tegilmaydi) | _—_ |
| `plan id` | _—_ |

Lokal test bazasidagi namunaviy chiqish formati (haqiqiy ma’lumot emas):

```
| A2-linked files | 2 |
| ready to clean (all references old A2) | 0 (0 bytes) |
| kept (blocked) | 2 |
...
| `a2-audio/a08f….m4a` | 2816 | kept: used by the A2 Audio Manager | a2_audio_manager A2/2 'A2 2.Unterricht Hören' |
```

## 5. Nima o‘zgartirilmadi

- Production bazasi, fayllari, servislari, Telegram botlar — tegilmagan.
- Eski `[Archiv]` / `a2_material_key` vazifalari, ularning savollari, `listening_audio_archives` qatorlari — o‘zgarishsiz.
- Mavjud Media Management, A1 Hören boshqaruvi, boshqa darajalar fayllari — o‘zgarishsiz.
- Umumiy media kutubxonasi (`media_assets`) — qamrovda emas.
