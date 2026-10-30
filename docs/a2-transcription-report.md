# A2 transkripsiya hisoboti (1–13-darslar)

Sana: 2026-10-30. **Holat: 24 mazmun / 28 fayl — 24 `TRANSCRIBED`, 0 `NEEDS_REVIEW`, 0 `FAILED`.**

## Usul

| | |
|---|---|
| Model | faster-whisper **large-v3** (asosiy) + **medium** (ikkinchi model, nazorat uchun). CPU, int8, til `de`, beam 5, so‘z darajasidagi ishonch va vaqt belgilari bilan |
| Qaysi fayl | production’dagi faylning o‘zi. Ishlov berishdan oldin har bir saqlangan fayl SHA-256 bilan transkripsiya qilingan fayl bilan solishtirildi; biri farq qilsa, skript hech narsa qilmaydi |
| Takror yo‘q | bitta mazmun (SHA-256) bir marta transkripsiya qilinadi (`a2_audio_transcripts`, unique `sha256`). 12 va 13-darsdagi bir xil fayllar bitta transkriptni ishlatadi. Ikkinchi `apply` 28 faylning hammasida mavjud transkriptni qayta ishlatdi (`created 0, reused 28`) |
| Ma’lumot | `backend/app/data/a2_audio_transcripts.json`: matn, segmentlar `[start, end, text]`, sifat ko‘rsatkichlari |
| Saqlanadigan joy | 1. `a2_audio_transcripts` jadvali (admin panel). 2. Vazifaning `listenings.transcript` maydoni (o‘quvchi uchun) — faqat audio vazifaga mos bo‘lsa (MATCHED) va vazifada hali transkript bo‘lmasa |
| O‘quvchiga ko‘rinishi | savolli vazifada birinchi topshirilgan urinishdan keyin (mavjud LMS qoidasi); savolsiz vazifada (Text 1–3) darhol. Matn boshida „Transkript (automatisch aus dem Audio erstellt; unverständliche Stellen sind markiert)“ yozuvi bor |

## Holat qoidasi

- **`TRANSCRIBED`** — large-v3 dagi past ishonchli so‘zlar (ehtimollik < 0.6) so‘zlar sonining ≤ 3 % i va noaniq joylar ≤ 3 ta.
- **`NEEDS_REVIEW`** — shundan ko‘p.
- **`FAILED`** — transkripsiya bo‘lmasa.

Noaniq joy ikki xil bo‘ladi. Ikkalasi ham taxmin bilan to‘ldirilmadi, matnda `[unverständlich]` deb belgilandi:
- ehtimolligi < 0.3 bo‘lgan va ikkinchi model eshitmagan so‘z;
- ikkala model ham ma’nosiz so‘z bergan joy.

So‘zlar o‘zgartirilmadi; faqat raqam va defis yozuvi bir xillashtirildi („1 .500“ → „1.500“, „T -Shirt“ → „T-Shirt“).

## Fayllar bo‘yicha

