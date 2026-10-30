# A2 nashr hisoboti (1–13-darslar)

Sana: 2026-10-30, production.

**Natija:**
- **27 Hören vazifasidan 22 tasi `Veröffentlicht`.**
- 5 tasi `Entwurf` (Needs review): 6-dars — 1, 13-dars — 4.

Kursning boshqa materiallari allaqachon nashr qilingan edi va o‘zgartirilmadi.

## Nashr qoidasi

Vazifa avtomatik nashr qilinadi, agar **hammasi** bajarilgan bo‘lsa:
1. audio fayl serverda bor va ijro etiladi;
2. transkript bor;
3. audio vazifaga mos (MATCHED, SHA-256 tekshirilgan fayl);
4. savollar bo‘lsa — hamma kalit LMS → Lösung’da VERIFIED (mavjud Hören qoidasi, `hoeren_pdf_import.readiness`);
5. savolsiz Text vazifasi (4-dars) — audio A2 kutubxonasida tekshirilgan.

Biror shart bajarilmasa, vazifa nashr qilinmaydi, qolganlari esa to‘xtamaydi. Hech narsa nashrdan olinmadi, o‘quvchi urinishlari va ballariga tegilmadi.

## Vazifalar

| U. | Vazifa | Holat | Sabab |
|---|---|---|---|
| 1 | Hören: Warum haben Sie Ihren Beruf gewählt? | **Veröffentlicht** | audio + kitob transkripti + 12/12 kalit |
| 2 | Hören: Sendung „Gemeinschaftskreis“ | **Veröffentlicht** | 12/12 |
| 3 | Hören: Die Empfehlungen eines Arztes | **Veröffentlicht** | 8/8 |
| 4 | Hören: Text 1 | **Veröffentlicht** | audio (kutubxonaga qabul qilindi, avtomatik tekshirildi) + transkript, savolsiz |
| 4 | Hören: Text 2 | **Veröffentlicht** | shunday |
| 4 | Hören: Text 3 | **Veröffentlicht** | shunday |
| 5 | Hören: Steigende Mieten in Deutschland! | **Veröffentlicht** | 8/8 (Q4 tuzatildi, 2 ortiqcha savol olib tashlandi) |
| 6 | Hören: Konflikte zwischen Lukas und Jonas / Paul und Leon | Entwurf — **Needs review** | 12 ochiq savol „Prüfung nötig“ |
| 7 | Hören Test: Reisen (Max und Sara) | **Veröffentlicht** | 15/15, ikki audio (Text 1, Text 2) |
| 8 | Hören: Einkauf von Susanna und Einkauf von Johann | **Veröffentlicht** | 12/12 |
| 9 | Hören: Aufgabe zum Hören — Medien zuordnen | **Veröffentlicht** | Zuordnung 1/1 |
| 10 | Teil 1 · Teil 2 · Teil 3 · Teil 4 | **Veröffentlicht** (4) | 5/5 har biri |
| 11 | Teil 1 · Teil 2 · Teil 3 · Teil 4 | **Veröffentlicht** (4) | 5/5 har biri |
| 12 | Teil 1 · Teil 2 · Teil 3 · Teil 4 | **Veröffentlicht** (4) | 5/5 har biri |
| 13 | Teil 1 · Teil 2 · Teil 3 · Teil 4 | Entwurf — **Needs review** (4) | audio = 12-dars fayli (MISMATCH), kalit yo‘q |

## A2 darslari 1–13

Kursning o‘zi:
- „Elementary“ aktiv, tavsifi bor;
- darslar 1–13 nashr qilingan, tartib 1→13;
- 14 („Wiederholung“) ataylab nashrsiz;
- kompetensiyalar (Einführung, Wortschatz, Grammatik, Lesen, Hören, Sprechen, Schreiben, Zusammenfassung) har darsda ochiq.

Joriy nashrdagi Lesen / Schreiben / Sprechen / Grammatik-mashqlarining hammasi nashr qilingan, kalitlari to‘liq. Qoralama qolganlari faqat `[Archiv]` (1-nashr) nusxalari — ataylab yopiq.

| U. | Hören | O‘quvchi ko‘radi | Izoh |
|---|---|---|---|
| 1 | 1/1 | Hören + test + transkript (urinishdan keyin) | 1-dars bepul preview |
| 2–3 | 1/1 | ✓ | |
| 4 | 3/3 | Text 1–3, transkript darhol | savollar yo‘q (pastda) |
| 5 | 1/1 | ✓ | |
| 6 | 0/1 | Hören bo‘limi „hali kontent yo‘q“ | Needs review |
| 7 | 1/1 | ✓, 2 player | |
| 8–9 | 1/1 | ✓ | |
| 10–12 | 4/4 | ✓ | |
| 13 | 0/4 | Hören bo‘limi „hali kontent yo‘q“ | to‘g‘ri audio kerak |

**Bo‘sh kompetensiya qoidasi.** Nashr qilingan kontenti yo‘q kompetensiya dars yakunlanishiga hisoblanmaydi (mavjud qoida). Shuning uchun 6 va 13-dars o‘quvchi uchun bloklanmaydi.

**Savolsiz Hören vazifasi** (4-dars Text 1–3) Hören natijasiga ham hisoblanmaydi (`results._hoeren`).

## Tayyorlik indikatori (Admin → Media Management → A2)

Holat: **`NEEDS_CONTENT`**.

| Tekshiruv | Holat |
|---|---|
| Yangi `hoeren_published` | ochiq. 6-dars va 13-darsning 4 vazifasi sabablari bilan ro‘yxatda |
| `price`, `lessons`, `description`, `manifest`, `audio_complete`, `audio_verified`, `links` | OK |
| `payment_tested`, `access_tested`, `responsive_tested`, `tests_passed` | qo‘lda tasdiqlanadi (SUPER_ADMIN) |

**A2 sotuvi** production’da avvaldan yoqilgan (SUPER_ADMIN, 2026-10-28). Men o‘zgartirmadim.

## Media Management’da ko‘rinadigan holatlar

„A2 Audio-Verarbeitung · 1.–13. Unterricht“ paneli:
- **holat nishonlari:** Uploaded · Transcribing · Transcribed · Matched · Answer key verified · Published · Needs review · Failed;
- **umumiy progress:** 22/27 = 81 %;
- **har bir dars bo‘yicha:** n/m veröffentlicht;
- **har bir vazifa ichida:** audio fayl(lar), transkript (vaqt belgilari bilan), moslashtirish natijasi, savollar va variantlar (to‘g‘ri javob ✓), Lösung holati va izohi, nashr holati, xatoliklar.
