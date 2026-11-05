# Module registry

Updated 2026-11-01 · checked against the repo (Wortschatz / Lesen / Schreiben: A2 module separation; see `current-state.md`).
Sources: directory listings of `backend/app/{api,services,models}`, `frontend/src/{app,features,components}`,
`backend/tests`, `app/main.py`, `core/security/roles.py`, and the files named below.
`(?)` = not checked in code yet — verify before relying on it. Paths: `be/` = `backend/app/`, `fe/` = `frontend/src/`.
API prefixes are listed without `/api/v1` (every router is mounted bare and under `/api/v1`).

## 1. Authentication & Users

- **Purpose:** register/login by email or phone, JWT access + refresh tokens, "remember me", session
  revocation, Telegram login, login history, rate limiting, profile/settings.
- **Backend:** `be/api/auth/router.py` (`/auth`), `be/api/users/router.py` (`/users`),
  `be/api/admin/users_router.py` (`/admin/users`); services `be/services/auth/{service,identifier,rate_limit}.py`;
  deps `be/api/dependencies/auth.py`; roles `be/core/security/roles.py`.
- **Tables:** `users`, `refresh_tokens`, `login_history`, `auth_rate_limit_events`, `user_languages`, `user_tags`.
- **Frontend:** `fe/app/(auth)/{login,register,forgot-password,reset-password}`, `fe/features/auth/`,
  `fe/features/profile/`, settings `fe/app/(dashboard)/settings`. Profile photo: `POST /users/me/photo` (+ optional square crop `crop_x/y/size`)
  → `be/services/profile_photo.py` (Pillow decode, type = declared MIME, ≥96 px, EXIF orientation, 512×512 WebP, random name in
  `uploads/avatars/`); browser cropper `fe/features/profile/{components/photo-cropper.tsx,utils/photo-crop.ts}`; `DELETE /users/me/photo`.
  The same photo is the Battle player picture.
- **Tests:** `test_auth*`, `test_remember_me`, `test_session_revocation`, `test_login_email_case_insensitive`,
  `test_telegram_login`, `test_telegram_init_data_validation`, `test_route_protection`, `test_security_hardening`, `test_profile_photo`.
- **Rules:** admin panel login needs the second factor `SUPER_ADMIN_VERIFICATION_PASSWORD`
  (`docs/super-admin-verification-secret.md`); token storage plan `docs/auth-token-storage-plan.md`.
- **Issues:** `SUPER_ADMIN_VERIFICATION_PASSWORD` not set on production (see known-issues).

## 2. LMS & Digital Courses

- **Purpose:** the A1–C1 course system: levels, lessons, 10 competencies per lesson, resources, lock/unlock,
  purchase gate. Architecture doc: `docs/lms-architecture.md`.
- **Backend:** `be/api/lms/router.py` (`/lms`), `be/api/lms/admin_router.py` (`/admin/lms`); services
  `be/services/lms/{structure,access,progress,resources,grammar_text_only}.py`; content import
  `be/api/content_import/router.py` (`/admin/content-import`) + `be/services/content_import/`.
  Legacy CRUD still mounted: `/courses`, `/modules`, `/lessons`, `/languages`.
- **Tables:** `courses`, `modules`, `lessons`, `lesson_competencies`, `learning_resources`,
  `student_competency_progress`, `content_imports`, `kompetenzen`.
- **Frontend:** student `fe/app/(dashboard)/kurse/[level]`, `fe/app/(dashboard)/lektion/[lessonId]/[kompetenz]`,
  `fe/components/lms/*`, `fe/features/lms/services/lms-service.ts`; admin `fe/app/admin/{lms,kurse,levels,lessons,modules}`,
  `fe/features/admin/components/{lms,lms-course}/`.
- **Tests:** `test_lms_unit`, `test_lms_multilevel`, `test_lms_visit_race`, `test_lesson*`, `test_section_*`.
- **Rules:** `LEVEL_LESSON_COUNTS` A1 14 · A2 14 · B1 20 · B2 30 · C1 22; `COMPETENCY_ORDER` EINFUEHRUNG,
  WORTSCHATZ, GRAMMATIK, LESEN, HOEREN, SPRECHEN, SCHREIBEN, UEBUNGEN, ABSCHLUSSTEST, ZUSAMMENFASSUNG.
  Draft lesson → 404, locked → 403 `LESSON_LOCKED`. A competency with no published content does not count.
