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
- **Tests:** `test_lms_unit`, `test_lms_multilevel`, `test_lms_visit_race`, `test_lesson*` (incl.
  `test_lesson_purchase_gating`), `test_section_*`; E2E `lesson-gating.spec.ts`.
- **Rules:** `LEVEL_LESSON_COUNTS` A1 14 · A2 14 · B1 20 · B2 30 · C1 22; `COMPETENCY_ORDER` EINFUEHRUNG,
  WORTSCHATZ, GRAMMATIK, LESEN, HOEREN, SPRECHEN, SCHREIBEN, UEBUNGEN, ABSCHLUSSTEST, ZUSAMMENFASSUNG.
  Draft lesson → 404, locked → 403 `LESSON_LOCKED`. A competency with no published content does not count.
- **Purchase gate (one place):** `lms/access.lesson_access` → `vizu_pay/access.can_access_lesson`; every lesson-content
  endpoint (`require_lesson_access` / `ensure_lesson_open`), video + resource stream tokens and the legacy
  `/quiz-questions` `/quiz-options` lists (`services/quiz/student_view.py`) use it. First lesson of a released level free
  (`free_lessons`, card `free` → "Bepul"); lesson 2+ → 403 `PREMIUM_REQUIRED` unless an APPROVED, unexpired order covers
  the level (A1–C1 snapshot opens B2/C1 when released); `LEVEL_SALES_CLOSED` only when no ACTIVE package opens the level
  (`offers.level_purchasable`). `is_preview` opens only videos without a lesson. UI: closed card / direct URL opens
  `lms-purchase-modal` ("Kursni davom ettirish uchun xarid qiling!", Xarid qilish → `/angebote`, Ortga qaytish).
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
- **Audio upload + trim (central, reused):** `be/services/audio_files/service.py` (store ORIGINAL, ffmpeg trim into a new
  TRIMMED file, original kept; ffmpeg/ffprobe via `FFMPEG_BIN`/`FFPROBE_BIN` or PATH, no new dependency), `/admin/audio-files`
  (`be/api/audio_files/router.py`); UI `fe/features/admin/components/audio/audio-trimmer-dialog.tsx` used by Media
  Management (`mm-audio-trim-btn`, slot scissors button) and Multilevel Audio. The plain upload buttons are unchanged.
- **Scripts:** `a2_audio_processing`, `a2_lesson4_hoeren`, `a2_audio_cleanup`, `a2_audio_manifest`, `a2_audio_inventory`.
- **Tests:** `test_a2_audio_manager`, `test_a2_audio_management`, `test_a2_lesson4_hoeren`, `test_a2_audio_processing`,
  `test_video*`; E2E `a2-*.spec.ts`. Skill: `vizu-media`.

## 11. Payments & Promotions (VIZU Pay)

- **Backend:** `be/api/vizu_pay/router.py` (`/vizu-pay`), `be/api/admin/vizu_pay_router.py` (`/admin/vizu-pay`);
  services `be/services/vizu_pay/{offers,access,service,admin_service,gateways,plans,purchases}.py`.
  Legacy `/payments` (`be/api/payment`, `be/services/payment/`): no other backend module imports it; the
  admin frontend still lists it in `fe/features/admin/constants/endpoints.ts` — treat as legacy, VIZU Pay is
  the live flow.
- **Tables:** `course_packages` (price, duration_days, status ACTIVE/COMING_SOON/DISABLED, included_levels,
  description per language), `subscription_orders` (+ `included_levels` / `duration_days` snapshot), `promo_codes`
  (+ `requires_approval`), `promo_code_requests`, `promo_code_redemptions`, `app_settings` (key `angebote`: levels,
  lesson-access gate "sales", free lessons).
- **Frontend:** `fe/app/(dashboard)/{vizu-pay,angebote}` (sidebar "Xarid qilish"), `fe/features/vizu-pay/` (offer card,
  A1–C1 warning modal, checkout with promo approval); admin `fe/app/admin/angebote` (packages + levels),
  `fe/app/admin/payments` (management, history, package purchases, promo codes, promo approvals, discount stats — no
  Telegram tab), `premium-users`.
- **Rules:** packages via `offers.py` (reads `course_packages`, code defaults as fallback) + `packages.py` (admin edits,
  audited, never deleted); sold only when ACTIVE + priced + releases something (A1–C1 opens A1–B1 now, B2/C1 for its
  buyers once released, no new payment); order stores amount, days and levels at checkout; access = APPROVED + within
  `access_*_date` (days from approval, server time); manual gateway, SUPER_ADMIN approves (row-locked, idempotent);
  promo codes with `requires_approval` give no discount until an admin approved the student's request; the server
  computes every price. Only lesson 1 of each course is free.
