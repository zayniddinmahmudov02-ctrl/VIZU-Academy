# A2 Hören — javob kalitlarini tekshirish (1–13-darslar)

Sana: 2026-10-30.

**Natija:**
- 27 vazifa, 160 savol (5-dars 2 ta savol olib tashlangandan keyin).
- **128 ta kalit VERIFIED** (19 vazifa to‘liq).
- **12 ta NEEDS_REVIEW** (6-dars).
- 20 savolga kalit qo‘yilmadi (13-dars, noto‘g‘ri audio).
- 4-darsning 3 ta Text vazifasi savolsiz.

## Usul

1. **Dalil.** Har bir savol shu vazifa faylining transkripti bilan solishtirildi (SHA-256 bir xil). Kalitni isbotlovchi ibora vaqt belgisi bilan topildi. Ibora ikkala modelda ham bor:

   ```
   a2p_review.py        savollar + kalit + transkript
   a2p_quotes.py        dalil iboralari, 10–12-darslar
   ```

2. **Ma’lumot.** 2026-10-21 dagi audit kalitlari (`a2_keys_data.py`, 1-nashr) faqat qayta tekshiruvda tasdiqlangan joyda olindi. Kitob nashrining savollari xuddi shu.
   - Har bir vazifaning dalili: `backend/app/scripts/a2_audio_processing_data.py` va LMS → Lösung’dagi izohda („Neu geprüft 2026-10-30 …“).
3. **Yozish.**
   - Editor validatsiyasi bilan, LMS → Lösung’da VERIFIED (fingerprint bilan) yoki NEEDS_REVIEW (sabab bilan): `a1_hoeren_keys.plan_task` / `apply_question`.
   - Baholash formati o‘zgarmadi: MC/RF — to‘g‘ri variant (`is_correct`), Lückentext — `config.gaps.accepted`, Zuordnung — `config.pairs`.
4. **Hech narsa taxmin qilinmadi.** Audio isbotlamagan javob VERIFIED qilinmadi.

## Vazifalar

| U. | Vazifa | Savollar | VERIFIED | NEEDS_REVIEW | Kalitsiz | O‘zgarish |
|---|---|---|---|---|---|---|
| 1 | Warum haben Sie Ihren Beruf gewählt? | 12 | 12 | — | — | mavjud kalitlar tasdiqlandi (0 o‘zgarish) |
| 2 | Sendung „Gemeinschaftskreis“ | 12 | 12 | — | — | tasdiqlandi (0) |
| 3 | Die Empfehlungen eines Arztes | 8 | 8 | — | — | tasdiqlandi (0) |
| 4 | Text 1 / Text 2 / Text 3 | 0 | — | — | — | savolsiz (pastda) |
| 5 | Steigende Mieten in Deutschland! | 10 → **8** | 8 | — | — | **Q4 kaliti tuzatildi; 2 savol olib tashlandi** |
| 6 | Konflikte Lukas/Jonas, Paul/Leon | 12 | 0 | **12** | — | kalit varianti yozildi, „Prüfung nötig“ |
| 7 | Reisen (Max und Sara) | 15 | 15 | — | — | 15 kalit yangi; **Q15 raqami „16.“ → „15.“**; **„Text 2“ treki qo‘shildi** |
| 8 | Einkauf von Susanna / Johann | 12 | 12 | — | — | tasdiqlandi (0), Q6 izohi |
| 9 | Medien zuordnen (Zuordnung) | 1 (6 juft) | 1 | — | — | tasdiqlandi (0) |
| 10 | Teil 1 · 2 · 3 · 4 | 5+5+5+5 | 20 | — | — | 20 kalit yangi; **Teil 3 Q15 varianti „b) als Arzt“ → „b) als Krankenschwester (weißer Kittel, Bild b)“** |
| 11 | Teil 1 · 2 · 3 · 4 | 5+5+5+5 | 20 | — | — | 20 kalit yangi; **Teil 2 varianti „f) Waffeln“ → „f) Gebäck (Kuchen)“** |
| 12 | Teil 1 · 2 · 3 · 4 | 5+5+5+5 | 20 | — | — | 20 kalit yangi |
| 13 | Teil 1 · 2 · 3 · 4 | 5+5+5+5 | 0 | — | **20** | **qo‘yilmadi: audio 12-darsniki** |

