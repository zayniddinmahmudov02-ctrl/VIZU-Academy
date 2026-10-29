# Global Chat

Barcha login qilgan foydalanuvchilar (student, teacher, admin) uchun bitta umumiy chat. Dashboardning pastki o‘ng burchagidagi ikonka orqali ochiladi. Guruh chatlaridan (`study_group_messages`) to‘liq alohida: o‘z jadvallari, o‘z API’si bor, umumiy kodi yo‘q.

## Qayerda

| Qism | Fayl |
|---|---|
| Model | `backend/app/models/global_chat.py` |
| Migration | `backend/alembic/versions/c8f2a6d4e1b9_global_chat.py` (`b7e3d9a2c5f1` dan keyin), `e9b4c2f7a3d1_global_chat_edit_delete.py` (tahrirlash/o‘chirish), `f3a8c1d5e7b2_global_chat_reply.py` (javob berish) |
| Servislar | `backend/app/services/global_chat/` — `access.py`, `messages.py`, `restrictions.py`, `word_filter.py` |
| API | `backend/app/api/global_chat/router.py` |
| Testlar | `backend/tests/test_global_chat.py`, `e2e/tests/global-chat.spec.ts` |
| Chat oynasi | `frontend/src/features/global-chat/components/global-chat-widget.tsx`, `chat-panel.tsx` |
| Mute/ban dialogi | `frontend/src/features/global-chat/components/restrict-dialog.tsx` |
| Admin panel | `/admin/global-chat` → `admin-global-chat.tsx` |
| Ikonka ulangan joylar | `components/dashboard/dashboard-layout.tsx`, `components/teacher/teacher-shell.tsx`, `components/admin/admin-shell.tsx` |

## Jadvallar

| Jadval | Vazifasi |
|---|---|
| `global_chat_messages` | Xabarlar. `status`: `visible` / `pending` (so‘z filtri ushlab qoldi) / `hidden` (moderator yashirdi) / `deleted` (muallif o‘chirgan). Pin shu jadvalda saqlanadi (`pinned_at`, `pinned_by`). Tahrir va o‘chirish vaqti `edited_at`, `deleted_at` ustunlarida. `reply_to_id` — javob berilgan xabar (FK shu jadvalning o‘ziga, `ON DELETE SET NULL`, partial index); eski xabarlarda `NULL`. |
| `global_chat_message_edits` | Har bir tahrirdan oldingi matn va holat. Faqat moderatorlar ko‘radi. |
| `global_chat_restrictions` | Mute va ban. `kind`, `starts_at`, `ends_at` (NULL = doimiy ban), ichki `reason`, foydalanuvchiga ko‘rinadigan `public_note`, `created_by`, `revoked_*`. |
| `global_chat_moderation_actions` | Audit jurnali: kim, nima, qachon, nega. Bu jadvalga token, parol yoki boshqa secret yozilmaydi. |
| `global_chat_reads` | Har bir foydalanuvchining `last_read_at` qiymati, o‘qilmagan xabarlar sonini hisoblash uchun. |

**Xabarlarni o‘chirish siyosati.** Bazadan hech qanday qator o‘chirilmaydi.

- Moderator yashirgan (`hidden`) yoki muallif o‘chirgan (`deleted`) xabarning matni moderatorlar va audit uchun saqlanib qoladi; oddiy foydalanuvchilar uni ko‘rmaydi.
- Bunday xabar avtomatik ravishda pin’dan olinadi.
- Akkaunt o‘chirilsa, xabar qoladi, lekin `sender_id = NULL` bo‘ladi va muallif o‘rnida “O‘chirilgan akkaunt” ko‘rsatiladi.

## O‘z xabarini tahrirlash va o‘chirish

O‘z xabaringizdagi `…` menyusida “Tahrirlash / Bearbeiten” va “O‘chirish / Löschen” amallari bor. Boshqa foydalanuvchining xabarida bu menyu chiqmaydi.

**Kim bajara oladi.** Faqat xabar muallifi. Muallif token’dan olinadi; body’da faqat `body` qabul qilinadi, `user_id`, `sender_id` va `role` berilsa 422 qaytadi. Moderator ham boshqa userning xabarini tahrirlay olmaydi; buning uchun “yashirish” amali bor.

**Server javoblari:**

