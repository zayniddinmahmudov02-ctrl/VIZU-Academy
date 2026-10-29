# Global Chat — xabarga javob berish (Reply): audit va hisobot

Sana: 2026-10-30. Holat: **kod tayyor, lokal test qilingan, production’ga deploy QILINMAGAN**, production migration bajarilmagan.

## 1. Boshlang‘ich holat (audit)

| Savol | Topilgan |
|---|---|
| Global Chat qayerda | `backend/app/models/global_chat.py`, `services/global_chat/`, `api/global_chat/router.py`, frontend `features/global-chat/` (batafsil: `docs/global-chat.md`) |
| Guruh chatidan ajratilganmi | Ha — o‘z jadvallari (`global_chat_*`), o‘z API’si; `study_group_messages` bilan umumiy kod yo‘q |
| Reply oldin bormidi | Yo‘q |
| Tahrirlash / o‘chirish | **Mavjud** (`e9b4c2f7a3d1`, `edit_own` / `delete_own`, versiyalar jadvali, “bearbeitet” belgisi). O‘zgartirilmadi, reply bilan birga sinaldi |
| Mute / ban / rate limit / so‘z filtri / audit log | Mavjud, serverda; o‘zgartirilmadi |
| Real-time | Polling (`/updates`, 4 s) — WebSocket yo‘q; reply ham polling orqali keladi |
| Alembic head | `e9b4c2f7a3d1` (yagona) |

## 2. Nima qilindi

**Backend**
- `global_chat_messages.reply_to_id` (UUID, FK → `global_chat_messages.id`, `ON DELETE SET NULL`), partial index `ix_global_chat_messages_reply_to WHERE reply_to_id IS NOT NULL`. Migration `f3a8c1d5e7b2` (additive, `downgrade` bor). Eski xabarlar `NULL` — o‘zgarishsiz ishlaydi.
- `POST /global-chat/messages` body: `{body, reply_to_id?}` (`SendIn`, `extra="forbid"`). `PATCH` (tahrir) avvalgidek faqat `{body}` — javobni boshqa xabarga ko‘chirib bo‘lmaydi.
- Tekshiruv tartibi: matn → mute/ban (`403`) → reply maqsadi → rate limit (`429`) → so‘z filtri. Maqsad mavjud bo‘lmasa, o‘chirilgan bo‘lsa, yuboruvchiga ko‘rinmasa (boshqa userning `pending`/`hidden` xabari) yoki guruh chati xabari id’si bo‘lsa — bir xil `422 reply_not_found` (mavjudlik oshkor qilinmaydi). FK bazada ham faqat Global Chat id’sini qabul qiladi.
- Har bir xabarda server quradigan `reply_to: {id, available, sender{id,name}, excerpt}` (140 belgi, bo‘shliqlar yig‘iladi). Client yuborgan matn/muallif ishlatilmaydi. Maqsad o‘chirilgan yoki ko‘ruvchiga ko‘rinmasa — `available: false`, matn va muallifsiz.

**Frontend**
- Reply tugmasi har bir xabarda: desktopda hover / klaviatura fokusi bilan, sensorli ekranda (`@media (hover:none)`) doim ko‘rinadi. Klaviatura: Tab → Enter.
- Mobil swipe: chapga surish (`reply-swipe.ts` — sof funksiyalar, 15 ta unit test bilan). Vertikal scroll (`touch-action: pan-y`), o‘ngga “orqaga” imo-ishorasi, matn tanlash va uzoq bosish buzilmaydi; tugmalar/havolalar ustida swipe boshlanmaydi.
- Yozish maydoni tepasida preview (muallif + parcha + X). Escape avval reply’ni bekor qiladi, keyin chatni yopadi.
- Javob ichidagi iqtibos → asl xabarga scroll + ajratib ko‘rsatish; yuklanmagan bo‘lsa 5 tagacha eski sahifa yuklanadi; topilmasa xabar chiqadi.
- Iqtibos mazmuni (`reply-preview.ts`): asl xabar oynada bo‘lsa — uning hozirgi (tahrirlangan) matni; polling uni olib tashlagan bo‘lsa — “Xabar mavjud emas”; aks holda server iqtibosi.
- Matn React text sifatida chiqadi (`dangerouslySetInnerHTML` yo‘q), emoji hisobida kesilmaydi.

## 3. O‘zgartirilgan / yangi fayllar

