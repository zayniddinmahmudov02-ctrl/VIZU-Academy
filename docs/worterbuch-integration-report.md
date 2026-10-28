# Wörterbuch integratsiyasi: CSV → baza → sayt

Sana: 2026-10-28 · Holat: **lokal va test bazada ishlaydi, production'ga chiqarilmagan.**

## 1. Arxitektura

```
docs/{A1..C1}-words.csv            22 ustun, yagona manba (5600 qator)
docs/worterbuch-extra-data.csv     level+id orqali bog‘lanadi
docs/worterbuch-needs-review.csv   level+id orqali bog‘lanadi
        │  python -m app.scripts.import_woerterbuch [--dry-run]
        ▼
dictionary_entries                 bitta CSV qatori = bitta yozuv, UNIQUE(level, source_id)
dictionary_user_words              UNIQUE(user_id, entry_id): yulduzcha va ko‘rilgan so‘zlar
        │  /api/v1/dictionary/*  (faqat tizimga kirgan foydalanuvchi)
        ▼
/woerterbuch                       Wörterbuch suchen · Random Wörter · Gespeicherte Wörter
```

- **So‘z ID'si:** `level-id`, masalan `A1-2`. Ya’ni CSV fayli va undagi asl `id`.
- **Takror qatorlar:**
  - bir daraja ichida takrorlangan qatorlar ham alohida saqlanadi;
  - qidiruv va Random'da guruhning faqat birinchi qatori ko‘rsatiladi (`is_primary`), toki „Haus“ ro‘yxatda uch marta chiqmasin;
  - turli darajalardagi bir xil so‘z alohida yozuv bo‘lib qoladi; kartochkada „B1 ro‘yxatida ham“ deb ko‘rsatiladi.
- **Yashirin qatorlar:** so‘zning o‘zi noto‘g‘ri bo‘lgan 18 qator (`invalid_lemma` / `misspelling` / `wrong_article`) bazada saqlanadi, lekin ko‘rsatilmaydi.
- **Status:** CSV'dagi status o‘zgarishsiz olinadi; `needs_review` hech qachon `verified` ga aylantirilmaydi. Kartochkada „tekshirilmagan“ belgisi turadi.

## 2. Ma’lumotlar bazasi

- Migratsiya: `d4b8e2f6a9c1_woerterbuch` (down: `a7c2e9f4b1d6`). Faqat 2 ta yangi jadval yaratadi; mavjud jadvallarga tegmaydi.
- **Bu migratsiya qayta yozildi.** Oldingi varianti faqat lokal test bazalarda ishlatilgan edi. Production'ga chiqarishdan oldin serverda `alembic current` = `a7c2e9f4b1d6` ekanini tekshirish kerak.
- **Indekslar:**
  - `search_de` (`text_pattern_ops`, prefiks qidiruvi uchun);
  - `(is_published, is_primary, level)`, `(level, group_key)`, `word_type`;
  - foydalanuvchi so‘zlari: `user_id`, `entry_id`, `(user_id, saved)`.
- **Foreign key'lar:** `users.id` va `dictionary_entries.id` ga, `ON DELETE CASCADE` bilan.
- **Tekshirildi:** test bazada upgrade → downgrade → upgrade sikli o‘tdi.

## 3. Import

```
cd backend
python -m app.scripts.import_woerterbuch --dry-run   # tekshirish, hech narsa yozmaydi
python -m app.scripts.import_woerterbuch             # yozish (bitta tranzaksiya)
```

- **Avval tekshiruv:** barcha fayllar validatsiyadan o‘tadi. Sarlavha, 22 ustun, id raqam va takrorlanmaganligi, daraja, status, artikl tekshiriladi. Bitta xato bo‘lsa ham hech narsa yozilmaydi va xatolar ro‘yxati chiqadi (exit kodi 2).
- **Idempotent:**
  - `(level, id)` + content hash bo‘yicha ishlaydi;
  - o‘zgargan qator joyida yangilanadi, shuning uchun saqlangan yulduzchalar yo‘qolmaydi;
  - hech narsa o‘chirilmaydi: CSV'dan yo‘qolgan qatorlar faqat hisobotga yoziladi.
- **Test bazadagi natija:**

