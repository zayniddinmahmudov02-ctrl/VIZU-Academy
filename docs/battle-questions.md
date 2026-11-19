# VIZU Battle — matnli savollar bazasi (A1–C1)

2026-11-19. Rasmli savollardan tashqari har bir darajada kamida 500 ta lug'at va grammatika savoli. Rasmli tizim (`battle_words`,
`battle_images`, 89 ta A1 so'zi) o'zgarmagan.

## Qayerda

| Qism | Fayl |
| --- | --- |
| Jadval | `battle_questions` (`backend/app/models/battle.py`), migratsiya `a6c2e8f4b9d1` |
| Qoidalar, validatsiya, tanlash, admin CRUD/import, statistika | `backend/app/services/battle/question_bank.py` |
| O'yinga qo'shish | `backend/app/services/battle/questions.py` (`build`), raund ko'rinishi `engine.py` (`_text_round_view`) |
| Savollar (manba) | `backend/app/data/battle/questions/{A1,A2,B1,B2,C1}.json` |
| Seed | `python -m app.scripts.battle_questions_seed plan` → `apply --confirm <plan id>` |
| Admin | Admin → Game Management → Battle → „Fragen (Wortschatz & Grammatik)“ |
| Testlar | `tests/test_battle_questions.py`, `test_battle_questions_migration.py`, E2E `battle-questions.spec.ts` |

## Formatlar (10 ta)