| Holat | Javob |
|---|---|
| Xabar yo‘q yoki chaqiruvchi uni ko‘ra olmaydi (boshqa userning `pending`/`hidden` xabari) | `404` — xabar mavjudligi oshkor qilinmaydi |
| Boshqa userning ko‘rinadigan xabari | `403 not_author` |
| Moderator yashirgan xabar (muallifning o‘zi uchun ham) | tahrirlab ham, o‘chirib ham bo‘lmaydi (`409 message_hidden`). Oddiy muallif bunday xabarni ko‘rmaydi, shuning uchun unga `404` qaytadi. |
| Qadalgan xabarni tahrirlash | `409 message_pinned` — admin tanlagan matn o‘zgarmaydi. O‘chirish mumkin. |

**Tahrirlash:**

- Mute yoki ban holatida tahrirlash ham yozish hisoblanadi (`403 chat_muted` / `chat_banned`). O‘chirishga esa ruxsat bor.
- Matn yuborishdagi qoidalar bilan tekshiriladi: bo‘sh bo‘lmasligi, ko‘pi bilan 2000 belgi, control belgilar olib tashlanadi; daqiqasiga ko‘pi bilan 10 ta tahrir (`429 too_many_edits`).
- Tahrir qilingan matn **yana so‘z filtridan** o‘tadi. Filtr biror so‘z topsa, xabar `pending` holatiga o‘tadi va boshqa userlarning oynasidan olib tashlanadi.
- `pending` xabarni toza matnga tahrirlash uni avtomatik chiqarib yubormaydi: qarorni moderator chiqaradi.
- Har bir tahrirdan oldingi matn `global_chat_message_edits` jadvaliga yoziladi. Shu sababli tahrir orqali haqoratni moderatordan yashirib bo‘lmaydi. Bu tarixni oddiy foydalanuvchi ko‘ra olmaydi; admin panelda “frühere Versionen” orqali ko‘rinadi.
- Chatda xabar yonida “bearbeitet / tahrirlangan” belgisi chiqadi, kursor olib borilganda tahrir vaqti ko‘rinadi.
- Tahrir audit jurnaliga yozilmaydi (jurnal to‘lib ketmasligi uchun). Versiyalar jadvali tahrirlar tarixi bo‘lib xizmat qiladi.

**O‘chirish:**

- O‘chirishdan oldin tasdiqlash oynasi chiqadi.
- Status `deleted` bo‘ladi va `deleted_at` yoziladi. Pin avtomatik olib tashlanadi. Xabar o‘qilmaganlar sonidan ham chiqadi.
- Boshqa userlar uchun xabar butunlay yo‘qoladi (Telegram’dagi kabi): polling uning id’sini `removed_ids` ichida yuboradi.
- Moderator xabarni “Vom Autor gelöscht” belgisi bilan, asl matni bilan birga ko‘radi.
- Audit jurnaliga `message.delete` yoziladi: actor = muallif, meta’da oldingi holat, pin qilinganmi va matndan parcha.
- O‘chirilgan xabarni moderator pin qila olmaydi, tasdiqlay olmaydi va qayta ko‘rsata olmaydi (`409 message_deleted`).
- Muallif `pending` xabarini o‘chirsa, u tekshiruv navbatidan chiqadi.

Avvalgi moderatsiya yozuvlari (pin, hide, mute, ban, filtr) o‘zgarmaydi. Tahrirlash yoki o‘chirish ular ustidan yozmaydi.

## Xabarga javob berish (Reply)

- **Qanday:** xabar yonidagi ↩ “Antworten / Javob berish” tugmasi (desktopda hover yoki klaviatura fokusi bilan ko‘rinadi, sensorli ekranda doim ko‘rinadi) yoki mobil qurilmada xabarni **chapga surish**. Yozish maydoni tepasida muallif nomi va matndan parcha chiqadi; X yoki Escape javobni bekor qiladi (chat yopilmaydi).
- **Swipe qoidalari** (`reply-swipe.ts`, unit testlari bor): faqat aniq gorizontal, chapga harakat; o‘q 10 px dan keyin bir marta aniqlanadi. Vertikal yoki diagonal harakat — oddiy scroll (`touch-action: pan-y`), o‘ngga harakat (tizimning “orqaga” imo-ishorasi) — hech qachon javob emas. Uzoq bosib turish yoki matn tanlangan bo‘lsa swipe bekor qilinadi. Javob barmoq qo‘yib yuborilganda 64 px dan keyin ishlaydi, qaytarib tortilsa bekor bo‘ladi.
- **Chatda:** javob ichida asl xabar iqtibosi (muallif + 140 belgigacha parcha). Iqtibosga bosilsa asl xabarga scroll qilinadi va 1,6 s ajratib ko‘rsatiladi; kerak bo‘lsa eski sahifalar (ko‘pi bilan 5 ta) yuklanadi, topilmasa “Asl xabar tarixda topilmadi” xabari chiqadi.
- **Asl xabar o‘chirilgan / yashirilgan:** javob qoladi, iqtibos o‘rnida “Xabar mavjud emas / Nachricht nicht mehr verfügbar”. Matn va muallif bunday holatda hech kimga (moderator yashirgan xabar uchun — oddiy userlarga) yuborilmaydi.
- **Server qoidalari:** client faqat `reply_to_id` yuboradi; iqtibos matni va muallif serverda asl qatordan quriladi (body’da boshqa maydon → 422). Maqsad xabar Global Chat xabari bo‘lishi va yuboruvchiga ko‘rinishi shart (o‘chirilgan, boshqa userning `pending`/`hidden` xabari, guruh chati xabari yoki mavjud bo‘lmagan id → bir xil `422 reply_not_found`, mavjudligi oshkor qilinmaydi). Javob oddiy xabar: mute/ban (`403` — avval tekshiriladi), rate limit, dublikat va so‘z filtri o‘zgarmagan holda ishlaydi. Tahrirlash (PATCH) `reply_to_id` ni qabul qilmaydi — javob boshqa xabarga ko‘chirilmaydi.

