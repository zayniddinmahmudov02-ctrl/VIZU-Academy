# A2 audio manifest — qayta ishlash (1–13-darslar)

Sana: 2026-10-30.

**Manba:**
- production inventari: 2026-10-30 01:38 CET;
- qayta ishlash hisobotlari: `/var/backups/vizu/pre-a2proc-20261030-022802/a2-audio-processing-report{,-2}.json`;
- admin panel: Media Management → A2 → „A2 Audio-Verarbeitung“ (jonli holat).

## Qisqacha

| | |
|---|---|
| Joriy A2 Hören vazifalari (1–13) | **27** (4-darsda Text 1–3 = 3 ta vazifa) |
| Audio fayllar | **28**: 27 ta asosiy audio + 7-dars „Text 2“ treki |
| Bugun yuklangan | **27**, 2026-10-29 23:58 – 2026-10-30 01:34. 7-dars „Text 2“ yuklanmagan edi — men kitob faylidan qo‘shdim (pastda) |
| Turli audio mazmunlari (SHA-256) | **24**: 13-darsning 4 fayli 12-darsnikiga bayt-ma-bayt teng |
| Transkripsiya qilingan | **28/28** fayl, **24/24** mazmun. Bir xil mazmun ikki marta transkripsiya qilinmadi |
| Topshiriqqa mos (MATCHED) | 23 vazifa |
| Noto‘g‘ri audio (MISMATCH) | 4 vazifa — 13-dars |
| Topilgan, lekin vazifaga bog‘lanmagan fayl | 0 |

**Qayerda nima:**
- Fayllar `app/protected_storage/lesson-listening` da (shaxsiy, ommaviy URL yo‘q).
- Har bir fayl production’dagi SHA-256 bilan `D:\Nemis Tili Video dars\A2 darslar 15-28 (14)\A2 Hören` dagi kitob fayliga teng.
- Transkriptlar shu kitob fayllaridan olingan.

## Fayllar

„Art“ ustuni fayl nomidan aniqlangan (`app/services/a2_audio/filename.py`). „Dauer“ fayl dekoderidan o‘lchangan.

