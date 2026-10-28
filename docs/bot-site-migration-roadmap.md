# Bot → Sayt migratsiya yo'l xaritasi

Har bosqich alohida tasdiqlanadi va o'zidan oldingi bosqich yakunlanganidan keyin boshlanadi. 0-bosqich har qanday integratsiyadan oldin majburiy.

Umumiy qoidalar (har bosqichda):
- avval ikkala baza zaxiralanadi (`600` huquq) va restore testi o'tkaziladi;
- avval staging (prod dump'dan scratch DB) qilinadi;
- `git reset --hard` va `git clean` ishlatilmaydi;
- foydalanuvchi, progress, to'lov va media yozuvlari o'chirilmaydi;
- so'z o'yini kodi, uning jadvallari va CSV'lari tegilmaydi (8-bosqichdan tashqari, u ham faqat alohida qaror bilan).

---

## 0-bosqich. Xavfsizlik — shoshilinch

| | |
|---|---|
| **Vazifa** | S0: (1) BotFather'da bot tokenini almashtirish va yangi tokenni bot `.env` hamda sayt `TELEGRAM_BOT_TOKEN` ga bir vaqtda yozish; (2) GitHub repositoryni private qilish yoki `.env` ni olib tashlab `.gitignore` ga qo'shish, tarixni tozalash; (3) `ADMIN_PASSWORD` boshqa joyda ishlatilgan bo'lsa almashtirish. S1: `approve_payment`/`reject_payment` callback'lariga `is_admin` va "faqat `pending` bo'lsa" tekshiruvini qo'shish. S4: Flask'ni `127.0.0.1` ga bog'lash. S5: `/opt/vizu/academy` eski nusxasini arxivlash (`vizu-bot.service` disabled holatda qoladi). |
| **Natija** | Ochiq token kuchsiz; to'lovni faqat admin tasdiqlay oladi; bot tashqi portni ochmaydi |
| **Fayllar** | bot: `handlers/payment.py`, `main.py`, `.gitignore`, `.env` (serverda). Sayt: `backend/.env` (faqat token qiymati) |
| **DB migratsiya** | Yo'q |
| **Test** | Admin bo'lmagan test akkaunt bilan `approve_payment:<id>` → rad etiladi. Admin bilan pending to'lov → tasdiqlanadi. Takroriy tasdiq → "allaqachon" javobi. `/start`, so'z o'yini bitta blok, reyting — qo'lda smoke. Mini App kirishi yangi token bilan → 200, eski token bilan soxta `initData` → 401. |
| **Xavf / rollback** | Token almashtirilgach eski tokenga qaytib bo'lmaydi (bu maqsad). Kod o'zgarishi: `git revert` + restart. Ikki servis restart qilinadi — qisqa uzilish. |
| **Botga ta'sir** | Restart: xotiradagi FSM va yarim o'yin sessiyalari yo'qoladi (har restartdagidek) |
| **Sayt foydalanuvchilariga ta'sir** | Backend restart (bir necha soniya). Mini App kirishi yangi token bilan ishlaydi. |

## 1-bosqich. Zaxira va DB rollari

| | |
|---|---|
| **Vazifa** | `telegram_course2026` uchun kunlik zaxira (alohida timer yoki `backup_db.sh` kengaytmasi, 14 kun, `600`). Mavjud sayt dump'lari huquqini `600` ga o'tkazish. Bot uchun alohida PostgreSQL roli, faqat o'z bazasiga; sayt roli bot bazasiga kirmasligi. |
| **Natija** | Bot ma'lumoti tiklanadigan holatda; bazalar bir-biridan ajratilgan |
| **Fayllar** | `/opt/vizu/scripts/backup_db.sh` (yoki yangi skript), systemd timer, bot `.env` (`DATABASE_URL` yangi rol bilan) |
| **DB migratsiya** | Sxema emas: faqat rol va `GRANT`. Bot `init.py` har startda DDL bajaradi, shuning uchun yangi rol `telegram_course2026` jadvallarining egasi bo'lishi kerak (`ALTER TABLE … OWNER`). |
| **Test** | Dump → vaqtinchalik bazaga restore → jadval sonlarini solishtirish (26 jadval, `users` 1232 …). Bot restartdan keyin `init_database` xatosiz. Yangi rol bilan `vizu` ga ulanish rad etiladi. |
| **Xavf / rollback** | Egalik noto'g'ri bo'lsa, bot startda `ALTER TABLE` da yiqiladi. Rollback: eski `DATABASE_URL` ga qaytish va restart. |
| **Botga ta'sir** | Bitta restart |
| **Sayt foydalanuvchilariga ta'sir** | Yo'q |

## 2-bosqich. Bog'lash — sayt backend (flag o'chiq)

| | |
|---|---|
| **Vazifa** | `telegram_link_tokens` va `telegram_link_audit` jadvallari. Endpointlar: `POST /api/v1/telegram-link/start` (sessiya talab qiladi, deep-link qaytaradi), `POST /api/v1/internal/bot/link` (xizmat kaliti + `127.0.0.1`), `POST /api/v1/telegram-link/unlink`. nginx `/api/v1/internal/` ni bloklaydi. Flag `telegram_linking_enabled` (`app_settings`) — standart holatda o'chiq. |
| **Natija** | Bog'lash API tayyor, lekin yoqilmagan |
| **Fayllar** | `backend/alembic/versions/<yangi>.py`, `backend/app/models/telegram_link.py`, `backend/app/api/telegram_link/`, `backend/app/services/telegram_link/`, `backend/app/core/config.py` (`BOT_INTERNAL_API_KEY`), nginx config |
| **DB migratsiya** | Ha: 2 ta yangi jadval (additive, downgrade = drop) |
| **Test** | Unit: token TTL, bir martalik, xesh saqlanishi, "telegram_id band", "akkauntda boshqa telegram_id", banned, noto'g'ri xizmat kaliti, rate limit. Integratsiya: prod dump'dagi staging. nginx orqali `/internal` → 403/404. |
| **Xavf / rollback** | Past (flag o'chiq). Rollback: Alembic downgrade + kod revert. |
| **Botga ta'sir** | Yo'q |
| **Sayt foydalanuvchilariga ta'sir** | Yo'q (UI hali yo'q) |

## 3-bosqich. Bog'lash — bot handleri va sayt UI

| | |
|---|---|
| **Vazifa** | Bot: `/start link_<token>` handleri (`CommandStart(deep_link=True)`), ichki API mijozi, profil ekranida "Sayt akkaunti: bog'langan / bog'lanmagan". Sayt: Sozlamalarda "Telegram'ni bog'lash" va "Bekor qilish" tugmalari. Mini App kirishi: bog'lanmagan Telegram ID uchun yangi akkaunt yaratmaslik, "kiring yoki ro'yxatdan o'ting" ekranini ko'rsatish (`get_or_create_telegram_user`). Keyin flagni yoqish. |
| **Natija** | Foydalanuvchi o'z akkauntlarini xavfsiz bog'laydi |
| **Fayllar** | bot: `handlers/start.py` (deep-link tarmog'i; oddiy `/start` o'zgarmaydi), yangi `services/site_api.py`, `handlers/profile.py`. Sayt: `frontend/src/app/(dashboard)/settings/page.tsx`, `features/auth/components/telegram-auto-login.tsx`, `backend/app/services/auth/service.py` |
| **DB migratsiya** | Yo'q (2-bosqichdagi jadvallar) |
| **Test** | Haqiqiy test akkauntlari bilan (yangi prod foydalanuvchi yaratilmaydi; mavjud test akkaunti bo'lmasa, test o'tkazildi deb ko'rsatilmaydi): bog'lash → bekor qilish → qayta bog'lash; muddati o'tgan token; boshqa Telegram bilan bir xil token; oddiy `/start` va obuna tekshiruvi o'zgarmagan; so'z o'yini regression smoke. |
| **Xavf / rollback** | O'rta. Rollback: flagni o'chirish (bog'langan yozuvlar qoladi, ishlatilmaydi). Bot handleri: revert + restart. |
| **Botga ta'sir** | `/start` ga yangi tarmoq qo'shiladi; mavjud oqim saqlanadi |
| **Sayt foydalanuvchilariga ta'sir** | Yangi ixtiyoriy tugma. Mini App orqali bog'lanmagan holda kirgan foydalanuvchi endi avtomatik akkaunt olmaydi. |

## 4-bosqich. O'qish uchun ma'lumot almashinuvi

| | |
|---|---|
| **Vazifa** | Saytda bog'langan foydalanuvchi uchun "So'z o'yini" kartasi: umumiy XP, bloklar, W-Zertifikatlar. Manba: bot bazasidan faqat o'qish (alohida read-only rol, view) yoki botdagi kichik ichki HTTP endpoint. Botda: sayt tarifi holati (`GET internal/bot/user/{telegram_id}`). |
| **Natija** | Ikki tomon bir-birining natijasini ko'radi, hech kim yozmaydi |
| **Fayllar** | Sayt: `backend/app/services/bot_stats/`, dashboard komponenti. Bot: `handlers/profile.py` |
| **DB migratsiya** | Bot DB'da read-only rol va view'lar (sxema o'zgarmaydi); saytda yo'q |
| **Test** | View natijasi bot ekranidagi raqamlar bilan bir xil (profil XP, reyting o'rni). Bog'lanmagan foydalanuvchi uchun karta yo'q. |
| **Xavf / rollback** | Past. Rollback: flag yoki kartani o'chirish, rolni drop qilish. |
| **Botga ta'sir** | Yo'q (faqat o'qiladi) |
| **Sayt foydalanuvchilariga ta'sir** | Yangi ixtiyoriy karta |

## 5-bosqich. Sayt hodisalarini Telegram orqali yetkazish (outbox)

| | |
|---|---|
| **Vazifa** | `notification_outbox` (sayt): buyurtma tasdiqlandi yoki rad etildi, yangi bildirishnoma, uy vazifasi baholandi. Bot ichida yetkazuvchi vazifa: olish → yuborish → `ack`, qayta urinish, `RetryAfter`. Faqat bog'langan va botni bloklamagan foydalanuvchilarga. |
| **Natija** | Sayt foydalanuvchisi Telegram'da xabar oladi |
| **Fayllar** | Sayt: model, migratsiya, VIZU Pay va notifications servislariga yozish nuqtalari, `internal/bot/outbox` endpointi. Bot: `services/outbox.py`, `main.py` (yangi task). |
| **DB migratsiya** | Ha: `notification_outbox` (additive) |
| **Test** | Takroriy yuborishning oldi olinadi (bitta hodisa = bitta xabar), bot restartida yo'qolmaydi, bloklagan foydalanuvchi `attempts` dan keyin to'xtaydi, limitlar ishlaydi |
| **Xavf / rollback** | O'rta (ommaviy xabar). Rollback: yetkazuvchini flag bilan o'chirish (outbox to'planib qoladi, yo'qolmaydi). |
| **Botga ta'sir** | Yangi fon vazifasi |
| **Sayt foydalanuvchilariga ta'sir** | Telegram xabarlari (sozlamalarda o'chirish imkoni bo'ladi) |

## 6-bosqich. Sotuvni birlashtirish — biznes qarori kerak

| | |
|---|---|
| **Vazifa** | Qaror qabul qilinadi: bot "Video Kurslar" sotuvi davom etadimi yoki saytdagi VIZU Pay'ga Mini App orqali yo'naltiriladimi. Telegram kanal va guruh havolalari bilan nima bo'ladi. Tarixiy 69 ta bot xaridi (62 xaridor) saytda qanday ko'rsatiladi. Narxlar bitta manbada bo'ladimi (`app_settings.angebote` → bot uni `internal/bot/offers` dan oladi). |
| **Natija** | Bitta sotuv joyi va bitta narx manbai |
| **Fayllar** | bot: `handlers/video.py`, `handlers/payment.py`, `keyboards/video.py`. Sayt: `services/vizu_pay/*` (faqat qaror asosida) |
| **DB migratsiya** | Ehtimol: saytda `legacy_bot_purchases` (faqat o'qish, bog'langan foydalanuvchi uchun admin tasdig'i bilan) |
| **Test** | Narxlar bot va saytda bir xil; eski xaridorlarning Telegram kirishi saqlanadi; sayt kirish huquqi faqat sayt qoidasi bo'yicha beriladi |
| **Xavf / rollback** | Yuqori (pul). Rollback: bot eski menyuga flag bilan qaytadi. Bot `payments` jadvali hech qachon o'chirilmaydi. |
| **Botga ta'sir** | Kurs menyusi o'zgaradi |
| **Sayt foydalanuvchilariga ta'sir** | Botdan kelgan xaridorlar oqimi |

## 7-bosqich. Medien kutubxonasi va Hausaufgaben — tadqiqot va qaror

| | |
|---|---|
| **Vazifa** | (a) Kitob, film va musiqa: mualliflik huquqi bo'yicha qaror; saytda kutubxona moduli kerakmi (Media Management dars mediasi uchun, kutubxona uchun emas). (b) Hausaufgaben: bot modeli (kategoriya, parol, Telegram kanali, 1–5 ball) va sayt Schreiben/Sprechen modeli o'rtasida moslik loyihasi. 239 topshiriq va 736 faylni (Telegram `file_id`, eng kattasi 7.6 MB) saytga nusxalash kerakmi. |
| **Natija** | Hujjatlashtirilgan qaror; implementatsiya alohida rejada |
| **Fayllar** | Hujjatlar |
| **DB migratsiya** | Yo'q (tadqiqot) |
| **Test** | — |
| **Xavf / rollback** | — |
| **Botga ta'sir** | Yo'q. Bot media va Hausaufgaben funksiyalari qaror qabul qilinmaguncha o'zgarmaydi. |
| **Sayt foydalanuvchilariga ta'sir** | Yo'q |

## 8-bosqich. Botdagi ixtiyoriy tozalash — alohida tasdiq bilan

| | |
|---|---|
| **Vazifa** | Ishlatilmaydigan kodni olib tashlash: `handlers/xp.py`, `handlers/certificate.py`, `handlers/search.py`, `payment.py:start_payment` dublikati. `cleanup_quiz_memory` xatosini tuzatish. HTML escape qo'shish (S7). Hausaufgaben parol urinishlariga limit (S6). Eskirgan jadvallarni arxivlash (o'chirmasdan). **So'z o'yinidagi CSV birinchi qatori va `unlocked_level` qoidasi** — o'yin natijasiga ta'sir qiladi, shuning uchun alohida qaror kerak: blok tarkibi siljiydi va mavjud `best_score` boshqa so'zlar to'plamiga tegishli bo'lib qoladi. |
| **Natija** | Toza kod; o'yin mexanikasi faqat qaror bo'lsa o'zgaradi |
| **Fayllar** | Yuqoridagilar |
| **DB migratsiya** | Yo'q |
| **Test** | Bot uchun avtomatik testlar hozir yo'q. Avval so'z o'yini uchun regression testlar yoziladi (blok kesimlari, XP hisobi, qayta o'tish, ochilish qoidasi). |
| **Xavf / rollback** | Past–o'rta. `git revert` + restart. |
| **Botga ta'sir** | Restart |
| **Sayt foydalanuvchilariga ta'sir** | Yo'q |
