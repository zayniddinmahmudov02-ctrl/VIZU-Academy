# Wörterbuch CSV: yangi 22 ustunli formatga o‘tkazish hisoboti

Sana: 2026-10-28 · Faqat lokal fayllar o‘zgardi. Production bazasi, deploy, Telegram bot (kod, baza, servislar) — tegilmagan.

## 1. Natija qisqacha

- 5 ta fayl (`docs/A1-words.csv` … `docs/C1-words.csv`) bir xil sarlavha va ustunlar tartibiga o‘tkazildi. Fayl nomlari o‘zgarmadi.
- **Hech bir qator yo‘qolmadi.** 5600 → 5600, har bir fayl ichidagi `id` va qatorlar tartibi asl fayldagidek.
- **`verified` = 0, `needs_review` = 5600.** Sabab: hali hech bir qatorni o‘qituvchi tekshirmagan. Hammasidan muhimi, misol gaplarni men yozganman va ular tekshiruv kutmoqda. Tekshirilmagan ma’lumot `verified` deb belgilanmadi.
- `needs_review` qatorlar ikki guruhga bo‘lingan:
  - `high` — 1573 qator: aniq muammo yoki yetishmayotgan ma’lumot bor;
  - `example_only` — 4027 qator: tarjima va grammatika manbalarga mos, faqat misol gap tekshirilmagan.
- Fayllar `docs/worterbuch-needs-review.csv` ga yozilgan.

## 2. Zaxira nusxa

- Asl 5 fayl bayt-ma-bayt nusxalandi: `docs/backup/woerterbuch-csv-original-20261028/` (sha256 qiymatlari `SHA256SUMS.txt` da).
- Ikkinchi nusxa `backend/app/data/woerterbuch/source/` da. Bu ham bayt-ma-bayt bir xil; sayt lug‘atini quruvchi kod endi shu nusxadan o‘qiydi.
- Git: lokal kompyuterda git o‘rnatilmagan, shuning uchun `git status` ni tekshirib bo‘lmadi. `git reset` yoki `git clean` ishlatilmadi. Hech bir fayl o‘chirilmadi.

## 3. Asl fayllar (audit)

| Daraja | Qatorlar | Ustunlar | Kodlash / qator oxiri | Sarlavha | Ichki takror (ortiqcha qator) |
|---|---|---|---|---|---|
| A1 | 1000 | 5 (bitta qatorda 6) | UTF-8 / CRLF | yo‘q | 262 |
| A2 | 1000 | 5 (bitta qatorda 4) | UTF-8 / CRLF | yo‘q | 366 |
| B1 | 1000 | 5 | UTF-8 / CRLF | yo‘q | **753** |
| B2 | 1500 | 5 (bitta qatorda 4) | UTF-8 / CRLF | yo‘q | 264 |
| C1 | 1100 | 5 (bitta qatorda 6) | UTF-8 / CRLF | yo‘q | 57 |

Batafsil ma’lumot (sha256 bilan): `docs/worterbuch-original-counts.csv`.

- **Eski ustunlar:** `id, nemischa so‘z, to‘g‘ri o‘zbekcha javob, noto‘g‘ri javob 1, noto‘g‘ri javob 2`.
  - Oxirgi ikki ustun tarjima emas, so‘z o‘yini (quiz) uchun chalg‘ituvchi variantlar.
  - Shuning uchun `translation` ga faqat 3-ustun yozildi; uchala ustun birlashtirilmadi.
  - Chalg‘ituvchi variantlar yo‘qolmagan: ular `docs/worterbuch-extra-data.csv` da (`quiz_distractors`) va zaxira nusxada saqlanadi.
