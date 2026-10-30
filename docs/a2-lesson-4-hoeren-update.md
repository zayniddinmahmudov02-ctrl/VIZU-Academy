# A2 · 4. Unterricht · Hören — „Familie Mannsberg“ o‘rniga Text 1, Text 2, Text 3

Sana: 2026-10-30. Holat: **production’ga deploy qilingan (SUCCESS).** Text 1–3 tuzilmasi va Media Management sahifasi ishlaydi. **Haqiqiy Text 1–3 audio fayllari hali yuklanmagan**, shuning uchun uchala Text ham nofaol va o‘quvchilarga ko‘rinmaydi (2-bo‘lim oxiri).

## 1. Eski „Familie Mannsberg“ topshirig‘i

### Nima topildi (production, 2026-10-30 01:12 CET)

Faqat A2 → 4. Unterricht’da 2 ta Hören vazifasi bor edi. Boshqa darslarda ham, boshqa kurslarda ham „Mannsberg“ nomli vazifa yo‘q edi.

| Vazifa | content_id | Holat | Savollar / variantlar | Audio | O‘quvchi urinishlari | Kalit tekshiruvlari |
|---|---|---|---|---|---|---|
| `[Archiv] Hören: Familie Mannsberg` (1-nashr) | `vizu-a2-l04-hoeren-01` | qoralama | 12 / 36 (kalit bor) | `f8c9ac4a….mp3`, „A2 4.Unterricht Text 1.mp3“, 298 605 B | 0 | 0 |
| `Hören: Familie Mannsberg` (kitob nashri) | `vizu-a2buch-l04-hoeren-01` | qoralama | 12 / 36 (kalitsiz) | `f3b66c17….mp3`, „A2 4.Unterricht Text 1.mp3“, 298 605 B (2026-10-29 23:59 da yuklangan) | 0 | 0 |

Ikkala audio fayl bayt-ma-bayt bir xil (SHA-256 `032a9dacdf02284f…`). Ularga boshqa hech qanday vazifa, trek, arxiv versiyasi yoki A2 kutubxona yozuvi ishora qilmagan. Qo‘shimcha treklar, arxivlangan versiyalar va A2 kutubxona bog‘lanishlari bo‘lmagan.

### Nima qilindi

Ishni `python -m app.scripts.a2_lesson4_hoeren` bajardi: avval `plan` (faqat o‘qiydi, plan id `ff74f1106666`), keyin `apply --confirm ff74f1106666`.

1. **Backup.** Skriptdan oldin to‘liq backup olindi: `/var/backups/vizu/pre-a2l4-20261030-011331/`.
   - `db.dump` vaqtinchalik bazaga tiklab tekshirildi: 134 jadvalda qator soni mos.
   - `lesson-listening.tar` (48 fayl) va `SHA256SUMS` ham shu yerda.

   Skript ham o‘z backup’ini yozdi: `…/legacy/a2-l04-hoeren-20261030-001829-749811-ff74f1106666/`.
   - `tasks.json` — vazifa qatorlari, savollar, variantlar (`is_correct` bilan) va konfiguratsiya.
   - `files/` — ikkala audio, SHA-256 bilan tekshirilgan.
   - `files.json`, `report.json`.
2. **Ikkala vazifa o‘chirildi.** O‘quvchi tarixi yo‘q edi, shuning uchun savollar va variantlar cascade bilan ketdi. Qoida: o‘quvchi urinishi yoki kalit tekshiruvi bor vazifa o‘chirilmaydi. U faqat arxivlanadi (`[Archiv]`, nashrsiz), tarix saqlanadi — bu testda tekshirilgan.
3. **Ikkala audio fayl o‘chirildi**, chunki boshqa hech narsa ularni ishlatmagan; nusxalari backup’da. Boshqa joyda ishlatilgan fayl saqlanadi — bu ham testda tekshirilgan.
4. **Audit log’ga 4 ta yozuv tushdi:**
   - `a2_l04_hoeren_slots_created`;
   - `a2_l04_legacy_task_deleted` (×2);
   - `a2_l04_legacy_audio_deleted`.
