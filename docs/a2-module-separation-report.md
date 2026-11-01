# A2: Wortschatz, Lesen va Schreiben modullarini ajratish — hisobot

Sana: 2026-11-01 · Commit: `7749ea4` · Migratsiya: `d7e2b4f8a1c6` · Ma'lumot qadami: `python -m app.scripts.a2_module_separation`

## 1. Topilgan muammo (audit)

A2 kitob nashridagi 40 ta `writings` yozuvining hammasi Schreiben sahifasida ko'rinardi va Schreiben progressiga
hisoblanardi. Ularning 15 tasi aslida boshqa modulga tegishli edi:

| Modul | Soni | Yozuvlar (`content_id` `vizu-a2buch-…`) |
|---|---|---|
| Grammatik (yozma mashq) | 5 | `l02/l03/l04/l08/l09-schreiben-02` |
| Wortschatz (ish varag'i) | 9 | `l05`…`l13-schreiben-04` |
| Lesen (5-dars matni bo'yicha 5 ta ochiq savol) | 1 | `l05-schreiben-05` |
| Schreiben (haqiqiy yozma ish) | 25 | qolganlari |

Sababi: `writings` jadvalida topshiriq qaysi kompetensiyaga tegishli ekanini bildiruvchi maydon yo'q edi.
`results._schreiben`, `GET /writings/lesson/{id}` va eski `section_gate` / `lesson_scoring` darsdagi barcha yozma
topshiriqlarni Schreiben deb hisoblardi. Qo'shimcha holat:

- A2 Wortschatz'da nashr qilingan test yo'q edi. 40 ta WORTSCHATZ to'plami birinchi nashrdan qolgan arxiv bo'lib, nashr qilinmagan.
- Wortschatz bo'limi faqat ochilgani uchun "bajarildi" bo'lardi.

Production'da bu 15 topshiriqqa birorta ham o'quvchi javobi yo'q edi (0 submission, 0 baholash), shuning uchun ko'chirishda
hech kimning ishi yo'qolmadi.

## 2. Modullar strukturasi (natija)

- **Grammatik:** qoidalar, avtomatik mashqlar va **Grammatik-Aufgaben (yozma)**. Yozma mashqlar o'z rubrikasi bilan baholanadi.
- **Wortschatz:**
  - **Wörterbuch** — darsdagi so'zlar;
  - **Übungen** — so'z kartochkalari, kitob mashqlari va Wortschatz-Aufgaben;
  - **Tests** — 7 turdagi avtomatik testlar.
- **Lesen:** matnlar, avtomatik test va **Fragen zum Text** (ochiq savollar). AI javoblarni dars matni bilan solishtirib tekshiradi.
- **Hören:** o'zgarmadi.
- **Schreiben:** faqat Schreiben topshiriqlari: matn yozish, topshirish, tahlil, baho va topshirilgan ishlar tarixi.

Qoida: `writings.competency` = NULL/SCHREIBEN · GRAMMATIK · WORTSCHATZ · LESEN. Har bir sahifa, progress, ball va AI
rubrikasi shu maydonga qarab ishlaydi. Schreiben ichida Lesen yoki Wortschatz topshirig'i chiqmaydi. Schreiben tahlilidagi
"Wortschatz" mezoni esa mustaqil Wortschatz topshirig'i hisoblanmaydi.

## 3. Wortschatz

### 3.1. Lug'at

- Darsdagi so'zlar: L1 — 60, L2 — 40, L3 — 60, L4 — 50, L9 — 6, jami **216**.
  - L5–8 va L10–13 kitob sahifalarida tarjimali so'z ro'yxati yo'q, faqat ish varag'i bor. Shuning uchun lug'at yozuvi yaratilmadi.
- Kitobdagi so'z, artikl va tarjima hech qachon o'zgartirilmaydi.
- Bo'sh maydonlar faqat **status = verified** bo'lgan va artikl + lemma'si bir xil Wörterbuch yozuvidan to'ldiriladi. Bular:
  - Wortart;
  - Plural;
  - Präteritum, Partizip II, Hilfsverb;
  - Beispielsatz va Übersetzung.
- Har bir to'ldirilgan maydonning manbasi `vocabularies.data_sources` da saqlanadi (masalan `woerterbuch:A2-12`).
- Kitobda der/die/das bilan berilgan so'z → `Nomen` (`book:article`).
- **130 / 216** so'z Wörterbuch'da topildi. **86** tasi topilmadi. Ularning yetishmayotgan maydonlari "Fehlt" deb belgilanadi
  va admin to'ldiradi. Hech narsa taxmin qilinmagan.
- L9 dagi 6 so'zning "tarjimasi" kitobda o'zbekcha emas, nemischa izoh. Shu holicha qoldirildi.
- Talaffuz: brauzerning nemischa ovozi (TTS) ishlatiladi. Admin `audio_url` kiritsa, o'sha fayl ijro etiladi. Audio fayl yaratilmagan.

O'quvchi uchun:

- nemischa va o'zbekcha qidiruv (ä/ae, apostrof variantlari, artiklsiz yozish ham ishlaydi);
- "Shu dars / Barcha mavzular" — faqat o'quvchiga ochiq darslar;
- mavzu (dars) va so'z turkumi bo'yicha filtr;
- **saqlash** va **o'rganildi** belgilari serverda, har bir o'quvchi uchun alohida saqlanadi (`vocabulary_user_words`);
- mobil ekranda gorizontal skroll yo'q (E2E Pixel 7 da tekshirildi).

### 3.2. Testlar

`wortschatz_tests.py` testlarni faqat saqlangan ma'lumotlardan tuzadi. Har bir tur alohida to'plam: WORTSCHATZ `skill_exercises`,
manba `vizu`, `content_id` `vizu-a2buch-lNN-wortschatz-test-<tur>`. Turlar:

1. **Bedeutung** — nemischa so'z → ma'nosi.
2. **Übersetzung** — ma'no → nemischa so'z.
3. **Artikel** — der/die/das.
4. **Plural** — ko'plik shaklini yozish.
5. **Verbformen** — Präteritum, Hilfsverb (hat/ist), Partizip II.
6. **Lückentext** — misol gapdagi bo'sh joyga so'zni yozish (gap tarjimasi yordamchi sifatida beriladi).
7. **Kontext** — misol gapga mos so'zni 3 variantdan tanlash.

Qoidalar:

- Javob kalitlari faqat serverda saqlanadi, test o'quvchiga kalitsiz yuboriladi.
- Ball serverda hisoblanadi va progressga yoziladi (Wortschatz kompetensiyasi).
- Bitta to'plamda bir so'z ham, bir xil savol ham takrorlanmaydi.
  - 1–2 hamda 6–7 turlar so'zlarni o'zaro bo'lishadi, shuning uchun bitta misol gap ikki marta so'ralmaydi.
- Bir xil tarjimali so'zlar 1–2 turlarda so'ralmaydi.
- Faqat ko'plikda beriladigan so'zlar (die Medien) Artikel va Plural testlarida so'ralmaydi.
- Kerakli ma'lumoti yo'q so'z o'sha tur testiga kiritilmaydi.
- Admin testlarni "Wortschatz-Übungen und -Tests" bo'limida tahrirlaydi.

Soni (production apply):

| Dars | To'plam | Savol |
|---|---|---|
| 1 | 7 | 103 |
| 2 | 7 | 81 |
| 3 | 7 | 99 |
| 4 | 7 | 94 |
| 9 | 4 (Bedeutung, Übersetzung, Artikel, Plural) | 14 |
| **Jami** | **32** | **391** |

Lug'at maydonlari (191 so'z o'zgardi):

- Wortart — 191;
- Plural — 71;
- misol gap va uning tarjimasi — 130;
- Präteritum, Partizip II, Hilfsverb — 42.

### 3.3. Admin

- So'z formasida Wortart, Präteritum, Partizip II, Hilfsverb va Audio-URL maydonlari bor. "Fehlt" ustunida yetishmayotgan maydonlar ko'rinadi, "nur unvollständige" filtri ham bor.
- **CSV eksport** UTF-8 BOM bilan chiqadi. Formula bilan boshlanadigan kataklar zararsizlantiriladi.
- **CSV import:**
  - avval preview, keyin "Import ausführen";
  - har bir qator muharrir validatsiyasidan o'tadi; birorta qatorda xato bo'lsa, hech narsa yozilmaydi;
  - hech narsa o'chirilmaydi;
  - faqat `.csv` fayl, ≤ 1 MB;
  - faqat content editor rollari;
  - har bir import audit log'ga yoziladi.

## 4. Schreiben — tahlil va baholash

### 4.1. A2 tahlil mezonlari (100 ball)

| Mezon | Ball |
|---|---|
| Aufgabenbewältigung — topshiriqni bajarish | 20 |
| Grammatik — grammatik to'g'rilik | 15 |
| Wortschatz — so'z boyligi va qo'llash | 15 |
| Satzbau — gap tuzilishi | 15 |
| Rechtschreibung — imlo | 10 |
| Kohärenz — matn izchilligi | 15 |
| Textstruktur — matn tuzilishi | 10 |

Har bir mezon bo'yicha quyidagilar ko'rsatiladi: ball, izoh, shu mezonga tegishli xatolar (xato → to'g'ri variant + izoh) va
yaxshilash tavsiyasi. Yakunida:

- umumiy ball;
- kuchli tomonlar va kamchiliklar;
- tuzatilgan namuna — "AI yozgan, sizning matningiz emas" deb belgilangan;
- keyingi mashq uchun tavsiya.

A2 talablari promptda aniq yozilgan: B1/B2/C1 talablari qo'llanmaydi.

### 4.2. Ishonchlilik

- **Ball** serverda, mezon ballari yig'indisidan hisoblanadi; AI bergan umumiy ball ishlatilmaydi.
- **Xatolar:** faqat o'quvchi matnida so'zma-so'z bor xatolar saqlanadi.
- **Matn nusxalari:** har bir yakuniy topshirishdagi matn aynan `student_writing_versions` da saqlanadi va keyingi variant uni o'chirmaydi.
- **Baholash tarixi:** har bir AI baholashi (muvaffaqiyatli yoki xato bilan tugagani) va har bir o'qituvchi/admin qarori `ai_evaluations` da qoladi. Har biri qaysi variantga tegishli ekani `attempt_number` da yoziladi. Qayta tahlil oldingi natijani o'chirmaydi.
- **AI ishlamasa:** holat `EVALUATION_FAILED` bo'ladi, ball qo'yilmaydi, o'quvchiga "qayta baholash" tugmasi chiqadi.
  - Soxta tahlil yaratilmaydi.
  - Provayder xatosi o'quvchiga ko'rsatilmaydi, faqat `AI_UNAVAILABLE`.
- **O'qituvchi/admin:** natijani tasdiqlaydi yoki tuzatadi (Teacher Panel → Schreiben, Admin → Schülerergebnisse).
  - O'quvchida "Avtomatik tahlil" yoki "O'qituvchi tasdiqlagan" belgisi chiqadi.
  - O'qituvchi sahifasida modul belgisi va AI tahlili ko'rinadi.
- **Tarix:** o'quvchi "Topshirilgan ishlar tarixi" bo'limida variantlarni, ballarni va sanalarni ko'radi. Faqat o'z ishlarini.

Boshqa modullarning yozma topshiriqlari Schreiben mezonlari bilan baholanmaydi:

- **Wortschatz:** ma'no va tarjima / gapda qo'llash / shakl.
- **Grammatik:** mavzudagi struktura / umumiy to'g'rilik / imlo.
- **Lesen:** matnni tushunish / javob aniqligi. Promptga dars matni qo'shiladi.

## 5. Lesen

Lesen mustaqil: matnlar, savollar, javob variantlari, serverdagi kalitlar va avtomatik ball. Natijalar va progress o'zgarmadi.
5-darsning 5 ta ochiq savoli endi Lesen sahifasida "Matn bo'yicha savollar" sifatida chiqadi va Lesen natijasiga qo'shiladi.
Schreiben sahifasida Lesen matni ham, savoli ham chiqmaydi. Admin'da LMS → Lesen paneli: matnlar va savollar (avvalgidek),
pastda "Fragen zum Text".

## 6. Database o'zgarishlari (migratsiya `d7e2b4f8a1c6`, faqat qo'shimcha)

- `writings.competency` (NULL = Schreiben), CHECK `ck_writings_competency`.
- `vocabularies`: `word_type`, `verb_praeteritum`, `verb_partizip_ii`, `verb_auxiliary`, `dictionary_entry_id` (SET NULL), `data_sources`.
- Yangi jadval `vocabulary_user_words` (saved / learned).
- Yangi jadval `student_writing_versions`.
- `ai_evaluations.attempt_number`.

Downgrade faqat shu ustun va jadvallarni o'chiradi. Lokal test bazada upgrade → downgrade → upgrade sinovdan o'tgan.

Ma'lumot qadami (`a2_module_separation plan` → `apply --confirm <plan id>`):

- avval zaxira (`backup.json`), keyin 3 ta audit log yozuvi;
- 15 topshiriqqa kompetensiya beriladi;
- 40 kitob topshirig'ining rubrikasi NULL qilinadi, ya'ni daraja yoki kompetensiyaning standart rubrikasi ishlaydi;
- so'zlar Wörterbuch'dan to'ldiriladi va testlar yaratiladi;
- takror ishga tushirilsa, hech narsa o'zgarmaydi.

Kitob manbasi (`vizu_deutsch_a2_buch.WRITING_COMPETENCY`) ham yangilangan, shuning uchun qayta import ham to'g'ri natija beradi.

**Progressga ta'siri:** production'da A2 darsini to'liq tugatgan o'quvchi yo'q edi (0). 6 ta o'quvchida L1/L2 Wortschatz
faqat ochilgani uchun "bajarildi" turgan edi. Endi haqiqiy testlar bor, shuning uchun bu bo'lim ularda testlar ishlanmaguncha
"boshlanmagan" ko'rinadi. Hech qanday javob, urinish yoki ball o'chirilmagan.

## 7. Xavfsizlik

- Yangi student endpointlar `require_lesson_access` orqali o'tadi.
- So'z holatini faqat o'quvchining o'zi yozadi va so'z joylashgan dars unga ochiq bo'lishi shart. Pullik dars so'zlari
  "Barcha mavzular" ro'yxatiga chiqmaydi.
- History endpoint faqat o'quvchining o'z topshirig'ini ko'rsatadi (`get_current_user`).
- Admin: `/writings` create/update/delete endi `require_content_editor` (avval admin panelga kira oladigan har qanday rol,
  SUPPORT ham yoza olardi). So'z yozish va CSV import ham `require_content_editor` orqali o'tadi.
- O'quvchiga o'qituvchining id'si emas, faqat `teacher_reviewed` bayrog'i yuboriladi.

## 8. Testlar

| Tekshiruv | Natija |
|---|---|
| Backend (lokal, to'liq) | **949 passed, 17 skipped** (avval 917 / 17; yangi `test_a2_module_separation` 32 ta) |
| Migratsiya testi (upgrade → downgrade → upgrade) | o'tdi |
| Frontend `tsc --noEmit`, `eslint` (o'zgargan fayllar) | xatosiz |
| Frontend unit | 23 / 23 (yangi `wortschatz-filter` 4 ta) |
| `next build` (`.next-e2e`) | muvaffaqiyatli |
| E2E `a2-module-separation.spec.ts` (desktop + Pixel 7) | **11 passed**, 1 skipped (admin testi faqat desktop'da) |
| E2E: student-panel, admin, auth, a2-audio-processing, global-chat-reply | o'tdi |
| E2E `a2-audio-manager` | 1 ta yiqildi — bu kod o'zgarishi sababli emas. Spec seed'dagi "E2E Hören Lektion 1" vazifasini kutadi, lokal baza esa avvalgi A2 mashqidan beri haqiqiy kitob nashrini saqlaydi. Audio Manager kodi o'zgarmagan |

Testlar quyidagilarni qamraydi:

- lug'atning ko'rinishi, qidiruv va filtr;
- CSV import: preview, apply va "hammasi yoki hech narsa" qoidasi;
- test savollarining tuzilishi, kalitlar, takrorlanmaslik, server tomonida ball hisoblash va kalitning sizib chiqmasligi;
- progress;
- Schreiben: AI xatosi bo'lganda ball qo'yilmasligi, 7 mezon, har bir mezonga bog'langan xatolar, o'qituvchi bahosi va tarix;
- Lesen ochiq savollarini matn bo'yicha tekshirish;
- modullarning ajratilishi: Schreiben'da Lesen yoki Wortschatz topshirig'i yo'qligi, Lesen va Grammatik sahifalari;
- 401 / 403 / 422 va IDOR tekshiruvlari.

## 9. Production

**Revision:** `7749ea4` (server: `git pull --ff-only` from `91a5e70`) · **Alembic:** `c4f7a9e2d6b3` → `d7e2b4f8a1c6` · **Frontend:** slot `.next-a`, deployment `7749ea4-20261031214051`.

| Bosqich | Natija |
|---|---|
| Pre-check | SUCCESS. Upstream fayllarda serverda lokal o'zgarish yo'q; revision kutilgandek; servislar `active`; diskda 221 GB bo'sh joy |
| Backup | SUCCESS. `/var/backups/vizu/pre-a2modsep-20261031-213415`: `pg_dump` + scratch DB'ga to'liq tiklash, **135 jadval, 0 farq**; `lesson-listening.tar` (50 fayl); `SHA256SUMS` OK. Xato bilan ikkinchi nusxa ham olindi: `…-213514` |
| Kod | SUCCESS. `git pull --ff-only`; `requirements.txt` o'zgarmagan, paket o'rnatilmadi |
| Server testlari | SUCCESS. `unittest` 109 OK (15 skipped: DB va httpx testlari serverda o'tkazib yuboriladi) |
| Migratsiya | SUCCESS. Avval SQL preview tekshirildi (faqat ADD COLUMN, CREATE TABLE/INDEX, CHECK, FK), keyin `alembic upgrade head` |
| Backend | SUCCESS. Restart qilindi, health 11 soniyada 200 qaytardi, yangi xato yo'q |
| Ma'lumot qadami | SUCCESS. Plan `fe38129864b9` → apply: 15 topshiriq ko'chirildi, 191 so'z to'ldirildi, 32 test yaratildi. Takroriy plan bo'sh chiqdi; 3 ta audit yozuvi bor; zaxira va hisobot `…-213415/a2-module-separation-20261031-204014-fe38129864b9/` papkasida |
| Frontend | SUCCESS. `deploy-frontend.sh` orqali `.next-b` → `.next-a` almashtirildi. Rollback uchun `.next-b` saqlangan |
| Smoke | SUCCESS (batafsil quyida) |

Smoke tekshiruvi natijalari:

- `/`, `/login`, `/kurse`, `/kurse/A2`, `/woerterbuch`, `/admin/lms` → 200.
- Yangi API'lar tizimga kirmagan foydalanuvchiga 401 qaytaradi: `wortschatz/words`, `writings/lesson?competency`, `submissions/me/history`, `words.csv`.
- Natijalar faqat o'z modulida hisoblanadi:
  - L2: Schreiben'da 2 topshiriq, Grammatik yozma mashqi Grammatik'da;
  - L5: Schreiben'da 2 topshiriq, Wortschatz 1, Lesen 1;
  - L7: Schreiben'da 2 topshiriq, Wortschatz 1.
- Boshqa darajalardagi `vocabularies` / `writings` yozuvlarining birortasi o'zgarmagan.
- Yangi UI matnlari `.next-a` ichida bor.
- Backend log'larida xato yo'q (faqat ma'lum `SUPER_ADMIN_VERIFICATION` xabari).
- Frontend log'ida 3 ta `Failed to find Server Action "x"` bor. Bu tashqi so'rovlar: xuddi shu xabar deploy'dan oldin, eski jarayonda ham bor edi.
- `nano_bot` va `telegram-cours2026` ishlab turibdi; ularga tegilmagan.

Production'da test foydalanuvchi, token, to'lov yoki audio yaratilmadi.

Rollback (kerak bo'lsa):

- frontend: `cp frontend/.deploy/active.env.prev frontend/.deploy/active.env && systemctl restart vizu-frontend`;
- ma'lumot qadami: `backup.json` ichidagi qatorlar (faqat so'rov bo'yicha);
- migratsiya avtomatik downgrade qilinmaydi.

### 9.1. Qo'shimcha deploy (2026-11-01): grammatika to'ldirildi, admin huquqlari tuzatildi

- **Grammatika.** Egasining qarori: "Grammatikani to'ldir". Wörterbuch'da yo'q **89** ta so'z yozuvining grammatikasi standart nemis grammatikasi (Duden shakllari) bo'yicha to'ldirildi: Plural 64, Wortart 25, Präteritum / Partizip II / Hilfsverb 12. Manba `vizu-grammatik` deb yozilgan.
  - Ma'lumotlar `app/scripts/a2_wortschatz_grammar_data.py` faylida, qo'llash `python -m app.scripts.a2_wortschatz_grammar` (plan → apply, zaxira, audit).
  - Faqat bo'sh maydonlar to'ldirildi; kitob qiymati yoki admin kiritgan qiymat o'zgarmadi.
  - Ko'pligi yo'q otlar uchun "–" yozildi. Faqat ko'plikda ishlatiladigan shakllar (die Kopfschmerzen) o'z shaklida qoldi.
  - Misol gaplar yozilmadi.
- **Admin huquqlari.** `/admin/lesson-skills` dagi 17 ta kontent yozish endpointi endi `require_content_editor` talab qiladi: savollar, Hören audio, nusxalash, mashqlar, grammatika, natija sozlamasi. Ball tuzatish va qayta baholash avvalgidek qoldi. 403 testi qo'shildi.

## 10. Qolgan kamchiliklar

1. Misol gap (Beispielsatz + tarjima) Wörterbuch'da yo'q so'zlar uchun hali kiritilmagan. Ular kerak bo'lsa, admin yozadi yoki alohida topshiriq bo'ladi. Grammatika to'ldirilgan (9.1).
2. Kontekst testlarida chalg'ituvchi variantlar shu darsning boshqa so'zlaridan olinadi. Gap tarjimasi yordamchi bo'lgani uchun javob bir ma'noli, lekin ba'zi variantlar grammatik jihatdan o'z-o'zidan mos kelmaydi. Admin tahrirlashi mumkin.
3. L5–8 va L10–13 darslarida tarjimali so'z ro'yxati yo'q (kitobda ham yo'q), shuning uchun ularda Wortschatz testi ham yo'q. Bu darslarda faqat ish varag'i (yozma topshiriq) bor.
4. Wortschatz testlari birinchi apply paytidagi ma'lumotlardan tuzilgan. Yangi to'ldirilgan Plural va fe'l shakllari mavjud testlarga avtomatik qo'shilmaydi: o'quvchilar urinishlari bo'lgan to'plamlar o'zgartirilmaydi. Lug'atda ular ko'rinadi.
5. Talaffuz uchun audio fayllar yo'q: faqat brauzer TTS ishlaydi, sifati qurilmaga bog'liq.
6. Haqiqiy o'quvchi akkaunti bilan production'da yozma ish topshirilmadi va AI tahlili ishga tushirilmadi (test ma'lumoti yaratmaslik qoidasi). AI qismi lokal sinovlarda mock bilan tekshirilgan.