## Savollar va javob variantlaridagi o‘zgarishlar

Avvalgi holat backup’da saqlangan (`db.dump`) va audit log’da `a2_audio_processed` yozuvlari ichida „before/after“ bilan.

1. **5-dars, Q4** „Was kostet eine Wohnung in München?“:
   - import qilingan kalit „800–1000 Euro“ audioga zid;
   - audio [22.5 s]: „Dort kostet eine kleine Wohnung im Zentrum oft zwischen 1.500 und 2.100 Euro pro Monat“;
   - kalit **„1500–2100 Euro“**.
2. **5-dars, olib tashlangan savollar:** „Was machen viele Menschen in Berlin?“ (Fahrrad) va „Wie viele Tage arbeiten viele Menschen?“ (5 Tage).
   - Bu savollar kitob sahifasida (8 savol: 1–4, 7–10) ham, audioda ham yo‘q — o‘qish matnidan kelgan.
   - Urinishlar yo‘q edi (vazifa nashr qilinmagan), shuning uchun o‘chirish xavfsiz bo‘ldi.
3. **7-dars, Q15:** savol matnidagi raqam „16. Wer hört Musik im Zug?“ → „15. …“. Kitobda shu savol „16.“ deb chop etilgan, ketma-ketlik esa 15.
4. **10-dars Teil 3, Q15** „Wie verkleidet sich Rolf?“:
   - audio [4:44]: „wenn ich mich als Krankenschwester verkleide“;
   - rasm b — oq xalatli figura;
   - variant „b) als Arzt“ → „b) als Krankenschwester (weißer Kittel, Bild b)“.
5. **11-dars Teil 2, Jakob:**
   - audio [2:03]: „seine Mutter hat Kuchen gebacken und er hat uns welche gebracht“;
   - yagona pishiriq rasmi — f;
   - variant „f) Waffeln“ → „f) Gebäck (Kuchen)“.

## Dalil namunalari (to‘liq ro‘yxat LMS → Lösung izohlarida)

- **1-dars:**
  - [11 s] „Mein Beruf ist Architekt, weil mein Vater auch Architekt war“;
  - [85 s] „Ich habe Cristiano Ronaldo immer bewundert. Letztes Jahr habe ich in einer Mannschaft trainiert“.
- **2-dars:**
  - [22 s] Prof. Müller „arbeitet an der Universität München“;
  - [28 s] Frau Millner „Mutter von zwei Kindern“;
  - [81 s] „Tipps über Schule, Gesundheit“;
  - [93 s] „zu Hause klare Regeln“.
- **3-dars:**
  - [11 s] „Mein Name ist Dr. Martin Weber“;
  - [53 s] „Trinken Sie Wasser oder warmen Tee“;
  - [108 s] „Wenn Sie sich nach einigen Tagen nicht besser fühlen, gehen Sie zum Arzt“.
- **7-dars:**
  - Text 1: [6 s] Max „25 Jahre … aus Madrid“, [14 s] „mit dem Auto begonnen“, [53 s] „In Hamburg habe ich den Hafen gesehen“, [68 s] „Der Bus ist günstig, aber langsam“;
  - Text 2: [7 s] Sara „35 Jahre … aus München“, [26 s] „im Zug Musik gehört“, [45 s] „mit dem Flugzeug nach Rom“.
- **8-dars:**
  - [15 s] Susanna „80 bis 100 Euro“;
  - [92 s] Johann „2 Kilogramm Kartoffeln“;
  - [119 s] „trinkt hauptsächlich Wasser“;
  - [135 s] „Am Sonntag kauft er … ein Kuchen oder backt selbst“.
  - Q6 („manchmal am Wochenende“): audioda „Wochenende“ yo‘q, faqat [60–68 s] „manchmal … Süßigkeiten … 1–2 Tafeln Schokolade pro Woche“. Variantlardan faqat Schokolade mos — izohda yozildi.
