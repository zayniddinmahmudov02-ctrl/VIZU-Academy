# A2 kitobi (VIZU-Deutsch A2) va arxivlangan LMS kursi — audit

Sana: 2026-10-22. Server: 217.76.62.208, baza `vizu`. Backup: `/var/backups/vizu/a2-reset-20261022-185358/`.

## Manba
- Fayl: `VIZU-Deutsch A2.pdf`, 183 sahifa, 42 839 296 bayt.
- SHA-256: `84c0c491927da7a96722b5e7459a5e1bcbe8fa7dcba8467968609297e845096d` (lokal va serverda bir xil).
- Serverdagi nusxa: `/opt/vizu/a2-book/VIZU-Deutsch-A2.pdf` (repository'dan tashqarida, commit qilinmagan).
- Sahifalar skan-rasm (matn qatlami yo'q). Tekshiruv sahifa rasmlari bo'yicha qo'lda (kontakt varaqlar, past o'lchamda) bajarildi.

## Metod va chegaralari (halollik uchun)
- **Tekshirilgan:** dars sahifa oralig'i, bo'lim tuzilmasi (Grammatik / Lesen / Hören / Schreiben / Sprechen / Wortschatz), Teil/Aufgabe sarlavhalari va soni, Hören savollar soni, track raqamlari, javob kaliti mavjudligi (DB).
- **Tekshirilmagan:** har bir savol matni va javob varianti so'zma-so'z. Shuning uchun "Bestätigt" faqat *tuzilma va son* bo'yicha tasdiqlanganini bildiradi, matn bo'yicha emas.
- Kitobdagi bo'sh checkbox va javob chiziqlari javob kaliti hisoblanmagan. Kitobda yechimlar sahifasi ko'rilmadi.

## Darslar (kitob ↔ LMS)

| # | Kitob nomi | Sahifalar | LMS nomi | Holat |
|---|---|---|---|---|
| 1 | Beruf, Karriere und Ziele | 3–18 | mos | Bestätigt |
| 2 | Digitaler Alltag und soziale Medien | 19–30 | mos | Bestätigt |
| 3 | Bleiben Sie gesund und fit | 31–40 | mos | Bestätigt |
| 4 | Tagesablauf und Zeitmanagement | 41–52 | mos | Bestätigt |
| 5 | Wohnen und Lebensraum | 53–62 | mos | Bestätigt |
| 6 | Beziehungen und Kommunikation | 63–72 | mos | Bestätigt |
| 7 | Reisen im Alltag und Mobilität | 73–83 | mos | Bestätigt |
| 8 | Konsum, Werbung und Produkte | 84–93 | mos | Bestätigt |
| 9 | Medien, Nachrichten und Meinung | 94–103 | mos | Bestätigt |
| 10 | Lernen und Weiterbildung | 104–124 | mos | Bestätigt |
| 11 | Umwelt und Verantwortung | 125–146 | mos | Bestätigt |
| 12 | Kultur, Tradition und Gesellschaft | 147–163 | mos | Bestätigt |
| 13 | Geld, Finanzen und Alltag | 164–183 | mos | Bestätigt |
| 14 | **Wiederholung** | — (mundarijada bor, kitobda sahifasi YO'Q) | `Zukunft, Träume und Lebensplanung` | **Abweichung** |

14-dars: LMS'dagi nom kitobdan emas va uning butun kontenti (1 Schreiben, 2 Sprechen, 1 Grammatik, 4 mashq, 1 video) kitobda yo'q. Nomi `Wiederholung` ga tuzatilishi kerak, kontenti arxivda qoladi.

## Bo'limlar (LMS arxivi ↔ kitob)

| Dars | Lesen | Hören (savol) | Schreiben | Sprechen | Wortschatz |
|---|---|---|---|---|---|
| 1 | 3 matn ✓ (DB 35 savol, kitobda ko'ringan 18) → **Prüfung nötig** | 12 ✓ | 1 ✓ | 2 ✓ | 60 ✓ |
| 2 | 3 ✓ | 12 ✓ | 2 + Grammatik-Aufgabe ✓ | 2 ✓ | 40 ✓ |
| 3 | 2 ✓ | 8 ✓ | 2 + Grammatik-Aufgabe ✓ | 2 ✓ | 60 ✓ |
| 4 | 3 ✓ | 12 ✓ | 2 + Grammatik-Aufgabe ✓ | 2 ✓ | 50 ✓ |
| 5 | 1 ✓ | 10 ✓ | 2 + Wortschatz-Aufgabe ✓ | 2 ✓ | DB 50, kitobda 30 → **Abweichung** |
| 6 | 2 ✓ | 12 ✓ | 2 + Wortschatz-Aufgabe ✓ | 2 ✓ | DB 60, kitobda 30 → **Abweichung** |
| 7 | 1 ✓ | **DB 15, kitobda 16 → Abweichung** | 2 + Wortschatz-Aufgabe ✓ | 2 ✓ | DB 50, kitobda 30 → **Abweichung** |
| 8 | 1 ✓ | 12 ✓ | 2 + Grammatik + Wortschatz ✓ | 2 ✓ | DB 11, kitobda 5×6 variant → Prüfung nötig |
| 9 | 1 ✓ | 1 (A–F tartiblash, 6 element) → Prüfung nötig | 2 + Grammatik + Wortschatz ✓ | 2 ✓ | DB 6, kitobda 5×6 variant → Prüfung nötig |
| 10 | Teil 1–4 ✓ | Teil 1–4 ✓ (5+5+5+5) | Teil 1–2 ✓ | Frage + Teil 1–2 ✓ | kitobda 5×6 variant (DB 0) |
| 11 | Teil 1–4 ✓ | Teil 1–4 ✓ | Teil 1–2 ✓ | Frage + Teil 1–3 ✓ | kitobda 5×6 variant (DB 0) |
| 12 | Teil 1–4 ✓ | Teil 1–4 ✓ | Teil 1–2 ✓ | Frage + Teil 1–3 ✓ | kitobda 5×6 variant (DB 0) |
| 13 | Teil 1–4 ✓ | Teil 1–4 ✓ | Teil 1–2 ✓ | Frage + Teil 1–3 ✓ | kitobda 5×6 variant (DB 0) |

Qo'shimcha:
- Arxivdagi `learning_resources` (10–13-darslar, "Buch, S. 117/118, 138/139, 156/157, 176/177") sahifa havolalari PDF bilan **mos keladi** (Hören Teil 2 / Teil 3 rasmlari).
- Kitobda yo'q, LMS qo'shgan mashqlar: `Abschlusstest`, `Zuordnung`, `Der, die oder das?`, `Nemischa qanday?`, `Was bedeutet das?` va shunga o'xshash test-mashqlar (98 ta skill_exercise'ning katta qismi). Ular kitobdan emas → **Prüfung nötig** (o'quvchi ball tizimi shularga tayanishi mumkin).
- Grammatik mashqlari (zu+Infinitiv 1–60, weil/da, Präpositionen 25/30, Relativpronomen 24/25 va h.k.) kitobning grammatika mashqlariga mos (p44–45, p56, p77, p150), lekin savollarning so'zma-so'z mosligi tekshirilmagan.
- 1-darsda ikkita Hören yozuvi bor: haqiqiy ("Warum haben Sie Ihren Beruf gewählt", 12 savol) va eski `a2-l01-audio-01` ("A2 1.Unterricht Hören", 0 savol). Ikkinchisi dublikat/qoldiq → arxivda qoladi.

## Audio treklar va media slotlar (kitobdan)
- 12-dars: Hören Teil 1 = Track 27–31 (p155), Teil 2 = Track 32 (p156), Teil 3 = Track 33–37 (p157), Teil 4 = Track 38–39 (p158). Siz bergan 33–37 va 38–39 **tasdiqlandi**.
- 13-dars: Teil 1 = Track 40–44 (p175), Teil 2 = Track 45 (p176), Teil 3 = Track 46–50 (p177), Teil 4 = Track 51–52 (p178). **Tasdiqlandi.**
- 10-dars: Teil 3 va Teil 4 sahifalarida (p118, p119) ikkalasida ham `Track 7–11` yozilgan (kitobda xato bo'lishi mumkin); Teil 1–2 va 11-darsda trek raqami ko'rinmadi → **Prüfung nötig**.
- 1–9-darslarda trek raqami yo'q; har darsda bitta Hören-Aufgabe (1-dars: 12 savol, 6-dars: 2×6, 8-dars: 2×6, 9-dars: tartiblash).
- Media slot = mavjud Hören-Aufgabe yozuvi (1–9: 1 tadan; 10–13: 4 tadan = Teil 1–4). Jami 9 (1–9-darslar) + 16 (10–13-darslar) = **25** slot (26 ta yozuvdan 1-darsdagi dublikat chiqarilganda). Hozir hammasi audio faylsiz (yuklanmagan).
- Video: har darsda 1 ta video yozuvi (kitobda "Nemis tili video-darslar" sahifalari bor: A2 4-dars… 13-dars).

## Javob kalitlari (DB, serverda o'qilgan)
| Dars | Lesen: savol / kalitsiz | Hören: savol / kalitsiz |
|---|---|---|
| 1 | 35 / 0 | 12 / 0 |
| 2 | 24 / 0 | 12 / 0 |
| 3 | 12 / 0 | 8 / 0 |
| 4 | 18 / 0 | 12 / **12** |
| 5 | 16 / 0 | 10 / **1** |
| 6 | 23 / 0 | 12 / **12** |
| 7 | 12 / 0 | 15 / **15** |
| 8 | 10 / 0 | 12 / 0 |
| 9 | 8 / 0 | 1 / 0 |
| 10 | 16 / 0 | 20 / **20** |
| 11 | 15 / 0 | 20 / **20** |
| 12 | 14 / 0 | 20 / **20** |
| 13 | 16 / 0 | 20 / **20** |

- Kitobda javob kaliti yo'q; DB'dagi Lesen kalitlari ilgari admin/audit orqali kiritilgan (manba kitob emas). Kitob bilan solishtirilmagan → har qanday kalit "kitobdan tasdiqlangan" deb ko'rsatilmaydi.
- Hören kalitlari 4, 6, 7, 10–13-darslarda (va 5-darsda 1 ta) **yo'q** → bu vazifalar kalit kiritilmaguncha nashr qilinmasligi kerak (tizim qoidasi shunday). Audio ham hali yo'q.

## Dry-run: arxivni tiklash rejasi (HALI BAJARILMAGAN)
Asl nashr holati (backup'dan): 14 dars, 14 video, 33 Lesen, 3 Hören (23 tasi qoralama edi), 40 Schreiben, 35 Sprechen, 18 Grammatik, 98 mashq, 387 so'z, 8 resurs, 140 kompetensiya — hammasi nashr qilingan edi (Hören'dan tashqari).
Tiklash (bitta tranzaksiya, ID'lar o'zgarmaydi, yangi yozuv yaratilmaydi):
1. `[Archiv] ` prefiksini olib tashlash va `is_published` ni backup'dagi asl qiymatga qaytarish — faqat 1–13-darslar uchun.
2. 14-dars: nomini `Wiederholung` ga o'zgartirish; kontenti arxivda va nashrsiz qoladi.
3. 1-dars dublikat Hören (`a2-l01-audio-01`) arxivda qoladi.
4. Kalitsiz Hören vazifalari nashrsiz qoladi (23 ta qoralama o'zgarmaydi).
5. Kitobda yo'q LMS mashqlari (Abschlusstest, Zuordnung, ...) — qaror kerak (pastda).
6. A2 sotuvi yopiq qoladi (`sales.A2 = false`), progress/buyurtmalar tegilmaydi.
7. Baza va fayllar boshqa darajalarga tegmaydi.
Qaytarish: backup dump'idan yoki yana arxivlash SQL'i bilan.