| Fayl | Davom. | So‘z | Past ishonch | Ikkinchi model bilan mos | Holat | Noaniq joylar |
|---|---|---|---|---|---|---|
| A2 1.Unterricht Hören.m4a | 1:35 | 211 | 0 | 99.8 % | TRANSCRIBED | — |
| A2 2.Unterricht Hören.mp3 | 2:05 | 265 | 1 | 99.2 % | TRANSCRIBED | [43 s] „Weitungs“ (ikkinchi model: „Reitungs“; ehtimol „Einfluss“) |
| A2.  3.Unterricht Hören.mp3 | 2:04 | 293 | 0 | 99.7 % | TRANSCRIBED | — |
| A2 4.Unterricht Text 1.mp3 | 0:49 | 121 | 0 | 99.2 % | TRANSCRIBED | — |
| A2 4.Unterricht Text 2.mp3 | 0:50 | 117 | 0 | 99.6 % | TRANSCRIBED | [31 s] „ZRF“ (ehtimol „Café“) |
| A2 4.Unterricht Text 3.mp3 | 0:34 | 100 | 0 | 93.0 %¹ | TRANSCRIBED | [16 s] „ZRF“ (ehtimol „Café“) |
| A2 5.Unterricht Hören.mp3 | 1:44 | 235 | 1 | 100 % | TRANSCRIBED | — |
| A2 6.Unterricht.mp3 | 1:57 | 261 | 3 | 99.0 % | TRANSCRIBED | — |
| A2 7.Unterricht Text 1.mp3 | 1:18 | 185 | 5 | 99.5 % | TRANSCRIBED | [28 s] „Nacht.“ (0.15, ikkinchi modelda yo‘q) |
| A2 7.Unterricht Text 2.mp3 | 1:16 | 158 | 1 | 97.4 % | TRANSCRIBED | — |
| A2 8.Unterricht.mp3 | 2:27 | 348 | 8 | 94.2 % | TRANSCRIBED | — |
| A2 9.Unterricht Hören.mp3 | 1:31 | 154 | 2 | 99.7 % | TRANSCRIBED | — |
| A2 10.Unterricht Teil 1.m4a | 6:37 | 647 | 17 | 92.0 % | TRANSCRIBED | [364 s] „mal.“ |
| A2 10.Unterricht Teil 2.m4a | 2:17 | 247 | 4 | 84.8 %¹ | TRANSCRIBED | [137 s] „Bye.“ |
| A2 10.Unterricht Teil 3.m4a | 4:57 | 467 | 12 | 95.7 % | TRANSCRIBED | — |
| A2 10.Unterricht Teil 4.m4a | 4:53 | 581 | 7 | 98.3 % | TRANSCRIBED | — |
| A2 11.Unterricht Teil_1.m4a | 7:01 | 706 | 14 | 84.8 %¹ | TRANSCRIBED | — |
| A2 11.Unterricht Teil_2.m4a | 2:21 | 257 | 4 | 98.0 % | TRANSCRIBED | — |
| A2 11.Unterricht Teil_3.m4a | 4:53 | 463 | 13 | 95.1 % | TRANSCRIBED | [110 s] „gerne“ |
| A2 11.Unterricht Teil_4.m4a | 4:20 | 530 | 6 | 98.1 % | TRANSCRIBED | — |
| A2 12.Unterricht Teil_1.m4a (= 13 Teil 1) | 7:25 | 694 | 14 | 96.7 % | TRANSCRIBED | — |
| A2 12.Unterricht Teil_2.m4a (= 13 Teil 2) | 2:27 | 245 | 2 | 99.0 % | TRANSCRIBED | — |
| A2 12.Unterricht Teil_3.m4a (= 13 Teil 3) | 4:33 | 389 | 9 | 92.4 % | TRANSCRIBED | — |
| A2 12.Unterricht Teil_4.m4a (= 13 Teil 4) | 4:19 | 576 | 13 | 55.7 %¹ | TRANSCRIBED | — |

¹ Past moslik ikkinchi model xatosi: medium bir bo‘lakni tashlab ketgan yoki takrorlangan bo‘lakni bir marta yozgan. Bo‘laklar `a2p_quality.py -v` bilan alohida ko‘rib chiqildi. Asosiy model (large-v3) matni to‘liq.

**Imtihon audiolari (10–13-darslar):**
- Ichida diktor ko‘rsatmalari bor („Lies jetzt die Aufgabe 3“, „Du hörst die Aufgabe noch einmal“).
- Matnlar odatda ikki marta yangraydi.
- Transkriptda ham shunday qoldirildi.

## Dialog va spikerlar

Segmentlar vaqt belgisi bilan saqlandi (admin panelda `[m:ss]`). Avtomatik spiker ajratish (diarization) qilinmadi — uydirma spiker nomi qo‘shmaslik uchun. Spiker almashuvi matnning o‘zidagi tanishtirishlardan ko‘rinadi:
- „Hallo, mein Name ist Julia“, „Text 2 …“;
- 10–13-darslarda „Aufgabe 1 … 5“.

## Bajarilmagan / ochiq

- **1-dars:** vazifada kitob transkripti bor edi. U saqlandi, mashina transkripti faqat admin panelda.
  - Farq: kitobda „weil mein Vater auch Architekt **ist**“, audioda „**war**“. Bu farq 2026-10-21 dagi auditda ham qayd etilgan.
- **13-dars:** 12-dars transkripti o‘quvchiga ko‘rsatilmadi (MISMATCH).
- 7 ta noaniq joyni tinglab tekshirish kerak. Aniq so‘z topilsa, uni admin vazifa transkriptida tuzatadi.