- **9-dars:** Text 1 „aus Papier … jeden Morgen“ → F Zeitung; Text 2 → A Podcast; 3 → D Radio; 4 → B Internet; 5 → C Fernsehen; 6 → E Telefon.
- **10-dars:**
  - „Ich lasse mir mittellange Haare schneiden“;
  - „Nur mein Vater versteht mich“;
  - „am besten passt mir der Frühling“;
  - „Bayern München gewinnt gegen Atletico Madrid 2 zu 1“;
  - „Jeanshosen … nur 17 Euro“;
  - Flohmarkt: Anne → Tischdecke, Olaf → Äpfel, Harry → Legos, Niki → Puppen, Martin → „Mein Rad“;
  - Europa-Camp: „ab 14“, „in Italien“, „von 10 bis 12 einen Sprachkurs“, „Im Juli und August“, „Natürlich braucht man auch etwas Taschengeld“ (bermaydi → Nein).
- **11-dars:**
  - „Mein Vater hat eine neue Arbeit bekommen“;
  - „das Olympiastadion“;
  - „Immer muss ich das Geschirr spülen“;
  - „weil ich nicht so fit bin“;
  - „sonnig und schön warm“;
  - Sonja: „12 bis 16 Jahren“ (≠ 11–16 → Nein), „Kinder im Regen“ (≠ Meer → Nein), „im Netz … Blog“ → Ja, „in Afrika arbeiten“ (studieren emas → Nein).
- **12-dars:**
  - „hell und gemütlich“;
  - „Montagmorgen“;
  - „Der Kugelschreiber kostet 2,90 Euro“;
  - „Bitte hol deinen Bruder … ab“;
  - „Nur im Norden Regen“;
  - Koffer: Erika — schwarzes Kleid, Anna — Bikini, Markus — Flipflops, Jürgen — kariertes Hemd, Udo — „weißes und rotes T-Shirt“;
  - Sandra: „seit einem Jahr in Italien“, „achte Klasse“, „auf Englisch“, „Vom ersten Moment an hatte ich Freunde“ (→ Nein), „gut bezahlten Job“ (→ Nein).

## NEEDS_REVIEW va kalitsiz qolganlar

### 6-dars — 12 savol, NEEDS_REVIEW

**Holat.** Javoblar audioda aniq:
- [4 s] „im Sommerlager“;
- [9 s] „Fußball“;
- [27 s] „Jonas war traurig“;
- [41 s] „es tut mir leid“;
- [65 s] „Sie sind Brüder“;
- [67 s] „studiert im Ausland in Deutschland“;
- [72 s] „weil er viel lernen musste“;
- [111 s] „dass man immer miteinander sprechen muss“.

**Muammo.** Hamma savol ochiq matnli (Lückentext, „beantworten Sie die Fragen kurz“). Erkin javob so‘zma-so‘z solishtiriladi, shuning uchun to‘g‘ri, lekin boshqacha yozilgan javob xato deb hisoblanishi mumkin. Javob variantlari yozildi, lekin VERIFIED qilinmadi — nashr bo‘lmadi.

**Admin uchun:** LMS → Lösung’da variantlarni kengaytirish yoki savollarni Multiple Choice’ga o‘tkazish.

### 13-dars — 4 vazifa, kalitsiz

**Holat.** Audio fayllar 12-darsniki (SHA-256 bir xil):
- transkript: „Annas Zimmer … hell und gemütlich“, Koffer, Sandra;
- savollar: Carmens Geburtstag, Sebastian.

**Natija.** Hech bir kalit isbotlanmaydi va qo‘yilmadi.

**Admin uchun:** to‘g‘ri fayllarni yuklash, keyin `a2_audio_processing` ni qayta ishga tushirish (transkripsiya kerak bo‘ladi).

### 4-dars Text 1–3 — savollar yo‘q

Kitob savollari („Familie Mannsberg“, 12 ta „Wer …?“) oldingi vazifa bilan olib tashlangan; nusxasi `/var/backups/vizu/pre-a2l4-20261030-011331/legacy/…/tasks.json` da. Yangi savol o‘zimdan yaratilmadi.
