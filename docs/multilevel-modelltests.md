# Multilevel Modelltest 1–10

Provider `NATIONAL` (National-Multilevel Zertifikat) → yangi daraja **„Multilevel B1–C1"**. Mavjud B1/B2/C1 darajalari tegilmagan.

## Manba va qoidalar

- 1–6: `D:\Multilevel_Pdf\Multilevel Mock Variant 1–6.pdf` dan so'zma-so'z (qisqartirilmagan). PDF larda javob kaliti,
  vaqt va baholash mezonlari **yo'q** → kalitlar bo'sh, vaqtlar standart (Lesen 60, Hören 40, Schreiben 60, Sprechen 15 daq.).
- 7–10: VIZU tomonidan yozilgan, namunalar bilan bir xil format: 7↔V1, 8↔V2, 9↔V3, 10↔V4 (Teil, savol va variant soni,
  matnlar so'z soni ±1%, `tests/test_multilevel_modelltests.py` tekshiradi). Kalitlar bor, Hören yo'q („Noch nicht verfügbar").
  Tavsif: „von VIZU erstellt (Übungstest, kein offizielles Prüfungsmaterial)".
- Ma'lumot: `backend/app/data/multilevel/modelltest-NN.json` (+ `images/`, 7–10 manbasi `src/mtNN.ml`),
  quruvchi `app/scripts/multilevel_build.py`.
- Import: `python -m app.scripts.multilevel_import plan --pdf-dir DIR` → `apply --confirm <plan id> --pdf-dir DIR`.
  Idempotent: bor test o'zgartirilmaydi/o'chirilmaydi, yangilari DRAFT. PDF + tekshiruv ro'yxati
  `app/protected_storage/mock-exam-sources/<model_test_id>.pdf|.json` (faqat Super Admin).
- Nashr: Admin → Prüfungsvorbereitung → Multilevel → Modelltest → „Veröffentlichen". Backend rad etadi
  (`MODEL_TEST_NOT_READY`), agar biror savolda kalit yo'q yoki Hören Teil audiosiz bo'lsa. Talaba sahifasi
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

## Ochiq

- Talaba pleyeri faqat ko'rsatadi (matn, savollar kalitsiz); javob berish/baholash oqimi hali yo'q.
- Hören audio admin media-upload orqali yuklanadi (mavjud mexanizm, `/uploads` — ochiq URL).