- **4 ta buzilgan qator** (ustunlar soni noto‘g‘ri) aniq qoida bilan tiklandi: A1 #420 weich, A2 #279 leiden, B2 #664 auswirken, C1 #28 „unter der Voraussetzung, dass“. Ular `needs_review` ro‘yxatida `source:repaired_row` sababi bilan turibdi.
- **`id`:**
  - har bir fayl ichida 1…N va unikal, lekin fayllar orasida takrorlanadi;
  - saytning importi `id` ni ishlatmaydi: o‘z `stable_id` si bor, u lemma asosida hisoblanadi;
  - Telegram bot `docs/` dagi fayllarni emas, o‘z repositoriysidagi nusxalarni o‘qiydi.
  - Shu sababli eski `id` lar o‘zgartirilmadi. Global unikal kalit kerak bo‘lsa — `level` + `id`.

## 4. Yangi format

```
id,level,lemma,word_type,article,plural,translation,verb_praeteritum,verb_partizip_ii,verb_auxiliary,presens_ich,presens_du,presens_er_sie_es,presens_wir,presens_ihr,presens_sie_Sie,adjective_komparativ,adjective_superlativ,example_de,example_uz,audio_text,status
```

Texnik talablar:

- UTF-8 (BOM'siz), CRLF qator oxiri, Python `csv` writer bilan yozilgan standart quoting.
- Masalan, „unter der Voraussetzung, dass“ qo‘shtirnoq ichida.
- Bo‘sh qiymat — bo‘sh maydon. `NULL`, `None`, `N/A` yo‘q; buni test tekshiradi.
- Excel'da ochishda kodlashni UTF-8 deb tanlash kerak bo‘lishi mumkin.

Maydonlarni to‘ldirish qoidalari:

- **`lemma`**:
  - artiklsiz yoziladi (`Apfel`);
  - refleksiv fe’l `sich` bilan (`sich bewerben`);
  - ibora asl ko‘rinishida.
- **`word_type`**:
  - `Nomen`, `Verb`, `Adjektiv`, `Adverb`, `Konjunktion`, `Praeposition`;
  - `Wendung` — ko‘p so‘zli ibora (asosan C1: 678 ta);
  - 30 qatorda turi aniqlanmagan: maydon bo‘sh, sababi `word_type:unknown`.
- **`article` / `plural`**:
  - faqat `Nomen` uchun; ko‘plik artiklsiz yoziladi (`Äpfel`);
  - ko‘plik topilmagan bo‘lsa, maydon bo‘sh qoldi va sababi `noun:plural_missing` deb yozildi;
  - Pluraletantum (faqat ko‘plikda ishlatiladigan otlar) alohida qayd etilgan.
- **Fe’l ustunlari**:
  - faqat `Verb` uchun, hammasi Wiktionary'dan; umumiy qoida bilan yasalmagan;
  - ajraladigan fe’llar: `rufe an` / `rief an`;
  - refleksiv fe’llar: `bewerbe mich`;
  - Perfektda ikkala yordamchi fe’l bilan ishlatiladigan 29 ta fe’lda `haben/sein` yozilgan va qator `needs_review`.
- **Sifat darajalari**:
  - faqat `Adjektiv` uchun: `gut → besser → am besten`;
  - darajalanmaydigan sifatlar majburan darajalanmadi; maydon bo‘sh, sababi `adjective:not_comparable`.
- **`translation`**:
  - asl qatordagi to‘g‘ri javob;
  - faqat o‘zbekcha apostroflar bitta yozuvga keltirildi (o‘, g‘ uchun ‘; tutuq belgisi uchun ’);
  - 301 qatorda shu tuzatish bo‘lgan, ular `translation:apostrophes_normalized` bilan qayd etilgan.
- **`audio_text`** (TTS uchun matn, audio fayl emas):
  - otlarda artikl bilan: `der Apfel`;
  - qolgan so‘zlarda lemma;
  - nemischa bo‘lmagan yoki xato yozilgan 14 ta so‘zda bo‘sh qoldirildi, toki TTS xatoni o‘qimasin;
  - audio fayllar mavjud deb ko‘rsatilmagan.
- **`status`**: `verified` faqat tarjima, grammatika va misolni o‘qituvchi tekshirgan bo‘lsa beriladi. Hozircha bunday qator yo‘q.

## 5. Daraja bo‘yicha hisob

„Grammatika manbadan“ — Wiktionary'dan olingan va shubhali emas (`sourced`). „Tarjima izchil“ — so‘z ro‘yxatida bir xil javob, ziddiyat yoki bayroq yo‘q. Bu o‘qituvchi tekshiruvi emas.

| | A1 | A2 | B1 | B2 | C1 | Jami |
|---|---|---|---|---|---|---|
| Eski qatorlar | 1000 | 1000 | 1000 | 1500 | 1100 | 5600 |
| Yangi qatorlar | 1000 | 1000 | 1000 | 1500 | 1100 | 5600 |
| Tarjima izchil (manba) | 930 | 858 | 834 | 1341 | 1040 | 5003 |
| Grammatika kerak (Nomen/Verb/Adjektiv) | 923 | 922 | 800 | 1382 | 383 | 4410 |
| Grammatika Wiktionary'dan, shubhasiz | 827 | 691 | 663 | 1208 | 130 | 3519 |
| Misol gap + tarjima bor | 1000 | 991 | 996 | 1497 | 1094 | 5578 |
| `verified` | 0 | 0 | 0 | 0 | 0 | **0** |
| `needs_review` | 1000 | 1000 | 1000 | 1500 | 1100 | **5600** |
| — shundan `high` | 169 | 381 | 307 | 384 | 332 | 1573 |
| — shundan `example_only` | 831 | 619 | 693 | 1116 | 768 | 4027 |
| Daraja ichidagi takror guruhlar | 160 | 219 | 158 | 235 | 55 | 827 |
| Daraja ichidagi ortiqcha qatorlar | 262 | 366 | 753 | 264 | 57 | 1702 |

Grammatika maydonlarining to‘liqligi:

| | A1 | A2 | B1 | B2 | C1 |
|---|---|---|---|---|---|
| Nomen: artikl + ko‘plik bor | 496/510 | 473/500 | 240/241 | 698/775 | 192/307 |
| Verb: barcha shakllar bor | 197/197 | 199/199 | 261/261 | 392/413 | 26/26 |
| Adjektiv: Komparativ bor | 187/216 | 169/223 | 237/298 | 141/194 | 34/50 |

C1 da qo‘shma otlarning ko‘p qismi oxirgi bo‘lagi bo‘yicha aniqlangan (masalan, `Forschungsstrategie` → `Strategie`). Shuning uchun ular „shubhasiz“ hisobiga kirmaydi va tekshirilishi kerak.

## 6. Dublikatlar (`docs/worterbuch-duplicates.csv`)

- 869 ta takror guruh topildi. **Hech biri o‘chirilmagan va birlashtirilmagan** (`action = kept`).
- `duplicate_kind = same_level` — bir fayl ichida takror:
  - 827 guruh, 1702 ortiqcha qator;
  - B1 fayli ayniqsa ko‘p takrorlanadi: 1000 qatorning 753 tasi shu fayldagi boshqa qatorni takrorlaydi.
- `cross_level` — so‘z turli darajalarda uchraydi: 409 guruh. Daraja farqi saqlangan.
- `answers_in_group = different`:
  - bir xil so‘zga turli o‘zbekcha javob berilgan: daraja ichida 58 guruh;
  - bunday qatorlar `translation:variants` sababi bilan `needs_review`.
- Bir xil yozilgan, lekin artikli farq qiladigan so‘zlar alohida yozuv hisoblanadi (`der See` / `die See`). Ot va fe’l ham hech qachon birlashtirilmaydi.

**Tavsiya:** qaysi takrorni qoldirishni kontent egasi hal qilsin, ayniqsa B1 da. Fayl qisqartirilsa, saytdagi lug‘atga ta’sir qilmaydi, chunki u takrorlarni o‘zi birlashtiradi.

## 7. Sxemaga sig‘magan ma’lumotlar (`docs/worterbuch-extra-data.csv`)

Yangi 22 ustunda joyi yo‘q, lekin yo‘qotilmasligi kerak bo‘lgan ma’lumotlar har bir qator uchun alohida yozildi (`level, id, lemma, kind, value`):

| kind | Soni | Mazmuni |
|---|---|---|
| quiz_distractors | 5600 | eski 4–5-ustunlar (so‘z o‘yini variantlari) |
| other_translation | 652 | shu so‘zga boshqa qatorlarda berilgan boshqa tarjimalar |
| noun_genitive | 1685 | otning Genitiv shakli |
| noun_plural_variants | 29 | ikkinchi ko‘plik shakli |
| verb_perfekt | 1046 | `hat angerufen` |
| verb_separable / verb_conjugation_type | 1075 / 1075 | ajraladigan fe’lmi; schwach / stark / gemischt |
| conjunction_word_order | 153 | bog‘lovchidan keyingi so‘z tartibi |
| grammar_note | 214 | „nicht steigerbar“, „Partizip II als Adjektiv“ va h.k. |
| ipa | 3635 | talaffuz transkripsiyasi |

**Sxema kengaytmasi uchun taklif:**

- qo‘shimcha ustunlar: `translations_extra`, `genitive`, `separable`, `perfekt`, `ipa`;
- har bir maydon uchun alohida status: tarjima / grammatika / misol;
- `review_note` ustuni.

Bitta `status` ustuni „tarjima to‘g‘ri, misol tekshirilmagan“ kabi holatni ifodalay olmaydi.

## 8. Tekshirish kerak bo‘lganlar (`docs/worterbuch-needs-review.csv`)

Ustunlar: `level, id, lemma, word_type, translation, priority, reasons, suggestion`. Asosiy sabablar (qatorlar soni):

| Sabab | Qatorlar | Ma’nosi |
|---|---|---|
| example:not_reviewed | 5578 | misolni VIZU yozgan, o‘qituvchi tekshirmagan |
| grammar:not_in_wiktionary | ~977 | Wiktionary'da yo‘q (asosan iboralar) |
| translation:variants | 587 | bir so‘zga turli javoblar |
| translation:apostrophes_normalized | 301 | faqat apostrof yozilishi o‘zgardi |
| noun:plural_missing | 234 | ko‘plik topilmadi (ko‘pincha sanalmaydigan otlar) |
| grammar:compound_derived_from_* | ~400 | qo‘shma ot oxirgi bo‘lagidan aniqlangan |
| grammar:reflexive_pronoun_accusative_assumed | 118 | `mich/dich` (Akkusativ) taxmin qilingan; `mir/dir` emasligini tekshirish kerak |
| grammar:verb_homonym_forms_differ / noun_homonym_forms_differ | 18 so‘z | omonimlarning shakllari farq qiladi (pastga qarang) |
| example:missing | 22 | misol ataylab yozilmagan, chunki so‘z noto‘g‘ri |
| invalid_lemma / misspelling / wrong_article | 14 so‘z | `suggestion` ustunida to‘g‘ri variant |
| translation (bayroq) | 6 so‘z | aniq xato tarjima: „Wolkenkratzer = skyscraper“, „Vorurteil = xurofot“, „Betriebssystem = ish tizimi“ |

**Bu ishda topilgan va tuzatilgan xato (yangi himoya):**

- Muammo: Wiktionary'da omonim so‘zlarning shakllari farq qilishi mumkin. Masalan:
  - `bewegen`: bewog/bewogen (undamoq) va bewegte/bewegt (harakatlanmoq);
  - `Bank`: Bänke (o‘rindiq) va Banken (bank);
  - `Mutter`: Mütter (ona) va Muttern (gayka);
  - `übersetzen`.
- Avval birinchi variant tanlanardi; masalan „sich bewegen“ uchun „bewog“ chiqardi.
- Endi bunday 18 so‘z avtomatik `needs_review` oladi va to‘g‘ri shaklni ma’noga qarab inson tanlaydi.
- „während“ `Praeposition` deb belgilangan, lekin tarjimasi „holbuki“ — bu Konjunktion ma’nosi. Bayroq qo‘yildi.

## 9. Import bilan moslik

> **2026-10-28, keyinroq:** quyidagi holat o‘zgardi. Endi sayt to‘g‘ridan-to‘g‘ri `docs/` dagi CSVlarni import qiladi; ular yagona manba. `export_csv.py` docs'ni `--force` bersiz qayta yozmaydi. Batafsil: [worterbuch-integration-report.md](worterbuch-integration-report.md).

- Saytdagi lug‘at (`dictionary_entries`) **docs/ dagi CSVlardan to‘g‘ridan-to‘g‘ri o‘qilmaydi.** U zanjir bo‘yicha quriladi: asl fayllar (`backend/app/data/woerterbuch/source/`) + Wiktionary + misollar + bayroqlar → `dictionary.json` → import.
- Yangi docs CSVlar shu ma’lumotdan `export_csv.py` orqali yaratiladi. Bu jarayon takrorlanadi va test hamda yangi eksport natijasi diskdagi fayllar bilan baytma-bayt solishtiriladi.
- **Moslashtirish zarurati:** yangi CSVlarni qo‘lda tahrirlash (masalan, o‘qituvchi tuzatishlari) hozircha saytga o‘tmaydi.
- Ular haqiqiy manba bo‘lishi uchun keyingi bosqichda ikki ish kerak:
  - 22 ustunni o‘qiydigan import;
  - 7-bo‘limdagi sxema kengaytmasi, aks holda tarjima variantlari va maydon statuslari yo‘qoladi.
- Ungacha tuzatishlar `review_flags.json` va misol fayllari orqali kiritiladi.

Qayta yaratish buyruqlari:

```
cd backend
python -m app.scripts.woerterbuch.build
python -m app.scripts.woerterbuch.export_csv
```

## 10. Testlar

`tests/test_woerterbuch.py` — 30 test, hammasi OK. Bunga kiradi:

- 5 faylda bir xil sarlavha, 22 ustun, asl `id` va tartib;
- grammatika ustunlari faqat o‘z so‘z turkumida;
- `NULL`/`None`/`N/A` yo‘qligi;
- `verified` = 0;
- docs fayllari yangi eksport bilan baytma-bayt bir xil;
- ma’lum qatorlar: Apfel, anrufen, lärmlich;
- omonim himoyasi;
- PostgreSQL integratsiya testlari.

Butun backend: 796 test OK (17 skipped).

## 11. O‘zgargan fayllar

- **Qayta yozildi:** `docs/A1-words.csv`, `A2`, `B1`, `B2`, `C1`.
- **Yangi:**
  - `docs/backup/woerterbuch-csv-original-20261028/`;
  - `docs/worterbuch-csv-migration-report.md`;
  - `docs/worterbuch-needs-review.csv`, `worterbuch-duplicates.csv`, `worterbuch-original-counts.csv`, `worterbuch-extra-data.csv`;
  - `backend/app/scripts/woerterbuch/export_csv.py`.
- **O‘zgardi:**
  - `backend/app/scripts/woerterbuch/source.py` — asl fayllarni `data/woerterbuch/source/` dan o‘qiydi;
  - `build.py` — docs'dan nusxa olmaydi, `pos` bayrog‘ini qo‘llaydi;
  - `wiktionary.py` — omonim himoyasi;
  - `review_flags.json` — „während“ qo‘shildi;
  - `wiktionary_grammar.json`, `dictionary.json` — qayta qurildi;
  - `tests/test_woerterbuch.py`.