- **Multilevel Modelltest Premium (2026-11-16, migration `a7c4e2f9b1d8`):** `be/services/vizu_pay/multilevel_premium.py` — one
  purchase (`plan = ML_PREMIUM`, default 99 000 = `offers.ML_PREMIUM_PRICE`, admin override `app_settings["multilevel_premium"]`)
  opens **every** Multilevel Modelltest 1–10, unlimited (owner 2026-11-19: nothing is free; `multilevel_service.FREE_TEST_NUMBERS` is empty —
  `OPEN_TEST_NUMBERS` 1–6 is only the lenient publish rule); access = active `user_entitlements` row (PAYMENT on approval, PROMO for a 100 %
  Multilevel code) or staff (`access.can_access_model_test` → `free_test` or `has_multilevel_premium`; legacy Premium does not open it); manual
  card payment with receipt or "Chek mavjud emas" + date/time, no auto-expiry, one open ML order, refund revokes. Student
  `fe/features/vizu-pay/components/multilevel-premium-modal.tsx` on `/vorbereitung/multilevel` (10 cards, LOCKED / OPEN /
  "Tayyorlanmoqda" for DRAFT tests).
- **Promo codes (2026-11-16):** `product_category` COURSES / PACKAGES / MULTILEVEL (never mixed: `VizuPayService.promo_category_fits`);
  every code starts PENDING and works only when a Super Admin approved + activated it (`AdminVizuPayService.review_promo`; a changed
  type / value / category / scope sends it back to PENDING); personal codes (`assigned_user_id`). "Promo so'rovi" = `promo_code_requests`
  kind COURSE_REQUEST (student picks a package; admin approves with a new personal code or an existing ACTIVE one —
  `review_course_request`; nothing is bought by it). Admin `/admin/payments`: Overview, Payment Requests, Course Payments, Multilevel
  Modelltest Payments (+ Premium holders), Promo Codes, Promo Requests, Purchase History, Payment Settings
  (`fe/features/admin/components/payments/{payments-sections,payment-tabs,buyer-card}.tsx`).
- **Tests:** `test_angebote`, `test_course_packages*`, `test_promo_*`, `test_admin_purchase_analytics`,
  `test_course_access_terms`, `test_multilevel_premium*`; E2E `purchase.spec.ts`, `multilevel-premium.spec.ts` (E2E helper
  `grantMultilevelPremium` in `e2e/tests/helpers.ts`; Modelltest 1–6 no longer need it).

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
- **Frontend:** `fe/features/global-chat/`, admin `fe/app/admin/global-chat`. The floating button (`global-chat-widget.tsx`, mounted in the
  student / teacher / admin shells) shows ONLY on `/dashboard`, `/teacher`, `/admin` (`chat-visibility.ts`, owner 2026-11-19); a page change closes it.
- **Docs/tests:** `docs/global-chat.md`, `docs/audit/global-chat-reply.md`; `test_global_chat*`, unit `chat-visibility.test.mjs`, E2E `global-chat*.spec.ts`.
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

**Student navigation (since 2026-11-15, frontend only):** the dashboard `fe/components/dashboard/home/dashboard-hub.tsx` has five cards
(`data-card` courses → `/kurse`, media → `/medien`, prep → `/vorbereitung`, certificates → `/certificates`, purchase → `/angebote`); the level
buttons A1–C1 live only on `/kurse` (`components/lms/lms-level-card.tsx`, `data-status` from `features/lms/level-status.ts`: ACTIVE if owned
/ staff, COMING_SOON, LOCKED if no ACTIVE package sells it, else PURCHASE_REQUIRED — presentation only, access stays server-side).
Language switcher: top of `sidebar.tsx` (variant `sidebar`, collapsed `compact` = one cycling button) and `mobile-nav.tsx` (variant `drawer`,
44 px); persisted in `localStorage` key `vizu-language`. Texts: namespace `hub` (uz/de in `translations.ts`, en/ru in `extra/part10.ts`).
Certificates page `app/(dashboard)/certificates/page.tsx`: only non-revoked rows of `GET /my-certificates`, view / download / print
(`lib/save-blob.ts:printBlob`). E2E `dashboard-nav.spec.ts` (needs `psql` for one seeded certificate + `serviceWorkers: "block"` for stubs).

## 19. Production Deployment

See `deployment-map.md`, skill `vizu-deploy`, `docs/deploy-frontend.md`, `docs/lms-deploy-runbook.md`.