- **Depends on:** Payments (access), Progress, every skill module.

## 3. A1–C1 courses (content)

- **Purpose:** the book content per level, generated from Python sources and imported idempotently.
- **Sources:** `be/scripts/vizu_deutsch_a1/` (A1, "modul_NN"), `be/scripts/vizu_deutsch_a2/` (A2 first edition,
  now `[Archiv]` on production), `be/scripts/vizu_deutsch_a2_buch/` (A2 book edition: `DROP`, `FIXES`),
  `be/scripts/vizu_deutsch_b1/`; built JSON in `be/data/vizu_deutsch_*`; importers
  `be/scripts/import_vizu_deutsch_a1.py` (`--level A1|A2|B1`), `import_vizu_deutsch_a2_buch.py`.
- **Keys/audit scripts:** `a1_hoeren_keys(_data).py`, `a2_keys(_data).py`, `a2_audio_processing(_data).py`.
- **Tests:** `test_vizu_a1_*`, `test_a2_buch_edition`, `test_a2_keys`, `test_a1_hoeren_keys`.
- **Rules:** content ids `vizu-a1-…`, `vizu-a2-…` (archived), `vizu-a2buch-…`, `vizu-b1-…`; re-import skips
  existing ids. B2/C1: structure only (?). A2 state: `docs/a2-publishing-report.md`.

## 4. Grammatik

- **Backend:** `be/services/lms/grammar_text_only.py` = rule "Grammatik is text only" (student APIs drop
  images of the Grammatik competency, admin refuses new images); exercises = `skill_exercises` with
  skill GRAMMATIK (`be/services/lesson_skills/exercises.py`, `/lesson-skills/{lesson}/…` exercise routes);
  legacy `be/api/grammar/router.py` (`/grammars`, table `grammars`).
- **Frontend:** `fe/components/lesson-player/grammar/`, admin `fe/features/admin/components/lesson-skills/grammar-manager.tsx`,
  `exercise-manager.tsx`.
- **Tests:** `test_lesson_skills`, `test_skill_applicable_duplicate_assessment` (?).

## 5. Wortschatz

- **Backend:** content arrives through the import: item `skill: "wortschatz"` (`words`, `exercises`,
  `auto_practice`) in `be/services/content_import/service.py` (preview ~l.508, `practice_sets()` builds the
  automatic sets) → `vocabularies` rows + `skill_exercises` with skill WORTSCHATZ (`models/lesson_skill.py`,
  served generically by `be/services/lesson_skills/exercises.py` via `EXERCISE_SKILLS` →
  `GET /lesson-skills/{lesson}/{skill_slug}`); competency ↔ slug map `be/services/lms/progress.py` (~l.61).
  Book editions: `vizu_deutsch_a2_buch._normalise` sets `auto_practice=False` and `DROP` removes handout lists.
  Lesson words API `be/api/vocabularies/router.py` (`/vocabularies`, `be/services/vocabulary/service.py`); Wörterbuch
  (dictionary) `be/api/dictionary/router.py` (`/dictionary`, tables `dictionary_entries`, `dictionary_user_words`),
  import `be/scripts/import_woerterbuch.py`, CSVs `docs/*-words.csv`, audits `docs/woerterbuch-*.md`.
- **Student dictionary + tests (2026-11-01):** `be/services/lesson_skills/wortschatz.py` (lesson words as dictionary,
  enrichment from VERIFIED Wörterbuch entries with the same article + lemma, `missing_fields`, saved/learned in
  `vocabulary_user_words`), `GET /lesson-skills/{lesson}/wortschatz/words[?scope=level]`, `PUT …/words/{id}/state`;
  tests generator `be/services/lesson_skills/wortschatz_tests.py` (7 types → WORTSCHATZ `skill_exercises`, source `vizu`,
  content_id `vizu-a2buch-lNN-wortschatz-test-<type>`); admin CSV `be/services/lesson_skills/word_csv.py`
  (`GET /admin/lesson-skills/lessons/{id}/words.csv`, `POST …/words/import`). Data step: `be/scripts/a2_module_separation.py`.
