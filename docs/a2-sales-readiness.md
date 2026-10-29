# A2 kursi — sotuvga tayyorlik

Sana: 2026-10-30. **Production indikatori (deploy’dan keyin, 2026-10-29 22:0x UTC): `NEEDS_CONTENT`. A2 kontent jihatidan sotuvga tayyor EMAS.**

> ⚠ **Diqqat:** production’da A2 sotuvi **allaqachon yoqilgan** — SUPER_ADMIN 2026-10-28 19:32 da Admin → Angebote orqali `sales.A2 = true` qilgan (audit log: `angebote_config_updated`). A2 taklifi `purchasable: true`, narx 99 000 UZS. Hozircha A2 buyurtmalari yo‘q (0). Bu biznes qarori bo‘lgani uchun men uni o‘zgartirmadim. Tavsiya: audio va kalitlar tayyor bo‘lguncha sotuvni yopish yoki o‘quvchilarga “audio hali yuklanmagan” holatini ochiq aytish — qaror sizda.

Production’dagi tekshiruvlar:

| Tekshiruv | Holat | Tafsilot |
|---|---|---|
| `price` | OK | 99 000 UZS (200 000 dan), aktiv |
| `lessons` | OK | 14 tadan 13 ta dars nashr qilingan (14 — “Wiederholung”, ataylab nashrsiz) |
| `description` | OK | kurs tavsifi bor |
| `manifest` | — | kutubxonada 0 fayl |
| `audio_complete` | — | 25 tadan 3 ta Hören vazifasida audio |
| `audio_verified` | — | bog‘langan fayl yo‘q |
| `links` | — | 0 bog‘lanish |
| `payment_tested`, `access_tested`, `responsive_tested`, `tests_passed` | ochiq | qo‘lda tasdiqlanmagan |
| “Noch auszufüllen” | 20 | kaliti yo‘q Hören vazifalari |

Sotuvni men yoqmadim va narxni o‘zgartirmadim.

## 1. Mavjud sotuv tizimi (audit, o‘zgartirilmagan qismlar)

| Talab | Holat | Qayerda |
|---|---|---|
| Narx — bitta manba | **Bor.** A2: 200 000 → **99 000 UZS**, 50 %, `active: True`. Frontend narxni faqat `GET /vizu-pay/offers` dan oladi (frontend kodida narx yo‘q — tekshirildi) | `backend/app/services/vizu_pay/offers.py`, Admin → Angebote (`app_settings.angebote`) |
| Sotuv ruxsati | **A2 yopiq** (`LEVEL_SALES_DEFAULT["A2"] = False`). Yopiq daraja: “Tez orada”, buyurtma qabul qilinmaydi (`409 OFFER_NOT_AVAILABLE`), pullik darslar yopiq; A1→B1 paketi ham sotilmaydi | `offers.is_purchasable`, `vizu_pay/access.py` |
| Bepul preview | Har kursning **1-darsi** bepul (`FREE_LESSONS_PER_COURSE = 1`) — saqlandi | `access.is_free_lesson` |
| To‘lov | **Qo‘lda** (ManualGateway): o‘quvchi chek yuklaydi, SUPER_ADMIN tasdiqlaydi. Avtomatik Click/Payme yo‘q (kodda ataylab stub qilinmagan) | `vizu_pay/gateways.py`, `service.create_order`, `admin_service.approve_order` |
| Takroriy buyurtma / kirish | Bir vaqtda bitta PENDING (`PAYMENT_REQUEST_ALREADY_PENDING`, user qatori row-lock), egasi bo‘lsa `OFFER_ALREADY_OWNED`, approve/reject/refund row-lock va faqat bir marta | `service.py`, `admin_service.py` |
| To‘lov bekor/rad | REJECTED / EXPIRED / REFUNDED — kirish yo‘q | `access.owned_levels` (faqat APPROVED + muddat ichida) |
| Promo kodlar | PERCENT / SPECIAL_PRICE / FREE_ACCESS; kurs/paketga bog‘lash; narx serverda hisoblanadi | `service._check_promo`, `tests/test_promo_*` |
| Kabinet | Sotib olingan kurslar `course_accesses` (muddat, holat) | `service.get_status` |
| Kirish nazorati | Har bir dars kontent endpointi `require_lesson_access` orqali; audio `private, no-store`, ommaviy URL yo‘q | `api/dependencies/progress.py`, `lesson_skills/router.py` |