| Fayl | |
|---|---|
| `backend/app/models/global_chat.py` | `reply_to_id`, `reply_to` relationship, index |
| `backend/alembic/versions/f3a8c1d5e7b2_global_chat_reply.py` | yangi migration |
| `backend/app/services/global_chat/messages.py` | `reply_preview`, `_reply_target`, `post(..., reply_to_id)` |
| `backend/app/api/global_chat/router.py` | `SendIn` |
| `backend/tests/test_global_chat.py` | +2 kontrakt/unit, +6 integratsiya testi |
| `backend/tests/test_global_chat_reply_migration.py` | upgrade → downgrade → upgrade (alohida DB) |
| `frontend/src/features/global-chat/reply-swipe.ts`, `reply-preview.ts` | sof mantiq |
| `frontend/src/features/global-chat/components/reply-ui.tsx` | `SwipeToReply`, `ReplyQuote`, `ReplyComposerPreview` |
| `frontend/src/features/global-chat/components/chat-panel.tsx` | integratsiya |
| `frontend/src/features/global-chat/global-chat-service.ts` | `reply_to`, `sendMessage(body, replyToId)` |
| `frontend/src/lib/i18n/translations.ts` | 8 ta yangi kalit (de/uz) |
| `frontend/tests/unit/reply-*.test.mjs`, `frontend/package.json` (`test:unit`) | unit testlar, yangi dependency yo‘q |
| `e2e/tests/global-chat-reply.spec.ts` | E2E |
| `docs/global-chat.md` | Reply bo‘limi, API, rollback |

## 4. Talab qilingan 12 holat va testlar

| # | Holat | Backend | Frontend unit | E2E |
|---|---|---|---|---|
| 1 | Oddiy javob | `test_reply_links_to_the_original` | — | “reply with the button…” (desktop+mobile) |
| 2 | Asl xabar bilan bog‘lanish | o‘sha (DB `reply_to_id`, polling) | `resolveReply` | API testi |
| 3 | Boshqa chat xabari rad | `test_reply_to_unknown_or_foreign_message_is_refused` (guruh chati id) | — | — |
| 4 | Mavjud bo‘lmagan xabar rad | o‘sha | — | API testi (`422`) |
| 5 | Asl xabar o‘chirilgan | `test_reply_to_deleted_message` | fallback testi | “the original is deleted…” |
| 6 | Preview bekor qilish | — | — | X va Escape |
| 7 | Mobil swipe | — | 15 ta swipe testi | mobile (Pixel 7) |
| 8 | Swipe ↔ scroll | — | vertikal/diagonal/o‘ngga/uzun bosish | vertikal drag → reply yo‘q, `touch-action: pan-y`, gorizontal scroll yo‘q |
| 9 | Asl xabarga qaytish | — | — | iqtibosga bosish → `data-highlighted`, viewport ichida |
| 10 | Mute/ban, rate limit | `test_reply_respects_mute_ban_and_rate_limit` (+ so‘z filtri) | — | — |
| 11 | Eski xabarlar, migration | `test_old_messages_without_reply_still_work`, migration round-trip | — | — |
| 12 | Tahrirlash/o‘chirish bilan | `test_reply_with_edit_and_delete` | — | — |

Shuningdek tekshirildi: uzun xabar (2000 belgi limiti o‘zgarmagan, iqtibos 140), emoji (`excerpt` testi, E2E 🎉/👍), bo‘sh xabar (avvalgi testlar), tez-tez yuborish (`too_fast`, `too_many_messages`, `duplicate_message`).

Natijalar: `docs/audit/test-results.md`.

## 5. Ma’lum cheklovlar

- Iqtibos polling bilan yangilanadi: asl xabar tahrirlansa, boshqa userlarda u oynada yuklangan bo‘lsa darhol, aks holda keyingi sahifa yuklanganda yangilanadi.
- Jump faqat ko‘pi bilan 5 ta eski sahifagacha qidiradi (200 xabar).
- Moderatorlar yashirilgan asl xabarning iqtibosini ko‘radi (ular xabarning o‘zini ham ko‘radi) — oddiy userlarga fallback.

## 6. Deploy (alohida tasdiqdan keyin)

1. Backup → `alembic upgrade head` (`e9b4c2f7a3d1 → f3a8c1d5e7b2 → a6d2f9c4e8b1`; ikkinchisi A2 Audio Manager, `docs/audit/a2-implementation-report.md`).
2. Backend restart, frontend `.next-a`/`.next-b` slot orqali (`docs/deploy-frontend.md`).
3. Rollback: oldingi frontend slot. DB: odatda kerak emas (ustun additive, eski frontend uni e’tiborsiz qoldiradi). Kerak bo‘lsa `alembic downgrade e9b4c2f7a3d1` — reply ustuni olib tashlanadi, xabarlar qoladi; **diqqat:** bu undan keyingi `a6d2f9c4e8b1` (A2 Audio Manager jadvali) ni ham olib tashlaydi.