**Cheklovlar** quyidagi qoidalar bo‘yicha ishlaydi:

- Cheklov faol hisoblanadi, agar u bekor qilinmagan bo‘lsa va hozirgi vaqt `starts_at ≤ now < ends_at` oralig‘ida bo‘lsa.
- Muddati tugagan cheklov o‘z-o‘zidan kuchini yo‘qotadi; buning uchun cron yoki job kerak emas.
- Partial unique index har bir user va har bir tur (`kind`) uchun bittadan ortiq “tirik” qatorga yo‘l qo‘ymaydi. Yangi mute yoki ban qo‘yilganda eskisi `revoke_reason = superseded` bilan yopiladi.
- Mute va ban bir vaqtda faol bo‘lsa, ban ustuvor.

## Rollar (backendda tekshiriladi)

| Kim | Huquqi |
|---|---|
| Har bir login qilgan user | O‘qiydi. Mute yoki ban qilinmagan bo‘lsa, yozadi. |
| `SUPER_ADMIN`, `ADMIN` | Moderatsiya: pin/unpin, yashirish/qayta ko‘rsatish, tasdiqlash, mute, ban, muddatni o‘zgartirish, cheklovni bekor qilish, so‘z filtri. |
| Faqat `SUPER_ADMIN` | Doimiy ban berish, uni o‘zgartirish va bekor qilish. |

Qo‘shimcha qoidalar:

- Moderatorni (`SUPER_ADMIN`/`ADMIN`) mute yoki ban qilib bo‘lmaydi. O‘zini cheklab ham bo‘lmaydi.
- So‘rov tanasida (body) chaqiruvchining `user_id` yoki `role` maydonlari qabul qilinmaydi (`extra="forbid"`).
- `/admin` UI hozircha faqat `SUPER_ADMIN` uchun ochiq (mavjud `AdminGuard`). `ADMIN` moderatsiyani chat oynasining o‘zida bajaradi; backend API unga ham ruxsat beradi.

Mute va ban **faqat** Global Chatda yozishni to‘xtatadi. `users` jadvalining hech bir ustuni o‘zgarmaydi: akkaunt, kurslar, to‘lovlar, progress va guruh chatlariga ta’sir qilmaydi.

## Muddatlar

- **Mute:** 10 daqiqa, 1 soat, 24 soat, 3 kun, 7 kun, 30 kun yoki maxsus muddat (ko‘pi bilan 1 kalendar yil).
- **Ban:** 1, 2, 3, 5 yil yoki doimiy.
  - Yillar 365 kun deb emas, **kalendar** bo‘yicha qo‘shiladi (UTC): 29.02.2028 + 1 yil = 28.02.2029.
  - Admin banni uzaytirishi yoki qisqartirishi mumkin: yangi sana kiritadi yoki boshlanishdan 1/2/3/5 yil tanlaydi.

## So‘z filtri

