# A2 kitobi — sahifama-sahifa kontent auditi (2026-10-26)

Manba: `frontend/books/VIZU-Deutsch A2.pdf` (183 sahifa, SHA-256 `84c0c491…096d`), sahifa rasmlari `D:\vz_tmp\a2\pg\NNN.jpg`.
Taqqoslanadigan kod: `backend/app/scripts/vizu_deutsch_a2/unterricht_NN.py` (oldingi raqamlashtirish, dars PDF'larining matn qatlamidan).
Usul: har bir sahifa rasmi to'liq o'lchamda vizual o'qildi va koddagi yozuv bilan so'zma-so'z solishtirildi.

Belgilar: **OK** = matn va tuzilma mos · **FIX** = tuzatildi (nima) · **NEEDS_REVIEW** = ishonchli aniqlab bo'lmadi · **VIZU** = kitobda yo'q (yangi kursga kiritilmaydi, arxivda qoladi).

Qarorlar (foydalanuvchi, 2026-10-26): kitobda yo'q VIZU mashqlari kiritilmaydi · 14-dars "Wiederholung", bo'sh, nashrsiz · kitobda kaliti yo'q Hören topshiriqlari kalitsiz.

## 1-dars — Beruf, Karriere und Ziele (p.3–18)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 1 | Muqova | — | — | OK (kontent yo'q) |
| 2 | Inhaltsverzeichnis | 14 band, 14 = Wiederholung (sahifasiz) | 14 dars | OK; 14-dars nomi FIX → "Wiederholung" |
| 3 | Dars muqovasi | "Beruf, Karriere und Ziele"; Wortschatz/Hören/Sprechen/Schreiben | EINFUEHRUNG matni (VIZU yozgan) | Einführung matni VIZU → kiritilmaydi |
| 4 | Frage des Themas | 3 savol + 3 javob, iqtibos | 3 savol + 3 javob | OK; iqtibos qo'shiladi (FIX); gapirish vaqti 10–120 s kitobda yo'q → olib tashlanadi (FIX) |
| 5 | Grammatik 1. Präsens | jadval 6 qator + izoh | aynan | OK |
| 6 | Grammatik 2. Präteritum | jadval 6 qator + izoh | aynan | OK |
| 7 | Grammatik 3. Perfekt | jadval 6 qator + izoh | aynan | OK |
| 8 | Grammatik Aufgabe 1 | 6 jumla, qavsda shakl ko'rsatmalari | 6 gap_fill, kalit = ko'rsatmalar | OK; ko'rsatmalar o'quvchiga ko'rinmaydi → FIX (matnga qo'shiladi) |
| 9 | Grammatik Aufgabe 2 | 6 jumla, ko'rsatmalar | 6 gap_fill | OK; ko'rsatmalar FIX; 2-jumla kalit `wohntest` (kitob ko'rsatmasi `wohnte`, du-shakli hisoblangan) |
| 10 | Lesen Aufgabe 1 | Frederich matni, 6 R/F | matn aynan, 6 R/F + | OK |
| 11 | Lesen Aufgabe 2 | Markus matni, 6 R/F | aynan | OK |
| 12 | Lesen Aufgabe 3 | Michael matni, 6 R/F | aynan | OK; kitobda imlo xatosi "verschiedemen" → kodda "verschiedenen" (tuzatilgan holda qoldirildi) |
| 10–12 | Lesen qo'shimcha | — | +17 R/F "dars varag'i"dan (kitobda yo'q) | **VIZU** → chiqariladi; kitobdagi 18 savol qoladi. Kalit: kitobda yo'q, matndan iqtibos bilan hisoblangan (`key_source=text`) |
| 13 | Hören Aufgabe 1 | 12 MC (a/b/c) | 12 MC aynan | OK; kalit manbai "Vizu-Antworten A2" (kitob emas), p.14 transkripti bilan 12/12 mos |
| 14 | Hören Transkription | Johann/Julia/Mikey | transkript | **FIX**: "Architekt ist" (kodda "war"), "mit ihm gezeichnet" (kodda "gearbeitet"); kitobdagi "Krankenkaus" imlo xatosi → "Krankenhaus" |
| 15 | Musik Zeit | qo'shiq matni (Berge, "Glück auf dem Asphalt") | **yo'q** | FIX: sahifa rasmi resurs sifatida (qo'shiq so'zlari qayta terilmaydi — mualliflik huquqi) |
| 16 | Schreiben "Mein Traum Beruf" | 5 qadam + har birida Beispiel + Kompletter Beispieltext | 5 qadam qisqartirilgan, Beispiellar yo'q; 50–150 so'z, 25 daqiqa | **FIX**: qadamlar va Beispiellar to'liq; 4-qadam "Futur I oder Präsens mit Zukunftsbedeutung"; so'z soni/vaqt kitobda yo'q → olib tashlanadi |
| 17 | Sprechen "Ich möchte … werden" | Aufgabe, 4 savol, Tipp, Beispiel | aynan | OK; 30–150 s kitobda yo'q → olib tashlanadi |
| 18 | Wortschatz | 60 so'z | 60 so'z aynan | OK; VIZU guruh nomlari olib tashlanadi; VIZU mashqlari (Zuordnung 1–4, Der/die/das, Was bedeutet das?) chiqariladi |
| — | Übungen / Abschlusstest / Zusammenfassung | kitobda yo'q | Unterrichtsblatt 20 jumla, "Nemischa qanday?", Abschlusstest 12, Zusammenfassung | **VIZU** → chiqariladi |

**1-dars natija:** 16/16 sahifa tekshirildi. Kitob topshiriqlari: Frage 1, Grammatik 2 (12 jumla), Lesen 3 (18 R/F), Hören 1 (12 MC), Schreiben 1, Sprechen 1, Wortschatz 60, resurs 1 (Musik Zeit).

## 2-dars — Digitaler Alltag und soziale Medien (p.19–30)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 19 | Dars muqovasi | "Digitaler Alltag und soziale **Media**" | — | OK; dars nomi mundarijadagi "…Medien" bo'yicha |
| 20 | Frage des Themas | savol + 4 tezis, "Deine Meinung zählt!" | aynan | OK; 10–120 s olib tashlanadi |
| 21 | Grammatik "Die Konditionale Sätze" | Erklärung, Struktur 1–2, Merke, 4 Beispiel | aynan | OK |
| 22 | Grammatik Lückenübung | 20 jumla boshi | 20 jumla, o'qituvchi tekshiradi | OK; 60–300 so'z / 25 daqiqa kitobda yo'q → olib tashlanadi |
| 23 | Lesen Aufgabe 1 (Lukas) | matn + 4 R/F | aynan | OK |
| 24 | Lesen Aufgabe 2 (Anna) | matn + 4 R/F | aynan | OK |
| 25 | Lesen Aufgabe 3 (Thomas) | matn + 4 R/F | aynan | OK; kitobda "hlifreich" → "hilfreich" |
| 23–25 | Lesen qo'shimcha | — | +12 MC "dars varag'i"dan | **VIZU** → chiqariladi; 12 R/F qoladi (kalit matndan) |
| 26 | Hören Aufgabe | 12 savol (a/b/c) | aynan | OK; kalit "Vizu-Antworten A2"; kitobda transkript yo'q |
| 27 | Video Pause | "Meinung der Menschen über Soziale Netzwerke!" | — | video slot (dars videosi) |
| 28 | Schreiben 1 Thema / 2 E-Mail | ca. 30–40 so'z; E-Mail: so'z soni yo'q | 30–60 / 15 daq; E-Mail 30–80 / 20 daq + support_phrases | **FIX**: 30–40; vaqt va E-Mail so'z soni/support_phrases (VIZU) olib tashlanadi |
| 29 | Sprechen Thema | 4 nuqta, ca. 1–2 Minuten, Tipps | 60–150 s | **FIX**: 60–120 s |
| 30 | Wortschatz | 40 so'z | 40 aynan | OK; kitobda "der Nachteile" → "der Nachteil"; VIZU mashqlari chiqariladi |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "Nemischa qanday?", Abschlusstest 10 | **VIZU** → chiqariladi |

**2-dars natija (p.19–30):** 12/12 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 1 yozma mashq (20 jumla), Lesen 3 (12 R/F), Hören 1 (12 MC), Schreiben 2, Sprechen 1, Wortschatz 40, video 1.

## 3-dars — Bleiben Sie gesund und fit (p.31–40)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 31 | Dars muqovasi | "Bleiben Sie Gesund und Fit", Grammatik: Imperativ Sätze | — | OK |
| 32 | Frage des Themas | 3 savol + Beispielantwort | aynan | OK; 20–120 s olib tashlanadi; kitobda "gesundheit" (kichik harf) |
| 33 | Grammatik Imperativ | du/ihr/Sie: Struktur, Regel, Beispiele, Merke | aynan + "Beispiel (Unterrichtsblatt)" | **NEEDS_REVIEW**: kitobda du uchun "Verbstamm + t/Ø" (grammatik jihatdan xato), kodda "e/Ø". **FIX**: "Unterrichtsblatt" misollari (kitobda yo'q) olib tashlanadi |
| 34 | Imperativ – Übung | 10 jumla, du/ihr/Sie, Tipp | 10 jumla + Beispiel + support_phrases | **FIX**: Beispiel qatori va support_phrases (kitobda yo'q), 60–300 so'z / 25 daqiqa olib tashlanadi |
| 35 | Lesen Aufgabe 1 | "Gesund bleiben im Alltag" + A1–A6 | aynan | OK; kitobda "intensiv Sport" → kodda "intensiven" |
| 36 | Lesen Aufgabe 2 | "Was kann man tun, wenn man krank ist?" + A7–A12 | aynan | OK; kalit "Vizu-Antworten A2", matn bilan mos |
| 37 | Hören | 8 R/F (A1–A8) | aynan | OK; kalit "Vizu-Antworten A2"; transkript yo'q |
| 38 | Schreiben 1 Thema / 2 E-Mail | "mindestens 80 Wörter"; E-Mail so'z soni yo'q | 80–160 / 25 daq; E-Mail 40–100 / 20 daq + support_phrases | **FIX**: faqat min 80; qolganlari olib tashlanadi |
| 39 | Sprechen Thema | 4 nuqta | aynan | OK; 45–150 s olib tashlanadi |
| 40 | Wortschatz | 60 so'z | 60 aynan | OK |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "Imperativ: richtige Form", "Nemischa qanday?", Abschlusstest 10 | **VIZU** → chiqariladi |

**3-dars natija:** 10/10 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 1 yozma mashq (10 jumla × 3 shakl), Lesen 2 (12 MC), Hören 1 (8 R/F), Schreiben 2, Sprechen 1, Wortschatz 60.

## 4-dars — Tagesablauf und Zeitmanagement (p.41–52)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 41 | Video-darslar muqovasi | "Nemis Tili Video-darslar A2 4-Dars", 8 rasmli gap boshi | — | video slot (dars videosi) |
| 42 | Frage des Themas | savol, Wortschatz 9, Beispielantwort, kun tartibi jadvali (8 qator) | savol + Wortschatz + Beispiel | **FIX**: jadval qo'shiladi; "Erzählen Sie über Ihren Tagesablauf" (kitobda yo'q) olib tashlanadi; 20–120 s olib tashlanadi |
| 43 | Grammatik "Infinitiv mit zu – Regeln" | 6 qoida + Merksatz | aynan | OK |
| 43 | — | — | "Infinitivgruppe um/ohne/anstatt" qoidasi + 60 zu+Inf + 30 um/ohne/anstatt gap_fill ("Unterrichtsblatt") | **VIZU** → chiqariladi |
| 44 | Aufgabe 1 | 10 juft | 10 juft | OK |
| 45 | Aufgabe 2 | 10 juft, "mit „zu“ + Infinitiv" | 10 juft, "mit „um … zu“" | **FIX**: ko'rsatma kitobdagidek; 80–400 so'z / 30 daq olib tashlanadi |
| 46 | Lesen Aufgabe 1 (Ali) | matn + 1–6 (R/F/nichts dazu) | aynan | OK; kalit matndan |
| 47 | Lesen Aufgabe 2 (Lena) | matn + 7–12 | aynan | OK |
| 48 | Lesen Aufgabe 3 (Martin) | matn + **19–24** | matn aynan, savollar **boshqa** (6 ta, boshqa manba) | **FIX**: kitobdagi 19–24 savollar, kalit matndan: 19 B, 20 C, 21 B, 22 B (**NEEDS_REVIEW**: matnda "manchmal", savolda "oft"), 23 B, 24 A. Kitob raqamlashida 13–18 yo'q |
| 49 | Hören (Familie Mannsberg) | 12 savol, A/B/C | aynan | OK; kitobda kalit va transkript yo'q → kalitsiz (qaror) |
| 50 | Schreiben Thema / E-Mail | 6 + 6 nuqta, so'z soni yo'q | 60–150 / 25; 40–100 / 20 + support_phrases | **FIX**: so'z soni, vaqt, support_phrases olib tashlanadi |
| 51 | Sprechen "Mein Wochenende" | 8 savol | aynan | OK; 60–180 s olib tashlanadi |
| 52 | Wortschatz | 50 so'z | 50 aynan | OK |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "zu oder kein zu?", "Nemischa qanday?", Abschlusstest 10 | **VIZU** → chiqariladi |

**4-dars natija:** 12/12 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 1 yozma mashq (20 juft), Lesen 3 (18 savol, 3 variant), Hören 1 (12, kalitsiz), Schreiben 2, Sprechen 1, Wortschatz 50, video 1.

## 5-dars — Wohnen und Lebensraum (p.53–62)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 53 | Video-darslar muqovasi | "Nemis tili video-darslar A2 5. Unterricht" | — | video slot |
| 54 | Frage des Themas | savol (kitobda "Wo wurden Sie wohnen/"), 3 Beispiel | 3 Beispiel aynan | OK; savol "Wo würden Sie wohnen?"; 20–120 s olib tashlanadi |
| 55 | Grammatik Kausalsätze weil/da | qoidalar, Struktur, 5+5 Beispiel, inglizcha izohlar, Merksatz | aynan, inglizcha izohlarsiz | **FIX**: 2 inglizcha izoh qo'shiladi |
| 56 | Grammatik Aufgabe | 30 juft (1 va 16 namuna) | 28 savol (2–15, 17–30) | OK |
| 57 | Lesen matni + 5 ochiq savol | matn, "Aufgabe" 5 savol | matn aynan; 5 savol faqat metadata'da | **FIX**: 5 ochiq savol topshiriq sifatida (o'qituvchi tekshiradi) |
| 58 | Lesen Aufgabe | 16 MC | 16 MC aynan | OK; kalit matndan; 9-savolda kitob maket xatosi ("Saft nur" 2 marta, 2 ta "B") |
| 59 | Hören "Steigende Mieten" | 10 savol; 10-savolda D) takroriy "2000 Euro" | 10 savol, D olib tashlangan | OK; kalit "Vizu-Antworten A2"; **NEEDS_REVIEW**: 4-savol (Vizu-Antworten B, audio tahlili C), 5-savol (kalit mazmunga mos emas) → draft qoladi |
| 60 | Schreiben Thema / E-Mail | "mindestens 80 Wörter"; E-Mail so'z soni yo'q | 80–160 / 25; 50–120 / 20 | **FIX**: faqat min 80 |
| 61 | Sprechen "Wo würde ich wohnen?" | 7 nuqta, Tipps, "mindestens 1–2 Minuten" | aynan; 60–180 s | **FIX**: min 60 s, max yo'q |
| 62 | Wortschatz ish varag'i | 30 so'z, **tarjimasiz** (o'quvchi yozadi), Tipp | yozma topshiriq 30 so'z + 50 tarjimali so'z (dars varag'idan) | OK (yozma topshiriq); **VIZU**: 50 so'z ro'yxati chiqariladi; 60–500 so'z / 40 daq olib tashlanadi |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "weil oder da?", "Nemischa qanday?", Abschlusstest 10 | **VIZU** → chiqariladi |

