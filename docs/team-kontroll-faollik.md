# Team, Kontroll va faollik statistikasi (overlay 22, 2026-11-23)

Kod: `backend/app/services/teacher/{team,panel}.py`, `backend/app/services/activity/{tracker,stats}.py`, migration `c8d3f5a1e7b2`.
Batafsil qoidalar shu fayllarning docstring'larida. Bu hujjat — qisqa qo'llanma.

## 1. Admin → Team

- **Lehrer hinzufügen:** to'liq ism, username (3–50: a–z 0–9 _ . -), e-mail ixtiyoriy, vaqtinchalik parol (avtomatik, 14 belgi yoki o'zi
  yozadi, kamida 10 belgi, harf + raqam), savol **„Darf dieser Lehrer auf den Bereich „Kontroll“ zugreifen?“** — standart **Nein**.
- Parol faqat bir marta ko'rsatiladi, bazada faqat hash. O'qituvchi birinchi kirishda o'z parolini o'rnatmaguncha Teacher Panel API 403
  `PASSWORD_CHANGE_REQUIRED` qaytaradi.
- O'qituvchi username bilan kiradi (faqat TEACHER hisoblari uchun; talabalar e-mail / telefon bilan kiradi).
- Profil oynasida: ism / login / e-mail, Kontroll ha / yo'q, aktiv / nofaol (darhol sessiyalar tugaydi), parolni tiklash, guruh va kurs
  biriktirish. "Guruhni olib tashlash" guruhni amalni bajarayotgan Super Adminga o'tkazadi (guruhda har doim bitta o'qituvchi bo'ladi).
- Har bir o'zgarish `audit_logs` (`team_*`) ga yoziladi; "Änderungsverlauf" shu yerdan o'qiladi. Hamma endpointlar faqat SUPER_ADMIN uchun.

## 2. Teacher Panel

12 bo'lim: Dashboard, Schüler, Gruppen, Kurse, Unterricht, Aufgaben, Hausaufgaben, Prüfungen, Materialien, Nachrichten, Kontroll (faqat
ruxsat bilan), Einstellungen. Yangi o'qituvchida hammasi bo'sh holat matni bilan ochiladi, sozlash shart emas.

Doira: o'qituvchining guruhlari (`study_groups.teacher_id`) + unga biriktirilgan kurslar. Doiradan tashqaridagi o'quvchi = 404.
Schüler profilida faqat o'qish ma'lumotlari bor (progress, uy vazifalari, imtihonlar); foydalanish vaqti va media faqat Kontroll'da.

## 3. Kontroll

- Barcha ro'yxatdan o'tgan o'quvchilar (test domenlari bundan mustasno, `student_stats` qoidasi), qidiruv, saralash, sahifalash.
- Batafsil: umumiy vaqt / bugun / 7 kun / shu oy, faol kunlar, oxirgi kirish, kurslar (masalan A1 — 12/14 dars — 86%), musiqa, lug'at, kitoblar,
  filmlar, kunlik xronologiya.
- Faqat GET endpointlar (o'chirish / tahrirlash / ko'chirish / o'quvchi nomidan kirish yo'q). Har bir batafsil ko'rish `kontroll_student_viewed`
  audit yozuvini qoldiradi.

## 4. Vaqt qanday o'lchanadi

- Brauzer har ~30 soniyada heartbeat yuboradi, faqat foydalanuvchi faol bo'lsa (sahifa ko'rinib turibdi va so'nggi 2 daqiqada harakat bo'lgan)
  yoki qo'shiq / film o'ynayotgan bo'lsa.
- Vaqtni server o'z soati bo'yicha hisoblaydi. Bitta heartbeat uchun ko'pi bilan 45 soniya; birinchi heartbeat va 150 soniyadan uzun
  tanaffusdan keyingisi 0. Barcha tablar bitta sessiyada — ikki marta hisoblanmaydi. Kun Toshkent vaqti bo'yicha.
- Musiqa / film: pleyer pozitsiyasi siljishi kerak (pauza = 0), kontent nashr qilingan va ruxsat bo'lishi kerak. Kitob: o'quvchi ochiq turgan va
  foydalanuvchi faol vaqt. Ochilgan kitob ≠ o'qilgan kitob (sahifa / "tugatilgan" alohida ko'rsatiladi).
- Faqat STUDENT hisoblari kuzatiladi. Lernserie (`learning_activity`) va dars progressi bu ma'lumotdan foydalanmaydi.
- Vaqt hisobi deploy qilingan kundan boshlanadi. Ijrolar soni (`media_play_history`) va ochilgan kitoblar avvalgi davrdan ham ko'rinadi.
- Shaffoflik: talabaning Medien sahifasida "Was wird gemessen?" izohi bor (nima o'lchanadi, kim ko'radi).

## 5. Bibliothek kategoriyalari

Migration oltita kategoriyani shu tartibda qo'yadi: Literatur, Historisch, Beruflich, Sonstige, Prüfungsvorbereitung, Wortschatz.
Eski Lektüren / Zertifikatsbücher / Grammatik nofaol bo'ladi (o'chirilmaydi). Kitoblarni mazmuni bo'yicha joylash skripti:

    python -m app.scripts.medien_library_categories plan
    python -m app.scripts.medien_library_categories apply --confirm <plan id> --backup-dir /var/backups/vizu/<dir>

Har bir kitob sababi bilan `ASSIGNMENTS` da (sarlavha bo'yicha). Faqat `media_books.category_id` o'zgaradi; ID, fayl, progress va xaridlar joyida qoladi.

## 6. Rollback

- Kod: overlay zaxirasidagi asl fayllar (`docs-originals.tar` / overlay tar) bilan qaytariladi.
- DB: `alembic downgrade b7e4c2a9d6f1` faqat qo'lda va zaxiradan keyin: yangi jadvallar va ustun o'chadi (faollik ma'lumoti yo'qoladi),
  kategoriyalar eski nomiga qaytadi, Historisch / Beruflich nofaol bo'ladi. Production'da avtomatik downgrade qilinmaydi.
