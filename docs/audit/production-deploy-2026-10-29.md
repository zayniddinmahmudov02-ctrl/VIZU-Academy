# Production deploy — Global Chat reply + A2 Audio Manager

Server `217.76.62.208`, `/opt/vizu/VIZU-Academy`. Vaqt: 2026-10-29 22:40–23:05 CET (server vaqti). Telegram botlar, ularning kodi, DB va systemd servislariga tegilmadi. Production’da test fayli yuklanmadi, test xabari yozilmadi, to‘lov yaratilmadi.

## 1. Deploydan oldingi holat (topilgan)

| | |
|---|---|
| Git | branch `main`, HEAD `a2ed438` (2026-10-30 02:01 +05). Bu commit lokal o‘zgarishlarni allaqachon o‘z ichiga olgan: 43 ta o‘zgargan faylning hammasi lokal sinalgan fayllar bilan bayt-ma-bayt bir xil (CRLF/LF normallashtirilib, SHA-256 bilan tekshirildi) |
| Working tree | `M frontend/package-lock.json`, `?? "hlarni xavfsiz saqlash"`, `?? package-lock.json` — avvaldan bor edi, tegilmadi |
| Alembic | DB `e9b4c2f7a3d1`, kod head `a6d2f9c4e8b1` (yagona head) — **migratsiya qilinmagan** |
| Backend | 22:06 CET da yangi kod bilan qayta ishga tushirilgan, lekin migratsiyasiz → **Global Chat so‘rovlari `UndefinedColumn: global_chat_messages.reply_to_id` bilan yiqilayotgan edi** (22:39 dagi xato logda). Deploy shu nosozlikni ham tuzatdi |
| Frontend | aktiv slot `.next-a` (deployment `491a453-20261029020424`); yangi kod build qilinmagan. Alohida `.next` papkasi (22:06, slot emas) — tegilmadi |
| Disk / servislar | 221 GB bo‘sh; `vizu-backend`, `vizu-frontend`, `postgresql`, `nginx` — active |

## 2. Backup — SUCCESS

`/var/backups/vizu/pre-gcr-a2-20261029-224405/` (root, 700):

| Fayl | |
|---|---|
| `db.dump` | `pg_dump -Fc`, 2 555 435 bayt, 22:44:06, TOC 895 yozuv; DB 34 MB, revision `e9b4c2f7a3d1` |
| Restore tekshiruvi | dump vaqtinchalik bazaga tiklandi (postgres superuser), **133 jadvalning barchasida qatorlar soni live bilan teng**, vaqtinchalik baza o‘chirildi |
| `lesson-listening.tar` + `.sha256` | Hören audio storage: 26 fayl, 69 MB |
| `listening-audio-metadata.csv`, `listening-audio-archives.csv` | audio ↔ vazifa bog‘lanishlari |
| `frontend-active.env`, `git-head.txt`, `requirements.txt.before` | oldingi holat |
| `SHA256SUMS` | `sha256sum -c` OK |

Tiklash: `pg_restore --clean --if-exists --no-owner -d vizu db.dump` (backend to‘xtatilgan holda); fayllar `tar -xf lesson-listening.tar -C backend/app/protected_storage`.

## 3. Dependency audit — SUCCESS (faqat requirements.txt)

| Paket | Kodda | Production venv | Qaror |
|---|---|---|---|
| `reportlab` | `services/certificate/pdf.py`, `vizu_multilevel/certificate_pdf.py` | 5.0.0 o‘rnatilgan | qo‘shildi `==5.0.0` (+ `charset-normalizer==3.4.9`, `pillow==12.3.0`) |
| `qrcode` | `services/certificate/qr.py` | 8.2 | qo‘shildi `==8.2` |
| `boto3` / `botocore` | `core/storage/r2.py` (R2 kalitlari `.env` da bor) | 1.43.53 | qo‘shildi (+ `jmespath==1.1.0`, `s3transfer==0.19.1`, `python-dateutil==2.9.0.post0`, `urllib3==2.7.0`) |
| `openpyxl` | `admin/users_router.py` (`/admin/users/export.xlsx`, lazy import) | **o‘rnatilmagan** | qo‘shilmadi — production’ga yangi paket o‘rnatish bu deploy qamrovidan tashqari; **ochiq muammo** (5-bo‘lim) |
| `httpx` | app kodida yo‘q, faqat testlar | yo‘q | qo‘shilmadi (test dependency; HTTP testlari usiz skip bo‘ladi) |

