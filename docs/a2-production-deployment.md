# A2 audio processing — production deploy

Sana: 2026-10-30, server `217.76.62.208:/opt/vizu/VIZU-Academy`.

**Holat: SUCCESS.**
- 22/27 Hören vazifasi nashr qilindi.
- 5 tasi Needs review — sababi `docs/a2-publishing-report.md` da.

## Bosqichlar

| # | Bosqich | Holat | Tafsilot |
|---|---|---|---|
| 1 | Lokal tekshiruv | SUCCESS | testlar pastda |
| 2 | Revision | SUCCESS | server HEAD `bc56365`; `origin/main` da 1 commit (`e414b68` — oldingi 4-dars ishining commit’i). U o‘zgartirgan 20 faylning hammasi server working tree bilan bayt-ma-bayt bir xil edi; alembic `b8e3d1a7c5f2` |
| 3 | Backup | SUCCESS | `/var/backups/vizu/pre-a2proc-20261030-022802/`: `db.dump` 2 560 186 B (vaqtinchalik bazaga tiklab tekshirildi, 134/134 jadval mos), `lesson-listening.tar` (49 fayl) + `lesson-listening.sha256`, metadata CSV, `SHA256SUMS` OK |
| 4 | Dependency | SUCCESS | yangi paket kerak emas; `requirements.txt` o‘zgarmadi. Transkripsiya oflayn — serverda Whisper ishlatilmaydi |
| 5 | Kod | SUCCESS | `git pull --ff-only` → HEAD **`e414b68`**; keyin 17 fayl LF formatida staging’dan qo‘yildi (tar SHA-256 tekshirildi, har bir mavjud fayl avval `HEAD` bilan bir xil ekani tekshirildi). Keyinroq 2 fayl yangilandi (Text slot audio’sini kutubxonaga qabul qilish, + test) |
| 6 | Migratsiya | SUCCESS | `b8e3d1a7c5f2 → c4f7a9e2d6b3` (`a2_audio_transcripts`, faqat yangi jadval); SQL oldin offline ko‘rib chiqildi |
| 7 | Backend | SUCCESS | restart, health 200 |
| 8 | Qayta ishlash | SUCCESS | `python -m app.scripts.a2_audio_processing apply --confirm <plan id> --audio-dir /root/a2-book-audio`. 1-yurish (`bedcb334b15b`): 19 vazifa nashr; Text 1–3 nashr bo‘lmadi — audio oddiy Hören upload’i bilan yuklangan, A2 kutubxonasida yozuvi yo‘q edi. Tuzatish deploy qilinib, 2-yurish (`0ee4ef66e2cd`): Text 1–3 kutubxonaga qabul qilindi va nashr qilindi; qolganlari o‘zgarmadi (idempotent). Hisobotlar: `…/a2-audio-processing-report{,-2}.json`, loglar: `…/a2-audio-processing-apply{,-2}.log` |
| 9 | Frontend | SUCCESS | `deploy-frontend.sh`: faol slot **`.next-b`** (deployment `e414b68-20261030024115`); `.next-a` rollback uchun saqlangan |
| 10 | Loglar | SUCCESS | backend restart’dan keyin va frontend deploy’dan keyin xato 0; ma’lum ogohlantirish `SUPER_ADMIN_VERIFICATION_PASSWORD is not set` (avvaldan bor) |
| 11 | O‘quvchi ko‘rinishida tekshiruv | SUCCESS (server tomonda) | pastda |

## O‘quvchi ko‘rinishidagi tekshiruv (production ma’lumoti, faqat GET, hech narsa yozilmadi)

O‘quvchi endpoint funksiyalari (`get_hoeren`, audio stream) va dars eshigi (`require_lesson_access`) production bazasida chaqirildi. 2–13-darslar xodim sifatida tekshirildi — sotib olgan o‘quvchi bilan bir xil endpoint; A2 sotib olgan o‘quvchi hozircha yo‘q.

| Dars | Hören vazifalar | Ijro etiladigan audio | Natija |
|---|---|---|---|
| 1, 2, 3, 5, 8, 9 | 1 | 1 | transkript urinishdan keyin, kalit yuborilmaydi |
| 4 | 3 (Text 1–3) | 3 | transkript darhol |
| 6 | 0 | — | Hören bo‘limi bo‘sh (Needs review) |
| 7 | 1 | **2** (Text 1 + Text 2) | ✓ |
| 10, 11, 12 | 4 | 4 | ✓ |
| 13 | 0 | — | bo‘sh (noto‘g‘ri audio) |

Jami: 22 vazifa, 23 audio fayl. Har biri `Cache-Control: private, no-store` bilan uzatiladi.

**Kirish:** A2 sotib olmagan o‘quvchi uchun 1-dars 200 (bepul preview), 2 va 13-darslar 403. Tizimga kirmagan foydalanuvchiga quyidagilar 401:
- `/a2-audio/processing`;
- `/a2-readiness`;
- `/global-chat/messages`.

**Sahifalar:** `/`, `/login`, `/kurse`, `/admin/media-management`, `/admin/media-management/a2/lesson-4/hoeren` — 200. Yangi admin panel jonli bundle’da.