**5-dars natija:** 10/10 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 1 yozma mashq (28), Lesen 1 (16 MC) + 5 ochiq savol, Hören 1 (10), Schreiben 2, Sprechen 1, Wortschatz ish varag'i 30 so'z (tarjimasiz → lug'at yozuvi yo'q), video 1.

## 6-dars — Beziehungen und Kommunikation (p.63–72)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 63 | Dars muqovasi | "Über Familie, Freunde und gute Kommunikation sprechen" | — | OK |
| 64 | Frage des Themas | savol + A/B/C (6 tadan nuqta) | aynan | OK; 20–120 s olib tashlanadi |
| 65 | Grammatik dass-Sätze | 8 blok (Was ist…, Struktur, Satzbau, Wann, Unterschied, Beispiele, Typische Fehler, Mini-Übung) | aynan | OK |
| 66 | Grammatik Aufgaben 1–4 | 4 × 6 jumla | 4 × 6 aynan | OK; kalit kitobda yo'q → grammatik qoida bo'yicha hisoblangan (`key_source=computed`) |
| 67 | Lesen Lukas und Jonas | matn + **10** R/F | matn aynan; 12 R/F (kitobda yo'q 2 ta: "…bald wiedersehen", "…schwach") | **FIX**: kitobdagi 10 savol (raqam 1–10); kalit matndan |
| 68 | Lesen Paul und Leon | matn + **10** R/F | matn aynan; 11 R/F (kitobda yo'q 1: "Paul ihm nicht wichtig"; kitobdagi 9-savol olinmagan) | **FIX**: kitobdagi 10 savol; 9 "Paul bekommt gute Noten in der Schule" → **NEEDS_REVIEW** (matnda faqat "in der Schule alles gut läuft", R/F'da aniq kalit yo'q) |
| 69 | Hören | 2 × 6 ochiq savol | aynan | OK; kitobda kalit/transkript yo'q → kalitsiz; ochiq savol → o'qituvchi tekshiradi |
| 70 | Schreiben Thema / E-Mail | ikkalasi "mindestens 80 Wörter" | 80–160 / 25 | **FIX**: faqat min 80 |
| 71 | Sprechen | 6 nuqta | aynan | OK; 60–180 s olib tashlanadi |
| 72 | Wichtige Wörter (ish varag'i) | 30 so'z, **tarjimasiz** | yozma topshiriq 30 so'z + 60 tarjimali so'z (dars varag'idan) | OK (yozma topshiriq); **VIZU**: 60 so'z ro'yxati chiqariladi |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | VIZU mashqlari | **VIZU** → chiqariladi |

**6-dars natija:** 10/10 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 4 mashq (24), Lesen 2 (20 R/F), Hören 1 (12 ochiq), Schreiben 2, Sprechen 1, Wortschatz ish varag'i 30 so'z (lug'at yozuvi yo'q).

## 7-dars — Reisen im Alltag und Mobilität (p.73–83)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 73 | Video-darslar muqovasi | "Nemis tili video-darslar A2 7-Dars" | — | video slot |
| 74 | Frage des Themas | savol + A/B/C (6 tadan nuqta) | aynan | OK; 20–120 s olib tashlanadi |
| 75 | Präpositionen mit Dativ / Akkusativ | Dativ **6** (aus…von), Akk 7, Merke | Dativ **11** (zu, außer, gegenüber, entgegen, ab + kitobda yo'q misollar) | **FIX**: Dativ jadvali kitobdagi 6 qator |
| 76 | Wechselpräpositionen + Übersicht | 9 qatorli Wo?/Wohin? jadvali, 3 ustunli Übersicht, Merke | aynan | OK |
| 77 | Grammatik Aufgaben | 30 MC (A/B/C) | 25 baholanadi; 5 tasi (2, 9, 18, 25, 26) faqat metadata'da | **FIX**: 30 tasi ko'rsatiladi, 25 tasi avtomatik; 5 tasi **NEEDS_REVIEW** (kitobda aniq to'g'ri javob yo'q; 26-savolda B va C ikkalasi "von"), baholanmaydi |
| 78 | Lesen matni | 5 abzas | aynan | OK; kitobda "fahrem" → "fahren" |
| 79 | Lesen R/F | 12 savol | aynan | OK; kalit matndan |
| 80 | Hören Test: Reisen | 15 savol (1–14, 16; 7 va 8 bir xil) | aynan | OK; kalit/transkript kitobda yo'q → kalitsiz. Eski audit "16 savol" yozuvi xato |
| 81 | Schreiben 1/2 Aufgabe | "Wähle eine Aufgabe" (ikkisidan biri), so'z soni yo'q | 2 ta alohida majburiy topshiriq; 60–150 / 25; 50–120 / 20 + support_phrases | **FIX**: "bittasini tanlang" ko'rsatmasi; so'z soni, vaqt, support_phrases olib tashlanadi. LMS'da tanlash mexanizmi yo'q → ikkalasi ko'rsatiladi, ko'rsatmada "bittasini" deyiladi |
| 82 | Sprechen "Meine letzte Reise" | 6 nuqta | aynan | OK; 60–180 s olib tashlanadi |
| 83 | 30 schwierige Wörter | 30 so'z, tarjimasiz | yozma topshiriq 30 + 50 tarjimali so'z | OK (yozma topshiriq); **VIZU**: 50 so'z ro'yxati chiqariladi |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "Wo? oder Wohin?", "Nemischa qanday?", Abschlusstest 10 | **VIZU** → chiqariladi |

**7-dars natija:** 11/11 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 2 qoida + 30 MC (25 baholanadi), Lesen 1 (12 R/F), Hören 1 (15, kalitsiz), Schreiben 2 (bittasini tanlash), Sprechen 1, Wortschatz ish varag'i 30 so'z, video 1.

## 8-dars — Konsum, Werbung und Produkte (p.84–93)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 84 | Dars muqovasi | "Konsum, Werbung und Produkte" | — | OK |
| 85 | Frage des Themas | savol + A/B/C (6 tadan) | aynan | OK; 20–120 s olib tashlanadi |
| 86 | Grammatik trotzdem | Bedeutung, 14 Beispiel, Vergleich: aber, **Vergleich + mehr Beispiele (6)**, **Mini-Übungen (6)** | birinchi 3 blok + kitobda yo'q "Position 2" izohi | **FIX**: 2 blok qo'shiladi, izoh olib tashlanadi. **NEEDS_REVIEW**: kitobning o'zida mazmuniy xatolar ("Ich habe Hunger, aber sie fährt nicht allein", "Es ist kalt, Trotzdem gehe …") — matn kitobdagidek, muallifga xabar |
| 87 | Grammatik Aufgaben A/B/C | A 10, B 10, C 10 | B + C (+ kitobda yo'q "Unterrichtsblatt 20 Sätze"); A kiritilmagan | **FIX**: A (10 jumla, o'qituvchi tekshiradi) qo'shiladi; C ko'rsatmasi kitobdagidek ("Finde die Fehler im Satz und korrigiere sie."); 20 jumla (VIZU) va 80–500 so'z / 40 daq olib tashlanadi |
| 88 | Lesen matni + yon panel | matn, Merke, statistik panel (Müll 552 kg, Plastik 36 kg, Elektroschrott 62 Mio t, Lebensmittel 931 Mio t, "Unser Ziel" 4 band) | matn + Merke | **FIX**: yon panel matni qo'shiladi |
| 89 | Lesen Test | 10 MC | aynan | OK; kalit matndan |
| 88 | — | — | Wortschatz 11 "Wichtige Begriffe" (dars varag'idan) | **VIZU** → chiqariladi |
| 90 | Hören MC-Test | 2 × 6 savol | aynan | OK; kalit "Vizu-Antworten A2"; transkript yo'q |
| 91 | Schreiben Thema / E-Mail | ikkalasi "mindestens 80 Wörter" | 80–160 / 25 | **FIX**: faqat min 80; kitobda "ein Laptop" (artikl xatosi) → kodda "einen" |
| 92 | Sprechen | 5 savol + har biriga namuna javob, Tipps | aynan | OK; 60–180 s olib tashlanadi |
| 93 | Wort zu Wort Wortschatzmethode | 5 variant × 6 so'z, Variante 1 namuna matni | aynan | OK (yozma topshiriq); 40–200 / 25 daq olib tashlanadi |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "trotzdem oder aber?", "Nemischa qanday?", Abschlusstest 10 | **VIZU** → chiqariladi |

**8-dars natija:** 10/10 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 3 yozma mashq (30 jumla), Lesen 1 (10 MC), Hören 1 (12 MC), Schreiben 2, Sprechen 1, Wortschatz-Aufgabe 1 (5 variant). Tarjimali lug'at ro'yxati kitobda yo'q.

## 9-dars — Medien, Nachrichten und Meinung (p.94–103)

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 94 | Video-darslar muqovasi | "Nemis tili video-darslar A2 9-Dars" | — | video slot |
| 95 | Frage des Themas | savol + Ja / Es kommt darauf an / Nein (6 tadan) | aynan | OK; 20–120 s olib tashlanadi |
| 96 | Grammatik Finalsätze damit / um … zu | Bedeutung, Zweck, Satzbau, 3 × 6 Beispiel | aynan | OK |
| 97 | Grammatik Aufgaben | 2 ustun × 15 juft, namuna 1-qatorda | um … zu: 14 short_answer (kalit hisoblangan); damit: yozma topshiriq | OK; um … zu kaliti grammatik qoida bo'yicha (`key_source=computed`); 60–300 so'z / 25 daq olib tashlanadi. **NEEDS_REVIEW**: kitob namunasi "damit ich … studieren **will**" (A2 uslubiga ko'ra "kann" yaxshiroq) — kitobdagidek |
| 98 | Lesen matni + Wichtige Wörter (6, nemischa izoh) | matn, 6 so'z izohi | matn aynan; 6 so'z Wortschatz sifatida | OK; 6 so'z kitobda bor (tarjima o'rniga nemischa izoh) → lug'at yozuvi saqlanadi |
| 99 | Lesen Test | 8 R/F | aynan | OK; kalit matndan. **NEEDS_REVIEW** 6-savol: "Weniger als 30 % … problematisch" — matnda "fast 30 %" (= 30% dan kam), kalit "richtig" mantiqan to'g'ri, lekin noaniq |
| 100 | Hören Zuordnung | 6 shaxs ↔ A–F | aynan | OK; kalit "Vizu-Antworten A2" (1F 2A 3D 4B 5C 6E) |
| 101 | Schreiben Thema / Kommentar | ikkalasi "mindestens 80 Wörter" | 80–160 / 25 | **FIX**: faqat min 80 |
| 102 | Sprechen "Meine Mediennutzung" | 6 nuqta | aynan | OK; 60–180 s olib tashlanadi |
| 103 | Wort zu Wort Wortschatzmethode | 5 variant × 6, Variante 1 namuna | aynan | OK; 40–200 / 25 daq olib tashlanadi |
| — | Übungen / Abschlusstest / Zusammenfassung | yo'q | "damit oder um … zu?", Abschlusstest 8 | **VIZU** → chiqariladi |

**9-dars natija:** 10/10 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 2 mashq (14 + 15), Lesen 1 (8 R/F), Hören 1 (6 Zuordnung), Schreiben 2, Sprechen 1, Wortschatz 6 (izoh bilan) + Wortschatz-Aufgabe 1, video 1.

## 10-dars — Lernen und Weiterbildung (p.104–124) — Goethe A2 formati

| Sahifa | Bo'lim | Kitob | Kod | Holat |
|---|---|---|---|---|
| 104 | Dars muqovasi ("10.UNTERICHT") | — | — | OK |
| 105 | Frage des Themas | savol + 3 javob | aynan | OK; 20–120 s olib tashlanadi |
| 106 | Grammatik Futur I / II | ta'rif, Vorform, Beispiele, Unterschied | aynan (takroriy "Beispiele" bloki qisqartirilgan) | OK. **NEEDS_REVIEW**: kitobda Futur I misoli "Lisa wird wohl schon geschlafen haben" — bu Futur II (kitobdagidek qoldirildi) |
| 107 | Aufgaben | 2 × 15 so'z tartiblash | 2 × 15 short_answer | OK; kalit grammatik qoida bo'yicha hisoblangan (`key_source=computed`) |
| 108 | Lesen Teil 1 matni | "Tolle Sehenswürdigkeiten" | aynan | OK |
| 109 | Lesen Teil 1 Aufgaben | 0 (namuna) + 1–5 | 1–5 | OK; kalit matndan (C, A, B, A, C) |
| 110 | Lesen Teil 2 Aufgaben | 0 + 6–10 | 6–10 | OK; kalit matndan (A, B, C, B, B) |
| 111 | Lesen Teil 2 Informationstafel | **1–5 Stock** (Erdgeschoss yo'q) | Erdgeschoss qatori qo'shilgan | **FIX**: Erdgeschoss qatori olib tashlanadi (kitobda yo'q) |
| 112 | Lesen Teil 3 E-Mail | Inge → Matilda | aynan | OK |
| 113 | Lesen Teil 3 Aufgaben | 11–15 | aynan | OK; kalit matndan (C, B, B, A, A) |
| 114 | Lesen Teil 4 Anzeigen | a–f | aynan | OK |
| 115 | Lesen Teil 4 Aufgaben | 0 + 16–20, X | aynan | OK; kalit matndan (16e, 17X, 18f, 19c, 20d) |
| 116 | Hören Teil 1 | 1–5 (a/b/c) | aynan | OK; kitobda kalit/transkript yo'q → kalitsiz; trek raqami yo'q |
| 117 | Hören Teil 2 Flohmarkt | 0 + 6–10, rasmlar a–i | aynan | OK; kalitsiz; trek raqami yo'q |
| 118 | Hören Teil 3 | 11–15, rasmli | aynan | OK; kalitsiz; **NEEDS_REVIEW**: "Track 7-11" |
| 119 | Hören Teil 4 | 16–20 Ja/Nein | aynan | OK; kalitsiz; **NEEDS_REVIEW**: "Track 7-11" (Teil 3 bilan bir xil — kitob xatosi bo'lishi mumkin) |
| 120 | Schreiben Teil 1 SMS | "Schreib 20–30 Wörter" | 20–40 / 10 daq | **FIX**: 20–30; vaqt olib tashlanadi |
| 121 | Schreiben Teil 2 E-Mail | "Schreib 30–40 Wörter" | 30–50 / 15 daq | **FIX**: 30–40; vaqt olib tashlanadi |
| 122 | Sprechen Teil 1 | 2 nomzod × 4 karta | aynan | OK; 30–150 s olib tashlanadi |
| 123 | Sprechen Teil 2 | Karte A / B × 4 | aynan | OK; 45–150 s olib tashlanadi |
| 124 | Wort zu Wort Wortschatzmethode | 5 × 6 so'z, tarjimasiz | yozma topshiriq + WORTSCHATZ kompetensiya matni | OK; 40–200 / 25 daq olib tashlanadi |
| — | Abschlusstest / Zusammenfassung | yo'q | Abschlusstest 8 | **VIZU** → chiqariladi |

**10-dars natija:** 21/21 sahifa. Kitob topshiriqlari: Frage 1, Grammatik 1 qoida + 2 mashq (30), Lesen Teil 1–4 (20 savol), Hören Teil 1–4 (20, kalitsiz), Schreiben Teil 1–2, Sprechen Teil 1–2, Wortschatz-Aufgabe 1.