5. **Qayta import eski vazifani qaytarmaydi.** Kitob nashri importidan bu vazifa chiqarildi (`vizu_deutsch_a2_buch.DROP` ga `vizu-a2-l04-hoeren-01`), `app/data/vizu_deutsch_a2_buch/unterricht_04.json` qayta qurildi. Faylda faqat shu bitta element o‘chdi, qolgan 12 dars fayli o‘zgarmadi.

Birinchi nashr manbasi (`app/scripts/vizu_deutsch_a2/`, `a2_keys_data.py`) arxiv sifatida o‘zgarishsiz qoldi. Uning content id’lari (`vizu-a2-…`) importda arxiv deb hisoblanadi.

**Diqqat:** o‘chirilgan „A2 4.Unterricht Text 1.mp3“ 29-oktabr kechasi Mannsberg vazifasiga yuklangan edi. U yangi Text 1 uchun mo‘ljallangan bo‘lishi mumkin. Taxmin bilan bog‘lamadim. Nusxasi: `…/legacy/a2-l04-hoeren-…/files/f3b66c17d11843f1b16a289cbf0d0fe7.mp3`. To‘g‘ri fayl bo‘lsa, uni Text 1 ga yuklash kerak.

### Natija

- Bazada „Mannsberg“ nomli Hören vazifasi yo‘q: 0 qator.
- Storage’da 48 fayl edi, endi 46 ta: faqat shu ikkitasi olib tashlandi.
- Audio metadata (backup bilan saralab solishtirildi): faqat shu 2 qator ketdi; A1 16/16, boshqa A2 vazifalari o‘zgarmagan.
- Eski A2 arxivini tozalash rejasi (`docs/a2-media-cleanup-plan.md`) endi 5 ta faylni ko‘rsatadi, plan id `552c5c27371e`. Karantin bajarilmadi.

## 2. Yangi struktura

```
A2
└── 4. Unterricht
    └── Hören
        ├── Text 1   (listenings, task_key a2-u04-hoeren-text-1, „Hören: Text 1“)
        │   └── Audio  (A2 Audio Manager yozuvi, Unterricht 4 · TEXT · Teil 1)
        ├── Text 2   (… text-2)
        │   └── Audio
        └── Text 3   (… text-3)
            └── Audio
```

- Har bir Text — oddiy Hören vazifasi (`listenings` qatori). Unga barqaror `task_key` va o‘z audiosi berilgan; savollar hozircha yo‘q.
- **Savollar uchun tayyor.** Savollar, javob variantlari va kalitlar keyinroq mavjud Hören savol muharriri orqali qo‘shiladi (`listening_questions` / `listening_options`). Bu uchun yangi jadval kerak emas. Savollar o‘zimdan yaratilmadi.
- **Tartib.** Uchala Text darsda eski vazifaning o‘rnida turadi (`order_index` 2, 3, 4).

**Holat:** uchala Text yaratilgan, nofaol, audiosiz. O‘quvchilarga hech biri ko‘rinmaydi.

## 3. Media Management

**Yo‘l:** Admin Panel → Media Management → Niveau A2 → „A2 → 4. Unterricht → Hören: Text 1, Text 2, Text 3 verwalten“. Manzil: `/admin/media-management/a2/lesson-4/hoeren`.

Har bir Text alohida kartada:

