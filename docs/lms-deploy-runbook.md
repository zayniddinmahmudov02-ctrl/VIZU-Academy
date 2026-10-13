# VIZU LMS (A1–C1) — deploy, tozalash va rollback qo'llanmasi

Server: `/opt/vizu/VIZU-Academy`, servislar `vizu-backend` va `vizu-frontend`, domen `https://vizu-deutsch.com`.

Har bir bosqich alohida tasdiq bilan bajariladi. **Production ma'lumotlarini o'zgartiradigan bosqichlar 4, 6 va 8.**

## 0. Oldindan
- Branch `lms-final` ko'rib chiqiladi, keyin `main` ga merge va push qilinadi. Serverda `git pull --ff-only` faqat shundan keyin bajariladi.
- `frontend/scripts/deploy-frontend.sh` ishlashi uchun bir martalik systemd sozlamasi kerak (`docs/deploy-frontend.md`). U qilinmagan bo'lsa, 7-bosqichdagi muqobil buyruqlar ishlatiladi.

## 1. Holatni tekshirish (faqat o'qiydi)
```bash
cd /opt/vizu/VIZU-Academy
git status --short          # bo'sh bo'lishi shart
git fetch && git log --oneline HEAD..origin/main
cd backend && .venv/bin/python -m alembic current
```
`alembic current` shuni ko'rsatadi: serverda qaysi migrationlar hali qo'llanmagan. Ehtimol b3e8d1c5a7f2, c4f9a2e7b1d3, d7a3c9e1f5b2, e8b1f4c2a9d6, f3d9b2e7c4a1.

## 2. Backup (majburiy, exit 0 bo'lishi shart)
```bash
cd /opt/vizu/VIZU-Academy/backend
RESTORE_CHECK=1 bash scripts/backup-course-content.sh
```
Natija: `/var/backups/vizu/course-reset-<vaqt>/`. Ichida `db.dump`, `files.tar` (`app/protected_storage` + `uploads`), `SHA256SUMS` va qator sonlari bo'ladi. Oxirida `OK: backup complete and verified` chiqmasa, deployni boshlamang.

## 3. Kod
```bash
cd /opt/vizu/VIZU-Academy && git pull --ff-only
```

## 4. Backend: migration va qayta ishga tushirish
```bash
cd /opt/vizu/VIZU-Academy/backend
.venv/bin/python -m alembic upgrade head      # additive, har birida downgrade bor
sudo systemctl restart vizu-backend
curl -s http://127.0.0.1:8000/api/v1/health    # port: systemctl cat vizu-backend
journalctl -u vizu-backend -n 50 --no-pager
```
`e8b1f4c2a9d6` migrationi darslarda takroriy raqam topsa, unique indeksni yaratmaydi va NOTICE chiqaradi. Bu holda takroriy raqamlarni admin muharriri orqali tuzatish kerak.

## 5. Frontend (build tugagach restart)
```bash
cd /opt/vizu/VIZU-Academy
HEALTH_URL=http://127.0.0.1:<PORT>/login bash frontend/scripts/deploy-frontend.sh
```
Slot sozlamasi hali qilinmagan bo'lsa (uzilish taxminan 1–2 daqiqa):
```bash
sudo systemctl stop vizu-frontend && cd frontend && npm ci && npm run build && sudo systemctl start vizu-frontend
```

## 6. LMS tuzilmasi (production ma'lumoti — tasdiq bilan)
```bash
cd /opt/vizu/VIZU-Academy/backend && .venv/bin/python -m app.scripts.ensure_lms_structure
```
Bu yetishmayotgan darslarni **draft** holatida yaratadi: talabalar ularni ko'rmaydi. Mavjud darslar o'chirilmaydi va qayta raqamlanmaydi.

## 7. Tekshiruv
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://vizu-deutsch.com/api/v1/health                      # 200
curl -s -o /dev/null -w "%{http_code}\n" https://vizu-deutsch.com/api/v1/lms/levels                  # 401 (auth kerak)
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" https://vizu-deutsch.com/courses              # 307 -> /kurse
curl -s -o /dev/null -w "%{http_code}\n" https://vizu-deutsch.com/kurse                              # 200
```
Brauzerda:
- talaba: `/kurse` → daraja → dars → kompetenz;
- admin: `/admin/kurse`, keyin "Dateien prüfen".

## 8. Eski kontentni tozalash (alohida tasdiq bilan)
```bash
cd /opt/vizu/VIZU-Academy/backend
.venv/bin/python -m app.scripts.course_content_audit --json /root/course-audit.json     # umumiy inventarizatsiya
.venv/bin/python -m app.scripts.legacy_content_cleanup --json /root/legacy-plan.json     # DRY RUN + PLAN CODE
```
Reja ko'rib chiqilgach, faqat tasdiqlangan kategoriyalar bilan:
```bash
.venv/bin/python -m app.scripts.legacy_content_cleanup --categories <tasdiqlangan> --execute \
  --confirm <PLAN CODE> --archive-dir /var/backups/vizu/legacy-$(date +%F) --i-have-a-verified-backup
```
- O'quvchi tarixi bor yozuvlar `--include-student-history` berilmasa o'chirilmaydi.
- Ma'lumot reja tuzilgandan keyin o'zgargan bo'lsa, PLAN CODE mos kelmaydi va skript hech narsa qilmaydi.

## Rollback
| Nima | Qanday |
|---|---|
| Frontend (slot) | `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && sudo systemctl restart vizu-frontend` |
| Faqat navigatsiya (`/kurse` → eski `/courses`) | O'tish commitini `git revert` qilish, frontendni qayta build qilish. Eski player kodi repoda saqlangan |
| Backend kodi | `git checkout <oldingi commit>`, keyin `sudo systemctl restart vizu-backend` |
| Migrationlar | `alembic downgrade d7a3c9e1f5b2`. Bu LMS jadvallarini (kompetenz matnlari, resurslar, kompetenz progressi) o'chiradi. Ma'lumot kiritilgan bo'lsa, buning o'rniga backupdan tiklang |
| Baza | servislarni to'xtatish → `pg_restore --clean --if-exists --no-owner -d <db> db.dump` → servislarni ishga tushirish |
| Fayllar | `backend/` ichida `tar -xf files.tar` |
| Tozalash | `--archive-dir` dagi JSONL va fayllar yoki to'liq baza backupi |