| | A1 | A2 | B1 | B2 | C1 | Jami |
|---|---|---|---|---|---|---|
| Import qilingan qatorlar | 1000 | 1000 | 1000 | 1500 | 1100 | **5600** |
| `needs_review` / `verified` | 1000 / 0 | 1000 / 0 | 1000 / 0 | 1500 / 0 | 1100 / 0 | 5600 / 0 |
| Saqlangan takror qatorlar | 262 | 366 | 753 | 264 | 57 | 1702 |
| Yashirilgan | 1 | 7 | 4 | 3 | 3 | 18 |
| Qidiruvda ko‘rinadigan so‘zlar | 737 | 628 | 246 | 1233 | 1040 | 3884 |
| Extra-data bog‘langan | 1000 | 1000 | 1000 | 1500 | 1100 | 5600 |

Ikkinchi marta ishga tushirilganda 5600 qatorning hammasi `unchanged`, yangi yozuv yaratilmadi. Ogohlantirishlar: 0.

## 4. API (`/api/v1/dictionary`)

| Metod | Yo‘l | Vazifasi |
|---|---|---|
| GET | `/meta` | darajalar bo‘yicha sonlar, so‘z turkumlari |
| GET | `/search?q=&level=&word_type=&page=&page_size=` | qidiruv (autocomplete), standart 10 ta natija |
| GET | `/entries/{level-id}` | to‘liq kartochka |
| POST | `/random` `{level: "ALL" \| "A1".."C1"}` | 5 ta so‘z |
| PUT | `/entries/{level-id}/saved` `{saved: bool}` | yulduzcha; idempotent |
| GET | `/saved?q=&level=&page=` | saqlangan so‘zlar: qidiruv, filtr, sahifalash |

Barcha endpointlar `get_current_user` talab qiladi. Foydalanuvchi har doim tokendan olinadi, so‘rov tanasidan emas.

## 5. Qidiruv

- **Qidiriladigan maydonlar:**
  - nemischa lemma (artikl va „sich“ siz ham topadi);
  - o‘zbekcha tarjima va qo‘shimcha tarjimalar;
  - grammatik shakllar: Plural, Präteritum, Partizip II, Präsens, Komparativ, Superlativ.
- **Natijalar tartibi:**
  1. lemma to‘liq mos keladi;
  2. lemma yozilgan harflar bilan boshlanadi;
  3. o‘zbekcha so‘z to‘liq mos keladi;
  4. grammatik shakl mos keladi;
  5. o‘zbekcha so‘z yozilgan harflar bilan boshlanadi;
  6. lemma ichida uchraydi.
- **Normalizatsiya:**
  - katta-kichik harf farq qilmaydi;
  - `ä/ae → a`, `ß → ss`;
  - o‘zbekcha apostroflar birlashtiriladi;
  - `%` va `_` oddiy belgi sifatida qidiriladi.
- **Misol:** `Haus` → Haus, Haushalt, Haustier, Hausaufgabe, Hausmeister… Boshqa misollar: `uy` → Haus; `läuft` → laufen; `aepfel` → Apfel; `Straße` = `Strasse`. Javob vaqti test bazada 5–60 ms.
- **Interfeys:**
  - `combobox` + `listbox`; natijalar har bir harfdan keyin yangilanadi (150 ms debounce);
  - ↑/↓ va Enter bilan tanlash; „Yana yuklash“ tugmasi;
  - natija topilmasa — xabar;
  - mobil qurilmada kartochka ro‘yxat ostida ochiladi va ekran unga aylantiriladi.

## 6. Random Wörter

- **Algoritm:**
  - „Aralash“ rejimida har bir darajadan bittadan, ya’ni 5 xil darajadan 5 ta so‘z;
  - biror daraja yetmasa, boshqalaridan to‘ldiriladi;
  - bitta to‘plamda bir xil nemischa so‘z ikki marta chiqmaydi;
  - foydalanuvchi oxirgi 7 kunda ko‘rgan so‘zlar faqat boshqasi qolmaganda qaytadi;
  - tanlov PostgreSQL `random()` bilan qilinadi, shuning uchun har safar boshqa so‘zlar chiqadi.
- **Tekshirildi:** 8 ta ketma-ket to‘plamda takror yo‘q, har birida 5 ta daraja; „Yana 5 ta so‘z“ oldingi to‘plam bilan kesishmadi.
- **Kartochka:**
  - so‘z, tarjima, daraja, turkum, qisqa grammatika qatori;
  - misol gap, talaffuz, yulduzcha;
  - „Batafsil“ tugmasi to‘liq kartochkani dialog oynasida ochadi.

## 7. Yulduzcha va saqlangan so‘zlar