| Talab | Qanday |
|---|---|
| Audio yuklash, MP3/M4A | „Hochladen“. Brauzer kengaytma va 100 MB chegarani tekshiradi. Server A2 Audio Manager qoidalari bilan tekshiradi: kengaytma, e’lon qilingan MIME va faylning birinchi baytlari bir xil formatni ko‘rsatishi kerak |
| Fayl nomi, hajmi, formati | kartada ko‘rinadi; original nom saqlanadi, serverda tasodifiy nom |
| Davomiylik | brauzer fayl metadata’sidan o‘qiydi va serverga yuboradi; o‘qib bo‘lmasa „—“ |
| Preview / tinglash | „Anhören“ — faqat admin uchun, Bearer bilan blob; ommaviy URL yo‘q |
| Qayta yuklash | „Ersetzen“. Faqat shu Text o‘zgaradi. Oldingi fayl A2 kutubxonasida bog‘lanmagan holda qoladi, o‘chirilmaydi |
| O‘chirish | 🗑 + tasdiq. Text audiosiz va nofaol qoladi. Kutubxona yozuvi o‘chadi; fayl boshqa joyda ishlatilmasa, u ham o‘chadi |
| Upload progress | foizli progress bar |
| Upload holati | Nicht hochgeladen / Wird hochgeladen / Hochgeladen / Fehler (= Yuklanmagan / Yuklanmoqda / Yuklandi / Xatolik) |
| Audio tekshirildi | „Geprüft“ yoki „Problem“ (izoh bilan). Muammoli audio Text’ni darhol nofaol qiladi |
| Aktiv / deaktiv | „Aktivieren“ / „Deaktivieren“. Faollashtirish faqat audio serverda bo‘lsa va tekshirilgan bo‘lsa mumkin; yangi audio Text’ni nofaol qiladi |
| Dublikat | Bir xil mazmun (SHA-256) boshqa Text’da bo‘lsa, rad etiladi va qaysi Text ekani aytiladi. Xuddi shu Text’ga qayta yuklansa — „SAME_FILE“. Kutubxonada bog‘lanmagan nusxa bo‘lsa, ikkinchi nusxa saqlanmaydi, mavjud yozuv qayta ishlatiladi |

Har bir Text mustaqil: boshqasining audiosi, holati va tekshiruvi o‘zgarmaydi. Har bir o‘zgarish audit log’ga yoziladi (`a2_l04_hoeren_*`).

A2 Audio Manager’da „A2 4.Unterricht Text N“ nomli fayl endi Text N vazifasini **taklif** qiladi. Bog‘lash baribir faqat admin tasdig‘i bilan. 7-darsdagi Text fayllari uchun taklif yo‘q.

**Endpointlar** (`/api/v1/admin/media-management/a2/lesson-4/hoeren`):

| Endpoint | Ruxsat |
|---|---|
| `GET` umumiy holat | admin panel |
| `POST /setup` — yetishmayotgan Text’larni yaratish | content editor |
| `POST /{1..3}/audio` — yuklash | content editor |
| `GET /{1..3}/audio` — preview | admin panel |
| `DELETE /{1..3}/audio` | content editor |
| `POST /{1..3}/verify` | content editor |
| `POST /{1..3}/active` | content editor |

## 4. O‘quvchi tomoni

- Text 1, Text 2, Text 3 — Hören bo‘limida alohida kartalar, har birida o‘z player’i. Mavjud `listening-section` o‘zgartirilmadi.
- Faqat aktiv va audiosi serverda bor Text ko‘rinadi. Audiosiz Text uchun bo‘sh player chiqmaydi.
- Audio mavjud `GET /lesson-skills/{lesson}/hoeren/{id}/audio` orqali beriladi: `require_lesson_access` + nashr qilingan vazifa, `Cache-Control: private, no-store`.
  - 4-dars pullik: A2 sotib olmagan o‘quvchi 403 oladi, kirmagan foydalanuvchi 401.
- Savolsiz Text’lar mavjud LMS qoidasiga ko‘ra Hören natijasiga va dars natijasiga kirmaydi (`results._hoeren`). Ular faqat tinglash uchun. Savollar qo‘shilgach, oddiy Hören testi va natija sifatida hisoblanadi.
- Mobil va desktop ko‘rinishlari E2E’da tekshirildi: gorizontal scroll yo‘q.

## 5. O‘zgartirilgan fayllar

**Backend:**
- `alembic/versions/b8e3d1a7c5f2_listening_task_key.py` (yangi)
- `app/models/listening.py` — `task_key` va unique partial index
- `app/services/a2_audio/lesson4_hoeren.py` (yangi) — Text 1–3, eski vazifani olib tashlash
- `app/services/a2_audio/assets.py` — „Text N“ taklifi
- `app/api/admin/media_management_router.py` — 7 endpoint
- `app/scripts/a2_lesson4_hoeren.py` (yangi) — `plan` / `apply`
- `app/scripts/vizu_deutsch_a2_buch/__init__.py` — `DROP`
- `app/data/vizu_deutsch_a2_buch/unterricht_04.json` (qayta qurilgan)

**Backend testlari:**
- `tests/test_a2_lesson4_hoeren.py` (yangi)
- `tests/test_listening_task_key_migration.py` (yangi)
- `tests/test_a2_audio_manager.py`
- `tests/test_a2_buch_edition.py`

