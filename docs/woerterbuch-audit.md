# Wörterbuch (A1–C1): audit va qurilish hisoboti

Sana: 2026-10-28 · Holat: **lokal, deploy qilinmagan** (migratsiya `d4b8e2f6a9c1` production'da bajarilmagan)

## 1. Manba CSV fayllar

> 2026-10-28 dan keyin: `docs/*-words.csv` yangi 22 ustunli formatda. Quyidagi jadval asl fayllar haqida; ular `docs/backup/woerterbuch-csv-original-20261028/` va `backend/app/data/woerterbuch/source/` da saqlanadi. Batafsil: [worterbuch-csv-migration-report.md](worterbuch-csv-migration-report.md).

| Fayl | Qatorlar | Ustunlar | Asosiy daraja bo‘yicha yozuvlar | Fayldagi bor so‘zlar |
|---|---|---|---|---|
| docs/A1-words.csv | 1000 | 5 | 738 | 738 |
| docs/A2-words.csv | 1000 | 5 | 549 | 634 |
| docs/B1-words.csv | 1000 | 5 | 80 | 247 |
| docs/B2-words.csv | 1500 | 5 | 1012 | 1236 |
| docs/C1-words.csv | 1100 | 5 | 1010 | 1043 |
| **Jami** | **5600** | | **3389** | |

- Format: UTF-8, NFC, CRLF, **header yo‘q**. Ustunlar: `id, Nemischa, to‘g‘ri o‘zbekcha javob, noto‘g‘ri1, noto‘g‘ri2`.
- **3- va 4-ustunlar tarjima emas.** Ular bot so‘z o‘yinining chalg‘ituvchi variantlari, shuning uchun lug‘atga hech qachon tarjima sifatida olinmaydi (`test_distractors_are_never_translations`).
- 4 ta buzilgan qator aniq ta’mirlangan va `source:repaired_row` bilan belgilangan:
  - A1 #420 → weich;
  - A2 #279 → leiden;
  - B2 #664 → auswirken;
  - C1 #28 → unter der Voraussetzung, dass.
- Asl fayllar o‘zgartirilmagan. Bayt nusxalari va sha256 qiymatlari `backend/app/data/woerterbuch/source/` da saqlanadi.

## 2. Dublikatlar va ularni hal qilish

- 5600 qator **3389 ta yozuvga** birlashtirildi. Kalit: artikl + lemma, `casefold`; umlaut saqlanadi, ya’ni „schon“ ≠ „schön“.
- 409 so‘z bir nechta darajada uchraydi. Avtomatik yo‘qotish yo‘q:
  - yozuv eng past darajada saqlanadi (`cefr_level`);
  - `levels` maydonida barcha darajalar bor; daraja filtri `levels` bo‘yicha ishlaydi;
  - har bir manba qatori `sources` ichida qoladi (`level`, `row`, `answer`, `distractors`). Bu audit izi.
- B1 fayli kuchli takrorlanadi: 1000 qatordan faqat 80 tasi yangi so‘z, qolganlari A1/A2 dagi so‘zlar.
- Bir so‘zga turli o‘zbekcha javoblar berilgan bo‘lsa, eng ko‘p uchragani asosiy tarjima bo‘ladi. Qolganlari `translations_extra` ga o‘tadi va yozuv `translation_status = needs_review` (`translation:variants`) oladi.
- Bir xil lemma, lekin turli artikl yoki ma’noga ega yozuvlar avtomatik birlashtirilmagan. Masalan „die Bewerbungsgespräch“ alohida qoldi va bayroq oldi.

## 3. Statistika (dictionary.json)

**So‘z turi:** Nomen 1623 · Wendung 752 · Verb 542 · Adjektiv 367 · Adverb 75 · Konjunktion 5 · Präposition 1 · aniqlanmagan 24

| Maydon | Qiymatlar |
|---|---|
| translation_status | source 3224 · **needs_review 165** |
| grammar_status | sourced 1995 · **needs_review 604** · none 790 (omonim himoyasidan keyin) |
| grammar_source | wiktionary 2104 · wiktionary_compound 381 · none 904 |
| example_status | **needs_review 3373** · none 16 |
| is_published | true 3375 · **false 14** |

Status ma’nolari:

- `source` — tarjima so‘z ro‘yxatidan bitta izchil javob sifatida olingan. Bu „o‘qituvchi tekshirgan“ degani emas.
- `sourced` — grammatika Wiktionary'dan olingan.
- `needs_review` — avtomatik qoidadan chiqarilgan, ziddiyatli yoki qo‘lda belgilangan ma’lumot.
- `reviewed` holati hozircha hech bir yozuvda yo‘q. Import `reviewed` yozuvlarni hech qachon ustidan yozmaydi.

## 4. Grammatika manbasi

- Wiktionary (inglizcha nashr, kaikki.org orqali), **CC BY-SA 4.0**. Atribusiya har bir kartochkada va sahifa pastida ko‘rsatiladi.
- Nomen: artikl, birlik, ko‘plik. Qo‘shma so‘zlarda (masalan Forschungsergebnis) jins va ko‘plik oxirgi qismdan olinadi va `needs_review` bo‘ladi.
- Verb: Präsens (6 shaxs), Präteritum, Partizip II, hat/ist, ajraladigan old qo‘shimcha. Refleksiv fe’llarda olmosh qo‘shiladi va yozuv `needs_review` bo‘ladi.
- Adjektiv: Komparativ va Superlativ, istisnolar Wiktionary'dan.
- Konjunktsiyalar: so‘z tartibi qoidasi (ergash yoki teng bog‘lovchi). Präpozitsiya: kelishik.
- 790 yozuvda grammatika yo‘q, ko‘pi Wendung. Grammatika **o‘ylab topilmagan**.

## 5. Misol gaplar

- 3373 ta misol (de + uz) VIZU uchun yozilgan. Barchasi `example_status = needs_review`, ya’ni o‘qituvchi tekshirishi kerak.
- 16 ta yozuvda misol ataylab yo‘q: so‘zning o‘zi noto‘g‘ri yoki aralash.
- Fayllar: `backend/app/data/woerterbuch/examples/{A1-1 … C1-4}.json`.

## 6. Qo‘lda topilgan manba muammolari (review_flags.json)

28 ta bayroq. Har biri `review_notes` ga yoziladi, avtomatik **tuzatilmaydi**.

| Turi | Natija | Yozuvlar |
|---|---|---|
| invalid_lemma / misspelling / wrong_article (14) | `is_published = false`: qidiruvda va Random 5 da ko‘rinmaydi, lekin bazada saqlanadi | lärmlich, gemütvoll, bequemlich, -stöckig, möglich qilmoq, normativ belgilangan, kritisch hinterleuchten/-et, das Verhaltenmuster, die Weiterbildungskursi, anderserseits, die Sicherheitlücke, die Bewerbungsgespräch, die Zeitungskiosk |
| translation (6) | `translation_status = needs_review` | das Betriebssystem („ish tizimi“), der Wolkenkratzer („skyscraper“), erfahren, das Vorurteil / die Vorurteile („xurofot“) |
| unidiomatic / rare_word (8) | ko‘rinadi, izoh bilan | das Krankenhausticket, eine Stellung nehmen, eine Verantwortung übernehmen, Erfahrung austauschen, erquicklich, wissenschaftlich argumentativ, folglich argumentieren/betrachtet/interpretiert |

**C1 haqida umumiy kuzatuv:** C1 ro‘yxatining taxminan 255–1009 qatorlari shablon asosida yasalgan akademik birikmalardan iborat. Ular „kritisch / methodisch / argumentativ / semantisch + ot yoki fe’l“ ko‘rinishida. Grammatik jihatdan to‘g‘ri, lekin ko‘pi lug‘atga xos barqaror ibora emas va bir-birini takrorlaydi. Har birini alohida bayroqlamadik. Kontent egasi bu qismni qisqartirish yoki qayta ko‘rib chiqishni o‘ylab ko‘rishi kerak.

## 7. Ma’lumotlar bazasi

Migratsiya **`d4b8e2f6a9c1_woerterbuch`** (down_revision `a7c2e9f4b1d6`) faqat 3 ta yangi jadval yaratadi va mavjud jadvallarga tegmaydi. Downgrade shu 3 jadvalni o‘chiradi. Test bazada upgrade → downgrade → upgrade sikli o‘tdi.

- `dictionary_entries`:
  - `stable_id` (`wb-` + sha1), lemma va grammatika maydonlari, statuslar, `review_notes`, `sources`;
  - `search_de` va `search_uz` (`text_pattern_ops` indekslari), `levels` (GIN), `content_hash`, `is_published`.
- `dictionary_user_words`: foydalanuvchi + so‘z bo‘yicha `saved`, `status` (known/unknown), seen/known/unknown hisoblagichlari, vaqtlar.
- `dictionary_random_sessions`: har bir Random 5 seansi (daraja, 5 ta id, pool hajmi, ko‘rilmaganlar soni).

Import: `python -m app.scripts.woerterbuch.build`, keyin `python -m app.scripts.import_woerterbuch --dry-run`, keyin dry-run'siz.

- Idempotent: `stable_id` + `content_hash` bo‘yicha ishlaydi; qayta ishga tushirilganda hammasi „unchanged“ chiqadi.
- Hech narsani o‘chirmaydi; `reviewed` yozuvlarni ustidan yozmaydi.

## 8. API (`/api/v1/dictionary`, faqat tizimga kirgan foydalanuvchi)

`GET /meta`, `GET /search?q=&level=&pos=&page=`, `GET /entries/{id}`, `GET /my`, `POST /random`, `POST /entries/{id}/mark`, `PUT /entries/{id}/saved`.

- Qidiruv nemischa va o‘zbekcha bo‘yicha ishlaydi:
  - artiklsiz yozish mumkin; ä/ae → a, ß → ss; o‘zbekcha apostrof variantlari birlashtiriladi;
  - tartib: aniq moslik > prefiks > o‘zbekcha so‘z > o‘zbekcha prefiks > ichida uchrashi;
  - sahifa hajmi ≤ 50.
- Kartochka `sources` va `review_notes` ni ko‘rsatmaydi. Statuslar badge sifatida ko‘rinadi.

## 9. Random 5

1. Server tanlangan daraja (yoki barcha darajalar) bo‘yicha `is_published` yozuvlardan foydalanuvchi **hali ko‘rmagan** so‘zlarni tasodifiy tanlaydi.
2. Ular 5 tadan kam bo‘lsa, eng uzoq vaqt oldin ko‘rilganlar bilan to‘ldiriladi. 5 tasi har doim har xil so‘z.
3. Tanlangan so‘zlar „ko‘rildi“ deb belgilanadi va seans saqlanadi.
4. Klientga faqat shu 5 ta kartochka yuboriladi. CSV yoki butun lug‘at hech qachon brauzerga bormaydi.
5. Javob yashirin turadi va „Ko‘rsatish“ bosilganda ochiladi. „Bilaman“ va „Bilmayman“ tugmalari natijani saqlaydi.

Spaced repetition qurilmagan. Talab bo‘yicha u alohida modul bo‘lishi kerak; `dictionary_user_words` dagi hisoblagichlar unga asos bo‘la oladi.

## 10. TTS (talaffuz)

- Brauzerning SpeechSynthesis API'si `de-DE` ovoz bilan ishlatiladi. Yozuvda `audio_url` bo‘lsa, avval u ijro etiladi.
- Cheklovlar:
  - ovoz sifati va mavjudligi qurilma va brauzerga bog‘liq;
  - ba’zi Android/Linux brauzerlarida nemischa ovoz yo‘q; bunda „nemischa ovoz topilmadi“ xabari chiqadi;
  - ba’zi qurilmalarda ovoz faqat foydalanuvchi bosgandan keyin ishlaydi.
- Xato holatlari: `unsupported`, `no-voice`, `failed`, har biri o‘z xabari bilan.
- Kelajakdagi backend audio provayder uchun `audio_url` maydoni tayyor. Hozir u hamma yozuvda bo‘sh.

## 11. Testlar va build (2026-10-28, lokal)

- `tests/test_woerterbuch.py`: **25/25 OK**. Bunga lokal Postgres'dagi DB integratsiya testlari ham kiradi: import idempotentligi, qidiruv tartibi, filtrlar, Random 5, mark/saved, yashirilgan yozuvlar.
- Butun backend suite: **791 test OK** (17 skipped).
- Frontend:
  - `tsc --noEmit` OK;
  - `eslint` (woerterbuch + i18n) OK;
  - `next build` OK; `/woerterbuch` statik sahifa sifatida yaratildi.

## 12. Yaratilgan yoki o‘zgartirilgan fayllar

- Backend:
  - `app/scripts/woerterbuch/` (`source.py`, `wiktionary.py`, `wiktionary_extract.py`, `build.py`);
  - `app/scripts/import_woerterbuch.py`;
  - `app/models/dictionary.py` (+ `models/__init__.py`);
  - `app/services/dictionary/`, `app/api/dictionary/` (+ `main.py` da router);
  - `alembic/versions/d4b8e2f6a9c1_woerterbuch.py`;
  - `app/data/woerterbuch/` (`dictionary.json`, `wiktionary_grammar.json`, `review_flags.json`, `examples/`, `source/`);
  - `tests/test_woerterbuch.py`.
- Frontend:
  - `src/features/woerterbuch/` (service, hooks, components);
  - `src/app/(dashboard)/woerterbuch/page.tsx`;
  - `src/lib/i18n/translations.ts` (woerterbuch bloki).
  - Eski `hooks/use-woerterbuch.ts` va `types/dictionary.ts` o‘chirildi.
- Telegram bot repositorysi, bot bazasi va boshqa modullarga tegilmagan.

## 13. Qolgan bo‘shliqlar

1. **O‘qituvchi uchun review UI yo‘q.** `needs_review` statuslarini `reviewed` ga o‘tkazish, bayroqli yozuvlarni tuzatish va nashr qilish uchun admin sahifa kerak. Hozircha buni faqat ma’lumot faylini tahrirlab va qayta import qilib qilish mumkin.
2. 3373 ta misol va 165 ta tarjima tekshirilishi kerak.
3. Audio fayllar yo‘q (`audio_url` bo‘sh). Hozir faqat brauzer TTS ishlaydi.
4. Spaced repetition qurilmagan.
5. Brauzerda haqiqiy akkaunt bilan qo‘lda sinov o‘tkazilmagan. Sinovlar avtomatik testlar va build bilan cheklangan.
6. Production: migratsiya, import va frontend deploy **tasdiq kutmoqda**.
