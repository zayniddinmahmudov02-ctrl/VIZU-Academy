# Bot → Sayt funksiyalar matritsasi

Manba: `telegram-bot-inventory.md` (F01–F20) va sayt kodi (`backend/app`, `frontend/src`). Audit sanasi 2026-10-28.

Tasniflar:
- **To'liq** — saytda to'liq mavjud;
- **Qisman** — saytda qisman mavjud;
- **Yo'q** — saytda mavjud emas;
- **Botda** — botda saqlanishi kerak;
- **Tekshiruv** — qo'shimcha tekshiruv talab qiladi.

"Botda" tasnifi funksiyani saytga ko'chirmaslikni bildiradi. Saytda uning ko'rinishi (masalan, faqat o'qish) baribir qo'shilishi mumkin.

## 1. Matritsa

| # | Bot funksiyasi | Saytdagi o'xshashi (dalil) | Tasnif | Murakkablik | Xavf | Izoh |
|---|---|---|---|---|---|---|
| F01 | Start + majburiy kanal obunasi | — | **Botda** | — | Past | Telegram kanaliga xos |
| F02 | Telegram foydalanuvchisini avtoro'yxat | `users.telegram_id` (unique, nullable), `get_or_create_telegram_user` (`services/auth/service.py:159`) | **Qisman** | O'rta | Yuqori | Sayt Mini App orqali kirganda **yangi** akkaunt yaratadi. Mavjud email/telefon akkauntiga bog'lash yo'q. Prod'da `telegram_id` 0 ta foydalanuvchida. |
| F03 | Mini App tugmasi (VIZU-De) | `POST /auth/telegram` + `telegram-auto-login.tsx` | **Qisman** | Past | Yuqori (S0) | Ishlaydigan kod bor, lekin token ochiq (S0); prod'da 30 kunda 1 ta urinish (401) |
| F04 | So'z o'yini (WortSpiel) | Yo'q. `Wörterbuch` sahifasi interfeys holida (`use-woerterbuch.ts`: "BACKEND TODO") | **Botda** | — | — | Talab bo'yicha botda qoladi. Saytda faqat natijalarni ko'rsatish mumkin. |
| F05 | Leaderboard (kun/hafta/oy/overall) | Saytda XP bor (`StudentProgress.total_score`), reyting yo'q | **Botda** | O'rta (ko'rinish) | O'rta | Bot va sayt XP'si har xil manbadan keladi, ularni birlashtirmaslik kerak |
| F06 | Champions + haftalik/oylik e'lon | — | **Botda** | — | Past | Bot jarayonidagi scheduler |
| F07 | W-Zertifikat PDF | `admin/zertifikate`, `my_certificates` — kurs va multilevel sertifikatlari (prod'da 0) | **Botda** | Past (ko'rinish) | Past | Qoida boshqa (blok ≥ 60%). Ikkalasini bitta jadvalga birlashtirmaslik kerak. |
| F08 | Mening profilim (XP, ism) | `/settings`, `/dashboard`, `/certificates` | **Qisman** | Past | Past | Ism ikki joyda saqlanadi; bog'lashdan keyin manba aniqlanishi kerak |
| F09 | Video kurslar katalogi + narxlar | `/angebote`, `app_settings.angebote`, `services/vizu_pay/offers.py` | **Tekshiruv** | Yuqori | Yuqori | **Har xil mahsulot:** bot Telegram kanaliga taklif havolasini sotadi (A1, A2, B1, A1–B1, A1–C1); sayt darslarga kirishni sotadi (hozir faqat A1). Narxlar ham farq qiladi (masalan, A2: bot 100 000, saytda sotuv yopiq). |
| F10 | Chek bilan to'lov + admin tasdiqi | VIZU Pay: `subscription_orders`, `POST /vizu-pay/orders`, `admin/vizu-pay/orders/{id}/approve` (`require_super_admin`) | **Tekshiruv** | Yuqori | Yuqori | Oqim o'xshash, natijasi har xil (kanal havolasi yoki sayt kirishi). Botda S1 (admin tekshiruvi yo'q). 78 bot to'lovi va 9 sayt buyurtmasi alohida. |
| F11 | Medien: Bücher (147), Filme (11), Musik (451) + sevimlilar | `admin/books` (PDF, 3 ta) | **Tekshiruv** | Yuqori | Yuqori (huquqiy) | Fayllar Telegram kanallarida (`copy_message`). Saytga ko'chirish = fayllarni yuklab olish va qayta tarqatish. Mualliflik huquqi bo'yicha alohida qaror kerak. |
| F12 | Ma'lumotlar (statik matnlar) | `/informationen`, `admin/page-management` | **Qisman** | Past | Past | Matnni bitta joyda saqlash mumkin |
| F13 | Hausaufgaben (3 kategoriya, parol, ko'p faylli topshiriq, kanal) | Dars ichidagi Schreiben/Sprechen, `/teacher/*`, `homework_submissions` (prod'da 0) | **Tekshiruv** | Yuqori | Yuqori | Model har xil: botda kategoriya + parol + erkin daraja/dars raqami + Telegram `file_id`; saytda darsga bog'langan topshiriq. 239 topshiriq va 736 fayl Telegram'da. |
| F14 | Sprechen guruh (jins, daraja guruhi, guruh havolasi, 20 dars) | — | **Botda** | — | O'rta | Telegram guruhlariga bog'liq |
| F15 | Uy vazifasini baholash 1–5 | `teacher/schreiben`, `teacher/sprechen` (boshqa shkala) | **Tekshiruv** | O'rta | O'rta | Shkala va status nomlari farq qiladi |
| F16 | Hausaufgaben Admin | Sayt admin paneli (boshqa model) | **Tekshiruv** | O'rta | O'rta | F13 bilan birga |
| F17 | Admin panel (statistika, xaridorlar, to'lovlar, sertifikatlar) | `admin` dashboard, `admin/payments`, `admin/users`, `admin/analytics` | **Qisman** | O'rta | O'rta | Saytda bot ma'lumotlarini faqat o'qish uchun yig'ma ko'rinish sifatida qo'shish mumkin |
| F18 | Reklama (Telegram'ga ommaviy xabar) | `admin/notifications` (faqat sayt ichida) | **Qisman** | O'rta | O'rta | Telegram yetkazish kanali saytda yo'q |
| F19 | Admin → foydalanuvchi shaxsiy xabar | `support` tiketlari | **Qisman** | Past | Past | Turli kanallar; ikkalasi qoladi |
| F20 | Flask health (:10000) | `GET /health` (sayt) | **Botda** | Past | O'rta (S4) | Localhost'ga yopish kerak |

## 2. O'xshash, lekin biznes qoidasi farq qiladigan juftliklar

Quyidagilar nomi o'xshash bo'lgani uchun birlashtirilmasligi kerak:

| Juftlik | Farq (dalil) |
|---|---|
| Bot `payments` ↔ sayt `subscription_orders` | Bot: `course` matn emoji bilan (`"🇩🇪 A1"`), `amount`, status `pending/approved/rejected`, Telegram ID. Sayt: `plan` (`MONTH_*`, offer kodlari), `final_amount`, promo/medal chegirmasi, `access_start/end_date`, status katta harfda, UUID. |
| Bot XP (`xp_events`, `user_scores`) ↔ sayt XP (`StudentProgress.total_score`) | Bot: so'z o'yini to'g'ri javoblari, qayta o'tishda faqat farq beriladi. Sayt: faoliyat turiga qarab belgilangan qiymat (video 10, writing 30 …). |
| W-Zertifikat ↔ sayt Zertifikate | Bot: lug'at bloklari bo'yicha. Sayt: kurs va multilevel natijasi bo'yicha. |
| Bot Hausaufgaben ↔ sayt Schreiben/Sprechen | Bot: dars raqami foydalanuvchi tomonidan kiritiladi (1–300) va saytdagi `lessons` ga bog'lanmaydi. Sayt: aniq dars va topshiriq ID. |
| Bot narxlari (`COURSE_INFO`) ↔ sayt `angebote` | Ikki manba; A1 narxi ikkalasida 50 000, qolganlari mos emas yoki saytda sotuv yopiq |
| Bot "kurs ochildi" ↔ sayt "kurs ochildi" | Bot: Telegram kanali va guruhiga taklif havolasi. Sayt: `subscription_orders` asosida darsga kirish. Bot xaridori saytda avtomatik kirish huquqini olmaydi. |

## 3. Media: bot vs sayt Media Management

| Bot media funksiyasi | Saqlash joyi | Sayt Media Management bilan almashtiriladimi? |
|---|---|---|
| Bücher, Filme, Musik katalogi | CSV + xususiy Telegram kanallari (`copy_message`) | **Yo'q, avtomatik emas.** Sayt Media Management (`admin/media-management`: `tree`, `items`, `videos/{id}/preview`, `a2-audio`) faqat **dars** videolari va Hören audiolari uchun. Kutubxona yo'q. Saytdagi `admin/books` (PDF) faqat kitoblarni qisman qoplaydi. |
| Musik sevimlilari | `favorite_music` (bot DB) | Saytda o'xshashi yo'q |
| Hausaufgaben fayllari | Telegram `file_id` (`homework_submission_files`) | Yo'q. Saytga ko'chirish uchun Bot API `getFile` bilan yuklab olish kerak; Bot API ≤ 20 MB cheklovi bor, kattaroq fayllar uchun boshqa yechim kerak. |
| W-Zertifikat PDF | Bot serveridagi disk (`certificates/generated`) | Shart emas (botda qoladi) |
| Kurs video darslari | Xususiy Telegram kanallari (taklif havolasi) | **Sayt Media Management bunga mos keladi** (dars videolari serverda saqlanadi, `videos` 36). Lekin bu kontent migratsiyasi emas — saytda videolar allaqachon alohida yuklangan. |

Xulosa: audio va video boshqaruvi saytda qoladi. Botdagi media funksiyalarining birortasi hozircha sayt Media Management bilan **to'g'ridan-to'g'ri almashtirilmaydi**. Bot media funksiyalarini o'chirishdan oldin kutubxona (kitob, film, musiqa) uchun alohida modul va huquqiy qaror kerak (roadmap 6-bosqich).