**Frontend:**
- `src/app/admin/media-management/a2/lesson-4/hoeren/page.tsx` (yangi)
- `src/features/admin/components/media-management/a2-lesson4-hoeren-client.tsx` (yangi)
- `src/features/admin/components/media-management/media-management-client.tsx` — A2 havolasi
- `src/features/admin/services/media-management-service.ts`

**E2E:** `e2e/tests/a2-lesson4-hoeren.spec.ts` (yangi). Lokal seed: `D:\vz_tmp\work\a2l4_e2e_seed.py` (faqat test bazasi).

Mavjud umumiy media tizimi qayta yozilmadi.

## 6. Migratsiya

`b8e3d1a7c5f2` (down_revision `a6d2f9c4e8b1`) — faqat qo‘shadi:

```sql
ALTER TABLE listenings ADD COLUMN task_key VARCHAR(80);
CREATE UNIQUE INDEX uq_listenings_task_key ON listenings (task_key) WHERE task_key IS NOT NULL;
```

Downgrade indeks va ustunni o‘chiradi; vazifalar qoladi.

Tekshiruvlar:
- **Lokal upgrade → downgrade → upgrade:** `test_listening_task_key_migration`, alohida test bazasida. Vazifalar saqlanadi; unique faqat NULL bo‘lmagan qiymatlarga.
- **Production:**
  - SQL avval offline ko‘rib chiqildi, keyin `a6d2f9c4e8b1 → b8e3d1a7c5f2` qo‘llandi;
  - `listenings`: 67 → 67;
  - eski vazifani olib tashlash va Text’larni yaratishdan keyin 68 (−2 +3).

## 7. Test natijalari

| Tekshiruv | Natija |
|---|---|
| Backend, lokal, to‘liq (PostgreSQL test bazasi, migratsiya testlari bilan) | **907 passed, 17 skipped**, 13 031 subtest |
| Yangi testlar `test_a2_lesson4_hoeren` | 5/5 |
| Migratsiya testlari (`task_key`, Global Chat reply) | 2/2 |
| Backend, serverda (tegishli modullar; DB testlari serverda skip) | Ran 124, OK (skipped 61) |
| TypeScript `tsc --noEmit` | 0 xato |
| ESLint, yangi/o‘zgargan fayllar | 0 |
| ESLint, butun frontend | 9 error / 10 warning — hammasi o‘zgartirilmagan fayllarda (avvaldan bor) |
| Frontend unit | 19/19 |
| Frontend build | lokal `.next-e2e`: OK. Production slot build: OK |
| E2E (Playwright, Chrome, desktop + Pixel 7) `a2-lesson4-hoeren.spec.ts` | **7 passed, 1 skipped** (upload oqimi ataylab faqat desktop’da) |

Talab qilingan tekshiruvlar qaysi testda:

1. **Mannsberg o‘quvchiga ko‘rinmaydi:** backend `test_legacy_removal…`, `test_students_see_only_active_texts…`; E2E lesson page.
2. **Eski audio va bog‘lanishlar to‘g‘ri ajratilgan:** `test_legacy_removal…` — o‘chirish yoki arxivlash; umumiy fayl saqlanadi; backup; audit; boshqa dars va daraja tegilmaydi.
3–5. **Text 1/2/3 upload:** `test_each_text_uploads…`; E2E.
6. **Alohida almashtirish:** `test_each_text_uploads…`; E2E (Text 3 almashtirilganda Text 1/2 o‘zgarmaydi).
7. **MP3/M4A validatsiyasi:** `test_format_validation…` (WAV, mazmun/kengaytma mos emas, audio emas, MIME); E2E.
8. **Dublikat:** `test_format_validation…`; E2E.
9. **Player:** E2E — admin preview, o‘quvchi sahifasida `<audio>`; backend stream 200, `private, no-store`.
10. **Ruxsatsiz foydalanuvchi:** backend HTTP — o‘quvchi 403, anonim 401; admin endpointlar o‘quvchiga 403. E2E va production smoke — anonim 401.
11. **A2 boshqa darslari:** backend test; production — saralangan metadata solishtirish.
12. **A1–C1:** backend test (A1 vazifasi tegilmagan); production — A1 audio 16/16, storage solishtirish.
13. **Global Chat va boshqa LMS:** to‘liq backend to‘plami; production — `/api/v1/global-chat/messages` 401, health 200, loglarda xato 0.
14. **Mobil/desktop:** E2E — ikkala qurilmada gorizontal scroll yo‘q, skrinshotlar ko‘rib chiqildi.