## 20. VIZU DEUTSCH BATTLE

- **Backend:** `be/api/battle/router.py` (`/battle`, `/admin/battle`), `be/services/battle/*` (engine, questions, media,
  themes, admin, commons, seed, question_bank, question_seed). Tables `battle_profiles`, `battle_words`, `battle_images`, `battle_matches`,
  `battle_answers`, `battle_points_ledger`, `battle_themes`, `battle_questions` (2026-11-19: ≥ 500 vocabulary + grammar text questions per
  level A1–C1, seed `be/scripts/battle_questions_seed.py` + `be/data/battle/questions/`; details `docs/battle-questions.md`).
  Seed `be/scripts/battle_seed.py` + `be/data/battle/`.
- **Frontend:** `fe/app/(battle)/battle/*`, `fe/features/battle/*`, admin `fe/app/admin/battle` (Übersicht, Wörter & Bilder,
  Design & Themes); entry points: dashboard tile `fe/components/dashboard/home/battle-banner.tsx` (`GET /battle/summary`), first card of
  "Lernwerkzeuge" (`learning-tools.tsx`, with Stufe Bestimmung / Wortschatz; dashboard order since 2026-11-15:
  welcome → compact Werbung banner → hub of five cards (`dashboard-hub.tsx`) → Lernwerkzeuge → compact Lernserie;
  Erfolge/Zertifikate cards not on the dashboard; E2E `dashboard-layout.spec.ts`, `dashboard-nav.spec.ts`),
  sidebar + mobile nav with the custom icon `fe/components/icons/battle-icon.tsx` (favicon `fe/public/battle/battle-icon.svg`).
- **Tests:** `test_battle`, `test_battle_migration`, `test_battle_questions` (data files, validator, choice, round view, seed, admin),
  `test_battle_questions_migration`, unit `battle-utils.test.mjs`, E2E `battle.spec.ts`, `battle-dashboard.spec.ts`, `battle-questions.spec.ts`.
- **Details / decisions:** `docs/ai-context/battle-overview.md`, `docs/battle-questions.md`.

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
`fe/app/(dashboard)/vorbereitung`; **every Multilevel Modelltest 1–10 needs the Multilevel Premium** (2026-11-19, see §11; 1–6 keep the lenient publish rule) — the student list shows every
test, DRAFT ones as "Tayyorlanmoqda"; Multilevel Modelltest 1–10 import, keys, source PDF, publish guard:
`be/services/mock_exam/multilevel_service.py`, `scripts/multilevel_import.py`, `docs/multilevel-modelltests.md`; **open tests 1–6** (2026-11-19, no migration):
`readiness()` gives `warn_only` / `publishable` / `warnings` — missing keys and audio are warnings, only a missing section blocks; 7–10 keep the full rule
(`MODEL_TEST_NOT_READY`); a question without a key is not scored (`multilevel_exam_service._has_key`, not in `raw_max`), a closed Lesen / Hören without any key
is "not scored" (`no_key`) and leaves the total (max 225 instead of 300, `attempt.max_score`); a Hören Teil without audio shows "Audio noch nicht verfügbar";
detaching audio keeps 1–6 published; script `app/scripts/multilevel_open_tests.py` plan / apply --confirm (links the unused "Variant 1 Hören" original as the
shared audio of Modelltest 1, publishes 1–6, audit `multilevel_open_publish`); tests `test_multilevel_open_tests`, E2E `multilevel-open-tests.spec.ts`; timed
exam mode + 0–75 scoring + B1/B2/C1 result: `be/services/mock_exam/multilevel_exam_service.py`, student
`fe/app/(dashboard)/vorbereitung/multilevel/{pruefung,ergebnis}`, admin `fe/app/admin/mock-exams/multilevel`, tests
`test_multilevel_exam*`, E2E `multilevel-exam.spec.ts`; **Multilevel Audio** (admin `/admin/mock-exams/multilevel-audio`,
one slot per Hören Teil of every Multilevel Modelltest; upload / trim / replace / delete play in that exam task at once;
exam paper gets a signed `/multilevel-exam/audio/{id}?token=` URL; **Modelltest 1 plays ONE shared audio** for its whole Hören section — 2026-11-16, migration
`e6d2b9a4c8f3` `kompetenzen.audio_file_id`, `multilevel_service.SHARED_AUDIO_NUMBERS = {1}`, admin `…/multilevel-audio/shared/{model_test_id}`, per-Teil slots of that test → 409
`SHARED_AUDIO_TEST`, readiness asks for one audio, paper `shared_audio` = one signed `/multilevel-exam/audio-shared/{kompetenz_id}?token=` URL, the Teile keep their own questions;
student `fe/features/vorbereitung/components/multilevel/shared-audio-player.tsx` docked at the bottom (the dashboard `<main>` scrolls, so `sticky` does not hold), position kept in
sessionStorage; audio length and exam time independent; tests `test_multilevel_shared_audio*`, E2E `multilevel-shared-audio.spec.ts`): `be/services/mock_exam/multilevel_audio.py`,
`be/api/audio_files/router.py`, `fe/features/admin/components/mock-exam/multilevel-audio-client.tsx`, tests
`test_multilevel_audio*`, E2E `multilevel-audio.spec.ts`; **Answer Key tool + exam times** (2026-11-16, migration `d4b9e2a7c3f1`: owner's Hören keys of Modelltest 1–6
(35 / 30 / 30 / 30 / 30 / 30 answers, `app/data/multilevel/hoeren-keys.json`), `be/services/mock_exam/multilevel_keys.py` = numbered table / text import ("1-b, 2-R …") /
single edits, letters per question type (a–c, a–h, r / f / a / b for true-false), count checked against the test, token kept as typed in `mock_questions.answer_key`, scoring
still reads `options.is_correct`; endpoints `/admin/multilevel-exam/model-tests/{id}/answer-keys` (GET, PUT, POST `/import`); script `app/scripts/multilevel_hoeren_keys.py`
plan / apply --confirm (also sets the exam times Lesen 60, Hören 60, Schreiben 60, Sprechen 15 = 195 min on every Modelltest; `DEFAULT_MINUTES` / `TOTAL_MINUTES`);
`mock_attempt_sections.duration_seconds` = what the server granted; student list cards show the four sections, 195 min and the state; admin
`fe/features/admin/components/mock-exam/multilevel-answer-keys.tsx`; tests `test_multilevel_keys`, `test_multilevel_keys_migration`, E2E `multilevel-keys.spec.ts`), assessment engine (`be/api/assessment_engine`), certificates
(`/certificates`, `/my-certificates`), books (`/books`), homework (`/homeworks`), quizzes, exams, calendar,
notifications, support, advertisements ("Werbung-Banner"), achievements.