Versiyalar production’da ishlab turganlarga aynan pin qilindi; `pip install --dry-run -r requirements.txt` → **hech narsa o‘rnatilmaydi**; `pip check` → buzilish yo‘q. Lokal va server fayli bir xil (LF SHA-256 `aa2c17e8…560c`). Keyin serverda o‘zgargan modullar testlari: **122 ta, OK, 56 skip** (DB integratsiya testlari test DB URL’siz skip bo‘ladi — production bazasiga yozilmadi).

## 4. Migratsiyalar — SUCCESS

Oldin offline SQL ko‘rib chiqildi (faqat `ALTER TABLE … ADD COLUMN`, `ADD CONSTRAINT`, `CREATE TABLE`, `CREATE INDEX`, `alembic_version` yangilash).

| Revision | Natija |
|---|---|
| `e9b4c2f7a3d1 → f3a8c1d5e7b2` | `global_chat_messages.reply_to_id uuid NULL`, FK, `ix_global_chat_messages_reply_to` |
| `f3a8c1d5e7b2 → a6d2f9c4e8b1` | `a2_audio_assets` + `uq_a2_audio_assets_sha256`, `uq_a2_audio_assets_listening`, index |
| Yakuniy | `a6d2f9c4e8b1 (head)`; 10 ta mavjud chat xabari saqlangan (`reply_to_id` NULL), `a2_audio_assets` bo‘sh |

## 5. Backend — SUCCESS

`systemctl restart vizu-backend` (22:46:28): `active`, health `200 {"status":"ok","environment":"production"}`, startup’da DB/migratsiya xatosi yo‘q, restartdan keyin `Traceback/UndefinedColumn` 0.

## 6. Frontend — SUCCESS (2-urinishda)

- Server’da: `tsc --noEmit` exit 0; `npm run test:unit` 19/19; ESLint 9 error / 8 warning — avvalgidek, yangi kodda emas.
- `bash scripts/deploy-frontend.sh` (loyiha slot skripti, `npm ci` siz — dependency o‘zgarmagan):
  - **1-urinish FAIL** (22:54): `next/font/google` (Inter) fayllarini build vaqtida yuklab bo‘lmadi — Turbopack buni “Module not found … queries have exactly one entry” deb ko‘rsatdi. Skript aktiv slotni **o‘zgartirmadi** (`.next-a` xizmat qilishda davom etdi). Google CSS va woff2 server’dan 200 qaytardi, lokal reproduksiya muvaffaqiyatli → vaqtinchalik tarmoq/yuklash xatosi.
  - **2-urinish OK** (22:58): `.next-b` build (“Compiled successfully in 49s”), chiqish tekshirildi, slot almashtirildi, health OK.
- **Aktiv slot: `.next-b`, deployment `a2ed438-20261029225824`.** Rollback uchun `.next-a` (`491a453-20261029020424`) saqlanib qoldi (`.deploy/active.env.prev`).

## 7. Smoke testlar

| Tekshiruv | Natija |
|---|---|
| `https://vizu-deutsch.com/`, `/login`, `/kurse`, `/admin/media-management`; `127.0.0.1:3000/login`; backend health | hammasi 200 |
| Servislar | `vizu-backend`, `vizu-frontend`, `postgresql`, `nginx` — active |
| Anonim so‘rovlar (Global Chat GET/POST/PATCH/DELETE; A2 assets GET/POST/link/DELETE; readiness GET/POST; eski `a2-audio`) | 11/11 → 401 |
| Yangi UI aktiv bundle’da (`global-chat-reply-preview`, `global-chat-swipe`, `a2-audio-manager`, `a2-readiness`, `hoeren-audio-pending`) | bor |
| Global Chat (servis kodi, READ ONLY tranzaksiya, rollback) | sahifa 10 xabar, har birida `reply_to` maydoni, javoblar 0; `viewer_status` ishlaydi; rate limit 10/min, 1 s, dublikat 60 s, tahrir 10/min — o‘zgarmagan; aktiv mute/ban 0 |
| A2 manifest / readiness (READ ONLY) | ishlaydi — 6–8-bo‘limlar |
| Narx | `/vizu-pay/offers`: A2 99 000 (backend’dan) |
| Boshqa kurslar audiosi | `lesson-listening` 26 faylning SHA-256 ro‘yxati backup bilan **aynan bir xil**; A1 16 ta audio fayliga tegilmagan |
| Loglar | backend: faqat avvaldan bor `SUPER_ADMIN_VERIFICATION_PASSWORD is not set` ogohlantirishi; frontend: 22:53 dagi “Failed to find Server Action” — eski deploydagi ochiq brauzer sahifasidan kelgan odatiy xabar |