**Boshqa ma’lumotlarga ta’sir:**
- A1 audio qatorlari 16/16, B1–C1 0/0 — o‘zgarmagan;
- A2 dan tashqari audio metadata farqi yo‘q;
- storage’dan hech narsa o‘chmagan (49 → 50: 7-dars „Text 2“ treki);
- o‘quvchi urinishlari / buyurtmalar / foydalanuvchilar — 337 / 15 / 147, skript ularga tegmaydi.

**Telegram botlar:** `nano_bot`, `telegram-cours2026` — active, tegilmadi.

**Bajarilmadi:** production’da brauzer orqali haqiqiy o‘quvchi login bilan tekshirish. Production parollari yo‘q; token yasalmadi, test foydalanuvchi yoki soxta to‘lov yaratilmadi. Bu oqim lokal E2E’da (real kitob kontenti va audio bilan) o‘tdi.

## Testlar

| Tekshiruv | Natija |
|---|---|
| Backend, lokal, to‘liq to‘plam (PostgreSQL, migratsiya testlari bilan) | **917 passed, 17 skipped**, 13 082 subtest |
| Yangi `test_a2_audio_processing` | 9/9: transkript saqlanishi, SHA-256 bo‘yicha bir marta, moslashtirish / MISMATCH, kalit va Lösung, nashr qoidasi, almashtirilgan fayl, kitob transkripti saqlanishi, trek qo‘shish, Text slot (kutubxona orqali va oddiy upload’dan qabul), readiness, kirish huquqi, baholash, transkript urinishdan keyin, progress |
| Migratsiya `c4f7a9e2d6b3` upgrade → downgrade → upgrade | OK (+ `b8e3d1a7c5f2`, `f3a8c1d5e7b2`) |
| Server, tegishli modullar (DB testlari serverda skip) | Ran 144, OK |
| TypeScript | 0 xato |
| ESLint, yangi / o‘zgargan fayllar | 0 |
| ESLint, butun frontend | 9 error / 10 warning — hammasi o‘zgartirilmagan fayllarda (avvaldan bor) |
| Frontend unit | 19/19 |
| Build | lokal `.next-e2e` OK, production slot OK |
| E2E `a2-audio-processing.spec.ts` (Chrome, desktop + Pixel 7, real kitob kontenti + audio, lokal stend) | **5 passed, 1 skipped** (urinish ataylab faqat desktop’da). 1–13-darslar ochiladi; har birida faqat nashr qilingan Hören; player’lar (7-dars — 2); 3-dars testi 100 %; natija va transkript qayta yuklashdan keyin saqlanadi; mobil’da gorizontal scroll yo‘q; admin panel 22/27, 13-dars sababi, transkript, savollar |
| Lokal repetitsiya | kitob nashri importi + barcha audio → `plan`/`apply` → 22/27, natija production bilan bir xil; qayta `plan` — 0 o‘zgarish |

## Rollback

| Nima | Qanday |
|---|---|
| Frontend | `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && systemctl restart vizu-frontend` |
| Nashr | Admin → vazifa → „Entwurf“ (yoki SQL: `update listenings set is_published=false where id=…`) |
| Kalit / savollar | `db.dump` dan; har bir o‘zgarishning „before/after“ — audit log `a2_audio_processed` |
| 7-dars „Text 2“ | Media Management → vazifa → trekni o‘chirish |
| Text 1–3 kutubxona yozuvlari | A2 Audio Manager → „unlink“ → yozuvni o‘chirish (faylni saqlab) |
| Migratsiya | avtomatik downgrade qilinmaydi; kerak bo‘lsa `alembic downgrade b8e3d1a7c5f2` (faqat jadvalni o‘chiradi) |
| Hammasi | servislarni to‘xtatib `pg_restore --clean --if-exists --no-owner -d vizu db.dump` |

## Qolgan muammolar

1. **13-dars Hören:** to‘g‘ri audio yo‘q — serverda ham, manba papkada ham fayllar 12-darsning nusxasi. To‘g‘ri fayllar yuklangach, `a2_audio_processing` (transkripsiya + kalit) qayta bajariladi.
2. **6-dars Hören:** 12 ochiq savol. Kalit variantlari yozilgan, lekin „Prüfung nötig“. Admin LMS → Lösung’da tasdiqlaydi yoki savollarni Multiple Choice’ga o‘tkazadi.
3. **4-dars Text 1–3:** savollar yo‘q (kitob savollari oldingi vazifa bilan backup’da).
4. **Transkriptdagi 7 ta noaniq joy** `[unverständlich]` — tinglab tekshirish kerak (`docs/a2-transcription-report.md`).
5. **Git:** serverdagi o‘zgarishlar commit qilinmagan (lokal mashinada git yo‘q) — repoga commit/push kerak.
6. **Avvaldan bor:**
   - A2 sotuvi yoqilgan, lekin indikator `NEEDS_CONTENT`;
   - `SUPER_ADMIN_VERIFICATION_PASSWORD` yo‘q;
   - `openpyxl` yo‘q.
