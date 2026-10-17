# Production serverga xavfsiz SSH ulanish (Windows → SSH → server → loyiha)

Server: `217.76.62.208` (Ubuntu 24.04) · loyiha: `/opt/vizu/VIZU-Academy` · servislar: `vizu-backend`, `vizu-frontend`.

Tamoyillar:
- Faqat SSH kalit bilan kirish. Parol kodda ham, terminal tarixida ham bo'lmaydi.
- Private kalit faqat Windows'dagi `~/.ssh` papkasida turadi, repoga hech qachon tushmaydi.
- Kalitni serverga faqat server egasi o'z sessiyasida o'rnatadi. Skript o'zi o'ziga ruxsat bera olmaydi, "bir martalik kod" degan narsa ham yo'q.
- Birinchi ulanishda faqat diagnostika bajariladi: hech narsa o'zgarmaydi. Production'dagi har qanday o'zgarish faqat aniq tasdiqdan keyin qilinadi.

| Fayl | Qayerda ishlaydi | Nima qiladi |
|---|---|---|
| `scripts/server_connect.sh` | Windows (Git Bash / Claude Code) | tekshirish, kirishni sinash, diagnostika, shell |
| `scripts/server_setup_on_server.sh` | serverda, siz `sudo` bilan | kalitni o'rnatish, ruxsatlarni tekshirish |
| `scripts/server_diagnose.sh` | serverda (`server_connect.sh diagnose` yuboradi) | faqat o'qiydi, hech narsa yozmaydi |

## 1. Windows: kalit va ssh-agent

Kalit allaqachon bor: `C:\Users\user\.ssh\claude_vizu` (ED25519, parol bilan himoyalangan).
Fingerprint: `SHA256:ccVF8b6YxICXG0MK6Y3L/lPZFTJEUMlZXt4pgPR4WbM`.

Kalit parol bilan himoyalangani uchun, Claude Code uni ishlatishi uchun kalit Windows `ssh-agent`ga yuklanishi kerak. Parolni faqat siz bir marta kiritasiz, Claude uni hech qachon ko'rmaydi.

PowerShell'ni **administrator** sifatida oching (bir martalik):
```powershell
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
```
Keyin oddiy PowerShell'da, o'z foydalanuvchingiz nomidan:
```powershell
ssh-add $env:USERPROFILE\.ssh\claude_vizu     # kalit parolini shu yerda kiritasiz
ssh-add -l                                     # ...ccVF8b6Y... claude-vizu (ED25519) ko'rinishi kerak
```

Tekshirish (Git Bash yoki Claude Code):
```bash
bash scripts/server_connect.sh check
```

## 2. Server: public kalitni o'rnatish (o'zingiz, o'z sessiyangizda)

1. Public kalitni oling. U maxfiy emas, uni yuborish mumkin:
   ```bash
   bash scripts/server_connect.sh pubkey
   ```
2. Serverga hozirgi usulingiz bilan kiring (o'z parolingiz bilan, Claude'siz).
3. Loyihada skript allaqachon bor. Agar `git pull` hali qilinmagan bo'lsa, skript faylini serverga ko'chiring.
4. Kalitni o'rnating:
   ```bash
   cd /opt/vizu/VIZU-Academy
   sudo bash scripts/server_setup_on_server.sh install "ssh-ed25519 AAAA...  claude-vizu"
   ```
   - Bu buyruq kalitni `vizu` foydalanuvchisiga qo'shadi, ruxsatlarni tekshiradi va hisobot chiqaradi.
   - Kalitni faqat sizning IP manzilingizdan ishlaydigan qilish uchun buyruq oldiga `VIZU_KEY_FROM="sizning.ip"` qo'shing.
   - Boshqa foydalanuvchi kerak bo'lsa, `VIZU_USER=...` qo'shing.
5. Hisobotda quyidagilarni tekshiring:
   - `pubkeyauthentication yes`;
   - `~/.ssh` papkasining ruxsati 700, `authorized_keys` faylining ruxsati 600;
   - `vizu` foydalanuvchisi loyiha katalogini o'qiy oladi va unga yoza oladi;
   - qaysi amallar uchun `sudo` kerakligi.
6. Hech qachon sshd sozlamalari skript bilan o'zgartirilmaydi. Parolli kirishni (`PasswordAuthentication no`) kalit bilan kirish ishlagani tasdiqlangandan keyin, o'zingiz yoping.
7. Kirish huquqini qaytarib olish:
   ```bash
   sudo bash scripts/server_setup_on_server.sh remove "claude-vizu"
   ```

## 3. Windows'dan ulanishni tekshirish

```bash
bash scripts/server_connect.sh test       # "connected as vizu on ..." chiqishi kerak
bash scripts/server_connect.sh diagnose   # faqat o'qish: disk, RAM, git, servislar, nginx, alembic, A1 hisoboti
```

Birinchi ulanishda server host kaliti `known_hosts`da bo'lishi kerak. Skript `StrictHostKeyChecking=yes` bilan ishlaydi, ya'ni noma'lum yoki o'zgargan host kalitiga ulanmaydi. `known_hosts`da `217.76.62.208` allaqachon bor. Agar ulanish "host key changed" deb rad etilsa:
1. Serverda `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` natijasini Windows'dagi ogohlantirish bilan solishtiring.
2. Fingerprintlar mos kelsa, eski yozuvni o'chiring: `ssh-keygen -R 217.76.62.208`.

## 4. Claude Code ishlash tartibi

1. **Birinchi ulanish:** faqat `test` va `diagnose` ishlatiladi. Hech qanday fayl o'zgarmaydi, bazaga yozilmaydi, servislar qayta ishga tushirilmaydi.
2. **Reja:** diagnostika natijasidan keyin Claude aniq reja va buyruqlar ro'yxatini beradi: backup, `git pull`, migratsiya, build, restart, A1 import.
3. **Bajarish:** har bir o'zgartiruvchi qadam faqat sizning aniq "ha, bajar" tasdig'ingizdan keyin bajariladi.

## 5. Xavfsizlik ro'yxati

- [ ] Private kalit repoda yo'q. `server_connect.sh check` buni tekshiradi. Hozircha git'da kalit fayllari kuzatilmaydi.
- [ ] `.gitignore`da kalit naqshlari yo'q (kalitlar repodan tashqarida, `~/.ssh`da turadi). Qo'shimcha himoya uchun qo'shishni tavsiya qilaman: `*.pem`, `*.ppk`, `id_rsa*`, `id_ed25519*`, `claude_vizu*`.
- [ ] Windows'da `claude_vizu` faylining ruxsatlari: faqat `user`, `SYSTEM` va `Administrators` (`icacls` bilan tekshirilgan).
- [ ] Serverda `vizu` foydalanuvchisi root emas. `sudo` faqat kerakli buyruqlarga, `visudo` orqali, siz qaror qilib beriladi.
- [ ] Parol chatga, skriptga yoki buyruq qatoriga yozilmaydi.
