# A2 audio manifest

Sana: 2026-10-30. **Bu ishda haqiqiy A2 audio fayllari yuklanmadi va yaratilmadi** — ular repository’da ham, lokal muhitda ham yo‘q. Manifest qo‘lda yozilmaydi: u A2 Audio Manager’ga yuklangan haqiqiy fayllardan avtomatik hosil bo‘ladi.

## 1. Manifest qayerdan olinadi

| Qayerda | Nima |
|---|---|
| Admin → Media Management → A2 → “A2-Audio-Bibliothek · Manifest” | jonli ko‘rinish (sonlar, yetishmayotgan audio ro‘yxati) |
| `GET /api/v1/admin/media-management/a2-audio/manifest` | JSON |
| `python -m app.scripts.a2_audio_manifest [--json]` | Markdown/JSON (faqat o‘qiydi) — serverda shu faylning 4-bo‘limini yangilash uchun |

Manifest tarkibi: har bir fayl (Unterricht, tur, qism, nom, original fayl nomi, format, hajm, SHA-256, davomiyligi, tekshiruv holati, qaysi Hören vazifasiga bog‘langani), har bir joriy A2 Hören vazifasi va unda audio bor-yo‘qligi, Unterricht’siz fayllar va audio yetishmayotgan vazifalar. Darslar soni LMS’dan olinadi (qat’iy ro‘yxat emas).

## 2. Skrinshotdagi nomlanish — namuna, yakuniy ro‘yxat emas

Skrinshotda ko‘ringan fayllar va parser ularni qanday o‘qishi (`app/services/a2_audio/filename.py`, testlari `TestFilenameParser`):

| Fayl nomi (skrinshot) | Format (skrinshot) | Unterricht | Tur | Qism |
|---|---|---|---|---|
| A2 1.Unterricht Hören | M4A, ~2.23 MB | 1 | HOEREN | — |
| A2 2.Unterricht Hören | MP3, ~918 KB | 2 | HOEREN | — |
| A2 3.Unterricht Hören | MP3, ~730 KB | 3 | HOEREN | — |
| A2 4.Unterricht Text 1 / 2 / 3 | MP3 | 4 | TEXT | 1 / 2 / 3 |
| A2 5.Unterricht Hören | MP3 | 5 | HOEREN | — |
| A2 6.Unterricht | MP3 | 6 | UNTERRICHT | — |
| A2 7.Unterricht Text 1 / 2 | MP3 | 7 | TEXT | 1 / 2 |
| A2 8.Unterricht | MP3 | 8 | UNTERRICHT | — |
| A2 9.Unterricht Hören | MP3 | 9 | HOEREN | — |
| A2 10.Unterricht Teil 1–4 | M4A | 10 | UNTERRICHT | 1–4 |
| A2 11.Unterricht Teil_1–Teil_4 | M4A | 11 | UNTERRICHT | 1–4 |
| A2 12.Unterricht Teil_1–Teil_4 | M4A | 12 | UNTERRICHT | 1–4 |
| A2 13.Unterricht Teil 1–4 | M4A | 13 | UNTERRICHT | 1–4 |

Bu jadval fayllar sonini belgilamaydi. Haqiqiy son yuklashdan keyin manifestda chiqadi.

## 3. Bog‘lash qoidalari (taxmin bilan bog‘lanmaydi)

- Yuklash hech qachon faylni darsga bog‘lamaydi. Fayl nomi faqat **taklif** beradi, admin “Verknüpfung bestätigen” ni bosgandagina bog‘lanadi.
- Taklif faqat bitta vazifa aniq mos kelganda chiqadi:
  - `Teil N` → shu darsdagi content id `…-hoeren-0N` bo‘lgan joriy Hören vazifasi (10–13-darslar, kitobda Teil 1–4);
  - qismsiz `Hören` / `Unterricht` → dars bitta joriy Hören vazifasiga ega bo‘lsa, o‘sha;
  - `Text N` (4, 7-darslar) → **taklif yo‘q**: kitobda bu darslarda bitta Hören topshirig‘i bor, “Text” fayllari qaysi faoliyatga tegishli ekani aniqlanmagan — admin qaror qiladi.
- Oldingi audit ma’lumotlari (`docs/a2-book-content-audit.md`): kitobda trek raqamlari faqat 12–13-darslarda tasdiqlangan; 10-darsda Teil 3 va 4 ikkalasida “Track 7–11” (ehtimol kitob xatosi) — NEEDS_REVIEW. 13-dars uchun avval yetkazilgan fayllar 12-darsnikiga teng bo‘lgan; qayta yuklansa SHA-256 bo‘yicha `DUPLICATE` deb rad etiladi.
- Bog‘langan vazifa qoralamaga o‘tadi; admin audio va savollarni tekshirib nashr qiladi. Vazifaning oldingi audiosi `listening_audio_archives` ga o‘tadi (o‘chirilmaydi).
- Faqat joriy A2 Hören vazifalari maqsad bo‘la oladi; `[Archiv]`, `a2_material_key` va boshqa darajalar vazifalari rad etiladi.

## 4. Hozirgi holat — production (2026-10-29 22:02 UTC, A2 Audio Manager deploy qilingandan keyin)

Manba: `python -m app.scripts.a2_audio_manifest` (faqat o‘qiydi) → `/var/backups/vizu/pre-gcr-a2-20261029-224405/a2-media-manifest.md`.

| | |
|---|---|
| A2 Audio Manager kutubxonasidagi fayllar | **0** — haqiqiy fayllar hali yuklanmagan; test fayllari production’ga yuklanmadi |
| Joriy A2 Hören vazifalari | **25** |
| Audio bor (eski per-vazifa upload orqali) | **3** — 1-dars “Warum haben Sie Ihren Beruf gewählt?”, 2-dars “Sendung „Gemeinschaftskreis“ …”, 3-dars “Die Empfehlungen eines Arztes” |
| Audio yo‘q | **22** — Admin → Media Management → A2 dagi “Audio fehlt” ro‘yxati |
| Eski arxiv (`[Archiv]` / legacy) | 6 fayl, faqat eski vazifalarga tegishli — `docs/a2-media-cleanup-plan.md` 4-bo‘lim |

Fayllar yuklangandan keyin manifestni shu buyruq bilan qayta chiqarib, bu bo‘limni yangilash kerak.