- **Frontend:** LMS page `fe/components/lesson-player/vocabulary/wortschatz-section.tsx` — since 2026-11-05 only two tabs,
  Lug'at/Wörterbuch and Testlar/Tests (generated tests + book Wortschatz sets + written Wortschatz tasks); word cards
  ("Bilaman") removed. `word-dictionary.tsx`, filter `fe/features/lessons/utils/wortschatz-filter.ts`, service
  `wortschatz-service.ts`; legacy route still `vocabulary-section.tsx`; `fe/app/(dashboard)/woerterbuch`, `fe/features/woerterbuch/`;
  admin `lesson-skills/word-manager.tsx` (fields, missing, CSV) + Wortschatz-Aufgaben via `WritingManager competency`.
- **Tests:** `test_woerterbuch`, `test_a2_module_separation`; unit `wortschatz-filter.test.mjs`; E2E `a2-module-separation.spec.ts`.
- **Rules:** never overwrite the book's word / article / translation; never use a `needs_review` entry; "die" + plural == word
  = plural form (no Artikel / Plural question). Written Wortschatz worksheets are `writings.competency = WORTSCHATZ`.
- **A2:** words L1 60 · L2 40 · L3 60 · L4 50 · L9 6 (L5–8, L10–13: book page has no translated list); L9 "translations" are
  German explanations (book).

## 6. Lesen

- **Backend:** `readings`, `reading_questions`, `reading_options` (legacy CRUD `/readings`, `/reading-questions`,
  `/reading-options`); student test `be/api/lesson_skills/router.py` `GET/POST /lesson-skills/{lesson}/lesen…`,
  grading `be/services/lesson_skills/skill_tests.py`; keys reviewed in Lösung.
- **Frontend:** `fe/components/lesson-player/reading/`, `skill-test/`; admin `lesson-skills/lesen-manager.tsx`.
- **Rules:** one Lesen test per lesson (all published texts); key in `reading_options.is_correct`. Open questions on a text =
  `writings.competency = LESEN` (shown on the Lesen page, counted in `lesen`, AI checks them against the lesson's reading texts,
  `ai_evaluation.lesen_source_text`), never in Schreiben.

## 7. Hören

- **Backend:** `listenings` (+ `listening_questions`, `listening_options`, `listening_audio_tracks`,
  `listening_audio_archives`); student `GET /lesson-skills/{lesson}/hoeren`, `/hoeren/{id}/audio`,
  `/audio-tracks/{track}`, start/submit/review; admin audio/questions `be/api/lesson_skills/admin_router.py`
  (`/admin/lesson-skills`), `be/services/lesson_skills/admin.py`; A1 answer PDF `/admin/hoeren-a1`
  (`be/services/lesson_skills/hoeren_pdf_import.py`); Lösung `/admin/loesung` (`be/services/lesson_skills/loesung.py`).
- **Frontend:** `fe/components/lesson-player/listening/listening-section.tsx`, `listening-player.tsx`;
  admin `lesson-skills/hoeren-manager.tsx`, Media Management (module 10).
- **Rules:** published + audio on disk → visible; transcript shown after the first submitted attempt
  (at once without questions); publish needs every key VERIFIED (`hoeren_pdf_import.readiness`).
  Tasks without questions do not count in results. `task_key` marks managed tasks (A2 L4 Text 1–3).
- **Tests:** `test_lesson_skills`, `test_hoeren_pdf_import`, `test_loesung`, `test_a2_*`.

## 8. Schreiben

- **Backend:** tasks `writings` (`/writings`), submissions `student_writings` (`/student-writings`),
  AI evaluation `be/services/lesson_skills/ai_evaluation.py` (history `ai_evaluations`), auto-graded
  practice = `skill_exercises` skill SCHREIBEN; teacher review via `/teacher`. Exam-style writing tables
  (`writing_tasks`, `writing_submissions`, `writing_evaluations`, `writing_rubric_criteria`) belong to the
  assessment engine (?).
- **Competency of a writing (2026-11-01):** `writings.competency` NULL/SCHREIBEN · GRAMMATIK · WORTSCHATZ · LESEN
  (`models/writing.py:writing_competency_filter`); `GET /writings/lesson/{id}?competency=` defaults to Schreiben;
  `results.py` counts each task in its own competency; legacy `section_gate` / `lesson_scoring` count Schreiben only.