- **Yulduzcha:**
  - to‘ldirilgan yulduz — saqlangan, kontur — saqlanmagan;
  - har bir bosish server bilan sinxron ishlaydi va qisqa xabar chiqaradi („So‘z saqlandi“ / „Saqlanganlardan olib tashlandi“);
  - bitta bosish qidiruv, kartochka, Random va saqlanganlar ro‘yxatini bir vaqtda yangilaydi (react-query keshi).
- **Ikki marta saqlash** dublikat yaratmaydi: `UNIQUE(user_id, entry_id)` + `ON CONFLICT`.
- **„Gespeicherte Wörter“ bo‘limi:**
  - nemischa yoki o‘zbekcha qidirish;
  - darajalar bo‘yicha filtr (har birida son);
  - sahifalash, kartochka;
  - yulduzcha orqali olib tashlash;
  - bo‘sh holat uchun xabar.
- **Ruxsatlar:** boshqa foydalanuvchining saqlangan so‘zlari ko‘rinmaydi. Bu test va real HTTP orqali tekshirildi.
- **Anonim foydalanuvchi:** qo‘llab-quvvatlanmaydi. Sahifa mavjud login tizimi ortida.

## 8. Talaffuz (TTS)

- Brauzerning `speechSynthesis` funksiyasi, `de-DE` ovozi bilan.
- Tugmalar: so‘z (`audio_text`) va misol gap. `audio_text` bo‘sh bo‘lsa, tugma umuman chiqmaydi.
- Audio fayllar yo‘q va soxta audio yaratilmagan.
- Ovoz yo‘q yoki TTS qo‘llab-quvvatlanmagan bo‘lsa, aniq xabar chiqadi.

## 9. Testlar

- **`tests/test_woerterbuch.py` — 31 test OK.** Tekshiriladi:
  - import: 5600 qator, darajalar, id, extra-data, `verified` = 0, saqlangan 1702 ta takror, idempotentlik;
  - xatoli fayl rad etiladi va bazaga yozilmaydi;
  - qidiruv: prefiks avval, o‘zbekcha, umlaut / ß, grammatik shakllar, filtrlar, LIKE belgilari;
  - kartochka so‘z turkumi bo‘yicha; yashirin qatorlar;
  - Random: 5 xil so‘z, 5 xil daraja, keyingi to‘plam yangi;
  - yulduzcha: foydalanuvchiga xos, idempotent, sinxron;
  - barcha route'lar autentifikatsiya talab qiladi.
- **Butun backend:** 797 test OK (17 skipped).
- **Real HTTP** (lokal uvicorn + test baza + haqiqiy login):
  - tokensiz barcha endpointlar 401;
  - qidiruv, kartochka, 404, Random, 422, saqlash/olib tashlash ishladi;
  - ikkinchi foydalanuvchi birinchisining so‘zini ko‘rmadi.
- **Frontend:** `tsc` OK, `eslint` OK, `next build` OK (`/woerterbuch`).
- **Tekshirilmagan:** brauzerda haqiqiy ekranda (desktop/mobil) qo‘lda sinov. Bu sessiyada brauzer vositasi yo‘q edi. Responsive layout kodda bor (`sm`/`lg` grid, mobilda pastdan ochiladigan dialog), lekin ko‘z bilan tekshirilmagan.

## 10. Holat

| Muhit | Holat |
|---|---|
| Lokal / test baza | ishlaydi, testlar o‘tdi |
| Staging | yo‘q (loyihada staging muhit yo‘q) |
| Production | **chiqarilmagan.** Migratsiya, import va frontend deploy tasdiq kutmoqda |

**Production uchun reja** (tasdiqdan keyin):

1. Baza backup.
2. `alembic current` = `a7c2e9f4b1d6` ekanini tekshirish.
3. `alembic upgrade head`.
4. `import_woerterbuch --dry-run`, keyin import.
5. Frontend'ni bo‘sh slotga build qilish.
6. Smoke test: `/woerterbuch`.

## 11. Qolgan masalalar

- 5600 qatorning hammasi `needs_review`. O‘qituvchi tekshiruvi uchun admin sahifa yo‘q; tuzatishlar CSV'ni tahrirlab, qayta import qilish orqali kiritiladi.
- Brauzerda qo‘lda UI sinovi qilinmagan (desktop va mobil).
- `docs/` dagi CSV endi manba. `export_csv.py --force` ularni qayta yozib, qo‘lda kiritilgan tuzatishlarni o‘chirib yuboradi; uni faqat ataylab ishlatish kerak.
- „ging“ kabi so‘zlar topilmaydi, agar ularning lemmasi (gehen) ro‘yxatda bo‘lmasa. Qidiruv faqat CSV'dagi shakllar bo‘yicha ishlaydi.
