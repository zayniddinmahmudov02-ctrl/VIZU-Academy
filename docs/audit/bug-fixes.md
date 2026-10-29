# Tuzatilgan xatolar (2026-10-29)

Barcha o‘zgarishlar **lokal**: commit qilinmagan, prod’ga deploy qilinmagan, prod bazasi migratsiya qilinmagan. Xavfsizlik tuzatishlari tafsiloti: [security-findings.md](security-findings.md).

## B-1 · P1 · Dars kompetensiyasini ochishda HTTP 500 (race condition)

- **Belgisi.** Prod’da 48 soat ichida `POST /api/v1/lms/lessons/{id}/competencies/{KIND}/visit` 53 marta 500 qaytargan: `IntegrityError: uq_student_competency_progress`. Barcha 9 ta kompetensiyada uchragan.
- **Sabab.** `record_visit()`, `persist()` va `_progress_row()` "o‘qi → yo‘q bo‘lsa yarat" usulida ishlaydi. Bitta talaba va bitta dars uchun ikkita parallel so‘rov ikkalasi ham "qator yo‘q" ni ko‘radi va ikkalasi ham INSERT qiladi.
- **Tuzatish.** `app/services/lms/progress.py` ga `_lock_lesson()` qo‘shildi: (talaba, dars) juftligi uchun `pg_advisory_xact_lock` (Global Chat’dagi naqsh bilan bir xil). `record_visit()` va `sync_lesson()` boshida chaqiriladi, lock commit’gacha ushlanadi. Boshqa talabalar yoki darslar bloklanmaydi.
- **Test.** `backend/tests/test_lms_visit_race.py`: 8 ta thread barrier orqali bir vaqtda visit yuboradi.
  - **Tuzatishdan oldin:** ikkala test ham `UniqueViolation` bilan yiqildi, ya'ni prod xatosi takrorlandi.
  - **Keyin:** 3 marta ketma-ket ishga tushirilganda 3/3 OK.

## B-2 · P2 · `/admin/media` sahifasi hech qachon deploy bo‘lmagan

- **Sabab.** Ildizdagi `.gitignore` da `media/` qoidasi bor. U backend media katalogi uchun yozilgan, lekin `frontend/src/app/admin/media/` ni ham ignore qilgan. Sahifa lokalda mavjud, git’da yo‘q.
  - Prod’da `/admin/media` 404 qaytaradi.
  - Page catalog esa unga havola qiladi, shuning uchun serverda `test_page_management` yiqilardi.
- **Tuzatish.** `.gitignore` ga `!frontend/src/app/admin/media/` istisnosi qo‘shildi.
- **Tekshiruv.** Serverda vaqtinchalik klonda (`/tmp`, keyin o‘chirildi) `git check-ignore` ishga tushirildi:
  - sahifa — tracked;
  - `backend/media/x.mp4` va `backend/uploads/y.png` — avvalgidek ignore.
- **Production build:** `/admin/media` ro‘yxatda bor va lokal stack’da 200 qaytaradi.
- **Kerak:** `frontend/src/app/admin/media/page.tsx` ni commit qilish. Bu fayl foydalanuvchining oldingi ishi, unga tegilmadi.

## B-3 · P2 · Migratsiyalarni `downgrade base` qilib bo‘lmasdi

| Revision | Sabab | Tuzatish |
|---|---|---|
| `87727891177f` | `drop_constraint(None, 'payments')` — autogenerate nom bermagan | Postgres bergan nom bilan: `payments_transaction_id_key` |
| `91184abc44ec` | `ix_student_speakings_user_id` ni `c9e4f2b8a1d7` downgrade’i allaqachon o‘chirgan | `drop_index(..., if_exists=True)` |
| `3b259bd099c5` | Ikkita nomsiz FK uchun `drop_constraint(None, ...)` | Olib tashlandi, chunki FK keyingi `drop_column` bilan birga o‘chadi |

- **Test.** Toza `vizu_audit` bazasida:
  - `upgrade head` → `downgrade base` (faqat `alembic_version` qoladi) → `upgrade head` — exit 0.
  - **Oldin:** `downgrade` 3 joyda yiqilgan.
- **Upgrade yo‘li o‘zgarmadi**, prod bazaga ta’sir qilmaydi.

## B-4 · P3 · Page catalog’da `/admin/groups` yo‘q edi

