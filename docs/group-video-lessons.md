# Guruh video darslari (LiveKit SFU) — arxitektura, ishlatish, holat

Sana: 2026-11-21 · Holat: **production'da o‘rnatilgan** (overlay 19). Haqiqiy qurilmalarda real qo‘ng‘iroq hali sinalmagan (pastda §9).

## 1. Eski urinish (olib tashlandi)

- Eski "Group Video Chat" kodi production'ga hech qachon chiqmagan; production DB `a6c2e8f4b9d1` da edi (`c1v7d3e9a5b2` qo‘llanmagan).
- O‘chirildi: `services/study_groups/video_chat.py`, migratsiya `c1v7d3e9a5b2_group_video_chat.py`, `tests/test_study_group_video_chat_migration.py`,
  `features/groups/components/group-video-chat.tsx`. Umumiy fayllar (guruh router, model, `groups.py`, config, `test_study_groups.py`, admin `groups/page.tsx`,
  guruh ko‘rinishlari, `groups-service.ts`, i18n) production nusxasiga qaytarildi — boshqa guruh funksiyalari o‘zgarmagan.
- Lokal test bazalar `a6c2e8f4b9d1` ga tushirildi; eski jadvallar (`study_group_video_*`) faqat lokal edi.
- **Diqqat:** egasining 2026-11-21 dagi push'lari (`60592fa5`, `3f6db0f3`) eski kodni `origin/main` ga olib chiqqan. Keyingi push lokal holatni
  (eski fayllar o‘chirilgan, yangi `b7e4c2a9d6f1`) yuborishi kerak; ungacha serverda `git pull` qilinmasin (ikki alembic head bo‘ladi).

## 2. Arxitektura

```text
brauzer ──HTTPS──> Cloudflare ──> nginx ──> /api/v1/... (FastAPI: ruxsat, token, moderatsiya)
brauzer ──WSS───> Cloudflare ──> nginx /livekit/ ──> 127.0.0.1:7880 (LiveKit signaling)
brauzer ──UDP 7882 / TCP 7881 / TURN UDP 3478──> 217.76.62.208 (media to‘g‘ridan-to‘g‘ri, Cloudflare'siz)
LiveKit ──webhook (imzoli)──> http://127.0.0.1:8000/api/v1/video-rooms/webhooks/livekit
```

- Media backend orqali o‘tmaydi; chat LiveKit data channel'da (yuboruvchini SFU belgilaydi, saqlanmaydi).
- Backend: `app/api/video_rooms/router.py`, `app/services/video_rooms/{permissions,service,moderation,livekit_service}.py`, model `app/models/video_room.py`.
- Frontend: `features/video-rooms/` (service, utils, komponentlar), sahifa `app/(meeting)/video-room/[roomId]`, admin `app/admin/video-rooms`.

## 3. Ruxsatlar va xavfsizlik (hammasi backend'da)

| Qoida | Qayerda |
|---|---|
| Ko‘rish / qo‘shilish: guruh o‘qituvchisi, SUPER_ADMIN, guruhning **faol** a’zolari; boshqalarga 404 `VIDEO_ROOM_NOT_FOUND` | `permissions.view_room` (guruh `require_view` ustida) |
| Boshqa guruh id'si bilan kirib bo‘lmaydi: room id faqat o‘z guruhida ochiladi | `view_room`, testlar |
| Moderatsiya faqat shu guruh host'i; a’zo talaba 403 `VIDEO_MODERATOR_REQUIRED`, begona 404 | `permissions.moderate_room` |
| Admin monitoring faqat SUPER_ADMIN (guruhlar admin siyosati bilan bir xil) | `require_super_admin` |
| Room nomini backend yaratadi (`vizu-<uuid>`); so‘rovlarda `extra="forbid"` | `service.create`, router |
| Token: identity = user id, faqat bitta room, 300 s (`VIDEO_ROOM_TOKEN_TTL_SECONDS`), `canUpdateOwnMetadata=false`, `roomAdmin` yo‘q | `livekit_service.join_token` |
| Token qayta ishlatish cheklovi: bir identity = bitta ulanish; olib tashlangan/bloklangan, guruhdan chiqqan yoki room tugagan bo‘lsa webhook uni LiveKit'dan chiqaradi; join rate limit | `moderation.webhook` |
| Rate limit (user / IP): join 12/5 min (IP 150/5 min), create 30/soat, moderatsiya 120/min, qo‘l 20/min | `service.LIMITS` |
| LiveKit secret faqat backend `.env` va `/etc/livekit/livekit.yaml` (640 root:livekit) da; frontendga, logga, hujjatga chiqmaydi. Join javobi `no-store`; nginx `/livekit/` access log yozmaydi | config, nginx |
| Webhook faqat LiveKit imzosi bilan (body sha256 JWT ichida), aks holda 401 | `livekit_service.verify_webhook` |