| U. | Datei | Art | Teil | Format | Dauer | Größe | SHA-256 | hochgeladen | Aufgabe | Transkript | Zuordnung |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | A2 1.Unterricht Hören.m4a | Hören | — | M4A | 1:35 | 2.24 MB | 80f8bbef | 2026-10-29 23:58 | Hören: Warum haben Sie Ihren Beruf gewählt? | TRANSCRIBED | MATCHED |
| 2 | A2 2.Unterricht Hören.mp3 | Hören | — | MP3 | 2:05 | 0.90 MB | 1ca91b4b | 2026-10-29 23:59 | Hören: Sendung „Gemeinschaftskreis“ — soziale Netzwerke | TRANSCRIBED | MATCHED |
| 3 | A2.  3.Unterricht Hören.mp3 | Hören | — | MP3 | 2:04 | 0.71 MB | 1a4b66a8 | 2026-10-29 23:59 | Hören: Die Empfehlungen eines Arztes | TRANSCRIBED | MATCHED |
| 4 | A2 4.Unterricht Text 1.mp3 | Text | 1 | MP3 | 0:49 | 0.28 MB | 032a9dac | 2026-10-30 01:34 | Hören: Text 1 | TRANSCRIBED | MATCHED |
| 4 | A2 4.Unterricht Text 2.mp3 | Text | 2 | MP3 | 0:50 | 0.29 MB | 503aefe3 | 2026-10-30 01:34 | Hören: Text 2 | TRANSCRIBED | MATCHED |
| 4 | A2 4.Unterricht Text 3.mp3 | Text | 3 | MP3 | 0:34 | 0.20 MB | 50ab5e4d | 2026-10-30 01:34 | Hören: Text 3 | TRANSCRIBED | MATCHED |
| 5 | A2 5.Unterricht Hören.mp3 | Hören | — | MP3 | 1:44 | 0.60 MB | c2939a12 | 2026-10-30 00:25 | Hören: Steigende Mieten in Deutschland! | TRANSCRIBED | MATCHED |
| 6 | A2 6.Unterricht.mp3 | Unterricht | — | MP3 | 1:57 | 0.67 MB | a667535f | 2026-10-30 00:25 | Hören: Konflikte zwischen Lukas und Jonas / Paul und Leon | TRANSCRIBED | MATCHED |
| 7 | A2 7.Unterricht Text 1.mp3 | Text | 1 | MP3 | 1:18 | 0.45 MB | 7ecc292a | 2026-10-30 00:25 | Hören Test: Reisen (Max und Sara) | TRANSCRIBED | MATCHED |
| 7 | A2 7.Unterricht Text 2.mp3 | Text | 2 | MP3 | 1:16 | 0.44 MB | 76e8dea2 | 2026-10-30 02:31 (qo‘shildi) | Hören Test: Reisen (Max und Sara) | TRANSCRIBED | MATCHED |
| 8 | A2 8.Unterricht.mp3 | Unterricht | — | MP3 | 2:27 | 0.84 MB | cf51ff0b | 2026-10-30 00:25 | Hören: Einkauf von Susanna und Einkauf von Johann | TRANSCRIBED | MATCHED |
| 9 | A2 9.Unterricht Hören.mp3 | Hören | — | MP3 | 1:31 | 0.52 MB | 3fb99700 | 2026-10-30 00:25 | Hören: Aufgabe zum Hören — Medien zuordnen | TRANSCRIBED | MATCHED |
| 10 | A2 10.Unterricht Teil 1.m4a | Teil | 1 | M4A | 6:37 | 6.13 MB | d5f8da8d | 2026-10-30 00:26 | Hören Teil 1: Fünf kurze Texte | TRANSCRIBED | MATCHED |
| 10 | A2 10.Unterricht Teil 2.m4a | Teil | 2 | M4A | 2:17 | 2.13 MB | b10d922d | 2026-10-30 00:26 | Hören Teil 2: Flohmarkt | TRANSCRIBED | MATCHED |
| 10 | A2 10.Unterricht Teil 3.m4a | Teil | 3 | M4A | 4:57 | 4.59 MB | b9a90683 | 2026-10-30 00:26 | Hören Teil 3: Fünf kurze Gespräche | TRANSCRIBED | MATCHED |
| 10 | A2 10.Unterricht Teil 4.m4a | Teil | 4 | M4A | 4:53 | 4.53 MB | d6a1216b | 2026-10-30 00:26 | Hören Teil 4: Interview — Europa-Camp | TRANSCRIBED | MATCHED |
| 11 | A2 11.Unterricht Teil_1.m4a | Teil | 1 | M4A | 7:01 | 6.50 MB | 890f6e12 | 2026-10-30 00:26 | Hören Teil 1: Fünf kurze Texte | TRANSCRIBED | MATCHED |
| 11 | A2 11.Unterricht Teil_2.m4a | Teil | 2 | M4A | 2:21 | 2.19 MB | 950a59b0 | 2026-10-30 00:26 | Hören Teil 2: Wie war Alisas Tag gestern? | TRANSCRIBED | MATCHED |
| 11 | A2 11.Unterricht Teil_3.m4a | Teil | 3 | M4A | 4:53 | 4.54 MB | 3cce7590 | 2026-10-30 00:26 | Hören Teil 3: Fünf kurze Gespräche | TRANSCRIBED | MATCHED |
| 11 | A2 11.Unterricht Teil_4.m4a | Teil | 4 | M4A | 4:20 | 4.01 MB | 1f879d92 | 2026-10-30 00:27 | Hören Teil 4: Interview mit Sonja | TRANSCRIBED | MATCHED |
| 12 | A2 12.Unterricht Teil_1.m4a | Teil | 1 | M4A | 7:25 | 6.87 MB | 7d4f1e93 | 2026-10-30 00:27 | Hören Teil 1: Fünf kurze Texte | TRANSCRIBED | MATCHED |
| 12 | A2 12.Unterricht Teil_2.m4a | Teil | 2 | M4A | 2:27 | 2.28 MB | 648466ec | 2026-10-30 00:27 | Hören Teil 2: Was kommt in den Koffer? | TRANSCRIBED | MATCHED |
| 12 | A2 12.Unterricht Teil_3.m4a | Teil | 3 | M4A | 4:33 | 4.22 MB | 8cdf903b | 2026-10-30 00:27 | Hören Teil 3: Fünf kurze Gespräche | TRANSCRIBED | MATCHED |
| 12 | A2 12.Unterricht Teil_4.m4a | Teil | 4 | M4A | 4:19 | 4.01 MB | ad8373bc | 2026-10-30 00:27 | Hören Teil 4: Interview mit Sandra | TRANSCRIBED | MATCHED |
| 13 | A2 13.Unterricht Teil 1.m4a | Teil | 1 | M4A | 7:25 | 6.87 MB | **7d4f1e93** | 2026-10-30 00:27 | Hören Teil 1: Fünf kurze Texte | (12-dars transkripti) | **MISMATCH** |
| 13 | A2 13.Unterricht Teil 2.m4a | Teil | 2 | M4A | 2:27 | 2.28 MB | **648466ec** | 2026-10-30 00:27 | Hören Teil 2: Wie war Carmens Geburtstag? | (12-dars transkripti) | **MISMATCH** |
| 13 | A2 13.Unterricht Teil 3.m4a | Teil | 3 | M4A | 4:33 | 4.22 MB | **8cdf903b** | 2026-10-30 00:27 | Hören Teil 3: Fünf kurze Gespräche | (12-dars transkripti) | **MISMATCH** |
| 13 | A2 13.Unterricht Teil 4.m4a | Teil | 4 | M4A | 4:19 | 4.01 MB | **ad8373bc** | 2026-10-30 00:28 | Hören Teil 4: Interview mit Sebastian | (12-dars transkripti) | **MISMATCH** |