- **Sabab.** Groups & Classroom sahifasi `app/services/page_management.py` dagi `_ROUTES` ga qo‘shilmagan. Natijada uni yashirib yoki arxivlab bo‘lmaydi va test yiqiladi.
- **Tuzatish.** `/admin/groups` qo‘shildi, `groups` domeni `study_group*` jadvallari bilan.
- **Test.** `tests/test_page_management.py`: 12/12. Domen jadvallarining hammasi `Base.metadata` da borligi tekshirildi.

## B-5 · P2 · Model va sxema farqi (`alembic check`)

- **Sabab.** Migratsiyalar yaratgan 9 ta indeks yoki constraint modellarda e'lon qilinmagan. Kelajakdagi `alembic revision --autogenerate` ularni jimgina o‘chirib yuboradi: login va audit tarixi indekslari, `uq_lessons_module_number`, `uq_promo_codes_code` va boshqalar.
- **Tuzatish.** `__table_args__` yoki `index=True` qo‘shildi. Faqat metadata, DDL yo‘q. O‘zgargan fayllar:
  - `models/audit_log.py`
  - `models/login_history.py`
  - `models/advertisement.py`
  - `models/lesson.py`
  - `models/managed_page.py`
  - `models/notification.py`
  - `models/promo_code.py`
  - `models/subscription_order.py`
  - `models/achievement.py`
- **Test.** `alembic check`: 10 ta farqdan 1 tasi qoldi. Bu `student_speakings.user_id` nullable, u ataylab qoldirilgan (O-5).

## B-6 · P2 · To‘lov va kirish muddati testlari hech qachon ishlamagan

- **Sabab.** `tests/test_course_access_terms.py` pytest uslubida yozilgan: modul darajasidagi funksiyalar, `parametrize`, `monkeypatch`. Loyiha esa `unittest discover` bilan ishlaydi.
  - **Lokalda** 0 ta test yig‘ilgan.
  - **Serverda** venv’da `pytest` yo‘q, shuning uchun import xatosi chiqqan.
- **Tuzatish.** Xuddi shu tekshiruvlar `unittest.TestCase` ga o‘tkazildi: `subTest` va `mock.patch.object`. Mantiq o‘zgarmadi.
- **Test.** 10/10 ta test endi haqiqatan ishlaydi va o‘tadi: kalendar oy qo‘shish, muddatlar, faollashtirish, uzaytirish, imzolangan media token.

## Xavfsizlik tuzatishlari (qisqacha)

To‘liq tafsilot [security-findings.md](security-findings.md) da.

| ID | Fayllar | Test |
|---|---|---|
| S-1 yuklash | `services/upload/service.py`, `core/storage/local.py` | `tests/test_upload_path_safety.py` (6) |
| S-2 IP spoofing | `core/client_ip.py` (yangi), `core/config.py`, `api/auth/router.py`, `api/study_groups/router.py`, `api/advertisements/router.py` | `tests/test_client_ip.py` (7) |
| S-3 baho yozish | `api/student_quiz/router.py` | `tests/test_student_quiz_permissions.py` (5) |
| S-5 header’lar | `frontend/next.config.ts` | Lokal `next start` javobida 3 ta header borligi tekshirildi |
| S-6 sertifikat verify | `api/v1/certificate/router.py` | `tests/test_certificate_verify_public.py` (2) |
| S-7 API docs | `core/config.py`, `main.py` | `tests/test_api_docs_setting.py` (3) |

## O‘zgargan fayllar (to‘liq ro‘yxat)

Lokal daraxt `origin/main` (`491a453`) bilan hash orqali solishtirildi.

- **O‘zgartirilgan (26):**
  - `.gitignore`
  - 3 ta migratsiya (`downgrade()` qismlari)
  - 9 ta model
  - router’lar: `advertisements`, `auth`, `student_quiz`, `study_groups`, `v1/certificate`
  - `core/config.py`, `core/storage/local.py`, `main.py`
  - servislar: `lms/progress.py`, `page_management.py`, `upload/service.py`
  - `tests/test_course_access_terms.py`
  - `frontend/next.config.ts`
- **Yangi (7):**
  - `backend/app/core/client_ip.py`
  - 6 ta test fayli: `test_api_docs_setting`, `test_certificate_verify_public`, `test_client_ip`, `test_lms_visit_race`, `test_student_quiz_permissions`, `test_upload_path_safety`
- **Tegilmagan, lekin commit qilinmagan:** `frontend/src/app/admin/media/page.tsx` (foydalanuvchining avvalgi ishi, B-2).
- `frontend/tsconfig.json` audit build’i vaqtida o‘zgargan edi va asl holatiga qaytarildi.