## 8. Production deploy

| Bosqich | Holat | Tafsilot |
|---|---|---|
| Oldindan tekshirish | SUCCESS | HEAD `a2ed438`, alembic `a6d2f9c4e8b1`, servislar active. `origin/main` da 1 yangi commit (`bc56365`: hujjatlar va `requirements.txt`) bor edi; men o‘zgartirgan kod fayllariga tegmaydi |
| Backup | SUCCESS | `/var/backups/vizu/pre-a2l4-20261030-011331/`: `db.dump` (2 562 895 B, tiklash tekshiruvi 134/134), `lesson-listening.tar` (48 fayl), `SHA256SUMS` OK |
| Kod | SUCCESS | 1. Serverdagi `requirements.txt` `origin/main` bilan bir xil mazmunda edi (tekshirildi) → `git checkout` → `git pull --ff-only` → HEAD `bc56365`. 2. 17 fayl LF formatida staging’ga yuklandi (tar SHA-256 tekshirildi). 3. Har bir mavjud fayl serverda `HEAD` bilan bir xil ekani tekshirilib, keyin almashtirildi. Paketlar o‘zgarmadi |
| Testlar (server) | SUCCESS | Ran 124, OK |
| Migratsiya | SUCCESS | `a6d2f9c4e8b1 → b8e3d1a7c5f2` |
| Backend | SUCCESS | restart, health 200 |
| Eski vazifa olib tashlandi, Text 1–3 yaratildi | SUCCESS | 1-bo‘lim |
| Frontend | SUCCESS | `deploy-frontend.sh`: faol slot `.next-a` (deployment `bc56365-20261030011900`), `.next-b` rollback uchun saqlangan |
| Smoke | SUCCESS | sahifalar 200; 8 ta yangi/eski endpoint anonimga 401; yangi UI jonli bundle’da; servis tekshiruvlari — 2-, 4-bo‘limlar; Global Chat 401/health 200; backend va frontend xato 0 |
| Telegram botlar | tegilmadi | `nano_bot`, `telegram-cours2026` — active |

**Tizimga kirgan brauzer tekshiruvi production’da bajarilmadi.** Production parollari yo‘q, token yasalmadi, sun’iy audio production’ga yuklanmadi. Bu oqimlar lokal E2E’da o‘tdi.

**Rollback:**
- **Frontend:** `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && systemctl restart vizu-frontend`.
- **Backend kodi:** `git checkout -- <fayllar>` va yangi fayllarni o‘chirish, keyin `systemctl restart vizu-backend`. Yangi kodsiz `task_key` ustuni zararsiz.
- **Migratsiya:** avtomatik downgrade qilinmaydi. Kerak bo‘lsa — `alembic downgrade a6d2f9c4e8b1`.
- **Eski vazifani qaytarish:** `db.dump` yoki `legacy/…/tasks.json` + `files/`.

**Git:** o‘zgarishlar serverda working tree’da, commit qilinmagan (lokal mashinada git yo‘q). Repoga commit/push kerak, aks holda keyingi `git pull` to‘xtaydi.

## 9. Audio fayllar

**Text 1, Text 2, Text 3 uchun haqiqiy audio hali yuklanmagan.** Test fayllari production’ga yuklanmadi.

Keyingi qadamlar:
1. Har bir Text’ga audioni yuklash (Media Management → A2 → 4. Unterricht → Hören).
2. Tinglab, „Geprüft“ deb belgilash.
3. „Aktivieren“ — shundan keyin o‘quvchilar ko‘radi.
4. Kerak bo‘lsa, Hören muharririda har bir Text’ga savol va kalit qo‘shish.

A2 sotuvga tayyorlik indikatori: `NEEDS_CONTENT`. 27 Hören vazifasidan 24 tasida audio bor; yetishmayotganlari — shu uchta Text. A2 sotuvi production’da yoqilgan holda qolgan; men uni o‘zgartirmadim.