**Bajarilmagan (NOT RUN) va sababi:** brauzerda login qilib Reply tugmasini bosish, preview’ni bekor qilish, asl xabarga o‘tish, tahrir/o‘chirish, admin sahifasida upload — production foydalanuvchi parollari menda yo‘q; token yasash, test foydalanuvchi yaratish yoki haqiqiy chatga test xabar yozish (hamma ko‘radi) qilinmadi. Bu oqimlar lokal E2E’da sinalgan (`docs/audit/test-results.md`: 66 passed). Tavsiya: admin akkaunti bilan 2 daqiqalik qo‘lda tekshiruv (Reply → preview → X; Reply → yuborish → iqtibosni bosish; o‘z xabarini tahrirlash/o‘chirish).

## 8. Eski A2 audio arxivi — faqat PLAN (SUCCESS, o‘qish)

Plan id `18b3ca387a20`: A2 bilan bog‘liq **9 fayl**; **6 tasi** tozalashga tayyor (7.3 MB; 5 ta `[Archiv]` + 1 ta legacy `a2-l01-audio-01` vazifasi); **3 tasi saqlanadi** (joriy A2 vazifalari ishlatadi); boshqa daraja bilan umumiy 0; egasiz fayl 0; eski DB qatorlari 6. Karantin/purge/o‘chirish **bajarilmadi**. Batafsil: `docs/a2-media-cleanup-plan.md` 4-bo‘lim.

## 9. A2 sotuvi

- Indikator: **`NEEDS_CONTENT`** — kutubxonada 0 fayl, 25 Hören vazifasidan 3 tasida audio, 20 ta vazifada kalit yo‘q, qo‘lda tekshiruvlar ochiq. Narx, tavsif, darslar — OK.
- ⚠ **A2 sotuvi production’da allaqachon yoqilgan** (SUPER_ADMIN, 2026-10-28 19:32, Admin → Angebote, audit log bor), A2 `purchasable: true`, A2 buyurtmalari hozircha 0. Men yoqmadim va o‘chirmadim — biznes qarori. `docs/a2-sales-readiness.md`.

## 10. Rollback yo‘li (kerak bo‘lmadi)

- Frontend: `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && systemctl restart vizu-frontend` (`.next-a` ga qaytadi).
- Backend kodi: eski kod yangi ustunlar bilan ham ishlaydi (additive). DB downgrade **tavsiya etilmaydi**; zarur bo‘lsa avval backup’dan tiklash rejasi (2-bo‘lim).

## 11. Qolgan muammolar

1. **`openpyxl` production’da yo‘q** → `/admin/users/export.xlsx` ishlamaydi (avvaldan). Tuzatish: `pip install openpyxl==<versiya>` + requirements’ga qo‘shish — alohida qaror.
2. **`SUPER_ADMIN_VERIFICATION_PASSWORD` `.env` da yo‘q** (kamida 2026-10-20 dan beri logda) → Super Admin ikkinchi tasdiq bosqichi 503 beradi. `.env` ga tegilmadi.
3. **A2 sotuvi yoqilgan, kontent tayyor emas** (9-bo‘lim).
4. `backend/requirements.txt` o‘zgarishi server working tree’da va lokalda bor, lekin **commit qilinmagan** (lokal mashinada git yo‘q) — repoga commit/push qilish kerak, aks holda keyingi `git pull` konflikt beradi.
5. Production’da brauzer orqali qo‘lda smoke test (7-bo‘lim).
6. Eski arxiv: `quarantine --confirm 18b3ca387a20` — alohida tasdiq bilan.
