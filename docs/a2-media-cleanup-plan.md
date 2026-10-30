# Eski A2 audio arxivini tozalash rejasi

Sana: 2026-10-30. Holat: **vositalar production’ga deploy qilingan; production’da faqat `plan` (o‘qish) bajarilgan — 4-bo‘lim. Hech narsa ko‘chirilmagan va o‘chirilmagan.** Har bir keyingi bosqich alohida tasdiq bilan bajariladi.

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

Production’dagi aniq sonlar — 4-bo‘limda (2026-10-29 dagi `plan`).

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

> **Yangilanish (2026-10-30 00:22 UTC):** A2 4. Unterricht’dagi ikkala „Familie Mannsberg“ vazifasi va ularning audiolari (shu jumladan quyidagi `f8c9ac4a….mp3`) backup bilan olib tashlandi — `docs/a2-lesson-4-hoeren-update.md`. Shu sababli pastdagi plan id `18b3ca387a20` endi yaroqsiz. Yangi `plan` (faqat o‘qish): A2 bilan bog‘liq 29 fayl, tozalashga tayyor **5** (7 005 050 bayt), saqlanadi 24, umumiy/yo‘q/ishorasiz 0, **plan id `552c5c27371e`** (`/var/backups/vizu/pre-a2l4-20261030-011331/a2-cleanup-plan.{json,md}`). Karantin hali bajarilmagan.

## 4. Manifest — production `plan` natijasi (2026-10-29 22:02 UTC, faqat o‘qish)

Buyruq: `python -m app.scripts.a2_audio_cleanup plan --json … --md …`. Natija fayllari: `/var/backups/vizu/pre-gcr-a2-20261029-224405/a2-cleanup-plan.{json,md}`. `app/protected_storage` dagi fayllar soni plan’dan oldin va keyin: 178 / 178.

| Ko‘rsatkich | Qiymat |
|---|---|
| A2 bilan bog‘liq fayllar | **9** |
| Tozalashga tayyor (barcha ishoralar eski A2) | **6** (7 303 655 bayt) |
| Saqlanadi | **3** — joriy A2 Hören vazifasi ishlatadi |
| Boshqa daraja bilan umumiy | 0 |
| DB’da bor, diskda yo‘q | 0 |
| Eski DB qatorlari (o‘zgartirilmaydi) | 6 (`task_audio` 6, `task_track` 0, `archived_version` 0) |
| Hech narsa ishora qilmaydigan fayllar | 0 |
| `plan id` | `18b3ca387a20` |

| Fayl | Hajm | Holat | Ishora |
|---|---|---|---|
| `38e4f28a2cb44c1cb72ce8c1cd423c29.mp3` | 627 069 | tayyor | `[Archiv] Hören: Steigende Mieten in Deutschland!` (A2/5) |
| `42acd4c7ab6a43d2a52167e9cd5a8c95.m4a` | 2 345 068 | tayyor | `[Archiv] A2 1.Unterricht Hören`, key `a2-l01-audio-01` (A2/1) |
| `473564fa4a104d358c1b574f9eacbc39.m4a` | 2 345 068 | tayyor | `[Archiv] Hören: Warum haben Sie Ihren Beruf gewählt?` (A2/1) |
| `900fe1ccb29c4b84877291b439fd52a3.mp3` | 747 741 | tayyor | `[Archiv] Hören: Die Empfehlungen eines Arztes` (A2/3) |
| `e80e1092cd47415b937ac684fe085a5b.mp3` | 940 104 | tayyor | `[Archiv] Hören: Sendung „Gemeinschaftskreis“ …` (A2/2) |
| `f8c9ac4a9a504a479e1cf7dd41e76782.mp3` | 298 605 | tayyor | `[Archiv] Hören: Familie Mannsberg` (A2/4) |
| `c99dbc8947c74b20828ee611927161c9.m4a` | 2 345 068 | **saqlanadi** | joriy `Hören: Warum haben Sie Ihren Beruf gewählt?` (A2/1) |
| `8b6dda12f90d4e008997584421658a77.mp3` | 940 104 | **saqlanadi** | joriy `Hören: Sendung „Gemeinschaftskreis“ …` (A2/2) |
| `138b761dd0a041d3be7422c4dc3a2aa9.mp3` | 747 741 | **saqlanadi** | joriy `Hören: Die Empfehlungen eines Arztes` (A2/3) |

DB tomonda (A2 darslari): 25 ta `[Archiv]` Hören vazifasi (5 tasida audio), 25 ta joriy vazifa (3 tasida audio), 1 ta legacy `a2_material_key` vazifasi (audio bilan); arxivlangan versiyalar 0, qo‘shimcha treklar 0. A1 ning 16 ta audio fayli qamrovda emas va tegilmagan.

Kuzatuv: 1–3-darslarda `[Archiv]` va joriy vazifa fayllari bir xil hajmda — birinchi nashrdan nusxa olingan bo‘lishi mumkin. Joriy vazifalar o‘z nusxasini ishlatgani uchun `[Archiv]` nusxalarini karantinga olish ularga ta’sir qilmaydi (plan buni ishoralar bo‘yicha tekshirgan).

**Karantin, purge va DB o‘zgarishi bajarilmagan.** Keyingi qadam (alohida tasdiq): `quarantine --confirm 18b3ca387a20` (plan o‘zgargan bo‘lsa, buyruq o‘zi rad etadi).

## 5. Nima o‘zgartirilmadi

- Production bazasi, fayllari, servislari, Telegram botlar — tegilmagan.
- Eski `[Archiv]` / `a2_material_key` vazifalari, ularning savollari, `listening_audio_archives` qatorlari — o‘zgarishsiz.
- Mavjud Media Management, A1 Hören boshqaruvi, boshqa darajalar fayllari — o‘zgarishsiz.
- Umumiy media kutubxonasi (`media_assets`) — qamrovda emas.