Ruxsatlar (mikrofon, ekran, chat) LiveKit publish permission sifatida qo‘llanadi va har yangi token shu saqlangan holatdan yasaladi.

## 4. Jadvallar (migratsiya `b7e4c2a9d6f1`, down `a6c2e8f4b9d1`, faqat qo‘shimcha)

| Jadval | Mazmuni |
|---|---|
| `video_rooms` | guruh FK (CASCADE), created_by / ended_by (SET NULL), `room_name` unique, title, description, status scheduled/live/ended/cancelled (CHECK), vaqtlar, end_reason, max_participants (talaba o‘rinlari), xona bo‘yicha chat / ekran / mikrofon. Partial unique: guruhda bitta `live` |
| `video_room_participants` | (room, user) unique, rol host/student, ulanish holati, kirish/chiqish, mic / ekran / chat ruxsati, qo‘l, removed / blocked |
| `video_room_events` | hodisalar jurnali (`metadata` JSONB); token va chat matni yozilmaydi |

Downgrade faqat shu uch jadvalni o‘chiradi. Test: `tests/test_video_rooms_migration.py`.

## 5. API (`/api/v1`, `get_current_user`; webhook bundan mustasno)

- Guruh: `POST|GET /groups/{gid}/video-rooms`, `GET /groups/{gid}/video-rooms/active`.
- Room: `GET|PATCH /video-rooms/{id}`, `POST /video-rooms/{id}/{start,cancel,end,join,leave,connection,raise-hand}`, `GET /video-rooms/{id}/participants`.
- Moderatsiya: `POST /video-rooms/{id}/{mute-participant,mute-all,mic-permission,screen-share-permission,chat-permission,remove-participant}`.
- Admin: `GET /admin/video-rooms`, `POST /admin/video-rooms/{id}/end` (SUPER_ADMIN).
- Webhook: `POST /video-rooms/webhooks/livekit` (public, imzo bilan).

## 6. Production LiveKit

| Narsa | Qiymat |
|---|---|
| Binary | `/usr/local/bin/livekit-server` v1.13.11 (GitHub release, sha256 tekshirilgan) |
| Config | `/etc/livekit/livekit.yaml` (kalitlar shu yerda; ko‘rsatilmaydi) |
| Servis | `livekit.service` (user `livekit`, `Restart=always`, `MemoryMax=1200M`, `CPUQuota=150%`, systemd hardening), boot'da yoqiladi |
| Portlar | 7880 signaling faqat 127.0.0.1; ICE/TCP 7881; ICE/UDP 7882 (bitta port); TURN/UDP 3478; TURN relay UDP 30000–40000 |
| nginx | `location /livekit/` → `127.0.0.1:7880` (WebSocket upgrade, `access_log off`, error log faqat `crit`) |
| Backend `.env` nomlari | `LIVEKIT_URL` (= `wss://vizu-deutsch.com/livekit`), `LIVEKIT_API_URL` (= `http://127.0.0.1:7880`), `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`; ixtiyoriy `VIDEO_ROOM_TOKEN_TTL_SECONDS` (300), `VIDEO_ROOM_MAX_PARTICIPANTS` (25) |
| Room sozlamasi | `auto_create: false`, bo‘sh room 10 min, oxirgi odam chiqqach 5 min (keyin webhook darsni `empty` bilan yakunlaydi); jonli dars 6 soatdan keyin `expired` |
| Firewall | serverda host firewall yo‘q (UFW inactive); provayder tarafidagi filtr yo‘q ekani tashqaridan tekshirildi (TCP 7881, UDP 3478) |

