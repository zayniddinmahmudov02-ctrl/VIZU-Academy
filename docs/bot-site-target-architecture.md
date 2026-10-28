# Bot ↔ Sayt maqsadli arxitekturasi (taklif)

Holat: taklif. Implementatsiya alohida tasdiqlanadi. Asos: `telegram-bot-inventory.md`, `bot-to-site-feature-matrix.md`, `bot-site-database-audit.md`.

## 1. Tamoyillar

1. **Sayt backend yagona manba (source of truth):**
   - akkaunt;
   - xarid va kirish huquqi;
   - kurs, dars va kontent;
   - audio/video (Media Management).
2. **Bot — Telegram interfeysi.** Botga xos qismlar unda qoladi:
   - so'z o'yini (o'z bazasi bilan);
   - majburiy kanal obunasi;
   - Telegram guruh va kanallari;
   - Telegram'ga ommaviy xabar;
   - Sprechen guruhlari.
3. **Bot bazasiga saytdan yozilmaydi va aksincha.** Integratsiya faqat aniq belgilangan ichki API orqali bo'ladi.
4. **Telegram ID egalikni isbotlamaydi.** Bog'lash har doim ikki tomonlama tasdiq bilan bo'ladi.
5. **Har bir o'zgarish additive:**
   - yangi jadval yoki ustun qo'shiladi, mavjudlari o'chirilmaydi;
   - funksiya flag bilan yoqiladi;
   - rollback = flagni o'chirish.

## 2. Komponentlar

```
Telegram ──(update, polling)──▶ telegram-cours2026 (aiogram)
   ▲                               │  ├─ So'z o'yini, reyting, W-Zertifikat ── telegram_course2026 DB (o'zgarmaydi)
   │ sendMessage                   │  └─ Ichki API mijozi ──HTTP 127.0.0.1──┐
   │                               ▼                                       ▼
   └──────── Outbox yetkazuvchi ◀── vizu-backend (FastAPI) ── vizu DB (akkaunt, xarid, kontent, Media Management)
                                    ▲
Brauzer / Telegram Mini App ──HTTPS (nginx)── vizu-frontend (Next.js)
```

| Komponent | Vazifa | O'zgarish |
|---|---|---|
| `vizu-backend` | Akkaunt, bog'lash, xarid, kontent, Mini App kirishi | Yangi: `telegram_link_tokens` va `telegram_link_audit` jadvallari, `internal/bot/*` API, `notification_outbox` |
| `telegram-cours2026` | Telegram UI, so'z o'yini | Yangi: `/start link_<token>` handleri, ichki API mijozi. So'z o'yini kodi **tegilmaydi**. |
| Outbox yetkazuvchi | Sayt hodisalarini (buyurtma tasdiqlandi, bildirishnoma) bog'langan foydalanuvchiga Telegram orqali yetkazish | Bot jarayoni ichida davriy vazifa yoki alohida kichik servis |
| nginx | Faqat ommaviy yo'llar | `/api/v1/internal/*` tashqariga **ochilmaydi** |

## 3. Telegram akkauntini sayt akkauntiga xavfsiz bog'lash

### 3.1 Asosiy oqim: saytdan boshlanadigan deep-link (tavsiya)

1. Foydalanuvchi saytga o'z email/telefon va paroli bilan kiradi, "Telegram'ni bog'lash" tugmasini bosadi.
2. Backend tasodifiy token yaratadi (≥ 32 bayt).
   - Bazaga faqat token xeshi yoziladi (`telegram_link_tokens`: `user_id`, `token_hash`, `expires_at` (10 daqiqa), `used_at`).
   - Foydalanuvchiga `https://t.me/<bot>?start=link_<token>` qaytariladi.
3. Bot `/start link_<token>` ni oladi. `from_user.id` Telegram'ning o'z update'idan keladi, ya'ni bot tokeni bilan imzolangan kanal orqali.
4. Bot `POST /api/v1/internal/bot/link` ga `{token, telegram_id, username}` yuboradi. Bu `127.0.0.1` orqali, xizmat kaliti bilan amalga oshiriladi.
5. Backend tekshiradi:
   - token mavjud, muddati o'tmagan va ishlatilmagan;
   - sayt akkaunti banned emas;
   - `telegram_id` boshqa akkauntga bog'lanmagan;
   - bu akkauntda boshqa `telegram_id` yo'q.
   
   Shundan keyin bitta tranzaksiyada `users.telegram_id` ni yozadi, tokenni `used` qiladi va `telegram_link_audit` ga yozuv qo'shadi.
6. Bot ham, sayt ham foydalanuvchiga tasdiq xabarini ko'rsatadi. Saytda "Bog'lashni bekor qilish" tugmasi bo'ladi.

Nega xavfsiz: token sayt sessiyasi bilan yaratiladi (akkaunt egaligi isbot), Telegram ID esa Telegram'ning o'zidan keladi (Telegram egaligi isbot). Ikkalasi ham bo'lmasa, bog'lanish bo'lmaydi.

### 3.2 Qo'shimcha oqim: Mini App ichida

- Saytda kirgan foydalanuvchi Mini App ichida "Bog'lash" ni bosadi.
- Backend bir vaqtda ikkita narsani talab qiladi:
  - joriy sayt sessiyasi;
  - yangi `initData`, `max_age` qisqa (masalan 10 daqiqa; hozirgi `validate_telegram_init_data` default 86400).

### 3.3 Hozirgi Mini App kirishiga kerakli o'zgarish

`get_or_create_telegram_user` (`backend/app/services/auth/service.py:159`) bog'lanmagan Telegram ID uchun avtomatik **yangi** akkaunt yaratadi. Bog'lash joriy qilinganda bu oqim quyidagicha o'zgarishi kerak:
- bog'langan bo'lsa — kirish;
- bog'lanmagan bo'lsa — "kiring yoki ro'yxatdan o'ting, keyin bog'laysiz".

Aks holda bir odamda ikkita akkaunt paydo bo'ladi. Avval yaratilgan `@telegram.local` akkauntlar prod'da 0 ta, shuning uchun hozir migratsiya kerak emas.

### 3.4 Qat'iy qoidalar

- Faqat Telegram ID, faqat telefon yoki faqat ism bo'yicha avtomatik bog'lash yo'q (DB audit 4-bo'lim: telefon bo'yicha atigi 4 ta moslik va ular tasdiqlanmagan).
- `initDataUnsafe` ga hech qachon ishonilmaydi (sayt kodi buni allaqachon bajaradi).
- Bog'lash, bekor qilish va qayta bog'lash audit jurnaliga yoziladi. Qayta bog'lash uchun kutish vaqti qo'yiladi.
- **S0 hal qilinmaguncha bog'lash yoqilmaydi:** ochiq token bilan `initData` ni soxtalashtirish mumkin.

## 4. Autentifikatsiya va ruxsatlar

| Kanal | Mexanizm |
|---|---|
| Bot → sayt ichki API | Alohida xizmat kaliti (`BOT_INTERNAL_API_KEY`, faqat ikkala `.env` da). Faqat `127.0.0.1`. Har so'rov `telegram_id` ni o'z ichiga oladi; backend uni faqat bog'langan akkaunt uchun qabul qiladi. Bot hech qachon sayt JWT'sini olmaydi va saqlamaydi. |
| Sayt → bot | To'g'ridan-to'g'ri chaqiruv yo'q. Sayt `notification_outbox` ga yozadi, yetkazuvchi o'qiydi. |
| Bot admin | `ADMIN_IDS` (Telegram ID ro'yxati) saqlanadi, lekin **har bir** admin callback'i `is_admin` tekshiruvidan o'tadi. S1 (to'lov callback'i) tuzatiladi. |
| Sayt admin | Mavjud rollar (`require_super_admin` va boshqalar) |
| Secretlar | Bot tokeni va xizmat kaliti faqat backend va bot `.env` larida. Frontend'ga hech qachon bermaslik. `.env` Git'dan chiqariladi (S0). |

## 5. API va rate limiting

Ichki API (`/api/v1/internal/bot/*`):
- `POST link` — bog'lash.
- `GET user/{telegram_id}` — bog'langan akkaunt: ism, faol tariflar, kurs kirishi.
- `GET offers` — sayt narxlari (bot `COURSE_INFO` o'rniga, keyingi bosqichda).
- `POST unlink`.

Cheklovlar:
- har `telegram_id` uchun daqiqasiga N ta so'rov;
- har bog'lash tokeni uchun 5 ta urinish;
- xizmat kalitiga global limit.

Sayt hozir kirish limitlari uchun `auth_rate_limit_events` dan foydalanadi; xuddi shu mexanizm ishlatiladi.

Telegram tomonida yetkazuvchi Bot API limitlarini hurmat qiladi (`RetryAfter`, ~25 xabar/soniya). Bot broadcast servisidagi pacing (`services/broadcast.py`) qayta ishlatiladi.

## 6. Umumiy biznes mantiqi

| Soha | Qaror |
|---|---|
| Yangi xaridlar | Sayt VIZU Pay yagona joy. Bot kurs bo'limi saytdagi "Angebote" ga Mini App orqali yo'naltiradi (alohida tasdiqdan keyin). Bot `payments` oqimi tarixiy yozuvlar va Telegram kanaliga kirish uchun qoladi, toki ular bo'yicha qaror qabul qilinmaguncha. |
| Tarixiy bot xaridlari | Saytga **avtomatik** kirish huquqiga aylantirilmaydi: mahsulotlar har xil. Variant — bog'langan foydalanuvchiga admin tasdig'i bilan "legacy" yozuv. Biznes qarori kerak. |
| XP | Ikki XP alohida qoladi. Saytda ko'rsatilsa, "So'z o'yini XP" deb belgilanadi. |
| Sertifikatlar | W-Zertifikat botda. Saytda bog'langan foydalanuvchi uchun faqat ro'yxat ko'rinishi. |
| Uy vazifasi | Bot modeli (kategoriya, parol, kanal) saqlanadi. Saytga ko'chirish alohida loyiha (biznes qoidalarini moslash kerak). |

## 7. Schema va migratsiya strategiyasi

- **Sayt:** faqat Alembic, faqat additive migratsiyalar:
  - `telegram_link_tokens`;
  - `telegram_link_audit`;
  - `notification_outbox`.
  
  `users.telegram_id` allaqachon bor (unique, nullable). Har migratsiyaning downgrade yo'li yoziladi.
- **Bot:** `database/init.py` modeli o'zgarmaydi. Bot bazasiga yangi jadval faqat zarur bo'lsa qo'shiladi (masalan, bog'lash keshi). Uning o'rniga sayt API'sini so'rash afzal.
- **Ma'lumot ko'chirish** (masalan, uy vazifasi tarixi): faqat nusxa olish orqali. Manba o'zgarmaydi; idempotent skript, `--dry-run`, avval staging.

## 8. Fon vazifalari va schedulerlar

| Vazifa | Joyi |
|---|---|
| Champion schedulerlari, xotira tozalash | Botda qoladi (o'zgarmaydi) |
| Outbox yetkazish | Bot jarayonida yangi `asyncio` vazifa (masalan, har 5 soniyada `internal/bot/outbox` dan olish va `ack`) yoki alohida systemd servis. Takroriy yuborishga chidamli bo'lishi kerak (`delivered_at`, `attempts`). |
| Bot DB zaxirasi | Yangi systemd timer yoki `backup_db.sh` ni kengaytirish (2-bosqich) |
| FSM xotirasi | Ixtiyoriy: `MemoryStorage` → Redis (serverda `127.0.0.1:6379` ishlayapti). So'z o'yini sessiyalari bunga kirmaydi, chunki ular boshqa obyektlarda. |

## 9. Rollback va tiklash

- Har funksiya flag bilan yoqiladi: sayt `app_settings`, bot `.env`. Rollback = flagni o'chirish va restart.
- Migratsiyalar additive. Downgrade faqat yangi jadvallarni o'chiradi. `users.telegram_id` ni tozalash faqat audit jurnali asosida, alohida tasdiq bilan.
- Har prod qadamdan oldin ikkala baza zaxiralanadi va restore testi o'tkaziladi.
- Bot kodi: oldingi commitga `git revert` (`reset --hard` emas) va restart. Sayt: mavjud `.next-a`/`.next-b` slotlari.
- Hech qachon foydalanuvchi, progress, to'lov yoki media yozuvlari ommaviy o'chirilmaydi.