- **Analysis:** A2 rubric = 7 criteria (`levels.py` WRITING_RUBRICS A2: task, grammar, vocabulary, sentence, spelling,
  coherence, structure); other competencies use `levels.COMPETENCY_RUBRICS`; result has per-criterion `tip`, errors with
  `criterion`, `weaknesses`, `improved_text` (AI-written, labelled), `next_practice`. Every final submission's text is kept in
  `student_writing_versions`; every run / teacher decision in `ai_evaluations` (with `attempt_number`); student history
  `GET /writings/{id}/submissions/me/history`; `teacher_reviewed` = AI vs teacher badge. AI failure → EVALUATION_FAILED, no score.
- **Frontend:** `fe/components/lesson-player/writing/` (`writing-section.tsx` `competency` prop, `writing-history.tsx`),
  `common/ai-evaluation-card.tsx`, teacher `fe/app/teacher/schreiben`, admin `fe/app/admin/writing`, `managers/writing-manager.tsx`
  (Kompetenz select / column / `competency` filter in the LMS competency panel).
- **Tests:** `test_writing_speaking_submission_rbac_and_idor`, `test_vizu_mock_schreiben_*`, `test_a2_module_separation`.

## 9. Sprechen

- **Backend:** `speakings` (`/speakings`, `task_kind` SPRECHEN/FRAGE), `student_speakings` (`/student-speakings`),
  AI evaluation as Schreiben; speech-to-text `be/services/speech/speech_to_text_service.py`.
- **Frontend:** `fe/components/lesson-player/speaking/`, teacher `fe/app/teacher/sprechen`, admin `fe/app/admin/speaking`.
- **Rules:** recorder cap 300 s (`vizu_deutsch_a2_buch.RECORDER_CAP_SECONDS`); recordings are private uploads.

## 10. Media Management

- **Purpose:** one admin page for videos and Hören audio of all levels; A2 Audio Manager (library, manifest,
  links, readiness); A2 4. Unterricht Text 1–3; A2 audio processing (transcripts, match, keys, publish).
- **Backend:** `be/api/admin/media_management_router.py` (`/admin/media-management`: `/tree`, `/items`,
  `/a2-audio*`, `/a2/lesson-4/hoeren*`, `/a2-readiness*`); services `be/services/a2_audio/{assets,filename,
  lesson4_hoeren,processing,readiness,cleanup}.py`; video `be/api/admin/videos_router.py` (`/admin/videos`),
  `be/services/video/`; legacy `/media-library`, `/upload`.
- **Tables:** `a2_audio_assets`, `a2_audio_transcripts`, `videos`, `video_upload_sessions`, `media_assets`, `listening_*`.
- **Frontend:** `fe/app/admin/media-management/{page,hoeren-a1,a2/lesson-4/hoeren}`,
  `fe/features/admin/components/media-management/` (`media-management-client`, `a2-audio-manager`,
  `a2-audio-processing`, `a2-lesson4-hoeren-client`, `audio-slots-panel`), service `media-management-service.ts` (BOM).
- **Scripts:** `a2_audio_processing`, `a2_lesson4_hoeren`, `a2_audio_cleanup`, `a2_audio_manifest`, `a2_audio_inventory`.
- **Tests:** `test_a2_audio_manager`, `test_a2_audio_management`, `test_a2_lesson4_hoeren`, `test_a2_audio_processing`,
  `test_video*`; E2E `a2-*.spec.ts`. Skill: `vizu-media`.

## 11. Payments & Promotions (VIZU Pay)

- **Backend:** `be/api/vizu_pay/router.py` (`/vizu-pay`), `be/api/admin/vizu_pay_router.py` (`/admin/vizu-pay`);
  services `be/services/vizu_pay/{offers,access,service,admin_service,gateways,plans,purchases}.py`.
  Legacy `/payments` (`be/api/payment`, `be/services/payment/`): no other backend module imports it; the
  admin frontend still lists it in `fe/features/admin/constants/endpoints.ts` — treat as legacy, VIZU Pay is
  the live flow.