- Standart ro‘yxat kodda turadi: o‘zbek (lotin va kirill), rus (translit ham), nemis va ingliz tillaridagi haqoratli so‘zlar.
- Admin ro‘yxatni `/admin/global-chat` → “Wortfilter” bo‘limida tahrirlaydi (`app_settings`, kalit `global_chat_word_filter`). U yerda filtrni o‘chirish yoki standart ro‘yxatga qaytarish ham mumkin.
- Faqat **butun so‘z** tekshiriladi, shuning uchun so‘z ichidagi harflar ketma-ketligi topilmaydi (`Dickdarm`, `Hui!`, `assessment` kabi so‘zlar bloklanmaydi).
- Katta-kichik harf, raqam bilan almashtirilgan harflar (`b1tch`) va cho‘zilgan harflar (`fuuuck`) aniqlanadi.
- `so‘z*` yozuvi shu bilan boshlanadigan barcha so‘zlarga mos keladi.
- Filtr topgan xabar `pending` bo‘ladi: uni faqat yuboruvchi va moderatorlar ko‘radi, xabar “Prüfen” navbatiga tushadi.
- Filtr **hech kimni avtomatik mute yoki ban qilmaydi**: yakuniy qarorni admin chiqaradi.
- Moderatorlarning xabarlari filtrdan o‘tkazilmaydi.
- Ma’lum cheklov: harflari bo‘sh joy bilan ajratib yozilgan so‘z (`f u c k`) aniqlanmaydi.

## Spam va xavfsizlik

- Xabar faqat matndan iborat bo‘ladi, ko‘pi bilan 2000 belgi. Control belgilar olib tashlanadi, bo‘sh xabar rad etiladi (422).
- Frontend matnni React text sifatida chiqaradi. `dangerouslySetInnerHTML` ishlatilmaydi, shuning uchun HTML yoki script bajarilmaydi (e2e testda tekshirilgan).
- Rate limit serverda, har bir user uchun advisory lock ostida ishlaydi:
  - daqiqasiga ko‘pi bilan 10 ta xabar;
  - ikki xabar orasida kamida 1 soniya;
  - bir xil matnni 60 soniya ichida qayta yuborib bo‘lmaydi.
  - Har bir buzilishga `429` (`too_many_messages` / `too_fast` / `duplicate_message`) qaytadi.
- Mute yoki ban qo‘yilgan zahoti server xabarni rad etadi (`403 chat_muted` / `chat_banned`). Frontendda tugmaning bloklanishi faqat qulaylik uchun.

## API (`/api/v1`, eski bare mount ham bor)

Foydalanuvchi uchun (login talab qilinadi):

| Metod | Yo‘l | |
|---|---|---|
| GET | `/global-chat/messages?before=<id>&limit=` | Eng yangi sahifa yoki `before` dan oldingi xabarlar. Javobda `pinned`, `me`, `unread`, `sync` ham bor. |
| GET | `/global-chat/updates?since=<sync>` | Polling: `since` dan keyin o‘zgargan xabarlar (`items`, `removed_ids`) va `reset`. |
| POST | `/global-chat/messages` `{body, reply_to_id?}` | Xabar yuborish; `reply_to_id` bilan — javob. Har bir xabarda `reply_to: {id, available, sender, excerpt} \| null`. |
| PATCH | `/global-chat/messages/{id}` `{body}` | O‘z xabarini tahrirlash. |
| DELETE | `/global-chat/messages/{id}` | O‘z xabarini o‘chirish (`204`). |
| GET | `/global-chat/pinned` | Qadalgan xabarlar. |
| GET | `/global-chat/unread-count` | O‘qilmagan xabarlar soni. |
| GET | `/global-chat/me` | Yozish mumkinmi; mute/ban turi, tugash vaqti va izoh. |
| POST | `/global-chat/read` `{until_id?}` | O‘qilganlik belgisini oldinga suradi (orqaga hech qachon qaytmaydi). |

Moderator uchun (`/admin/global-chat`):

| Metod | Yo‘l | |
|---|---|---|
| GET | `/stats` | Panel raqamlari. |
| GET | `/messages?filter=all\|pending\|hidden\|pinned\|flagged\|edited\|deleted&q=&user_id=` | Xabarlar ro‘yxati (email va rol bilan). |
| GET | `/messages/{id}/edits` | Xabarning oldingi versiyalari. |
| PATCH | `/messages/{id}` `{action: pin\|unpin\|hide\|unhide\|approve, reason?}` | Xabarni moderatsiya qilish. |
| GET/POST | `/restrictions` | Ro‘yxat (`state=active\|expired\|revoked\|all`) va yangi mute/ban. |
| PATCH | `/restrictions/{id}` `{ends_at \| ban_years \| permanent, reason?}` | Muddatni uzaytirish yoki qisqartirish. |
| POST | `/restrictions/{id}/revoke` | Cheklovni bekor qilish. |
| GET | `/actions` | Audit jurnali. |
| GET | `/users?q=` | Foydalanuvchi qidirish. |
| GET | `/users/{id}` | Bitta foydalanuvchining moderatsiya tarixi. |
| GET/PUT/DELETE | `/word-filter` | So‘z ro‘yxatini ko‘rish, saqlash va standartga qaytarish. |

