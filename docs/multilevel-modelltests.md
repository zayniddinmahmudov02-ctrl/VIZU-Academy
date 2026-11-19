# Multilevel Modelltest 1–10

Provider `NATIONAL` (National-Multilevel Zertifikat) → yangi daraja **„Multilevel B1–C1"**. Mavjud B1/B2/C1 darajalari tegilmagan.

## Manba va qoidalar

- 1–6: `D:\Multilevel_Pdf\Multilevel Mock Variant 1–6.pdf` dan so'zma-so'z (qisqartirilmagan). PDF larda javob kaliti,
  vaqt va baholash mezonlari **yo'q** → kalitlar bo'sh, vaqtlar (2026-11-16, egasi): Lesen 60, Hören 60, Schreiben 60, Sprechen 15 daq. = 195 daq.
- 7–10: VIZU tomonidan yozilgan, namunalar bilan bir xil format: 7↔V1, 8↔V2, 9↔V3, 10↔V4 (Teil, savol va variant soni,
  matnlar so'z soni ±1%, `tests/test_multilevel_modelltests.py` tekshiradi). Kalitlar bor, Hören yo'q („Noch nicht verfügbar").
  Tavsif: „von VIZU erstellt (Übungstest, kein offizielles Prüfungsmaterial)".
- Ma'lumot: `backend/app/data/multilevel/modelltest-NN.json` (+ `images/`, 7–10 manbasi `src/mtNN.ml`),
  quruvchi `app/scripts/multilevel_build.py`.
- Import: `python -m app.scripts.multilevel_import plan --pdf-dir DIR` → `apply --confirm <plan id> --pdf-dir DIR`.
  Idempotent: bor test o'zgartirilmaydi/o'chirilmaydi, yangilari DRAFT. PDF + tekshiruv ro'yxati
  `app/protected_storage/mock-exam-sources/<model_test_id>.pdf|.json` (faqat Super Admin).
- Nashr: Admin → Prüfungsvorbereitung → Multilevel → Modelltest → „Veröffentlichen". 7–10: backend rad etadi
  (`MODEL_TEST_NOT_READY`), agar biror savolda kalit yo'q yoki Hören Teil audiosiz bo'lsa. 1–6 (2026-11-19 dan): kalit / audio
  yo'qligi faqat ogohlantirish, faqat bo'lim yo'q bo'lsa rad etadi (pastda „Modelltest 1–6 ochiq"). Talaba sahifasi
  `/vorbereitung/multilevel` faqat PUBLISHED testlarni ochadi.

## Admin tekshiruv ro'yxati (qisqa)

| Test | Tekshirish kerak |
|---|---|
| 1–6 | Barcha kalitlar (Lesen 35, Hören 35/30) PDF da yo'q — admin kiritadi; Hören audio yuklanadi |
| 1 | Sprechen T3 (S. 24) Pro/Contra jadvali |
| 2 | Hören T3 (S. 15) o'zbekcha ko'rsatma qatori olib tashlangan; Hören T4 (S. 17) jadval |
| 3 | Sprechen T1.1 (S. 22) asl grammatik xatolar; Sprechen T3 (S. 23) jadval |
| 4 | Sprechen T2 (S. 20) asl xatolar; Sprechen T3 (S. 20) Pro/Contra tartibi |
| 5 | Hören S. 12–15 va Sprechen S. 18–19 rasmdan ko'chirilgan; Schreiben T1 (S. 16) tartib; Sprechen T1.2 rasm butun sahifa |
| 6 | Butun PDF rasm (18 bet) — hammasi rasmdan ko'chirilgan; Lesen T3 (S. 5) ko'rsatma V5 dan; Sprechen T1.2 (S. 17) rasm |
| 7–10 | Sprechen T1.2 uchun ikki rasm yuklash kerak |

To'liq ro'yxat har bir test sahifasida („Prüfliste").

## Imtihon rejimi (2026-11-06)

- Talaba `/vorbereitung/multilevel` → Modelltest → „Prüfung starten". Daraja tanlanmaydi. Bitta testga bitta ochiq urinish,
  yakunlangandan keyin qayta topshirish; barcha urinishlar saqlanadi (tarix: shu sahifa + profil/„Einstellungen").
- Bo'limlar (Lesen, Hören, Schreiben, Sprechen) istalgan tartibda, bir vaqtda bittasi; vaqt = `Kompetenz.duration_minutes`,
  muddatni server qo'yadi (+30 s), muddatdan keyin javob qabul qilinmaydi va bo'lim avtomatik yopiladi. Javoblar topshirguncha
  o'zgartiriladi. „Prüfung beenden": boshlanmagan bo'limlar 0 ball.
- Ball faqat serverda: Lesen/Hören = to'g'ri/savollar × 75 (yaxlitlash), Schreiben/Sprechen = o'qituvchi 0–75 beradi
  (Admin → „Multilevel (National Zertifikat)"); hech narsa yozilmagan/yozib olinmagan bo'lsa avtomatik 0. Jami /300.
- Bo'lim darajasi: 0–38 Nicht bestanden, 39–49 B1, **50 = sozlama** (standart „Ungeklärt"), 51–64 B2, 65–75 C1.
- Umumiy daraja: sozlama „Gesamtniveau" — standart **„Nicht bestätigt" → Ungeklärt** (rasmiy qoida yo'q); Super Admin
  „Durchschnitt" yoki „Niedrigstes Teilniveau" ni tanlashi mumkin, saqlangan natijalar qayta hisoblanadi (audit log).
- Natija va to'g'ri javoblar faqat 4 bo'lim yopilgandan keyin. Sprechen yozuvlari private (`protected_storage/mock-exam-speaking`).
- Nashr qilish: barcha 4 bo'lim to'liq bo'lishi shart → 7–10 (Hören bo'sh) nashr qilinmaydi; 1–6 — kalit / audio yo'qligi ogohlantirish (2026-11-19).

## Hören kalitlari 1–6 va imtihon vaqtlari (2026-11-16)

- Egasi bergan Hören kalitlari: `backend/app/data/multilevel/hoeren-keys.json` (harflar aynan yozilganidek: R / F / A / B / C, katta-kichik harf tekshiruvda bir xil).
  Soni: 1-test 35, 2–6 testlar 30 ta (jami 185). Harf → variant: a/b/c = 1/2/3-variant, A–H moslashtirishda, R/F (yoki a/b) rost-yolg'on uchun.
- Admin → Multilevel → „Answer Key": test + bo'lim (Hören / Lesen) tanlanadi, raqamlangan jadval, bitta javobni tahrirlash, ro'yxatni joylash (`1-b, 2-b, …`) →
  „Prüfen" (son va harflar tekshiriladi) → „Übernehmen". Hammasi yoki hech narsa; audit logga yoziladi.
- Productionga qo'llash: `python -m app.scripts.multilevel_hoeren_keys plan` → `apply --confirm <plan id>` (mavjud boshqa kalit bo'lsa to'xtaydi, `--overwrite` kerak).
  Skript Hören kalitlarini va barcha Modelltestlarning vaqtini (Lesen 60, Hören 60, Schreiben 60, Sprechen 15 = 195 daq.) o'rnatadi; Lesen kalitlari, audio, Schreiben va Sprechen topshiriqlariga tegmaydi.
- **Hali yetishmaydi (1–6):** har bir testda Lesen kalitlari (35 / 30 ta, hozir 0) va 2–6 ning Hören audiosi (4 Teildan) — Answer Key vositasi Lesen uchun ham ishlaydi; audio: „Multilevel Audio".
  2026-11-19 dan bular nashrni to'xtatmaydi (pastga qarang).

## Modelltest 1 — bitta umumiy Hören audio (2026-11-16)

- Modelltest 1 ning Hören bo'limidagi 6 ta Teil **bitta** audio fayldan foydalanadi (`kompetenzen.audio_file_id`); boshqa testlarda har Teil uchun alohida audio (o'zgarmagan).
- Admin → Vorbereitung → Multilevel Audio → „Modelltest 1 · Gemeinsames Audio": yuklash, almashtirish, kesish, tinglash, o'chirish (o'chirilsa nashr qilingan test
  yana Entwurf bo'ladi). Shu testning Teil-slotlari alohida audio qabul qilmaydi (409 `SHARED_AUDIO_TEST`).
- Talaba: Hören bo'limida pastda bitta audio pleyer; Teil'lar o'z savollari bilan alohida ko'rinadi, Teil'dan Teil'ga o'tganda audio qayta boshlanmaydi,
  sahifa yangilansa audio taxminan shu joydan davom etadi. Audio davomiyligi va bo'lim vaqti (60 daq.) bir-biriga bog'liq emas.

## Multilevel Modelltest Premium (2026-11-16)

- Talaba panelida 10 ta Modelltest ko'rinadi. 2026-11-19 dan **1–6 hamma uchun bepul**, Premium faqat **7–10** ni ochadi
  (xodimlar uchun hammasi ochiq). Nashr qilinmagan (DRAFT) testlar «Tayyorlanmoqda» bo'lib turadi — ularni boshlab bo'lmaydi.
- Premium: bir martalik to'lov, narxi serverda (standart 99 000 so'm, `offers.ML_PREMIUM_PRICE`; Admin → Payments → Payment Settings
  da o'zgartirish yoki sotuvni to'xtatish mumkin, audit), muddatsiz.
- To'lov: karta 9860 0401 1406 3742 → chek (JPG/PNG/PDF) yoki «Chek mavjud emas» + sana va vaqt → PENDING → Super Admin
  (Admin → Payments → Multilevel Modelltest Payments) tasdiqlaydi yoki sabab bilan rad etadi. Tasdiq bir marta ishlaydi; refund
  Premiumni bekor qiladi.
- Promo: Multilevel kategoriyasidagi kod (foiz yoki 100 % bepul) faqat Super Admin tasdiqlab faollashtirgandan keyin ishlaydi;
  100 % kod to'lovsiz hamma testni ochadi. Kurs kodlari bu yerda ishlamaydi.

## Modelltest 1–6: yumshoq nashr qoidasi (2026-11-19)

- Kirish: **1 dan 10 gacha barcha Modelltest Multilevel Premium talab qiladi** (egasi, 2026-11-19 kech; 2026-11-18…19 kunlari 1–6 bepul edi).
  Bepul raqamlar `multilevel_service.FREE_TEST_NUMBERS` (hozir bo'sh); xodimlar (admin / kontent) har doim kiradi.
- `OPEN_TEST_NUMBERS` (1–6) endi faqat nashr qoidasini bildiradi, kirishni emas.
- Nashr: 1–6 da kalitsiz savollar va audiosiz Hören Teil'lar **ogohlantirish** („Nur Warnungen — Veröffentlichen ist möglich"); faqat bo'lim yo'q bo'lsa
  `MODEL_TEST_NOT_READY`. 7–10 eski qoida bilan. Audio o'chirilsa 1–6 nashrdan tushmaydi.
- Ball: kaliti yo'q savol hisoblanmaydi (maksimumga ham kirmaydi). Bo'limda birorta kalit bo'lmasa (hozir Lesen 1–6) — „baholanmaydi",
  jami maksimum 225 (300 o'rniga), natija sahifasida „Für diesen Teil gibt es noch keine Lösungen", savollar „nicht bewertet". Kalit kiritilgandan keyin
  yangi urinishlar avtomatik to'liq hisoblanadi (eski urinishlar o'zgarmaydi).
- Audiosiz Hören Teil: „Audio noch nicht verfügbar" yozuvi, savollarga javob berish mumkin.
- Productionga: `python -m app.scripts.multilevel_open_tests plan` (faqat o'qiydi) → `apply --confirm <plan id>`. Skript: ishlatilmagan „Variant 1 Hören"
  ORIGINAL faylini Modelltest 1 umumiy audiosi qilib bog'laydi (bir ma'noli bo'lsa; 2–6 Teil-audio talab qiladi → MANUAL), 1–6 ni nashr qiladi, audit
  `multilevel_audio_shared_set` / `multilevel_open_publish`. Bekor qilish: Multilevel Audio → Modelltest 1 → audio o'chirish (fayl Media'da qoladi) / „Verbergen".

## Ochiq

- 7–10 Hören: vazifalar (savollar + audio) hali yo'q; savollarni admin panelda yaratib bo'lmaydi — import kerak.
- 1–6 Lesen kalitlari (PDF da yo'q) va 2–6 Hören audio — egasi kiritadi / yuklaydi.
- Lesen/Hören uchun xom ball → 75 chiziqli konvertatsiya; rasmiy konvertatsiya jadvali bo'lsa, almashtirish kerak.