- **Tables:** `subscription_orders`, `promo_codes`, `promo_code_redemptions`, `app_settings` (key `angebote`).
- **Frontend:** `fe/app/(dashboard)/{vizu-pay,angebote}`, `fe/features/vizu-pay/`; admin `fe/app/admin/{angebote,payments,premium-users}`.
- **Rules:** price source `offers.py` (+ admin overrides in `app_settings.angebote`, sale per level needs a price);
  manual gateway: student uploads a receipt, SUPER_ADMIN approves; one PENDING order per user; access =
  APPROVED + within `access_*_date` (`access.owned_levels`); only lesson 1 of each course is free
  (`offers.free_lessons()`; some older docstrings still say "first 3" — outdated).
- **Tests:** `test_angebote`, `test_promo_*`, `test_admin_purchase_analytics`, `test_course_access_terms`.

## 12. Admin CMS

- **Backend:** `be/api/admin/router.py` (`/admin`), page registry `be/api/admin/page_management_router.py`
  + `be/services/page_management.py`, notifications `/admin/notifications`, support `/admin/support`,
  advertisements `/admin/advertisements`, achievements `/admin/achievements`, books `/admin/books`,
  certificates `/admin/zertifikate`, dashboard `be/services/admin/enterprise_dashboard_service.py`.
- **Frontend:** `fe/app/admin/*` (see frontend-map), `fe/features/admin/{components,services}`, `fe/components/admin/`.
- **Rules/tests:** see skill `vizu-admin`; `test_page_management`, `test_notifications_support`, `test_advertisement`.

## 13. Teacher Dashboard

- **Backend:** `be/api/teacher/router.py` (`/teacher`, `require_teacher_panel_access` = TEACHER or SUPER_ADMIN),
  `be/services/teacher/{scope,service,vizu_multilevel_*_review_service}.py`; assignments
  `/admin/teacher-assignments` (`teacher_assignments`).
- **Frontend:** `fe/app/teacher/{groups,schreiben,sprechen,students}`, `fe/features/teacher/`.
- **Tests:** `test_teacher_panel_rbac`, `test_teacher_scope`.

## 14. Groups & Classroom

- **Backend:** `be/api/study_groups/router.py` (`/groups`), `be/services/study_groups/{access,chat,codes,groups,notify,progress,scope}.py`.
- **Tables:** `study_groups`, `study_group_courses`, `study_group_members`, `study_group_join_codes`,
  `study_group_messages`, `study_group_announcements`, `study_group_tasks`, `study_group_audit_logs`.
- **Frontend:** `fe/app/(dashboard)/groups`, `fe/app/teacher/groups`, `fe/app/admin/groups`, `fe/features/groups/components/`.
- **Doc:** `docs/groups-classroom.md` (2026-10-28 said "not on production"; production state (?)).
- **Tests:** `test_study_groups`.

## 15. Global Chat

- **Backend:** `be/api/global_chat/router.py` (`/global-chat`, `/admin/global-chat`), `be/services/global_chat/
  {messages,access,restrictions,word_filter}.py`. Tables: `global_chat_messages` (+`reply_to_id`),
  `global_chat_message_edits`, `global_chat_restrictions`, `global_chat_moderation_actions`, `global_chat_reads`.
- **Frontend:** `fe/features/global-chat/`, admin `fe/app/admin/global-chat`.
- **Docs/tests:** `docs/global-chat.md`, `docs/audit/global-chat-reply.md`; `test_global_chat*`, E2E `global-chat*.spec.ts`.
  Skill: `vizu-chat`.

## 16. Progress & Scoring

- **Backend:** lesson completion `be/services/learning/{lesson_progress,unlock}.py`
  (`refresh_lesson_completion`), LMS competency progress `be/services/lms/progress.py`, skill results
  `be/services/lesson_skills/results.py`, lesson score `be/services/lesson_scoring/service.py`, section gate
  `be/services/lesson_progress/section_gate.py`, video progress `/videos/...` (`video_progress`), legacy
  `/student-progress`; achievements `be/services/achievements.py` + `be/services/learning/achievement/` + `/achievements`.
- **Tables:** `lesson_skill_attempts`, `student_competency_progress`, `student_progress`, `video_progress`,
  `learning_activity`, `user_achievements`.
- **Tests:** `test_refresh_lesson_completion`, `test_lesson_scoring_new_flow`, `test_section_gate_dynamic`,
  `test_video_progress_threshold`, `test_learning_activity_achievements`, `test_dashboard_current_lesson`.
- **Rules:** Lesen/Hören graded on the server; best score counts; attempts never touched by scripts.