## 22. VIZU Medienwelt (Bibliothek · Musik · Filme)

- **Purpose:** student media centre (`/medien`) + admin management (`/admin/medien`). Content: books (PDF), songs, films
  with categories, FREE / PAID (+ old price, special offer, featured), Published / Draft / Hidden. Separate from the course
  `books` and lesson `videos` (those are level-gated course material).
- **Backend:** `be/api/medien/{router,admin_router}.py` (`/medien`, `/admin/medien`), services `be/services/medien/{common,catalog,admin,subtitles,player,lookup}.py`,
  models `be/models/medien.py`, storage `ProtectedMedienStorage` (`app/protected_storage/medien`: books, songs, films, covers,
  subtitles, chunks). Duration of songs / videos via ffprobe/ffmpeg (`services/audio_files`).
- **Security:** a student gets a file only through `POST …/open|play|watch` (access check → short-lived signed URL) and
  `GET /medien/stream/{kind}/{id}?token=` (checks access again, HTTP Range via FileResponse). PAID = a GRANTED `media_purchases`
  row (student request → Super Admin grants/rejects/revokes, or direct grant by e-mail; no money is handled here). Covers are the
  only public files (`/medien/cover/…`). Uploads checked by content, size, random names; delete = row first, then files.
- **Film player + subtitles (2026-11-15, migration `b6e2d9f4a1c8`):**
  - *Subtitle files* (`services/medien/subtitles.py`, pure + unit-tested): `.srt` / `.vtt`, UTF-8 / UTF-16 / Windows-1252, ≤ 2 MB, ≤ 20 000 cues.
    Tolerant parser (broken blocks skipped + warned), tags / HTML / control characters removed (plain text only), stored as normalised WebVTT with
    escaped `& < >`; refused: wrong extension, binary, empty, no valid cue. Check report (`film_subtitles.cue_count / last_ms / source_format /
    warnings`): overlap, very short / long cues, long lines, `BEYOND_VIDEO` / `ENDS_EARLY` against `films.video_duration_ms` (else the rounded minutes).
    Languages de / uz / en (ru accepted by the API); one track per film + language.
  - *Student API:* `POST /medien/films/{id}/watch` also returns `sources` (Original + extra qualities), subtitle tracks with signed `cues_url`, `prefs`,
    `progress.state`, `neighbors` (previous / next film of the category), `duration_ms`. `GET /medien/subtitles/{id}/cues?token=` = plain cue list
    `[[start_ms, end_ms, text]]` (same token + access check as the WebVTT file; a damaged file gives an empty list). `GET /medien/rendition/{id}?token=`
    streams an extra quality (Range). `GET|PUT /medien/player-prefs` (size, colour from a palette, background 0–100, position, font, on/off, dual,
    second language — validated against fixed lists), progress `state` (subtitle, dual, secondary, speed from the menu values, quality / audio label;
    merged per key). `GET /medien/lookup?word=` answers a clicked word from `dictionary_entries` (`exact` headword / inflected `form` / `similar`
    suggestions only / `none`) — nothing is translated or invented; saving = the Wörterbuch's own `PUT /dictionary/entries/{id}/saved`.
  - *Admin API:* `POST …/subtitles` (check + normalise + store, replaces the language), `POST …/subtitles/check` (dry run), `GET …/subtitles/{id}` (preview
    cues + fresh report), `POST …/subtitles/{id}/check` (re-check, stored), `PUT …/subtitles/{id}` (language / label), `DELETE …`; extra qualities through
    the chunked upload (`video/init` with `quality` "720p" …, needs the film's own video first; the film keeps playing meanwhile),
    `DELETE …/renditions/{id}`.
  - *Tables:* `film_renditions`, `media_player_prefs`, columns `films.video_duration_ms`, `film_subtitles.*`, `media_progress.player_state`.
- **Bibliothek rework + book payments + Musik metadata (2026-11-15, migration `c2f7a9d1e4b6`):**
  - *Musik / FFmpeg:* root cause of "Die Audioverarbeitung ist auf dem Server nicht verfügbar" = the systemd unit's `PATH` has no `/usr/bin`, so `shutil.which("ffmpeg")`
    failed although FFmpeg is installed. `services/audio_files/service.py:find_tool` = env override (`FFMPEG_BIN` / `FFPROBE_BIN`) → `PATH` → system folders; the unit also
    gets a PATH drop-in. `services/medien/audio_meta.py` reads format, duration, bitrate, title / artist / album / genre (ffprobe JSON, else the `ffmpeg -i` report; tags on the
    container or the stream) and **never blocks an upload**: tool missing / crashing → song stored, `songs.metadata_status = FAILED` (+ note, logged), a file that is not audio →
    400 `UNSUPPORTED_FILE`. Formats MP3, WAV, M4A, AAC, OGG, FLAC (sniffed by content), stored byte-identical (no transcoding). Tags fill only what the admin left empty.
  - *PDF reader / preview:* `POST /medien/books/{id}/open` returns `mode` full | preview. A PAID book that is not owned gets a **separate preview PDF** with only the first
    `media_books.preview_pages_count` pages (default 10, admin 0–500, `catalog.preview_limit` never lets it cover the whole book: a short book keeps its last page closed), built
    with pypdf (`services/medien/pdf_tools.py`, annotations dropped, cached as `previews/<book>-<stem>-<n>.pdf`, removed on file / count change and delete); the original is never
    streamed to a non-owner, a `preview` token only reaches the preview, `download` tokens need full access. `POST …/download-link` + `GET /medien/download/book/{id}?token=`
    = original, file name from the title, only free / owned / staff. Reading position: `media_progress.position` (page) + `scroll_position` (0..1) + `last_opened_at`;
    a preview reader's position is clamped to the free pages and never "completed".
  - *Payments (manual card):* `book_payment_requests` (status PENDING / APPROVED / REJECTED / CANCELLED, one PENDING per student + book by a partial unique index, amount =
    the book's price taken by the server, receipt optional — without one date + time (Uzbekistan time, not in the future, ≤ 30 days) are required),
    `media_purchases.payment_request_id` (an approval creates / upgrades the GRANTED purchase = "BookPurchase"; the old direct grant and revoke keep working).
    `services/medien/book_payments.py`: rate limit (6 / h per student, 20 / h per IP, every attempt counts), receipts re-encoded by Pillow (EXIF / appended data gone) or
    plain PDFs without scripts / actions / attachments, random names in private storage, visible to the owner and the Super Admin only; student: `GET /medien/book-payment-info`,
    `POST /medien/books/{id}/payment-requests` (multipart), `GET /medien/book-payments/mine`, `POST …/{id}/cancel`, `GET …/{id}/receipt`; Super Admin:
    `GET /admin/medien/book-payments[/{id}[/receipt]]`, `POST …/{id}/decision` (row lock: decided once; REJECTED needs a reason the student sees; no self-review),
    `GET|PUT /admin/medien/book-payment-settings` (card number + holder; default = the VIZU Pay card). Everything is in `audit_logs` (card only as `****last4`).
    The legacy generic request is refused for books (`409 BOOK_PAYMENT_REQUIRED`); songs / films keep it.
  - *Frontend:* `pdf-reader.tsx` (pdf.js; since 2026-11-19 **book mode** by default everywhere = `book-view.tsx`, else continuous scroll with lazy pages; zoom, fullscreen with
    phone fallback, progress line, resume page + position, download button, preview badge + "Das vollständige Buch freischalten!" dialog at page 11), `book-payment.tsx`
    (payment window, buy button with pending / rejected states, "Meine Zahlungen"), `download-pdf-button.tsx`; admin `book-payments-admin.tsx` (Bibliothek → tab
    Zahlungsanfragen: list, receipt check, "geprüft" box, approve / reject with reason, card settings), `preview_pages_count` field in the book dialog, song format / bitrate /
    metadata warning in `songs-admin.tsx`. Texts: `medien.pay.*`, `medien.paywall*`, `medien.reader*`, `medien.err.<payment codes>`.
- **Vinyl music player (2026-11-18, frontend only):** around the one `<audio>` of `GlobalAudioPlayer` (dashboard layout, never remounted):
  `vinyl-player.tsx` = large player (base-ui Dialog: turning record `vinyl-disc.tsx` with the cover as label + tone arm, title, artist, progress, prev /
  play / next, shuffle, repeat, volume, favourite; "Verkleinern" / Escape keeps the music, X = `stop()`); opens when a song is started on Medien → Musik,
  closes on every page change. `floating-vinyl.tsx` = turning disc with progress ring bottom-right on every other page (above the chat button's place — the button itself is on /dashboard only; on the
  Multilevel exam page above the Hören dock on phones), tap → panel (title, artist, progress, prev / play / next, large player, X). The Musik page keeps
  its bar (cover / expand button → large player, X). View rules = `lib/player-view.ts` (unit test `medien-player-view.test.mjs`); store fields
  `isLargePlayerOpen`, `isMusicPageActive`, `isFloatingPanelOpen`, selector `isFloatingPlayerVisible`, `stop()` (pauses, removes the source, clears queue +
  saved copy). One sound at a time: another audio / video that starts pauses the music; the music pauses other playing media. The silent unlock clip of
  the first tap no longer resets / skips a restored song. Media Session: artwork sizes + `stop`. E2E `medien-vinyl-player.spec.ts`.
- **Film AI subtitles (2026-11-19, migration `d5f1b8e3a9c7`):** `be/services/medien/subtitle_ai.py` (pure timing helpers + providers) and `subtitle_jobs.py` (background jobs).
  - *Flow:* admin → film → Untertitel → "KI-Untertitel": audio language auto / de / en / uz / ru + translation languages → TRANSCRIBE job: ffmpeg `silencedetect` once, audio cut
    into pieces of `SUBTITLE_CHUNK_SECONDS` (180) at pauses (16 kHz mono MP3, AAC fallback, `nice`), each piece → speech-to-text with timed segments (new segment per speaker),
    segments shifted onto the film clock, `build_cues` (order, no overlap, ≥ 0.7 s, wrap at 42 chars, piece-border duplicates merged) + `snap_to_speech` (edges onto pauses),
    checked like an upload → **DRAFT** track (`source` AI); then a TRANSLATE job per language (batches of 60 lines, a batch with the wrong count is split) → DRAFT `source`
    TRANSLATION. Students only get **APPROVED** tracks (`catalog.subtitles_of`, also the cue endpoint with an old token); uploads are APPROVED at once. Admin: approve /
    withdraw, edit lines (`edit_cues`: times + text, cleaned like an upload, status kept), translate any track, SRT / VTT download, live job list (Wartet / Läuft x/y /
    Fertig / Fehlgeschlagen + Wiederholen / Abbrechen); a retry continues with the missing pieces (`partial`).
  - *Worker:* a thread in the backend process (`kick()`), jobs claimed with `FOR UPDATE SKIP LOCKED`, heartbeat; `lifespan` in `main.py` puts a job that was running at a
    restart back to PENDING; a job list request also wakes the worker. `SUBTITLE_WORKER_ENABLED` (off in tests).
  - *Providers (settings, names only):* `SUBTITLE_STT_PROVIDER` gemini (`GEMINI_API_KEY`, default) / openai (Whisper, `OPENAI_API_KEY`); `SUBTITLE_TRANSLATE_PROVIDER` gemini /
    google (`GOOGLE_TRANSLATE_API_KEY`); `SUBTITLE_AI_MODEL` (empty = `GEMINI_MODEL` then fallback). Keys only in a request header. No key → `AI_NOT_CONFIGURED` shown
    in the panel, nothing invented. `fake` provider = local test stack only (`APP_ENV=test`).
  - *Player:* `watch` returns `original_language` (the AI transcript's language, else `films.language`); the dual view puts it on top; the subtitle menu has "Original" /
    "Übersetzung" switches (+ translation language) besides the language list (`lib/subtitles.ts` `switchesOf` / `stateFromSwitches`); Russian card in the admin.
  - *Agents (2026-11-19, migration `f3b9d1a6c4e8` `film_subtitle_jobs.auto_approve`, `services/medien/subtitle_agents.py`):* per piece **Hörer** (fast model
    `SUBTITLE_FAST_MODEL` = flash-lite first, JSON `responseSchema`; bare JSON arrays are accepted) → **Prüfer** (`check_segments`: too dense / loop / no timing → retry
    with the strong models (1 try each), then split at a pause (≥ 40 s, depth 2); what still fails becomes a **gap**, the job goes on; an empty answer gets a second
    fast listen, then it is believed = credits / music, never the slow model) → **Korrektor** (`SUBTITLE_PROOFREAD`, German
    spelling / umlauts / punctuation, same line count or the text stays) → **Taktgeber** (`build_cues` / `snap_to_speech`; drops lines without a letter
    such as "..." / "[…]", a line stays ≤ `MAX_CUE_MS` 8 s) → **Übersetzer**. Gaps: job COMPLETED with
    `error_code` GAPS + `stats.agents.gaps`; retry ("Lücken nachholen") only redoes the gap pieces and renews the same track. A 429 with a DAILY quota
    (`quota_kind`: QuotaFailure id / message) = `AI_QUOTA`, not retried; a per-minute limit is an ordinary retried 429. Translation jobs are claimed
    before other transcriptions. Hörer + Korrektor use ONLY the fast model (`fast_only`, 5 / 4 quick tries); a busy service (5xx / 429 / network, `is_transient`) is never sent to
    the slow strong model: the job waits 30 s / 1 / 2 / 4 min with heartbeat (`_patiently`, also per translation batch), then FAILED with that code.
    `auto_approve` (checkbox "Sofort freigeben") stores tracks APPROVED; job cards have a one-click "Freigeben". Default audio language **de**.
  - *Tests:* `test_medien_subtitle_ai` (16 unit), `test_medien_subtitle_agents`, `test_medien_subtitle_jobs` (6 integration, real ffmpeg), `test_medien_subtitle_ai_migration`,
    `test_medien_subtitle_auto_approve_migration`; unit `medien-reader-shelf.test.mjs`; E2E `medien-ai-subtitles-reader.spec.ts`.
- **Musik bulk upload of up to 500 songs (2026-11-19, migration `e8a3c5f1b7d2` `songs.sha256`):** the 10-file limit is gone (it was in the frontend only).
  - *Frontend:* `fe/features/admin/store/song-upload-store.ts` (zustand, lives outside the page: switching admin pages does not stop it) + pure helpers
    `fe/features/admin/lib/song-upload.ts` (unit `song-upload.test.mjs`); `songs-admin.tsx` BulkUpload = drag & drop / multi-select, per file: SHA-256 in the
    browser → duplicate check (same file twice in the list; already on the server via `POST /admin/medien/songs/duplicates`, batches of 25) → upload
    `CONCURRENCY` = 3 at a time, one request per file, progress per file; panel Gesamt / Hochgeladen / Verbleibend / Fehler / Doppelt / Metadaten in
    Arbeit + percent of bytes; filter tabs, 50 rows a page, pause / continue, retry one / all failed, "Trotzdem hochladen" for a duplicate. The list
    (without files) is saved in localStorage at most once a second: after a reload the same files are chosen again (matched by name + size + date) and
    only the missing ones go up; a warning before leaving while uploading.
  - *Backend:* `POST /admin/medien/songs` takes `sha256` (the stored file must match, else 400 `CHECKSUM_MISMATCH` and nothing stays), `check_duplicate`
    (409 `SONG_DUPLICATE: <id> <title>`, under `pg_advisory_xact_lock(hashtext(sha))` so parallel copies cannot both pass; without it the endpoint
    behaves as before), `defer_metadata` (status PENDING → `services/medien/song_processing.py` queue: one ffprobe at a time in a worker thread,
    claim `FOR UPDATE SKIP LOCKED`, OK / FAILED / INVALID = not audio → DRAFT; `main.py` lifespan resumes it; `SONG_PROCESSING_WORKER_ENABLED`).
    `POST /admin/medien/songs/states` (what the queue read), `GET /admin/medien/songs/processing` (queue size). Originals are stored unchanged.
    `LocalStorage` size errors are `UploadTooLarge` now (a path race under parallel uploads was misreported as "too large"; the path check retries).
  - *Script:* `app/scripts/medien_song_hashes.py` plan / apply --confirm (hash of older songs). *Tests:* `test_medien_bulk_upload` (incl. parallel
    copies; `VIZU_STRESS_500=1` = 500 files, 6 parallel), `test_medien_song_hash_migration`; E2E `medien-bulk-500.spec.ts` (500 files, reload + resume,
    duplicates, lost connection + retry, other admin page meanwhile).
- **Bibliothek bookshelf + book reader (2026-11-19, frontend only):** `bibliothek-client.tsx` = one shelf per category (admin order; books without one → "Weitere Bücher"),
  boards stacked vertically, books per board from the width (`lib/shelf.ts` `shelfColumns`: ≥ 96 px covers on phones, 2–8), covers 2:3 with title + author below the board,
  free / bought / price + lock sign; page size 60. Reader book mode (`book-view.tsx`, maths in `lib/reader-gestures.ts`): page fitted to the screen, previous / current / next
  drawn, 3D turn over the spine; swipe (right-to-left = next), click on the left / right third, ← → / PageUp / PageDown, buttons (big bar at the bottom on phones); pinch zoom
  around the fingers + one-finger pan when zoomed (never a page turn), double tap = 2× / whole page, ctrl + wheel; quick clicks during a turn are queued. "Kitobdan chiqish"
  button → `/medien/bibliothek` (position saved); the X still closes to the book page. The preview paywall and the server-side page limit are unchanged.
- **Frontend:** student `fe/app/(dashboard)/medien/*` + `fe/features/medien/` (global player store + `GlobalAudioPlayer` in the
  dashboard layout: one `<audio>`, queue/position/volume restored after reload, Media Session; `PdfReader` = pdf.js
  (`pdfjs-dist@5.4.449`, page + zoom + fullscreen, last page saved); `FilmPlayer` = own controls around one `<video>` (play, ±10 s, previous / next film,
  volume, speed 0.5–2×, quality menu when extra qualities exist, audio-track menu when the browser exposes tracks, subtitles, Picture-in-Picture,
  fullscreen with a fixed-position fallback for phones without element fullscreen, keyboard shortcuts + `?` help, saved position + state incl.
  keepalive save). Subtitles are drawn by us from the plain cue list (`lib/subtitles.ts` pure helpers, `hooks/use-film-subtitles.ts` = the video's
  own clock per frame, so seek / pause / every speed stay in sync, `components/subtitle-overlay.tsx`): de / uz / en / off, dual view (German on top),
  look settings (`components/subtitle-menu.tsx`, saved to the profile with a 600 ms debounce). German words / dragged phrases open
  `components/word-popup.tsx` (Wörterbuch card: translation, article, word type, example; save = star, copy, pronounce, search; pauses the film while
  open, switchable); event `medien:subtitle-word` is still fired. Menus are right-aligned panels on desktop and full-player sheets on phones.)
  Admin `fe/app/admin/medien/*` + `fe/features/admin/components/medien/` (bulk song upload ≤ 10 with per-file progress, chunked film video upload;
  film dialog = four sections Video-Informationen / Videodatei (readiness, extra qualities) / Untertitel (`subtitle-manager.tsx`: per language check,
  upload / replace, preview with time scrubber, re-check, re-assign language, delete) / Zugang).
- **Tests:** `test_medien`, `test_medien_migration`, `test_medien_subtitles` (23 unit), `test_medien_player` (integration), `test_medien_player_migration`;
  unit `tests/unit/medien-subtitles.test.mjs`; E2E `medien.spec.ts`, `film-player.spec.ts`, `medien-library-payments.spec.ts`, `medien-music-formats.spec.ts` (need ffmpeg locally); backend `test_medien_audio`, `test_medien_books_reader`, `test_medien_payments`, `test_medien_books_payments_migration`. Texts: namespace `medien`
  (uz/de in `translations.ts`, en/ru in `extra/part9.ts`; keys `fp.*` player, `wp.*` word card).