Har bir faylning yakuniy qayta ishlash holati — `docs/a2-publishing-report.md`.

## E’tibor talab qiladigan fayllar

1. **13-dars (4 fayl):** 12-dars fayllarining nusxasi (SHA-256 bir xil). Manba papkada ham shunday, ya’ni 13-darsning haqiqiy audiosi yo‘q.
   - Transkript 12-dars mazmunini beradi: Annas Zimmer, Koffer, Sandra. 13-dars savollari esa boshqa: Carmens Geburtstag, Sebastian.
   - Shuning uchun kalit qo‘yilmadi, vazifalar nashr qilinmadi.
   - Kerak: 13-darsning to‘g‘ri fayllarini yuklash.
2. **7-dars „Text 2“:**
   - 15 savoldan 7 tasi (Sara haqida) faqat shu fayl bilan javob topadi, lekin fayl production’ga yuklanmagan edi.
   - Uni kitob faylidan qo‘shdim. SHA-256 transkripsiya qilingan fayl bilan bir xil (`76e8dea2…`).
   - Joyi: vazifaning ikkinchi treki „Text 2“; asosiy audio „Text 1“ deb belgilandi.
   - Qaytarish: Media Management → vazifa → „Text 2“ trekini o‘chirish.
3. **4-dars Text 1–3:**
   - Audio Media Management’ning oddiy Hören upload’i orqali yuklangan, A2 kutubxonasiga yozilmagan edi.
   - Shu fayllarning o‘zi kutubxonaga „qabul qilindi“ (yozuv shu saqlangan faylga ishora qiladi, fayl ko‘chirilmadi). Endi Text 1–3 sahifasi ularni boshqaradi.

## Qayta chiqarish

Faqat o‘qiydi:

```bash
cd /opt/vizu/VIZU-Academy/backend
.venv/bin/python -m app.scripts.a2_audio_processing plan --audio-dir /root/a2-book-audio
```

Admin panel: Media Management → Niveau A2 → „A2 Audio-Verarbeitung · 1.–13. Unterricht“.