Ishlatish: `systemctl status livekit`, `journalctl -u livekit`, health `curl http://127.0.0.1:7880/` → `OK`, tashqaridan `https://vizu-deutsch.com/livekit/` → `OK`.
Admin: `/admin/video-rooms` (LiveKit holati, live / rejalashtirilgan / oxirgi darslar, majburan yakunlash).

**Rollback (tartibda):** frontend `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && systemctl restart vizu-frontend`;
LiveKit `systemctl disable --now livekit`; nginx — backup'dagi `nginx-vizu-deutsch.com` ni qaytarib `nginx -t && systemctl reload nginx`;
backend fayllari `overlay-originals.tar` dan + yangi fayllarni o‘chirish + restart; `.env` — backup'dagi `backend.env`. Migratsiya avtomatik qaytarilmaydi
(jadvallar qo‘shimcha, eski kod ularga tegmaydi). Backup: `/var/backups/vizu/pre-video-rooms-20261121-113114`.

## 7. TURN/TLS va `meet` domeni — BLOCKED (egasi qiladi)

UDP butunlay yopiq va faqat 443/TCP ochiq tarmoqlar (ba’zi korporativ / mehmonxona Wi-Fi) uchun TURN/TLS kerak. Buning uchun:

1. Cloudflare'da **proxy'siz (DNS only, kulrang bulut)** A yozuv: masalan `turn.vizu-deutsch.com → 217.76.62.208`. Hozir bunday yozuv yo‘q.
2. Shu nom uchun sertifikat (`certbot certonly --standalone` yoki DNS challenge) va LiveKit `turn.domain`, `turn.tls_port: 5349`, `cert_file` / `key_file`.
3. Port 5349/TCP (yoki 443 uchun alohida IP / L4 proxy). Keyin `systemctl restart livekit`.
`meet.vizu-deutsch.com` kerak emas: signaling `vizu-deutsch.com/livekit` orqali ishlaydi.

## 8. Testlar (lokal, 2026-11-21)

- Backend: `test_video_rooms.py` (24 test: kontrakt, token, webhook imzosi, rollar, boshqa guruh, moderatsiya → token, remove/block, qo‘l, sig‘im,
  rate limit, webhook sinxroni, yakunlash, admin, eskirish), migratsiya testi, `test_route_protection` (webhook allowlist). To‘liq backend: 1251 OK, 18 skip.
- Frontend: `tsc`, `eslint`, `tests/unit/video-rooms.test.mjs` (10), jami unit 86 OK.
- E2E: `e2e/tests/video-rooms.spec.ts` — **haqiqiy lokal LiveKit server** (v1.13.11, `D:\vz_tmp\livekit`) va Chrome fake kamera/mikrofon bilan, desktop + Pixel 7:
  o‘qituvchi va talaba bir-birini ko‘radi (video kadrlar), eshitadi (qabul qilingan audio signal darajasi), mic/kamera, o‘qituvchi mute + talabaga xabar,
  chat va chatni o‘chirish, qo‘l ko‘tarish/tushirish, ekran ulashish, chiqish, qayta kirish, darsni yakunlash, begona 404, telefon kengligida gorizontal scroll yo‘q. 4/4 OK.
- Seed: `D:\vz_tmp\work\video_e2e_seed.py` (faqat `vizu_gcr_e2e`).

## 9. Holat

| Narsa | Holat |
|---|---|
| Backend + migratsiya + frontend production'da | DONE |
| LiveKit servis, nginx WSS, `.env`, webhook (imzoli 200, imzosiz 401) | DONE |
| Tashqaridan: `/livekit/` OK, WS tokensiz 401, TCP 7881 ochiq, 7880 yopiq, STUN/TURN UDP 3478 javob beradi | DONE |
| TURN/TLS (443/5349) va alohida domen | BLOCKED (§7) |
| UDP 7882 orqali real media production'da | NOT TESTED (token kerak; production'da test foydalanuvchi/token yaratilmaydi) |
| Haqiqiy qurilmalar (Android, iPhone Safari, turli brauzerlar), UDP bloklangan tarmoq, TURN fallback | NOT TESTED — egasi haqiqiy o‘qituvchi + talaba akkaunti bilan sinaydi |
| Android ilova (Capacitor): manifest'da CAMERA / RECORD_AUDIO bor, yangi APK kerak emas | real telefonda NOT TESTED |