## 17. Database & Alembic

See `database-map.md` and `.claude/rules/database.md`.

## 18. Frontend & UI

See `frontend-map.md` and `.claude/rules/frontend.md`. PWA: `fe/features/pwa`, `fe/components/pwa`,
`frontend/scripts/verify-pwa.mjs`; i18n `fe/lib/i18n/translations.ts`.

## 19. Production Deployment

See `deployment-map.md`, skill `vizu-deploy`, `docs/deploy-frontend.md`, `docs/lms-deploy-runbook.md`.

## 20. VIZU DEUTSCH BATTLE

- **Backend:** `be/api/battle/router.py` (`/battle`, `/admin/battle`), `be/services/battle/*` (engine, questions, media,
  themes, admin, commons, seed). Tables `battle_profiles`, `battle_words`, `battle_images`, `battle_matches`,
  `battle_answers`, `battle_points_ledger`, `battle_themes`. Seed `be/scripts/battle_seed.py` + `be/data/battle/`.
- **Frontend:** `fe/app/(battle)/battle/*`, `fe/features/battle/*`, admin `fe/app/admin/battle` (Übersicht, Wörter & Bilder,
  Design & Themes); entry points: dashboard tile `fe/components/dashboard/home/battle-banner.tsx` (`GET /battle/summary`), first card of
  "Lernwerkzeuge" (`learning-tools.tsx`, with Stufe Bestimmung / Wortschatz / Zertifikatsprüfungen; dashboard order:
  welcome → compact Werbung banner → Lernwerkzeuge → ONE collapsible "A1–C1 Kurse" frame (`dashboard-courses.tsx`, open by
  default) → compact Lernserie; Erfolge/Zertifikate cards not on the dashboard; E2E `dashboard-layout.spec.ts`),
  sidebar + mobile nav with the custom icon `fe/components/icons/battle-icon.tsx` (favicon `fe/public/battle/battle-icon.svg`).
- **Tests:** `test_battle`, `test_battle_migration`, unit `battle-utils.test.mjs`, E2E `battle.spec.ts`, `battle-dashboard.spec.ts`.
- **Details / decisions:** `docs/ai-context/battle-overview.md`.

## 21. Mobile App (Android APK + iOS PWA)

- **Overview / decisions:** `docs/ai-context/mobile-app-overview.md` (start here; links the other `mobile-*`, `android-capacitor`,
  `ios-pwa`, `apk-release-management` docs).
- **Android shell:** `mobile/` (Capacitor 8, `com.vizu.deutsch`, loads <https://vizu-deutsch.com>; `MainActivity.java` download
  listener; icons from `mobile/assets/vizu-mark.svg` via `npm run assets`).
- **Backend:** `be/api/app_releases/router.py` (`/app`, `/admin/app-releases`), `be/services/app_releases/{apk,service}.py`,
  table `app_releases`.
- **Frontend:** `/download` (`fe/app/download`, `fe/features/mobile-app/*`), admin `fe/app/admin/app-management`, update prompt
  `fe/components/pwa/native-app-update.tsx`, manifest `fe/app/manifest.ts`, service worker `fe/public/sw.js`.
- **Tests:** `test_app_releases`, `test_app_releases_migration`, unit `mobile-platform.test.mjs`, E2E `mobile-app.spec.ts`.

## Other mounted modules (not in the list above)

VIZU-Multilevel level test (student UI name "Stufe Bestimmung" since 2026-11-05; code, routes, APIs and admin keep
"VIZU-Multilevel"; `/vizu-multilevel`, legacy alias `/vizu-mock`, `be/services/vizu_multilevel/`,
`fe/app/(dashboard)/vizu-multilevel`), Vorbereitung mock exams (`/mock-exam*`, `be/services/mock_exam/`,
`fe/app/(dashboard)/vorbereitung`; Multilevel Modelltest 1–10 import, keys, source PDF, publish guard:
`be/services/mock_exam/multilevel_service.py`, `scripts/multilevel_import.py`, `docs/multilevel-modelltests.md`), assessment engine (`be/api/assessment_engine`), certificates
(`/certificates`, `/my-certificates`), books (`/books`), homework (`/homeworks`), quizzes, exams, calendar,
notifications, support, advertisements ("Werbung-Banner"), achievements.
