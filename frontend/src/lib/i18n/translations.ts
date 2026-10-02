interface Entry {
  de: string;
  uz: string;
}

type Namespace = Record<string, Entry>;

export const translations: Record<string, Namespace> = {
  sidebar: {
    dashboard: { de: "Dashboard", uz: "Boshqaruv paneli" },
    courses: { de: "Kurse", uz: "Kurslar" },
    vorbereitung: { de: "Vorbereitung", uz: "Tayyorgarlik" },
    certificates: { de: "Zertifikate", uz: "Sertifikatlar" },
    dictionary: { de: "Wörterbuch", uz: "Lug'at" },
    informationen: { de: "Informationen", uz: "Ma'lumot" },
    vizuPay: { de: "VIZU Pay", uz: "VIZU Pay" },
    profile: { de: "Profil", uz: "Profil" },
    settings: { de: "Einstellungen", uz: "Sozlamalar" },
    expand: { de: "Sidebar erweitern", uz: "Yon panelni kengaytirish" },
    collapse: { de: "Sidebar einklappen", uz: "Yon panelni yig'ish" },
    closeMenu: { de: "Menü schließen", uz: "Menyuni yopish" },
    toggleLanguageAria: { de: "Sprache umschalten", uz: "Tilni almashtirish" },
  },

  header: {
    menuOpen: { de: "Menü öffnen", uz: "Menyuni ochish" },
    searchPlaceholder: { de: "Suchen…", uz: "Qidirish…" },
    notifications: { de: "Benachrichtigungen", uz: "Bildirishnomalar" },
    notificationsEmpty: {
      de: "Du hast noch keine Benachrichtigungen.",
      uz: "Sizda hozircha bildirishnomalar yo'q.",
    },
    markAllRead: { de: "Alle als gelesen markieren", uz: "Barchasini o'qilgan deb belgilash" },
    markRead: { de: "Als gelesen markieren", uz: "O'qilgan deb belgilash" },
    playFeedback: { de: "Feedback anhören", uz: "Fikr-mulohazani tinglash" },
    calendarAria: { de: "Kalender öffnen", uz: "Kalendarni ochish" },
    logout: { de: "Abmelden", uz: "Chiqish" },
    learner: { de: "Lernender", uz: "O'quvchi" },
  },

  common: {
    starten: { de: "Starten", uz: "Boshlash" },
    fortsetzen: { de: "Fortsetzen", uz: "Davom etish" },
    auswaehlen: { de: "Auswählen", uz: "Tanlash" },
    errorTitle: { de: "Etwas ist schiefgelaufen", uz: "Nimadir noto'g'ri ketdi" },
    loading: { de: "Wird geladen…", uz: "Yuklanmoqda…" },
  },

  levels: {
    a1: { de: "Anfänger", uz: "Boshlang'ich" },
    a2: { de: "Grundstufe", uz: "Boshlang'ichdan yuqori" },
    b1: { de: "Mittelstufe", uz: "O'rta" },
    b2: { de: "Obere Mittelstufe", uz: "O'rta-yuqori" },
    c1: { de: "Fortgeschritten", uz: "Ilg'or" },
  },

  dashboard: {
    welcomeBack: { de: "Willkommen zurück,", uz: "Xush kelibsiz," },
    heroSubtitle: {
      de: "Setze deinen Lernfortschritt fort und erreiche deine Ziele.",
      uz: "O'quv jarayoningizni davom eting va maqsadlaringizga erishing.",
    },
    overallProgressLine1: { de: "Gesamt-", uz: "Umumiy" },
    overallProgressLine2: { de: "fortschritt", uz: "taraqqiyot" },
    statLernzeit: { de: "Lernzeit", uz: "O'qish vaqti" },
    statUnterrichte: { de: "Unterrichte abgeschlossen", uz: "Yakunlangan darslar" },
    statZertifikate: { de: "Zertifikate", uz: "Sertifikatlar" },
    statLernserie: { de: "Lernserie", uz: "O'quv seriyasi" },
    deltaWeek: { de: "+0% diese Woche", uz: "+0% shu hafta" },
    deltaMonth: { de: "+0 diesen Monat", uz: "+0 shu oy" },
    deltaStreak: { de: "Jetzt starten 🔥", uz: "Hozir boshlang 🔥" },
    continueLearning: { de: "Weiter lernen", uz: "O'qishni davom ettirish" },
    allCourses: { de: "Alle Kurse", uz: "Barcha kurslar" },
    lessonTitle: { de: "Unterricht 1 · Begrüßung", uz: "1-dars · Salomlashish" },
    lessonNumber: { de: "{number}. Unterricht", uz: "{number}-dars" },
    lessonsAvailable: { de: "{count} Unterricht verfügbar", uz: "{count} ta dars mavjud" },
    progressLabel: { de: "Fortschritt", uz: "Taraqqiyot" },
    jetztStarten: { de: "Jetzt starten", uz: "Hozir boshlash" },
    lessonsCount: { de: "{count} Unterricht", uz: "{count} ta dars" },
    quickAccess: { de: "Schnellzugriff", uz: "Tezkor kirish" },
    mockExams: { de: "Probeprüfungen", uz: "Mock imtihonlar" },
    mockExamsSubtitle: { de: "Testen Sie Ihr Wissen", uz: "Bilimingizni sinang" },
    woerterbuchSubtitle: { de: "Vokabeln nachschlagen", uz: "So'zlarni qidirish" },
    vizuMultilevelTitle: { de: "VIZU-Multilevel", uz: "VIZU-Multilevel" },
    vizuMultilevelSubtitle: {
      de: "Teste dein Deutschniveau kostenlos",
      uz: "Darajangizni bepul sinab oling",
    },
  },

  courses: {
    title: { de: "Deutschkurse", uz: "Nemis tili kurslari" },
    subtitle: { de: "Lernen von A1 bis C1 · {count} Module", uz: "A1 dan C1 gacha o'rganing · {count} ta modul" },
    filterAll: { de: "Alle", uz: "Barchasi" },
    newBadge: { de: "Neu", uz: "Yangi" },
    percentDone: { de: "{count}% abgeschlossen", uz: "{count}% tugallandi" },
    lessonFree: { de: "Kostenlos", uz: "Bepul" },
    lessonUnlocked: { de: "Freigeschaltet", uz: "Ochilgan" },
    lessonPremium: { de: "Premium", uz: "Premium" },
    lessonOpen: { de: "Öffnen", uz: "Ochish" },
    lessonsSubtitle: {
      de: "Die ersten 3 Lektionen sind kostenlos. Danach benötigst du Premium.",
      uz: "Dastlabki 3 ta dars bepul. Keyingilari uchun Premium kerak.",
    },
  },

  vorbereitung: {
    kicker: { de: "Vorbereitung zum Zertifikat", uz: "Sertifikatga tayyorgarlik" },
    title: { de: "Prüfungsvorbereitung", uz: "Imtihonga tayyorgarlik" },
    heroSubtitle: {
      de: "Wähle dein Niveau und dein Zertifikat. Danach findest du {count} Mock-Tests mit KI-Auswertung für Schreiben und Sprechen.",
      uz: "Darajangizni va sertifikatingizni tanlang. Shundan so'ng yozish va gapirish uchun sun'iy intellekt bahosi bilan {count} ta sinov testini topasiz.",
    },
    heroSubtitleGeneric: {
      de: "Wähle dein Niveau und dein Zertifikat. Danach findest du passende Mock-Tests mit KI-Auswertung für Schreiben und Sprechen.",
      uz: "Darajangizni va sertifikatingizni tanlang. Shundan so'ng yozish va gapirish uchun sun'iy intellekt bahosi bilan mos sinov testlarini topasiz.",
    },
    stepNiveau: { de: "Niveau", uz: "Daraja" },
    stepZertifikat: { de: "Zertifikat", uz: "Sertifikat" },
    stepMockTests: { de: "Mock-Tests", uz: "Sinov testlari" },
    step1Heading: { de: "1 · Wähle dein Niveau", uz: "1 · Darajangizni tanlang" },
    certCount: { de: "{count} Zertifikate", uz: "{count} ta sertifikat" },
    changeNiveau: { de: "Niveau ändern", uz: "Darajani o'zgartirish" },
    step2Heading: { de: "2 · Wähle dein Zertifikat für", uz: "2 · Sertifikatingizni tanlang —" },
    changeZertifikat: { de: "Zertifikat ändern", uz: "Sertifikatni o'zgartirish" },
    mockTestsCount: { de: "{count} Mock-Tests · KI-Auswertung", uz: "{count} ta sinov testi · SI bahosi" },
    mockTestLabel: { de: "Mock-Test {count}", uz: "Sinov testi {count}" },
    skillsRow: {
      de: "Lesen · Hören · Schreiben · Sprechen",
      uz: "O'qish · Tinglash · Yozish · Gapirish",
    },
    notStarted: { de: "Noch nicht begonnen", uz: "Hali boshlanmagan" },
    premiumRequired: { de: "Premium erforderlich", uz: "Premium talab qilinadi" },
    unlockPremium: { de: "Premium freischalten", uz: "Premium sotib olish" },

    // Static Multilevel section — see vorbereitung-view.tsx's own
    // docstring: everything here is a locked placeholder (no real
    // content exists yet), not backed by the provider/level/model-test
    // API at all. Multilevel is its own Niveau-step card (multilevelCard
    // Subtitle) leading to its own page (multilevelSection/Subtitle).
    multilevelCardSubtitle: { de: "Modelltests", uz: "Modelltestlar" },
    multilevelSection: { de: "Multilevel", uz: "Multilevel" },
    multilevelSubtitle: {
      de: "10 Modelltests · bald verfügbar",
      uz: "10 ta Modelltest · tez orada",
    },
    modelltestNumber: { de: "Modelltest {number}", uz: "Modelltest {number}" },
    comingSoonTitle: { de: "Noch nicht verfügbar", uz: "Hali baza qo'shilmagan" },
    comingSoonBody: {
      de: "Die Prüfungsinhalte für diesen Modelltest wurden noch nicht zur Datenbank hinzugefügt. Bald verfügbar.",
      uz: "Bu Modelltest uchun imtihon materiallari hali bazaga qo'shilmagan. Tez orada mavjud bo'ladi.",
    },
  },

  // VIZU-Multilevel — standalone free level check (A1–C1): Lesen, Hören,
  // Schreiben, Sprechen. Reuses the same i18n system, no new mechanism.
  vizuMultilevel: {
    title: { de: "VIZU-Multilevel", uz: "VIZU-Multilevel" },
    subtitle: { de: "Kostenloser Einstufungstest", uz: "Bepul daraja aniqlash testi" },
    levelRange: { de: "A1–C1", uz: "A1–C1" },
    heroTitle: { de: "Teste dein Deutschniveau kostenlos", uz: "Darajangizni bepul sinab oling" },
    heroBody: {
      de: "Bestimme dein Deutschniveau zwischen A1 und C1 durch Lesen, Hören, Schreiben und Sprechen.",
      uz: "A1–C1 oralig'idagi nemis tili darajangizni Lesen, Hören, Schreiben va Sprechen orqali aniqlang.",
    },
    howItWorks: { de: "So funktioniert's", uz: "Bu qanday ishlaydi" },
    minutesEach: { de: "je 20 Minuten", uz: "har biri 20 daqiqa" },
    totalDuration: { de: "Gesamtdauer: 100 Minuten", uz: "Umumiy davomiylik: 100 daqiqa" },
    startNewAttempt: { de: "Neuen Versuch starten", uz: "Yangi urinish boshlash" },
    step: { de: "Schritt {current} von {total}", uz: "{current}/{total}-qadam" },
    next: { de: "Weiter", uz: "Keyingi" },
    previous: { de: "Zurück", uz: "Orqaga" },
    submit: { de: "Einreichen", uz: "Yuborish" },
    finish: { de: "Abschließen", uz: "Yakunlash" },
    // Empty states — shown while a competency has no published content.
    preparingLesen: { de: "Lesen-Test wird vorbereitet.", uz: "Lesen testi tayyorlanmoqda." },
    preparingHoeren: { de: "Hören-Test wird vorbereitet.", uz: "Hören testi tayyorlanmoqda." },
    preparingSchreiben: { de: "Schreiben-Test wird vorbereitet.", uz: "Schreiben testi tayyorlanmoqda." },
    preparingSprechen: { de: "Sprechen-Test wird vorbereitet.", uz: "Sprechen testi tayyorlanmoqda." },
    preparingBody: {
      de: "Für diesen Teil gibt es noch keine Aufgaben. Du kannst einfach fortfahren.",
      uz: "Bu bo'lim uchun hali topshiriqlar yo'q. Davom etishingiz mumkin.",
    },
    sectionError: {
      de: "Dieser Abschnitt konnte nicht geöffnet werden. Bitte versuche es erneut.",
      uz: "Bu bo'limni ochib bo'lmadi. Iltimos, qayta urinib ko'ring.",
    },
    submitFailed: {
      de: "Das Einreichen ist fehlgeschlagen. Bitte versuche es erneut.",
      uz: "Yuborish amalga oshmadi. Iltimos, qayta urinib ko'ring.",
    },
    saveFailed: {
      de: "Speichern fehlgeschlagen — möglicherweise ist die Zeit abgelaufen.",
      uz: "Saqlab bo'lmadi — vaqt tugagan bo'lishi mumkin.",
    },
    listeningInstruction: { de: "Höre das Audio und beantworte die Fragen.", uz: "Audioni tinglang va savollarga javob bering." },
    aufgabeOf: { de: "Aufgabe {current} von {total}", uz: "{current} / {total}-Aufgabe" },
    audioTitle: { de: "Audio", uz: "Audio" },
    audioLoading: { de: "Audio wird geladen…", uz: "Audio yuklanmoqda…" },
    audioUnavailable: { de: "Audio ist derzeit nicht verfügbar.", uz: "Audio hozircha mavjud emas." },
    testsTitle: { de: "Tests", uz: "Testlar" },
    testNumber: { de: "Test {number}", uz: "Test {number}" },
    saveAnswers: { de: "Antworten speichern", uz: "Javoblarni saqlash" },
    answerAllFirst: {
      de: "Beantworte alle Tests, um Hören abzuschließen ({answered} / {total}).",
      uz: "Hörenni yakunlash uchun barcha testlarga javob bering ({answered} / {total}).",
    },
    answerAllRequired: {
      de: "Bitte beantworte zuerst alle 20 Tests.",
      uz: "Iltimos, avval barcha 20 ta testga javob bering.",
    },
    hoerenResultTitle: { de: "Hören Ergebnis", uz: "Hören natijasi" },
    hoerenTimeUp: { de: "Hören-Zeit ist abgelaufen.", uz: "Hören vaqti tugadi." },
    audioMissing: { de: "Für diese Aufgabe ist noch kein Audio hinterlegt.", uz: "Bu topshiriq uchun audio hali yuklanmagan." },
    aufgabeStep: { de: "Aufgabe {current} von {total}", uz: "{current}/{total}-Aufgabe" },
    question: { de: "Frage {number}", uz: "{number}-savol" },
    finishLesen: { de: "Lesen Test abschließen", uz: "Testni yakunlash" },
    testOf: { de: "Test {current} von {total}", uz: "Test {current} / {total}" },
    aufgabe: { de: "AUFGABE {number}", uz: "AUFGABE {number}" },
    lesenResultTitle: { de: "Lesen Ergebnis", uz: "Lesen natijasi" },
    points: { de: "Punkte", uz: "Ball" },
    determinedLevel: { de: "Ermitteltes Niveau", uz: "Aniqlangan daraja" },
    statCorrect: { de: "Richtige Antworten", uz: "To'g'ri javoblar" },
    statWrong: { de: "Falsche Antworten", uz: "Noto'g'ri javoblar" },
    statUnanswered: { de: "Unbeantwortet", uz: "Javobsiz savollar" },
    lesenBelowA1: {
      de: "Für eine zuverlässige Einstufung wurde noch kein Niveau erreicht.",
      uz: "Lesen bo'yicha darajani aniqlash uchun yetarli natija qayd etilmadi.",
    },
    continueNext: { de: "Weiter", uz: "Davom etish" },
    finishHoeren: { de: "Hören abschließen", uz: "Hörenni yakunlash" },
    // Schreiben — teacher-graded. No level/score is shown during the test.
    schreibenSave: { de: "Speichern", uz: "Saqlash" },
    schreibenSaved: { de: "Gespeichert", uz: "Saqlandi" },
    schreibenAbsenden: { de: "Schreiben absenden", uz: "Schreiben'ni yuborish" },
    schreibenConfirmCancel: { de: "Abbrechen", uz: "Bekor qilish" },
    sprechenAbsenden: { de: "Sprechen absenden", uz: "Sprechen'ni yuborish" },
    // Persistent "Testni yakunlash" — end the CURRENT competency at any
    // time; unanswered questions simply score 0.
    finishLabel: { de: "Test beenden", uz: "Testni yakunlash" },
    finishConfirmTitle: {
      de: "Möchtest du diesen Abschnitt wirklich beenden?",
      uz: "Ushbu bo'limni haqiqatan ham yakunlamoqchimisiz?",
    },
    finishConfirmBody: {
      de: "Unbeantwortete Fragen werden mit 0 Punkten gewertet. Diese Aktion kann nicht rückgängig gemacht werden.",
      uz: "Javob berilmagan savollar 0 ball bilan hisoblanadi. Bu amalni qaytarib bo'lmaydi.",
    },
    finishConfirmSubmit: { de: "Beenden", uz: "Yakunlash" },
    writingAnswerLabel: { de: "Deine Antwort", uz: "Sizning javobingiz" },
    maxRecording: { de: "Maximale Aufnahmedauer: {seconds} Sekunden", uz: "Maksimal yozuv davomiyligi: {seconds} soniya" },
    recordStart: { de: "Aufnahme starten", uz: "Yozishni boshlash" },
    recordStop: { de: "Aufnahme stoppen", uz: "Yozishni to'xtatish" },
    recording: { de: "Aufnahme läuft…", uz: "Yozilmoqda…" },
    recorded: { de: "Aufnahme bereit", uz: "Yozuv tayyor" },
    recordedSent: { de: "Aufnahme gesendet", uz: "Yozuv yuborildi" },
    reRecord: { de: "Neu aufnehmen", uz: "Qayta yozish" },
    micError: {
      de: "Mikrofon nicht verfügbar. Bitte erlaube den Zugriff auf das Mikrofon.",
      uz: "Mikrofon mavjud emas. Iltimos, mikrofonga ruxsat bering.",
    },
    // Results (Ergebnis)
    resultsTitle: { de: "VIZU-Multilevel Ergebnisse", uz: "VIZU-Multilevel Natijalari" },
    resultsOverall: { de: "Dein Niveau", uz: "Sizning darajangiz" },
    resultsPending: { de: "Noch nicht abgeschlossen", uz: "Hali yakunlanmagan" },
    resultsPendingNote: {
      de: "Das Ergebnis liegt noch nicht vollständig vor.",
      uz: "Natija hali to'liq emas.",
    },
    pendingReview: { de: "Wird von der Lehrkraft bewertet", uz: "O'qituvchi tomonidan baholanmoqda" },
    pendingReviewNote: {
      de: "Schreiben und Sprechen werden von einer Lehrkraft bewertet. Dein Gesamtergebnis erscheint danach hier.",
      uz: "Schreiben va Sprechen o'qituvchi tomonidan baholanadi. Umumiy natijangiz shundan keyin shu yerda ko'rinadi.",
    },
    notAvailable: { de: "Noch nicht verfügbar", uz: "Hali mavjud emas" },
    noContentNote: {
      de: "Der Test wird noch vorbereitet — es gibt noch kein Ergebnis.",
      uz: "Test hali tayyorlanmoqda — natija mavjud emas.",
    },
    belowA1: { de: "Unter A1", uz: "A1 dan past" },
    belowA1Note: {
      de: "Dein Ergebnis hat das Niveau A1 noch nicht erreicht.",
      uz: "Natijangiz hali A1 darajasiga yetmadi.",
    },
    notSavedNote: {
      de: "Dieses Ergebnis wird nicht in deinem Verlauf gespeichert.",
      uz: "Bu natija tarixingizda saqlanmaydi.",
    },
    resultNotKept: {
      de: "Für diesen Versuch ist kein gespeichertes Ergebnis vorhanden.",
      uz: "Bu urinish uchun saqlangan natija mavjud emas.",
    },
    viewCertificate: { de: "Zertifikat ansehen", uz: "Sertifikatni ko'rish" },
    certificateSubject: { de: "Deutsch Einstufung", uz: "Nemis tili darajasi" },
    certificateStudent: { de: "Student", uz: "Talaba" },
    certificateDate: { de: "Datum", uz: "Sana" },
    certificateOverallLevel: { de: "Gesamtniveau", uz: "Umumiy daraja" },
    certificateUnavailable: {
      de: "Für diesen Versuch ist kein Zertifikat verfügbar.",
      uz: "Bu urinish uchun sertifikat mavjud emas.",
    },
    oneAttemptNote: {
      de: "Der Test kann nur einmal abgelegt werden.",
      uz: "Testni faqat bir marta topshirish mumkin.",
    },
    startTest: { de: "Test starten", uz: "Testni boshlash" },
    continueTest: { de: "Test fortsetzen", uz: "Testni davom ettirish" },
    viewResult: { de: "Ergebnis ansehen", uz: "Natijani ko'rish" },
    notAvailableYet: { de: "VIZU-Mock ist derzeit nicht verfügbar.", uz: "VIZU-Mock hozircha mavjud emas." },
    loadError: {
      de: "Beim Laden der Testdaten ist ein Fehler aufgetreten.",
      uz: "Test ma'lumotlarini yuklashda xatolik yuz berdi.",
    },
    retry: { de: "Erneut versuchen", uz: "Qayta urinish" },
    aufgabePos: { de: "Aufgabe {current} / {total}", uz: "Aufgabe {current} / {total}" },
    answeredOf: { de: "{answered} / {total} beantwortet", uz: "{answered} / {total} javob berildi" },
    minRequired: {
      de: "{answered} / {min} beantwortet — mindestens {min} Aufgaben beantworten",
      uz: "{answered} / {min} javob berildi — kamida {min} ta topshiriqqa javob bering",
    },
    minReached: { de: "Mindestanzahl erreicht", uz: "Minimal son bajarildi" },
    minRequiredError: {
      de: "Bitte beantworte mindestens {min} Aufgaben.",
      uz: "Iltimos, kamida {min} ta topshiriqqa javob bering.",
    },
    missingTitle: { de: "Noch nicht abgeschlossen", uz: "Hali yakunlanmagan" },
    missingBody: {
      de: "Der Test kann erst beendet werden, wenn alle vier Kompetenzen abgegeben sind. Offen:",
      uz: "Test barcha to'rt kompetenz topshirilgandan keyingina yakunlanadi. Qolganlar:",
    },
    resultHeading: { de: "Dein Ergebnis", uz: "Sizning natijangiz" },
    totalPoints: { de: "Gesamtpunkte", uz: "Umumiy ball" },
    strengths: { de: "Stärken", uz: "Kuchli tomonlar" },
    improvements: { de: "Verbesserungspotenzial", uz: "Rivojlantirish kerak" },
    nextSteps: { de: "Nächster Lernschritt", uz: "Keyingi o'rganish yo'nalishi" },
    noStrengthsYet: {
      de: "Noch keine Kompetenz liegt bei 75 % oder mehr — der nächste Lernschritt zeigt, wo du anfangen solltest.",
      uz: "Hali hech bir kompetenz 75% dan yuqori emas — keyingi qadam qayerdan boshlashni ko'rsatadi.",
    },
    noImprovementsNeeded: {
      de: "Alle bewerteten Kompetenzen liegen bei 75 % oder mehr.",
      uz: "Baholangan barcha kompetenzlar 75% va undan yuqori.",
    },
    fb_lesen_strong: {
      de: "Lesen: Du erfasst Hauptaussagen und Details sicher.",
      uz: "Lesen: asosiy fikr va detallarni ishonchli topyapsiz.",
    },
    fb_lesen_mid: {
      de: "Lesen: Achte stärker auf Detailinformationen und vergleiche jede Antwortoption genau mit dem Text.",
      uz: "Lesen: detal ma'lumotlarga ko'proq e'tibor bering va har bir variantni matn bilan aniq taqqoslang.",
    },
    fb_lesen_weak: {
      de: "Lesen: Hauptaussage eines Textes finden, Detailinformationen herausfiltern und die Antwortoptionen mit dem Text vergleichen.",
      uz: "Lesen bo'yicha asosiy e'tibor: matndan asosiy fikrni topish, detal ma'lumotlarni ajratish va savol variantlarini matn bilan taqqoslash.",
    },
    fb_hoeren_strong: {
      de: "Hören: Du verstehst Schlüsselinformationen, Zahlen und Zeitangaben zuverlässig.",
      uz: "Hören: kalit ma'lumotlar, raqamlar va vaqtni ishonchli tushunyapsiz.",
    },
    fb_hoeren_mid: {
      de: "Hören: Konzentriere dich beim zweiten Hören auf Zahlen, Uhrzeiten und Begründungen.",
      uz: "Hören: tinglashda raqamlar, vaqt va sabablarga alohida e'tibor qarating.",
    },
    fb_hoeren_weak: {
      de: "Hören: Schlüsselwörter heraushören, Zahlen und Zeitangaben erkennen und die Hauptaussage bestimmen.",
      uz: "Hören bo'yicha asosiy e'tibor: kalit so'zlarni tinglab ajratish, raqamlar, vaqt va asosiy fikrlarni aniqlash.",
    },
    fb_schreiben_strong: {
      de: "Schreiben: Deine Texte sind gut strukturiert und sprachlich sicher.",
      uz: "Schreiben: matnlaringiz yaxshi tuzilgan va til jihatdan ishonchli.",
    },
    fb_schreiben_mid: {
      de: "Schreiben: Arbeite an Satzverbindungen und einem präziseren Wortschatz.",
      uz: "Schreiben: gaplarni bog'lash va aniqroq so'z boyligi ustida ishlang.",
    },
    fb_schreiben_weak: {
      de: "Schreiben: Satzbau, Grammatik, Wortschatz und Textstruktur gezielt üben.",
      uz: "Schreiben bo'yicha asosiy e'tibor: Satzbau, Grammatik, Wortschatz va matn strukturasi.",
    },
    fb_sprechen_strong: {
      de: "Sprechen: Du sprichst flüssig, verständlich und mit passendem Wortschatz.",
      uz: "Sprechen: ravon, tushunarli va mos so'zlar bilan gapiryapsiz.",
    },
    fb_sprechen_mid: {
      de: "Sprechen: Übe längere zusammenhängende Antworten und achte auf grammatische Genauigkeit.",
      uz: "Sprechen: uzunroq bog'langan javoblarni mashq qiling va grammatik aniqlikka e'tibor bering.",
    },
    fb_sprechen_weak: {
      de: "Sprechen: Flüssigkeit, Aussprache, Wortschatz und grammatische Genauigkeit trainieren.",
      uz: "Sprechen bo'yicha asosiy e'tibor: fluency, pronunciation, Wortschatz va grammatik aniqlik.",
    },
    next_lesen_strong: {
      de: "Lies jetzt authentische, längere Texte (Zeitungsartikel, Kommentare) und achte auf die Meinung des Autors.",
      uz: "Endi uzunroq haqiqiy matnlarni (maqola, sharh) o'qing va muallif pozitsiyasiga e'tibor bering.",
    },
    next_lesen_mid: {
      de: "Lies täglich einen kurzen Text und markiere zuerst die Hauptaussage, dann zwei Details.",
      uz: "Har kuni bitta qisqa matn o'qing: avval asosiy fikrni, keyin ikkita detalni belgilang.",
    },
    next_lesen_weak: {
      de: "Beginne mit kurzen Alltagstexten (Anzeigen, E-Mails) und beantworte zu jedem Text die W-Fragen.",
      uz: "Qisqa kundalik matnlardan (e'lonlar, e-mail) boshlang va har biriga W-savollariga javob bering.",
    },
    next_hoeren_strong: {
      de: "Höre Podcasts oder Nachrichten in normalem Tempo und fasse sie in zwei Sätzen zusammen.",
      uz: "Podkast yoki yangiliklarni oddiy tezlikda tinglang va ikki gapda xulosa qiling.",
    },
    next_hoeren_mid: {
      de: "Höre kurze Durchsagen und Dialoge zweimal und notiere Zahlen, Zeiten und Orte.",
      uz: "Qisqa e'lon va dialoglarni ikki marta tinglang, raqam, vaqt va joylarni yozib boring.",
    },
    next_hoeren_weak: {
      de: "Beginne mit langsamen, kurzen Hörtexten und lies das Transkript erst nach dem Hören mit.",
      uz: "Sekin va qisqa audiolardan boshlang, transkriptni esa faqat tinglagandan keyin o'qing.",
    },
    next_schreiben_strong: {
      de: "Schreibe argumentative Texte mit Einleitung, Begründung und Schluss.",
      uz: "Kirish, asoslash va xulosaga ega argumentativ matnlar yozing.",
    },
    next_schreiben_mid: {
      de: "Schreibe kurze E-Mails und verbinde Sätze mit weil, dass, obwohl.",
      uz: "Qisqa e-mail yozing va gaplarni weil, dass, obwohl bilan bog'lang.",
    },
    next_schreiben_weak: {
      de: "Übe einfache Sätze mit korrekter Verbstellung und schreibe täglich fünf Sätze über deinen Alltag.",
      uz: "Fe'l o'rni to'g'ri bo'lgan oddiy gaplarni mashq qiling va har kuni kundalik hayotingiz haqida 5 ta gap yozing.",
    },
    next_sprechen_strong: {
      de: "Diskutiere Themen und begründe deine Meinung zwei Minuten lang frei.",
      uz: "Mavzularni muhokama qiling va fikringizni ikki daqiqa erkin asoslang.",
    },
    next_sprechen_mid: {
      de: "Nimm dich täglich eine Minute lang auf und höre auf Aussprache und Fehler.",
      uz: "Har kuni bir daqiqa o'zingizni yozib oling va talaffuz hamda xatolarga quloq soling.",
    },
    next_sprechen_weak: {
      de: "Sprich einfache Sätze laut nach (Shadowing) und lerne feste Redemittel für die Vorstellung.",
      uz: "Oddiy gaplarni ovoz chiqarib takrorlang (shadowing) va tanishtirish uchun tayyor iboralarni o'rganing.",
    },
    backToHub: { de: "Zurück zu VIZU-Multilevel", uz: "VIZU-Multilevel ga qaytish" },
    historyTitle: { de: "Frühere Versuche", uz: "Oldingi urinishlar" },
    historyEmpty: { de: "Du hast noch keinen Versuch gestartet.", uz: "Siz hali birorta urinish boshlamadingiz." },
    statusInProgress: { de: "Läuft", uz: "Davom etmoqda" },
    statusCompleted: { de: "Abgeschlossen", uz: "Yakunlangan" },
    continueAttempt: { de: "Fortsetzen", uz: "Davom ettirish" },
    viewResults: { de: "Ergebnisse ansehen", uz: "Natijalarni ko'rish" },
  },

  certificates: {
    title: { de: "Zertifikate", uz: "Sertifikatlar" },
    subtitle: {
      de: "Deine erworbenen Zertifikate und Nachweise",
      uz: "Qo'lga kiritgan sertifikatlaringiz va tasdiqnomalaringiz",
    },
    emptyTitle: { de: "Noch keine Zertifikate", uz: "Hali sertifikat yo'q" },
    emptyBody: {
      de: "Schließe einen Kurs vollständig ab und bestehe den entsprechenden Mock-Test, um dein erstes Zertifikat zu erhalten.",
      uz: "Birinchi sertifikatingizni olish uchun kursni to'liq tugating va tegishli sinov testidan o'ting.",
    },
    verified: { de: "Verifiziert", uz: "Tasdiqlangan" },
  },

  woerterbuch: {
    title: { de: "Wörter suchen", uz: "So'zlarni qidirish" },
    placeholder: { de: "Deutsches Wort eingeben...", uz: "Nemischa so'zni kiriting..." },
    search: { de: "Suchen", uz: "Qidirish" },
    plural: { de: "Plural", uz: "Ko'plik" },
    translation: { de: "Übersetzung", uz: "Tarjima" },
    partOfSpeech: { de: "Wortart", uz: "So'z turkumi" },
    level: { de: "Niveau", uz: "Daraja" },
    example: { de: "Beispielsatz", uz: "Namuna gap" },
    emptyState: { de: "Suche nach einem deutschen Wort.", uz: "Nemischa so'zni qidiring." },
    subtitle: { de: "Vokabeln nachschlagen", uz: "So'zlarni qidirish" },
  },

  profile: {
    title: { de: "Dein Profil", uz: "Sizning profilingiz" },
    pageSubtitle: {
      de: "Verwalte deine persönlichen Angaben",
      uz: "Shaxsiy ma'lumotlaringizni boshqaring",
    },
    personalInfo: { de: "Persönliche Informationen", uz: "Shaxsiy ma'lumotlar" },
    name: { de: "Name", uz: "Ism" },
    email: { de: "E-Mail", uz: "Email" },
    country: { de: "Land", uz: "Mamlakat" },
    interests: { de: "Interessen", uz: "Qiziqishlar" },
    interestsBody: {
      de: "Deine Interessen und dein Ziel-Zertifikat helfen uns, dir passende Aufgaben zu empfehlen. Diese Angaben werden bei der Registrierung erfasst.",
      uz: "Qiziqishlaringiz va maqsad sertifikatingiz sizga mos topshiriqlarni tavsiya etishimizga yordam beradi. Bu ma'lumotlar ro'yxatdan o'tishda kiritiladi.",
    },

    firstName: { de: "Vorname", uz: "Ism" },
    lastName: { de: "Nachname", uz: "Familiya" },
    fullName: { de: "Vollständiger Name", uz: "To'liq ism" },
    phoneNumber: { de: "Telefonnummer", uz: "Telefon raqami" },
    notProvided: { de: "Nicht angegeben", uz: "Kiritilmagan" },
    emailReadOnlyNote: {
      de: "Dies ist deine Anmelde-E-Mail-Adresse und kann nicht geändert werden.",
      uz: "Bu sizning tizimga kirish uchun email manzilingiz va uni o'zgartirib bo'lmaydi.",
    },

    edit: { de: "Bearbeiten", uz: "Tahrirlash" },
    save: { de: "Speichern", uz: "Saqlash" },
    saving: { de: "Wird gespeichert...", uz: "Saqlanmoqda..." },
    cancel: { de: "Abbrechen", uz: "Bekor qilish" },
    saveSuccess: { de: "Änderungen gespeichert.", uz: "O'zgarishlar saqlandi." },
    saveError: {
      de: "Änderungen konnten nicht gespeichert werden.",
      uz: "O'zgarishlarni saqlab bo'lmadi.",
    },

    photo: { de: "Profilbild", uz: "Profil rasmi" },
    uploadPhoto: { de: "Hochladen", uz: "Yuklash" },
    replacePhoto: { de: "Ersetzen", uz: "Almashtirish" },
    removePhoto: { de: "Entfernen", uz: "O'chirish" },
    photoHint: {
      de: "JPG, PNG oder WEBP, maximal 5 MB.",
      uz: "JPG, PNG yoki WEBP, maksimal 5 MB.",
    },
    photoInvalidType: {
      de: "Bitte wähle ein JPG-, PNG- oder WEBP-Bild.",
      uz: "Iltimos, JPG, PNG yoki WEBP formatidagi rasmni tanlang.",
    },
    photoTooLarge: {
      de: "Das Bild darf maximal 5 MB groß sein.",
      uz: "Rasm hajmi 5 MB dan oshmasligi kerak.",
    },
    photoUpdated: { de: "Profilbild aktualisiert.", uz: "Profil rasmi yangilandi." },
    photoRemoved: { de: "Profilbild entfernt.", uz: "Profil rasmi o'chirildi." },

    security: { de: "Sicherheit", uz: "Xavfsizlik" },
    changePassword: { de: "Passwort ändern", uz: "Parolni o'zgartirish" },
    currentPassword: { de: "Aktuelles Passwort", uz: "Joriy parol" },
    newPassword: { de: "Neues Passwort", uz: "Yangi parol" },
    confirmPassword: { de: "Neues Passwort bestätigen", uz: "Yangi parolni tasdiqlang" },
    passwordHint: {
      de: "Mindestens 6 Zeichen.",
      uz: "Kamida 6 ta belgi.",
    },
    passwordChanged: {
      de: "Passwort geändert. Andere angemeldete Geräte wurden abgemeldet.",
      uz: "Parol o'zgartirildi. Boshqa kirilgan qurilmalar tizimdan chiqarildi.",
    },
    wrongCurrentPassword: {
      de: "Das aktuelle Passwort ist falsch.",
      uz: "Joriy parol noto'g'ri.",
    },
    showPassword: { de: "Passwort anzeigen", uz: "Parolni ko'rsatish" },
    hidePassword: { de: "Passwort verbergen", uz: "Parolni yashirish" },

    languageSettings: { de: "Sprache & Einstellungen", uz: "Til va sozlamalar" },
    interfaceLanguage: { de: "Sprache der Oberfläche", uz: "Interfeys tili" },
    languageUpdated: { de: "Sprache aktualisiert.", uz: "Til yangilandi." },

    accountInfo: { de: "Kontoinformationen", uz: "Hisob ma'lumotlari" },
    memberSince: { de: "Registriert seit", uz: "Ro'yxatdan o'tgan sana" },
    accountStatus: { de: "Kontostatus", uz: "Hisob holati" },
    statusActive: { de: "Aktiv", uz: "Faol" },
    statusBanned: { de: "Gesperrt", uz: "Bloklangan" },
    statusSuspended: { de: "Vorübergehend gesperrt", uz: "Vaqtincha bloklangan" },
    statusInactive: { de: "Inaktiv", uz: "Faol emas" },
  },

  settings: {
    title: { de: "Einstellungen", uz: "Sozlamalar" },
    subtitle: {
      de: "Verwalte deine Präferenzen und Benachrichtigungen",
      uz: "Afzalliklaringiz va bildirishnomalaringizni boshqaring",
    },
    notifications: { de: "Benachrichtigungen", uz: "Bildirishnomalar" },
    emailNotifications: { de: "E-Mail-Benachrichtigungen", uz: "Email bildirishnomalari" },
    dailyReminders: { de: "Tägliche Lern-Erinnerungen", uz: "Kunlik o'qish eslatmalari" },
    appearance: { de: "Darstellung", uz: "Ko'rinish" },
    appearanceBody: {
      de: "Das Farbschema lässt sich über den Schalter in der oberen Leiste wechseln.",
      uz: "Rang sxemasini yuqori paneldagi tugma orqali o'zgartirishingiz mumkin.",
    },
    language: { de: "Sprache", uz: "Til" },
    panelSwitcher: { de: "Panel wechseln", uz: "Panel almashtirish" },
    panelSwitcherBody: {
      de: "Wechsle zwischen den Bereichen, auf die dein Konto Zugriff hat.",
      uz: "Hisobingiz kirisha oladigan bo'limlar orasida almashing.",
    },
    panelStudent: { de: "Student-Panel", uz: "Student Panel" },
    panelStudentDesc: { de: "Deine Lektionen und Ergebnisse", uz: "Darslaringiz va natijalaringiz" },
    panelTeacher: { de: "Lehrer-Panel", uz: "Teacher Panel" },
    panelTeacherDesc: { de: "Schüler und Aufgaben", uz: "O'quvchilar va topshiriqlar" },
    panelAdmin: { de: "Admin-Panel", uz: "Admin Panel" },
    panelAdminDesc: { de: "Systemverwaltung", uz: "Tizim boshqaruvi" },
    panelCurrent: { de: "Aktuell", uz: "Joriy" },
  },

  teacher: {
    overviewTitle: { de: "Übersicht", uz: "Umumiy ko'rinish" },
    overviewSubtitle: {
      de: "Deine zugewiesenen Kurse und Schüler auf einen Blick",
      uz: "Sizga biriktirilgan kurslar va o'quvchilar bir qarashda",
    },
    assignedCourses: { de: "Zugewiesene Kurse", uz: "Biriktirilgan kurslar" },
    totalStudents: { de: "Schüler gesamt", uz: "Jami o'quvchilar" },
    myStudents: { de: "Meine Schüler", uz: "Mening o'quvchilarim" },
    myStudentsSubtitle: {
      de: "Schüler aus deinen zugewiesenen Kursen",
      uz: "Sizga biriktirilgan kurslardagi o'quvchilar",
    },
    noStudents: {
      de: "Dir sind noch keine Kurse zugewiesen, oder deine Kurse haben noch keine Schüler.",
      uz: "Sizga hali kurs biriktirilmagan yoki kurslaringizda o'quvchi yo'q.",
    },
    student: { de: "Schüler", uz: "O'quvchi" },
    course: { de: "Kurs", uz: "Kurs" },
    progress: { de: "Fortschritt", uz: "Progress" },
    lastActivity: { de: "Letzte Aktivität", uz: "Oxirgi faollik" },
    neverActive: { de: "Noch keine Aktivität", uz: "Hali faollik yo'q" },
    nav: { de: "Lehrer-Panel", uz: "Teacher Panel" },
    navStudents: { de: "Meine Schüler", uz: "Mening o'quvchilarim" },
    allLevels: { de: "Alle Niveaus", uz: "Barcha darajalar" },
    sourceCourses: { de: "Kurse", uz: "Kurslar" },
    navSchreiben: { de: "Schreiben", uz: "Yozish" },
    navSprechen: { de: "Sprechen", uz: "Gapirish" },
    toGrade: { de: "Zu bewerten", uz: "Baholanishi kerak" },
    newHomework: { de: "Neue Hausaufgaben", uz: "Yangi uy vazifalari" },
    gradedCount: { de: "Bewertet", uz: "Baholandi" },
    avgProgress: { de: "Ø Fortschritt", uz: "O'rtacha progress" },
    homeworkAll: { de: "Alle", uz: "Barchasi" },
    homeworkNew: { de: "Neue", uz: "Yangi" },
    homeworkToGrade: { de: "Zu bewerten", uz: "Baholanishi kerak" },
    homeworkGraded: { de: "Bewertet", uz: "Baholandi" },
    homeworkRevision: { de: "Zur Überarbeitung", uz: "Qayta ishlash" },
    homeworkEmpty: { de: "Keine Abgaben vorhanden.", uz: "Topshiriqlar yo'q." },
    homeworkSelectPrompt: { de: "Wähle eine Abgabe aus der Liste.", uz: "Ro'yxatdan topshiriqni tanlang." },
    homeworkStudentAnswer: { de: "Antwort des Schülers", uz: "O'quvchi javobi" },
    homeworkScore: { de: "Bewertung (0–100)", uz: "Baho (0–100)" },
    homeworkFeedback: { de: "Feedback", uz: "Fikr-mulohaza" },
    homeworkSave: { de: "Speichern", uz: "Saqlash" },
    homeworkMarkGraded: { de: "Als bewertet markieren", uz: "Baholandi deb belgilash" },
    homeworkMarkRevision: { de: "Zur Überarbeitung zurückgeben", uz: "Qayta ishlashga qaytarish" },
    homeworkSaving: { de: "Wird gespeichert...", uz: "Saqlanmoqda..." },
    homeworkSearchPlaceholder: { de: "Nach Name oder E-Mail suchen...", uz: "Ism yoki email bo'yicha qidirish..." },
  },

  lessons: {
    title: { de: "Lektionen", uz: "Darslar" },
    subtitle: { de: "Setze deine Lernreise fort.", uz: "O'quv sayohatingizni davom eting." },
    minutes: { de: "{count} Min.", uz: "{count} daqiqa" },
    loadError: { de: "Lektionen konnten nicht geladen werden.", uz: "Darslarni yuklab bo'lmadi." },
    loadLessonError: { de: "Lektion konnte nicht geladen werden.", uz: "Darsni yuklab bo'lmadi." },

    sectionVideo: { de: "Videokurs", uz: "Video dars" },
    sectionReading: { de: "Lesen", uz: "Lesen" },
    sectionListening: { de: "Hören", uz: "Hören" },
    sectionWriting: { de: "Schreiben", uz: "Schreiben" },
    sectionSpeaking: { de: "Sprechen", uz: "Sprechen" },
    sectionVocabularyQuiz: { de: "Wortschatztest", uz: "Wortschatz Test" },
    sectionLessonQuiz: { de: "Abschlusstest", uz: "Yakuniy Test" },
    sectionResults: { de: "Ergebnisse", uz: "Natijalar" },

    // Schreiben/Sprechen submission awaiting a teacher's grade.
    statusPending: { de: "Wird geprüft", uz: "Tekshirilmoqda" },
    notYetGraded: { de: "Noch nicht bewertet", uz: "Hali baholanmagan" },
    resultsDescription: { de: "Deine Ergebnisse für diese Lektion.", uz: "Ushbu dars bo'yicha natijalaringiz." },
    lessonCompleted: { de: "Lektion abgeschlossen ✓", uz: "Dars yakunlandi ✓" },

    navPrevious: { de: "Zurück", uz: "Orqaga" },
    navNext: { de: "Weiter", uz: "Keyingi" },
    navProgress: { de: "{completed}/{total} abgeschlossen", uz: "{completed}/{total} ta bajarildi" },

    videoDescription: {
      de: "Schau dir das heutige Video aufmerksam an, bevor du fortfährst.",
      uz: "Davom etishdan oldin bugungi videoni diqqat bilan tomosha qiling.",
    },
    videoNotAvailable: {
      de: "Für diese Lektion ist noch kein Video verfügbar.",
      uz: "Bu dars uchun hali video mavjud emas.",
    },
    videoProgressLabel: { de: "Videofortschritt", uz: "Video jarayoni" },
    mediaPlay: { de: "Abspielen", uz: "Ijro etish" },
    mediaPause: { de: "Pausieren", uz: "To'xtatish" },
    mediaSkipBack: { de: "10 Sekunden zurück", uz: "10 soniya orqaga" },
    mediaSkipForward: { de: "10 Sekunden vor", uz: "10 soniya oldinga" },
    mediaMute: { de: "Stummschalten", uz: "Ovozni o'chirish" },
    mediaUnmute: { de: "Stummschaltung aufheben", uz: "Ovozni yoqish" },
    mediaFullscreen: { de: "Vollbild", uz: "To'liq ekran" },
    mediaReplay: { de: "Erneut abspielen", uz: "Qayta ijro etish" },

    videoResumeFrom: { de: "Fortsetzen ab {time}", uz: "{time} dan davom eting" },
    videoCompleted: { de: "Video abgeschlossen", uz: "Video tugallandi" },

    videoSkipBack15: { de: "15 Sekunden zurück", uz: "15 soniya orqaga" },
    videoSkipForward15: { de: "15 Sekunden vor", uz: "15 soniya oldinga" },
    videoSeek: { de: "Videoposition", uz: "Video pozitsiyasi" },
    videoVolume: { de: "Lautstärke", uz: "Ovoz balandligi" },
    videoSettings: { de: "Einstellungen", uz: "Sozlamalar" },
    videoSpeed: { de: "Geschwindigkeit", uz: "Tezlik" },
    videoStreamError: {
      de: "Video konnte nicht geladen werden.",
      uz: "Videoni yuklab bo'lmadi.",
    },
    videoRetry: { de: "Erneut versuchen", uz: "Qayta urinish" },

    premiumRequiredTitle: { de: "🔒 Premium erforderlich", uz: "🔒 Premium talab qilinadi" },
    premiumRequiredHint: {
      de: "Die ersten 3 Lektionen jeder Stufe sind kostenlos. Schalte Premium frei, um auf diese Lektion zuzugreifen.",
      uz: "Har bir darajaning dastlabki 3 ta darsi bepul. Ushbu darsga kirish uchun Premiumni faollashtiring.",
    },



    readingDescription: {
      de: "Lies den Text aufmerksam durch.",
      uz: "Matnni diqqat bilan o'qing.",
    },

    listeningDescription: {
      de: "Höre dir das Audio an und bearbeite die Aufgabe.",
      uz: "Audioni tinglang va topshiriqni bajaring.",
    },
    listeningNotAvailable: {
      de: "Für diese Lektion ist noch kein Audio verfügbar.",
      uz: "Bu dars uchun hali audio mavjud emas.",
    },

    writingDescription: {
      de: "Formuliere deinen eigenen Text auf Deutsch.",
      uz: "O'z matningizni nemis tilida yozing.",
    },
    writingTaskLabel: { de: "Schreibaufgabe", uz: "Yozish topshirig'i" },
    writingMinWords: {
      de: "Mindestens {count} Wörter · frei formulieren",
      uz: "Kamida {count} ta so'z · erkin shaklda",
    },
    writingWordsLabel: { de: "{count} Wörter", uz: "{count} ta so'z" },
    writingWordsRemaining: {
      de: "Noch {count} Wörter bis zur Auswertung",
      uz: "Baholashgacha yana {count} ta so'z kerak",
    },
    writingPlaceholder: {
      de: "Schreibe hier deinen Text auf Deutsch…",
      uz: "Matningizni bu yerga nemis tilida yozing…",
    },
    writingStartEvaluation: { de: "KI-Auswertung starten", uz: "SI bahosini boshlash" },
    writingEvaluating: { de: "Wird ausgewertet…", uz: "Baholanmoqda…" },
    writingReset: { de: "Zurücksetzen", uz: "Qayta boshlash" },
    writingBold: { de: "Fett", uz: "Qalin" },
    writingItalic: { de: "Kursiv", uz: "Qiya" },
    writingUnderline: { de: "Unterstrichen", uz: "Tagiga chizilgan" },
    writingFontLabel: { de: "Schriftart", uz: "Shrift" },
    writingBackgroundLabel: { de: "Hintergrund {label}", uz: "Fon {label}" },
    writingFontSans: { de: "Sans", uz: "Sans" },
    writingFontSerif: { de: "Serif", uz: "Serif" },
    writingFontMono: { de: "Mono", uz: "Mono" },
    writingBgWhite: { de: "Weiß", uz: "Oq" },
    writingBgCream: { de: "Creme", uz: "Krem" },
    writingBgBlue: { de: "Blau", uz: "Ko'k" },
    writingBgMint: { de: "Mint", uz: "Yashil-ko'k" },
    writingBgDark: { de: "Dunkel", uz: "Qorong'i" },
    writingEvaluationError: {
      de: "Die KI-Auswertung ist fehlgeschlagen. Bitte versuche es erneut.",
      uz: "SI bahosi muvaffaqiyatsiz tugadi. Iltimos, qayta urinib ko'ring.",
    },

    speakingDescription: { de: "Übe deine Aussprache.", uz: "Talaffuzingizni mashq qiling." },
    speakingRecord: { de: "Aufnahme starten", uz: "Yozishni boshlash" },
    speakingStop: { de: "Aufnahme stoppen", uz: "Yozishni to'xtatish" },
    speakingPlay: { de: "Abspielen", uz: "Ijro etish" },
    speakingRerecord: { de: "Neu aufnehmen", uz: "Qayta yozish" },
    speakingPermissionDenied: {
      de: "Mikrofonzugriff wurde verweigert. Bitte erlaube den Zugriff in deinem Browser.",
      uz: "Mikrofonga ruxsat berilmadi. Iltimos, brauzeringizda ruxsat bering.",
    },
    speakingNotSupported: {
      de: "Sprachaufnahme wird von diesem Browser nicht unterstützt.",
      uz: "Ovoz yozish bu brauzerda qo'llab-quvvatlanmaydi.",
    },
    speakingStartEvaluation: { de: "KI-Auswertung starten", uz: "SI bahosini boshlash" },
    speakingEvaluating: { de: "Wird ausgewertet…", uz: "Baholanmoqda…" },


    quizDescription: { de: "Überprüfe dein Verständnis.", uz: "Tushunganingizni tekshiring." },
    quizCorrect: { de: "Richtig!", uz: "To'g'ri!" },
    quizIncorrect: { de: "Leider falsch. Versuch es noch einmal.", uz: "Afsuski noto'g'ri. Yana urinib ko'ring." },
    quizCheckAnswer: { de: "Antwort prüfen", uz: "Javobni tekshirish" },
  },

  assessment: {
    title: { de: "KI-Auswertung", uz: "SI bahosi" },
    estimatedLevel: { de: "Geschätztes Niveau:", uz: "Taxminiy daraja:" },
    corrections: { de: "Korrekturen", uz: "Tuzatishlar" },
  },

  notifications: {
    typeInformation: { de: "Information", uz: "Ma'lumot" },
    typeUpdate: { de: "Update", uz: "Yangilanish" },
    typeExam: { de: "Prüfung", uz: "Imtihon" },
    typeCourse: { de: "Kurs", uz: "Kurs" },
    typeSystem: { de: "System", uz: "Tizim" },
    timeJustNow: { de: "Gerade eben", uz: "Hozirgina" },
    timeMinutesAgo: { de: "vor {count} Min.", uz: "{count} daqiqa oldin" },
    timeHoursAgo: { de: "vor {count} Std.", uz: "{count} soat oldin" },
    timeDaysAgo: { de: "vor {count} Tagen", uz: "{count} kun oldin" },
  },

  calendar: {
    title: { de: "Kalender", uz: "Kalendar" },
    subtitle: {
      de: "Deine Lektionen, Prüfungen und Termine im Überblick.",
      uz: "Darslaringiz, imtihonlaringiz va tadbirlaringizga umumiy nazar.",
    },
    today: { de: "Heute", uz: "Bugun" },
    upcoming: { de: "Bevorstehende Aktivitäten", uz: "Yaqinlashib kelayotgan tadbirlar" },
    selectedDay: { de: "Termine an diesem Tag", uz: "Bu kundagi tadbirlar" },
    noEvents: { de: "Keine Termine an diesem Tag.", uz: "Bu kunda tadbirlar yo'q." },
    noUpcoming: {
      de: "Keine bevorstehenden Aktivitäten.",
      uz: "Yaqinlashib kelayotgan tadbirlar yo'q.",
    },
    eventTypeLesson: { de: "Lektion", uz: "Dars" },
    eventTypeExam: { de: "Prüfung", uz: "Imtihon" },
    eventTypePersonal: { de: "Persönlich", uz: "Shaxsiy" },
    eventTypeOther: { de: "Sonstiges", uz: "Boshqa" },
    previousMonth: { de: "Vorheriger Monat", uz: "Oldingi oy" },
    nextMonth: { de: "Nächster Monat", uz: "Keyingi oy" },
    addEvent: { de: "Termin hinzufügen", uz: "Tadbir qo'shish" },
    addEventTitle: { de: "Neuer persönlicher Termin", uz: "Yangi shaxsiy tadbir" },
    eventTitleLabel: { de: "Titel", uz: "Sarlavha" },
    eventTitlePlaceholder: { de: "z. B. Deutsch üben", uz: "masalan, nemis tilida mashq qilish" },
    eventDateLabel: { de: "Datum", uz: "Sana" },
    eventDescriptionLabel: { de: "Beschreibung (optional)", uz: "Tavsif (ixtiyoriy)" },
    save: { de: "Speichern", uz: "Saqlash" },
    cancel: { de: "Abbrechen", uz: "Bekor qilish" },
    deleteEvent: { de: "Termin löschen", uz: "Tadbirni o'chirish" },
    close: { de: "Schließen", uz: "Yopish" },
  },

  informationen: {
    pageSubtitle: {
      de: "Alles Wissenswerte über VIZU Academy und das Team dahinter.",
      uz: "VIZU Academy va uning jamoasi haqida bilishingiz kerak bo'lgan hamma narsa.",
    },
    aboutTitle: { de: "Über das Projekt", uz: "Loyiha haqida" },
    foundedLabel: { de: "Projekt gegründet:", uz: "Loyiha asos solingan:" },
    missionLabel: { de: "Mission:", uz: "Missiya:" },
    missionText: {
      de: "Wir helfen Millionen von Deutschlernenden durch moderne digitale Bildung.",
      uz: "Zamonaviy raqamli ta'lim orqali millionlab nemis tilini o'rganuvchilarga yordam beramiz.",
    },
    authorTitle: { de: "Autor", uz: "Muallif" },
    roleLabel: { de: "Rolle:", uz: "Lavozim:" },
    roleValue: { de: "Projektautor", uz: "Loyiha muallifi" },
    qualificationLabel: { de: "Qualifikation:", uz: "Malaka:" },
    qualificationValue: {
      de: "C1 Deutschsprachexperte",
      uz: "C1 nemis tili bo'yicha mutaxassis",
    },
    authorDescription: {
      de: "Deutschsprachspezialist und Gründer von VIZU Academy.",
      uz: "Nemis tili mutaxassisi va VIZU Academy asoschisi.",
    },
    socialTitle: { de: "Soziale Netzwerke", uz: "Ijtimoiy tarmoqlar" },
    telegramLabel: { de: "Telegram-Link", uz: "Telegram havolasi" },
    instagramLabel: { de: "Instagram-Link", uz: "Instagram havolasi" },
    youtubeLabel: { de: "YouTube-Link", uz: "YouTube havolasi" },
  },

  vizuPay: {
    title: { de: "VIZU Pay", uz: "VIZU Pay" },
    subtitle: {
      de: "Verwalte dein Premium-Abonnement und deine Zahlungen.",
      uz: "Premium obunangiz va to'lovlaringizni boshqaring.",
    },
    error: {
      de: "Zahlungsdaten konnten nicht geladen werden.",
      uz: "To'lov ma'lumotlarini yuklab bo'lmadi.",
    },
    pendingNotice: {
      de: "Deine Bestellung wird geprüft. Das dauert normalerweise nicht lange.",
      uz: "Buyurtmangiz tekshirilmoqda. Odatda bu uzoq davom etmaydi.",
    },

    plansTitle: { de: "Premium-Pläne", uz: "Premium tariflar" },
    plansPopular: { de: "Beliebt", uz: "Mashhur" },
    plansPerMonth: { de: "Monat", uz: "oy" },
    plansFeatureFull: { de: "Voller Zugriff auf alle Kurse", uz: "Barcha kurslarga to'liq kirish" },
    plansFeatureCertificates: { de: "Zertifikate inklusive", uz: "Sertifikatlar kiritilgan" },
    plansFeatureSupport: { de: "Vorrangiger Support", uz: "Ustuvor yordam" },
    plansSelect: { de: "Auswählen", uz: "Tanlash" },

    statusPremium: { de: "Premium aktiv", uz: "Premium faol" },
    statusValidUntil: { de: "Gültig bis {date}", uz: "{date} gacha amal qiladi" },
    statusNoPremium: {
      de: "Du hast derzeit kein aktives Abonnement.",
      uz: "Sizda hozircha faol obuna yo'q.",
    },

    promoRedeemTitle: { de: "Promocode verwenden", uz: "Promokod ishlatish" },
    promoRedeemPlaceholder: { de: "Code eingeben", uz: "Kodni kiriting" },
    promoRedeemButton: { de: "Einlösen", uz: "Faollashtirish" },
    promoRedeemSuccess: {
      de: "Promo-Code eingelöst — Premium ist jetzt aktiv.",
      uz: "Promokod faollashtirildi — Premium endi yoqilgan.",
    },
    promoRedeemError: {
      de: "Promo-Code konnte nicht eingelöst werden.",
      uz: "Promokodni faollashtirib bo'lmadi.",
    },

    statusRejectedTitle: { de: "🔴 Abgelehnt", uz: "🔴 Rad etildi" },
    rejectionReasonLabel: { de: "Ablehnungsgrund", uz: "Rad etish sababi" },
    rejectionAttemptsLabel: { de: "Versuche", uz: "Urinishlar" },
    statusBlockedTitle: { de: "🔒 Zahlungseinreichung gesperrt", uz: "🔒 Bloklangan" },
    statusBlockedBody: {
      de: "Deine Zahlungsanfrage wurde 3 Mal abgelehnt. Bitte kontaktiere den Support.",
      uz: "3 marta rad etilgan. Yangi to'lov so'rovi yuborish mumkin emas. Iltimos, qo'llab-quvvatlash xizmatiga murojaat qiling.",
    },
    checkoutBlockedError: {
      de: "Zahlungseinreichung ist nach drei Ablehnungen gesperrt. Bitte kontaktiere den Support.",
      uz: "Uch marta rad etilgandan so'ng to'lov yuborish bloklangan. Iltimos, qo'llab-quvvatlash xizmatiga murojaat qiling.",
    },
    checkoutPendingError: {
      de: "Deine Zahlungsanfrage wird bereits geprüft.",
      uz: "Sizning to'lov so'rovingiz allaqachon ko'rib chiqilmoqda.",
    },

    paymentCardsTitle: { de: "Zahlungskarten", uz: "To'lov kartalari" },
    paymentCardCopy: { de: "Kopieren", uz: "Nusxalash" },
    paymentCardCopied: { de: "Kopiert!", uz: "Nusxalandi!" },
    paymentInstructions: {
      de: "Führe die Zahlung über deine Banking-App oder am Geldautomaten durch und lade danach den Zahlungsbeleg hoch.",
      uz: "To'lovni ilovalardan yoki bankomatlardan amalga oshiring va chekni yuboring.",
    },

    checkoutFirstName: { de: "Vorname", uz: "Ism" },
    checkoutLastName: { de: "Nachname", uz: "Familiya" },
    checkoutPhone: { de: "Telefonnummer", uz: "Telefon raqami" },
    checkoutPaymentMethod: { de: "Zahlungsmethode", uz: "To'lov usuli" },
    checkoutPromoCode: { de: "Rabatt-Code (optional)", uz: "Chegirma kodi (ixtiyoriy)" },
    checkoutPromoPlaceholder: { de: "Code eingeben", uz: "Kodni kiriting" },
    checkoutApply: { de: "Anwenden", uz: "Qo'llash" },
    checkoutPromoApplied: { de: "Promo-Code angewendet.", uz: "Promo kod qo'llandi." },
    checkoutProof: { de: "Zahlungsnachweis", uz: "To'lov isboti" },
    checkoutProofUpload: { de: "Screenshot oder PDF hochladen", uz: "Skrinshot yoki PDF yuklang" },
    checkoutProofRequired: { de: "Bitte lade einen Zahlungsnachweis hoch.", uz: "Iltimos, to'lov isbotini yuklang." },
    checkoutProofHint: { de: "JPG, PNG, WEBP oder PDF, max. 10 MB.", uz: "JPG, PNG, WEBP yoki PDF, maks. 10 MB." },
    checkoutProofTooLarge: {
      de: "Die Datei ist zu groß (max. 10 MB).",
      uz: "Fayl hajmi juda katta (maks. 10 MB).",
    },
    checkoutSubtotal: { de: "Zwischensumme", uz: "Oraliq summa" },
    checkoutDiscount: { de: "Rabatt", uz: "Chegirma" },
    checkoutTotal: { de: "Gesamt", uz: "Jami" },
    checkoutSubmit: { de: "Bestellung einreichen", uz: "Buyurtmani yuborish" },
    checkoutSubmitError: {
      de: "Bestellung konnte nicht übermittelt werden. Bitte versuche es erneut.",
      uz: "Buyurtmani yuborib bo'lmadi. Iltimos, qayta urinib ko'ring.",
    },

    historyTitle: { de: "Zahlungsverlauf", uz: "To'lovlar tarixi" },
    historyEmpty: { de: "Noch keine Bestellungen.", uz: "Hozircha buyurtmalar yo'q." },
  },
};