## 2. Bu ishda qo‘shilgan / tuzatilgan

- **Sotuvni narxsiz ochib bo‘lmaydi:** Admin → Angebote’da darajaning sotuvini yoqish uchun shu darajaning narxi (override yoki standart) bo‘lishi shart (`validate_overrides`, test `test_angebote`). A2 narxi bor, shuning uchun A2 uchun hech narsa o‘zgarmaydi; B2/C1 ni narxsiz ochish endi rad etiladi.
- **Tayyorlik indikatori** (Admin → Media Management → A2, `GET /admin/media-management/a2-readiness`): har so‘rovda haqiqiy ma’lumotdan hisoblanadi; sotuvni o‘zi yoqmaydi.
- **O‘quvchi uchun “Audio hali yuklanmagan”:** nashr qilingan, lekin audiosi yo‘q (yoki fayli yo‘qolgan) Hören vazifasi player ko‘rsatmaydi; bo‘lim “Bu tinglash mashqi uchun audio hali yuklanmagan” deydi (`audio_pending`). Qoralamalar oshkor qilinmaydi.

## 3. Indikator tekshiruvlari

| Kalit | Guruh | Shart |
|---|---|---|
| `price` | configuration | A2 taklifi aktiv va narxi bor |
| `lessons` | configuration | A2 kursi aktiv, kamida bitta dars nashr qilingan, 1-dars (bepul preview) nashr qilingan |
| `description` | content | Kurs tavsifi to‘ldirilgan |
| `manifest` | content | A2 Audio Manager’da kamida bitta haqiqiy fayl |
| `audio_complete` | content | Har bir joriy Hören vazifasida audio bor (yetishmayotganlar ro‘yxati bilan) |
| `audio_verified` | content | Bog‘langan fayllar tinglangan (`verified`), muammoli/yo‘qolgan fayl yo‘q |
| `links` | content | Har bir bog‘lanish sinxron (vazifa shu faylni ijro etadi) va Unterricht dars raqamiga mos |
| `payment_tested` | testing (qo‘lda) | Test/sandbox’da buyurtma → tasdiq → rad oqimi tekshirildi |
| `access_tested` | testing (qo‘lda) | Sotib olgan — ochiq, olmagan — yopiq |
| `responsive_tested` | testing (qo‘lda) | Mobil va desktop |
| `tests_passed` | testing (qo‘lda) | Avtomatik testlar o‘tdi |

Holat: `NEEDS_CONFIGURATION` → `NEEDS_CONTENT` → `NEEDS_TESTING` → `READY` (birinchi mos keladigani). Qo‘lda tekshiruvlarni faqat SUPER_ADMIN tasdiqlaydi; kim va qachon tasdiqlagani saqlanadi (`app_settings.a2_sales_readiness`) va audit log’ga yoziladi. Fayl yo‘qolsa holat avtomatik `NEEDS_CONTENT` ga qaytadi (test bilan tekshirilgan).

Qo‘shimcha “Noch auszufüllen” ro‘yxati: javob kaliti yo‘q Hören vazifalari (ular kalitsiz nashr qilinmaydi — mavjud qoida).

## 4. Sotuvni ochishdan oldin qilinadigan ishlar

1. Deploy (alohida tasdiq): migratsiyalar `f3a8c1d5e7b2`, `a6d2f9c4e8b1`; backend; frontend slot.
2. Haqiqiy A2 audio fayllarini A2 Audio Manager orqali yuklash, natija hisobotini tekshirish (dublikat/xato).
3. Har bir faylni tinglash → “Geprüft”; darsga bog‘lash; vazifani tekshirib nashr qilish.
4. Kurs tavsifini to‘ldirish (matn bu ishda yozilmadi — uydirma kontent yaratilmaydi).
5. Hören kalitlari: 4, 5, 6, 7, 10–13-darslarda kitobda kalit yo‘q (oldingi audit) — admin audio tinglab kiritishi kerak, aks holda vazifa qoralama qoladi.
6. Sandbox/test: buyurtma, tasdiq, rad, refund, promo; mobil/desktop — indikatorda tasdiqlash.
7. Faqat shundan keyin: Admin → Angebote → A2 “Verkauf” ni yoqish (alohida biznes qarori).

Soxta to‘lov bilan real sotuv tasdiqlanmadi: to‘lov oqimi faqat lokal test bazasida, servis funksiyalari orqali sinaldi (`test_a2_purchase_flow_and_access`).