`de_uz` (nemischa → o'zbekcha), `uz_de` (o'zbekcha → nemischa), `word_choice` (to'g'ri nemischa so'z), `gap` (gapdagi bo'sh joy),
`grammar` (to'g'ri grammatik variant), `article` (der/die/das, 3 ta variant), `verb_form` (fe'l shakli), `synonym`, `antonym`,
`collocation` (so'z birikmasini yakunlash). Har birining nemischa + o'zbekcha ko'rsatmasi o'yinda chiqadi.

## Sonlar (seed fayllari)

| Daraja | Jami | Lug'at | Grammatika | Wörterbuch'dan | Qo'lda yozilgan | Mavzular |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 664 | 510 | 154 | 530 | 134 | 30 |
| A2 | 632 | 320 | 312 | 518 | 114 | 16 |
| B1 | 528 | 144 | 384 | 77 | 451 | 17 |
| B2 | 568 | 430 | 138 | 425 | 143 | 17 |
| C1 | 569 | 442 | 127 | 425 | 144 | 19 |
| **Jami** | **2961** | 1846 | 1115 | 1975 | 986 | |

- Lug'at: faqat production'dagi **tasdiqlangan** Wörterbuch qatorlaridan (tarjima, artikl, misol gap). Har bir so'zdan **bitta**
  savol (bir so'z turli shaklda takrorlanmaydi). Quyi darajada bor so'z yuqori darajada qayta so'ralmaydi (B1 Wörterbuch'idagi 246
  so'zdan 167 tasi A1/A2'da bor — shuning uchun B1 asosan qo'lda yozilgan grammatika).
- A1 lug'ati mavzular bo'yicha (oila, uy, oziq-ovqat, ranglar/raqamlar, kasblar, hayvonlar, vaqt, transport, joylar, tana, kiyim,
  bo'sh vaqt, tabiat, o'qish/ish, fe'llar, sifatlar); A2–C1 lug'ati so'z turkumi bo'yicha + kollokatsiya, sinonim/antonim, frazeologizm.
- Grammatika mavzulari daraja bo'yicha (A1: sein/haben, Präsens, olmoshlar, W-Fragen, nicht/kein, Possessiv, Modalverben, vaqt
  predloglari, Akkusativ, Imperativ; A2: Akk/Dat, Perfekt, trennbare Verben, Wechselpräpositionen, Komparativ, Präteritum, weil/dass/wenn …;
  B1: Konnektoren, Relativsätze, Passiv, zu-Infinitiv, Konjunktiv II, Plusquamperfekt, Präpositionen, predlogli fe'llar,
  Adjektivdeklination, Wortbildung …; B2: Passiversatz, Konjunktiv I/II, Nominalisierung, Partizipien, Genitiv-predloglar …;
  C1: murakkab bog'lovchilar, gap tuzilmasi, Nominalstil, Stilistik, murakkab predloglar …). Test `GRAMMAR_BY_LEVEL` A1'ga C1
  mavzusini kiritmaydi.

## Sifat qoidalari (avtomatik tekshiriladi)

- Bitta aniq to'g'ri javob: variantlar normallashtirilgandan keyin ham har xil, to'g'ri javob noto'g'rilar ichida yo'q.
- Chalg'ituvchilar: Wörterbuch savollarida shu daraja + shu so'z turkumidan (A1: shu mavzudan), ma'nosi yaqin so'z olinmaydi
  (inglizcha izoh, o'zbekcha so'z o'zagi, nemischa o'zak tekshiriladi); o'zbekcha tarjimasi boshqa so'zga ham to'g'ri keladigan so'zdan
  uz→de savol tuzilmaydi; bo'sh joyli gapda o'zbekcha tarjima yo'llanma bo'ladi. Qo'lda yozilganlarda muqobil to'g'ri javoblar
  (masalan „Sport machen“, „Was kostet …?“) variantga kiritilmagan.
- Takror yo'q: `norm_key` (format + normallashtirilgan savol) daraja ichida unique (bazada ham); darajalar orasida ham bir xil savol yo'q.
- O'zbekcha: kirill harfi yo'q, apostroflar Wörterbuch kabi (o‘ g‘ — U+2018, tutuq belgisi — U+2019).
- Validator kodlari (admin'da „Fehlerhaft“): `OPTIONS_NOT_UNIQUE`, `OPTION_COUNT`, `GAP_MISSING`, `ARTICLE_OPTIONS`, `TOPIC_KIND`,
  `CYRILLIC`, `UZ_APOSTROPHE`, `SPACES` …

## O'yinda

- Bosqich o'z darajasining faol (`published`) savollarini o'ynaydi (C1+ → C1). Daraja o'z rasmli so'zlariga ega bo'lsa (bugun A1),
  10 raunddan 4 tasi rasmli (`config.PICTURE_ROUNDS`), qolgani matnli; A2+ o'yinda kamida 3 ta grammatika savoli (`MIN_GRAMMAR`).
- Bir o'yinda bir savol (va bir so'z) ikki marta chiqmaydi; o'yinchilarning oxirgi 3 o'yinidagi savollar faqat boshqa savol qolmasa
  chiqadi. Javob kaliti va izoh raund tugagandan keyingina yuboriladi. Ball, vaqt, reyting, bot — o'zgarmagan.
- Matnli savol bo'lmasa (yoki < 10) bosqich avvalgidek faqat rasmli raundlarni o'ynaydi.

## Admin

Statistika (daraja bo'yicha: jami, lug'at, grammatika, faol, qoralama, o'chirilgan, takroriy, xatoli), filtrlar (daraja, tur, mavzu,
format, holat, „faqat xatolilar“), savol qo'shish / tahrirlash / o'chirish (audit yoziladi), JSON import (avval tekshirish: yaroqli /
takroriy / xatoli, keyin qo'shish; mavjud savollar o'zgartirilmaydi). Rasmli so'zlar „Wörter & Bilder“ bo'limida, avvalgidek.

## Qayta qurish (ishlab chiquvchi uchun)

Seed fayllari `D:\vz_tmp\work\bq_build\` dagi generator bilan yaratilgan (production'dagi tasdiqlangan Wörterbuch eksporti + qo'lda
yozilgan `authored/<daraja>.txt`). Fayllar repoda — yangi savol qo'shish uchun admin panel yoki import yetarli.