## Real-time: nega polling?

Loyihada WebSocket infratuzilmasi yo‘q. Production’da bir nechta uvicorn worker ishlaydi, shuning uchun WebSocket qo‘shish uchun quyidagilar kerak bo‘ladi:

- worker’lar orasida xabar tarqatish uchun pub/sub (Redis);
- nginx’da `Upgrade` sozlamalari (nginx o‘zgarishlari avval ham to‘xtab qolgan).

Bu yangi servis va deploy xavfi degani. Shu sababli chat guruh chatlaridagi kabi **polling** bilan ishlaydi:

- **Chat ochiq bo‘lsa:** har 4 soniyada `/updates?since=` so‘raladi. Sahifa ko‘rinmayotganda polling to‘xtaydi.
- **Chat yopiq bo‘lsa:** har 30 soniyada faqat `/unread-count` so‘raladi.
- `sync` — bazadagi vaqtdan 15 soniya oldingi qiymat. Shu “overlap” kech commit bo‘lgan tranzaksiyani ham ushlaydi; xabarlar `id` bo‘yicha birlashtirilgani uchun dublikat paydo bo‘lmaydi.
- Bitta `updated_at` so‘rovi yangi, tasdiqlangan, pin qilingan va yashirilgan xabarlarni birga qaytaradi (`ix_global_chat_messages_updated` index).
- `since` 10 daqiqadan eski bo‘lsa yoki o‘zgarishlar 200 tadan oshsa, server `reset` qaytaradi va client eng yangi sahifani qayta yuklaydi.

Kelajakda WebSocket qo‘shiladigan bo‘lsa, `/updates` mantiqi xuddi shunday qoladi. WebSocket faqat “yangilash kerak” signalini yuboradi, shuning uchun auth va ruxsat tekshiruvi yana shu HTTP endpointlarda bajariladi.

## Deploy / rollback

1. Backup oling, so‘ng `alembic upgrade head` ishga tushiring. Migration faqat 4 ta yangi jadval va ularning indekslarini yaratadi; mavjud jadvallarga tegmaydi.
2. Backend’ni qayta ishga tushiring, frontend’ni slot orqali deploy qiling (`.next-a` / `.next-b`).
3. Rollback:
   - frontend’ni oldingi slotga qaytaring;
   - faqat javob berish funksiyasini olib tashlash uchun `alembic downgrade e9b4c2f7a3d1` bajaring: `reply_to_id` ustuni va indeksi o‘chadi, javoblar oddiy xabar bo‘lib qoladi (matnlar saqlanadi). Bu keyingi `a6d2f9c4e8b1` (A2 Audio Manager jadvali) ni ham olib tashlaydi;
   - faqat tahrirlash/o‘chirish funksiyasini olib tashlash uchun `alembic downgrade c8f2a6d4e1b9` bajaring. U `global_chat_message_edits` jadvalini va 2 ta ustunni o‘chiradi. `deleted` holatidagi xabarlar `hidden` holatiga o‘tkaziladi (sababi: “deleted by author”), shuning uchun ular userlarga qayta ko‘rinib qolmaydi.
   - butun Global Chatni olib tashlash uchun `alembic downgrade b7e3d9a2c5f1` bajaring — u faqat `global_chat_*` jadvallarini o‘chiradi.

   Admin so‘z ro‘yxatini o‘zgartirgan bo‘lsa, `app_settings` jadvalidagi `global_chat_word_filter` qatori qoladi; bu zararsiz.

## Ma’lum cheklovlar

- Real-time polling orqali ishlaydi (yuqoriga qarang).
- Rasm va fayl yuborib bo‘lmaydi; birinchi versiyada faqat matn.
- Tahrirlash uchun vaqt chegarasi yo‘q: muallif eski xabarini ham tahrirlay oladi. Bunda oldingi versiya saqlanadi va filtr qayta ishlaydi.
- O‘chirilgan xabarning matni moderatorlar uchun bazada qoladi; foydalanuvchiga buni ochiq aytish (qoidalar matnida) tavsiya qilinadi.
- Shikoyat (“report”) tugmasi yo‘q. Tekshiruv navbati faqat so‘z filtridan to‘ldiriladi.
- Bir vaqtda ko‘pi bilan 5 ta xabar qadalishi mumkin; chat oynasida eng oxirgisi ko‘rsatiladi, qolganlari ochiladigan ro‘yxatda turadi.
