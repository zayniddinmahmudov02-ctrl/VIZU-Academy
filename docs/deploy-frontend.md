# Frontend deploy (vizu-frontend)

## Nega oddiy `npm run build` xavfli

`next build` o'z output papkasini tozalab, qaytadan yozadi. `vizu-frontend` shu `.next` papkadan ishlab turgan paytda build qilinsa, build tugaguncha server yarim tayyor papkadan xizmat qiladi. Logdagi quyidagi xatolar shundan:

- `Invariant: The client reference manifest for route "/admin/…" does not exist`
- `Failed to load static file for page: /500 … ENOENT`
- `ENOENT … .next/BUILD_ID`, `required-server-files.json`, `middleware-manifest.json`

Bu holat lokalda qayta chiqarildi: ishlab turgan server ustida in-place build vaqtida 73 ta route'dan 14 tasi HTTP 500 qaytardi.

## Yechim: ikki build slot

`scripts/deploy-frontend.sh` ketma-ket quyidagilarni qiladi:

1. Jonli bo'lmagan slotga build qiladi (`.next-a` yoki `.next-b`). Jonli slot shu paytda xizmat qilishda davom etadi.
2. Build to'liqligini tekshiradi: `BUILD_ID`, manifestlar, `pages/500.html`, `/admin/lessons|levels|modules` va lesson sahifasining client reference manifestlari.
3. `.deploy/active.env` faylini yangi slotga yo'naltiradi va servisni bir marta restart qiladi.
4. Health-check qiladi. Muvaffaqiyatsiz bo'lsa, oldingi slotga qaytaradi.

Slot nomi server bundle ichiga kompilyatsiya qilinadi (`distDir`). Shuning uchun papkani keyin qayta nomlab bo'lmaydi: servis aynan build qilingan `NEXT_DIST_DIR` bilan ishga tushishi shart.

Har bir build `NEXT_DEPLOYMENT_ID` oladi (git sha + vaqt). Bu Next.js'ning version skew himoyasini yoqadi: eski tab yangi deployga client-side navigatsiya qilsa, Next.js mismatch'ni sezadi va sahifani to'liq qayta yuklaydi.

## Bir martalik sozlash (serverda)

1. Hozirgi unitni ko'ring. `WorkingDirectory=/opt/vizu/VIZU-Academy/frontend` va `ExecStart` `next start` (yoki `npm run start`) bo'lishi kerak:

   ```bash
   systemctl cat vizu-frontend
   ```

   Agar `ExecStart` `server.js` (standalone) ishlatsa, to'xtang: bu sozlama u holat uchun emas.

2. Drop-in qo'shing. Mavjud unit fayli o'zgarmaydi:

   ```bash
   sudo mkdir -p /etc/systemd/system/vizu-frontend.service.d
   printf '[Service]\nEnvironmentFile=-/opt/vizu/VIZU-Academy/frontend/.deploy/active.env\n' \
     | sudo tee /etc/systemd/system/vizu-frontend.service.d/deploy-slot.conf
   sudo systemctl daemon-reload
   ```

   `-` prefiksi tufayli `active.env` hali yo'q bo'lsa ham servis odatdagidek `.next` bilan ishlaydi.

3. Health URL uchun portni aniqlang:

   ```bash
   sudo ss -ltnp | grep -E 'node|next'
   ```

## Har bir deploy

Fayl egasi bo'lgan foydalanuvchi bilan bajaring (`sudo` faqat `systemctl` uchun ishlatiladi):

```bash
cd /opt/vizu/VIZU-Academy
git pull
HEALTH_URL=http://127.0.0.1:<PORT>/login bash frontend/scripts/deploy-frontend.sh
```

- `package-lock.json` o'zgargan bo'lsa, `--install` qo'shing. U jonli `node_modules` ni qayta yozadi, shuning uchun restartgacha xatolar bo'lishi mumkin.
- Script `.env` fayllarga tegmaydi. `NEXT_PUBLIC_API_URL` avvalgidek `frontend/.env*` dan olinadi.

### Qo'lda rollback

```bash
cd /opt/vizu/VIZU-Academy/frontend
cat .deploy/active.env.prev                 # oldingi slot
cp .deploy/active.env.prev .deploy/active.env
sudo systemctl restart vizu-frontend
```

## Tekshiruvlar

- **Bitta frontend jarayoni:**

  ```bash
  pgrep -af 'next-server|next start'
  sudo ss -ltnp | grep node
  ```

  Bitta servis = bitta `next-server` bo'lishi kerak. Qo'lda ishga tushirilgan ortiqcha `next start` ham eski build'dan xizmat qilishi mumkin.

- **Faol slot:**

  ```bash
  cat frontend/.deploy/active.env
  curl -s http://127.0.0.1:<PORT>/login | grep -o 'data-dpl-id="[^"]*"'
  ```

- **`/opt/vizu/package-lock.json`:** Next.js shu fayl sabab `/opt/vizu` ni workspace root deb tanlagan. `next.config.ts` endi rootni `frontend/` ga qat'iy belgilaydi, shuning uchun bu fayl build'ga ta'sir qilmaydi. O'chirishdan oldin nima ekanini tekshiring:

  ```bash
  ls -la /opt/vizu
  head -c 300 /opt/vizu/package-lock.json
  ls /opt/vizu/node_modules 2>/dev/null | head
  ```

  Yonida `package.json` yoki `node_modules` bo'lmasa, odatda bu tasodifan `/opt/vizu` da bajarilgan `npm install` qoldig'i.

- **`Failed to find Server Action "x"`:** ilovada Server Action yo'q. Bu xabar soxta `Next-Action` header yuborgan tashqi so'rovlardan keladi (skanerlar). Next.js ularni 404 bilan rad etadi. Lokalda aynan shu so'rov bilan qayta chiqarildi.

- **Backend xatolari:** har bir API javobida `X-Request-ID` bor. 500 javob body'sida `request_id` ham bor. Logdan qidirish:

  ```bash
  journalctl -u vizu-backend | grep 'request_id=<ID>'
  ```
