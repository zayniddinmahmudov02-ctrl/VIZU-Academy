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
    a2: { de: "Grundlegend", uz: "Asosiy" },
    b1: { de: "Mittelstufe", uz: "O'rta daraja" },
    b2: { de: "Fortgeschritten", uz: "Yuqori daraja" },
    c1: { de: "Kompetent", uz: "Malakali" },
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
    lessonsAvailable: { de: "{count} Unterricht verfügbar", uz: "{count} ta dars mavjud" },
    progressLabel: { de: "Fortschritt", uz: "Taraqqiyot" },
    jetztStarten: { de: "Jetzt starten", uz: "Hozir boshlash" },
    lessonsCount: { de: "{count} Unterricht", uz: "{count} ta dars" },
    quickAccess: { de: "Schnellzugriff", uz: "Tezkor kirish" },
    mockExams: { de: "Mock Exams", uz: "Mock Exams" },
    mockExamsSubtitle: { de: "Teste dein Wissen", uz: "Bilimingizni sinang" },
    woerterbuchSubtitle: { de: "Vokabeln nachschlagen", uz: "So'zlarni qidirish" },
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
  },

  lessons: {
    title: { de: "Lektionen", uz: "Darslar" },
    subtitle: { de: "Setze deine Lernreise fort.", uz: "O'quv sayohatingizni davom eting." },
    minutes: { de: "{count} Min.", uz: "{count} daqiqa" },
    loadError: { de: "Lektionen konnten nicht geladen werden.", uz: "Darslarni yuklab bo'lmadi." },
    loadLessonError: { de: "Lektion konnte nicht geladen werden.", uz: "Darsni yuklab bo'lmadi." },

    sectionVideo: { de: "Video", uz: "Video" },
    sectionGrammar: { de: "Grammatik", uz: "Grammatika" },
    sectionVocabulary: { de: "Wortschatz", uz: "Lug'at" },
    sectionReading: { de: "Lesen", uz: "O'qish" },
    sectionListening: { de: "Hören", uz: "Tinglash" },
    sectionWriting: { de: "Schreiben", uz: "Yozish" },
    sectionSpeaking: { de: "Sprechen", uz: "Gapirish" },
    sectionHomework: { de: "Hausaufgabe", uz: "Uy vazifasi" },
    sectionQuiz: { de: "Quiz", uz: "Test" },

    navPrevious: { de: "Zurück", uz: "Orqaga" },
    navNext: { de: "Weiter", uz: "Keyingi" },
    navMarkComplete: { de: "Als abgeschlossen markieren", uz: "Bajarilgan deb belgilash" },
    navCompleted: { de: "Abgeschlossen", uz: "Bajarildi" },
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

    sectionLocked: {
      de: "🔒 Schließe zuerst das Video ab.",
      uz: "🔒 Avval videoni tugating.",
    },
    sectionLockedHint: {
      de: "Diese Aktivität wird freigeschaltet, sobald du das Video abgeschlossen hast.",
      uz: "Bu mashg'ulot videoni tugatgach ochiladi.",
    },
    premiumRequiredTitle: { de: "🔒 Premium erforderlich", uz: "🔒 Premium talab qilinadi" },
    premiumRequiredHint: {
      de: "Die ersten 3 Lektionen jeder Stufe sind kostenlos. Schalte Premium frei, um auf diese Lektion zuzugreifen.",
      uz: "Har bir darajaning dastlabki 3 ta darsi bepul. Ushbu darsga kirish uchun Premiumni faollashtiring.",
    },

    grammarDescription: {
      de: "Lerne die heutigen Grammatikregeln und Beispiele.",
      uz: "Bugungi grammatika qoidalari va misollarni o'rganing.",
    },
    grammarTopicTitle: { de: "Personalpronomen", uz: "Shaxs olmoshlari" },
    grammarExampleLabel: { de: "Beispiel", uz: "Misol" },

    vocabularyDescription: {
      de: "Lerne die neuen Wörter von heute.",
      uz: "Bugungi yangi so'zlarni o'rganing.",
    },
    vocabularyMarkLearned: { de: "Als gelernt markieren", uz: "O'rganilgan deb belgilash" },
    vocabularyLearned: { de: "Gelernt", uz: "O'rganildi" },
    vocabularyPlayAudio: { de: "Aussprache anhören", uz: "Talaffuzni tinglash" },

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

    homeworkDescription: {
      de: "Schließe die heutige Hausaufgabe ab.",
      uz: "Bugungi uy vazifasini bajaring.",
    },
    homeworkBody: {
      de: "Nimm eine kurze Selbstvorstellung auf und schreibe 5 Sätze über dich.",
      uz: "Qisqacha o'zingiz haqingizda tanishtiruv yozib oling va o'zingiz haqingizda 5 ta gap yozing.",
    },

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
