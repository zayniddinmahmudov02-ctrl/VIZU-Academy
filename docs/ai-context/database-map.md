# Database map

Updated 2026-11-23 · source: `backend/app/models/*.py` (`__tablename__`), `backend/alembic/versions/` (110 files).
PostgreSQL; connection from settings `DATABASE_HOST/PORT/NAME/USER/PASSWORD` (names only).

## Migrations

- Linear history, one head. **Head = `c8d3f5a1e7b2`** (production: see `current-state.md`)
- `c8d3f5a1e7b2` (2026-11-23): Team / Kontroll / activity / Bibliothek categories — additive: `users.must_change_password` (bool, default false);
  `teacher_profiles` (unique user_id CASCADE, `can_access_student_control` default false, control_changed_at / _by, created_by SET NULL);
  `student_sessions` (server-credited active time, `day` = Tashkent date, partial unique `uq_student_sessions_open` = one open session per user,
  `tabs` JSONB); `student_activity_events` (area CHECK COURSE / WORTSCHATZ / MUSIC / FILM / BOOK / EXAM, `ref_id`, seconds, last media `position`,
  session FK SET NULL). Data: BOOK categories Literatur, Historisch, Beruflich, Sonstige (was "Sonstige Bücher", same slug / id),
  Prüfungsvorbereitung, Wortschatz in this order; books of Lektüren / Zertifikatsbücher / Grammatik move to Literatur / Prüfungsvorbereitung /
  Sonstige and those three become inactive (no row deleted). Downgrade drops the tables / column, restores names / order, sets Historisch /
  Beruflich inactive (`test_team_kontroll_migration`). Rules: `services/activity/tracker.py`, `services/teacher/team.py`.
- `b7e4c2a9d6f1` (2026-11-21): Group video lessons (LiveKit) — additive: `video_rooms` (group FK CASCADE, `room_name` unique, status CHECK scheduled/live/ended/cancelled, partial unique index `uq_video_rooms_one_live_per_group`, room-wide chat / screen / mic switches), `video_room_participants` (unique room + user, role / connection CHECKs, per-participant mic / screen / chat, hand, removed / blocked), `video_room_events` (column `metadata` JSONB). Downgrade drops exactly these (`test_video_rooms_migration`). The earlier attempt `c1v7d3e9a5b2` was never applied anywhere but locally and its file is deleted (`docs/group-video-lessons.md` §1).
- `a6c2e8f4b9d1` (2026-11-19): VIZU Battle text questions — additive: new table `battle_questions` (level, kind vocab / grammar, format, topic, prompt, hint, answer, `wrong` JSONB, explanation, `norm_key` unique per level `uq_battle_questions_level_norm_key`, `seed_id` unique, `ref` = asked lemma, status draft / published / disabled, source seed / admin / import, `entry_id` → dictionary_entries SET NULL, created_by / updated_by → users SET NULL, index `ix_battle_questions_pool` (level, status, kind)). Picture tables untouched. Downgrade drops exactly this table (`test_battle_questions_migration`).
- `f3b9d1a6c4e8` (2026-11-19): Subtitle agents — additive: `film_subtitle_jobs.auto_approve` (boolean, NOT NULL, server default false → old jobs keep making drafts). Downgrade drops exactly this (`test_medien_subtitle_auto_approve_migration`).
- `e8a3c5f1b7d2` (2026-11-19): Musik bulk upload — additive: `songs.sha256` (nullable, index `ix_songs_sha256`, not unique: a deliberate copy stays possible). Older songs get it from `app/scripts/medien_song_hashes.py`. Downgrade drops exactly these (`test_medien_song_hash_migration`).
- `d5f1b8e3a9c7` (2026-11-19): Film AI subtitles — additive: `film_subtitles.status` (DRAFT / APPROVED, default APPROVED → existing tracks stay visible), `source` (UPLOAD / AI / TRANSLATION, default UPLOAD), `source_language`, `ai_model`, `approved_at`, `approved_by_id` (users SET NULL), `edited_at`; new table `film_subtitle_jobs` (kind TRANSCRIBE / TRANSLATE, status PENDING / PROCESSING / COMPLETED / FAILED, language, detected_language, source / result subtitle FKs SET NULL, film FK CASCADE, translate_to / partial / stats JSONB, progress, attempts, error, heartbeat; partial unique `uq_film_subtitle_jobs_active` = one active job per film + kind + language). Downgrade drops exactly these (`test_medien_subtitle_ai_migration`).
- `a7c4e2f9b1d8` (2026-11-16): Multilevel Modelltest Premium + promo approval — additive: new table `user_entitlements` (product access that is not a course level, e.g. `MULTILEVEL_MODELLTEST_PREMIUM`; source PAYMENT / PROMO, order / promo / granted_by FKs SET NULL, user FK CASCADE, `revoked_*` on refund, partial unique `uq_user_entitlements_active` = one active row per user + product); `promo_codes.product_category` (COURSES / PACKAGES / MULTILEVEL, CHECK), `approval_status` (PENDING / APPROVED / ACTIVE / REJECTED / DISABLED, CHECK, default PENDING), `approved_by_id`, `approved_at`, `review_note`, `assigned_user_id` (personal code, user FK CASCADE) — existing codes backfilled ACTIVE / DISABLED + approved by their creator (they were in use); `promo_code_requests.kind` (CODE_APPROVAL / COURSE_REQUEST) + `message`, `promo_code_id` nullable (CHECK: only a course request may have none), partial unique = one pending course request per user + package; `subscription_orders.paid_at`, `no_receipt`, `student_note`, `admin_note`. Downgrade drops exactly these and deletes course requests without a code (`test_multilevel_premium_migration`).
- `e6d2b9a4c8f3` (2026-11-16): Multilevel shared Hören audio — additive: `kompetenzen.audio_file_id` (nullable FK `audio_files`, ON DELETE SET NULL, indexed) = the one audio of a Hören section in shared mode (Modelltest 1). Downgrade drops exactly this (`test_multilevel_shared_audio_migration`).
- `d4b9e2a7c3f1` (2026-11-16): Multilevel answer key + section length — additive: `mock_questions.answer_key` (the key as typed, nullable), `mock_attempt_sections.duration_seconds` (granted length; existing rows filled from `deadline_at - started_at`). Downgrade drops exactly these (`test_multilevel_keys_migration`).
- `c2f7a9d1e4b6` (2026-11-15): Bibliothek reader + book payments + song metadata — additive: `media_books.preview_pages_count` (default 10) / `page_count`, `media_progress.scroll_position` / `last_opened_at`, `songs.audio_format / bitrate_kbps / metadata_status / metadata_note`, `media_purchases.payment_request_id`, new table `book_payment_requests` (status check, amount > 0, partial unique index = one PENDING per user + book; user FK cascades, book FK sets NULL and `book_title` stays). Downgrade drops exactly these (`test_medien_books_payments_migration`).
- `b6e2d9f4a1c8` (2026-11-15): Medienwelt film player — additive: `films.video_duration_ms`, `film_subtitles.cue_count / last_ms / source_format / original_name / file_size / warnings`, `media_progress.player_state` (JSONB), new tables `film_renditions` (extra video qualities, unique film + label) and `media_player_prefs` (one row per user, subtitle settings JSONB). Downgrade drops exactly these (`test_medien_player_migration`).
- `f4c8a1e6b9d2` (2026-11-15): VIZU Medienwelt — `media_categories` (seeded 7 book + 8 film categories), `media_books`, `songs`, `playlists` (owner NULL = official), `playlist_songs`, `user_favorite_songs`, `films`, `film_subtitles`, `media_purchases` (request → GRANTED by Super Admin), `media_progress` (book page / film second), `media_play_history` (`test_medien_migration`). Separate from the course `books` / lesson `videos` tables. (see `current-state.md` for production).
- `e8b4d2f6a1c3` (2026-11-15): `audio_files` (ORIGINAL / TRIMMED rows of the central audio service, private files in
  the lesson-listening storage, `source_id` → original is kept) + nullable `listening_contents.audio_file_id`
  (Multilevel Hören Teil → its audio; `audio_url` carries the marker `mlaudio:<id>`) (`test_multilevel_audio_migration`).
- `c7e1f3a9b2d5` (2026-11-14): `course_packages` (seeded: A1/A2 keep the price in force, B1 100 000/60 d, A1–B1
  200 000/180 d, A1–C1 400 000/365 d, B2/C1/B2–C1 COMING_SOON), `subscription_orders.included_levels`,
  `promo_codes.requires_approval`, `promo_code_requests` (`test_course_packages_migration`).
- Latest: `f3a8c1d5e7b2` Global Chat `reply_to_id` → `a6d2f9c4e8b1` `a2_audio_assets` → `b8e3d1a7c5f2` `listenings.task_key` →
  `c4f7a9e2d6b3` `a2_audio_transcripts` → `d7e2b4f8a1c6` A2 module separation (`writings.competency` + CHECK, vocabularies
  grammar fields + `dictionary_entry_id` + `data_sources`, `vocabulary_user_words`, `student_writing_versions`,
  `ai_evaluations.attempt_number`) → `e5a9c3f1b7d2` Battle: 7 new `battle_*` tables (additive; `battle_words.entry_id` →
  `dictionary_entries` ON DELETE SET NULL) → `f2b6d8a4c1e9` `app_releases` (Android APK releases; additive, partial unique
  index = one `is_latest` per platform) → `a3c9e7b5d1f4` Multilevel exam mode: `mock_attempt_sections` (per-section
  deadline, raw points, 0–75 score CHECK, level, grader), `mock_test_attempts.result_level/result_rule`, unique
  (attempt, question/task) on `mock_question_answers` / `mock_writing_submissions` / `mock_speaking_submissions`
  (`test_multilevel_exam_migration`).
- Migration tests (upgrade → downgrade → upgrade): `test_global_chat_reply_migration`,
  `test_listening_task_key_migration`, `test_a2_audio_transcripts_migration`, `test_a2_module_separation`
  (`TestModuleSeparationMigration`), `test_battle_migration`, `test_app_releases_migration`. Rules: `.claude/rules/database.md`.

## Tables by area (model file in parentheses when it differs)

- **Users/auth:** users, refresh_tokens, login_history, auth_rate_limit_events, user_languages, user_tags, audit_logs, app_settings
- **Course structure:** languages, language_settings, courses, modules, lessons, kompetenzen,
  lesson_competencies, learning_resources, student_competency_progress (lms), content_imports, managed_pages, managed_page_audits
- **Lesson content:** videos, video_upload_sessions, video_progress, vocabularies, grammars, readings, reading_questions,
  reading_options, reading_contents, listenings, listening_questions, listening_options, listening_audio_tracks,
  listening_audio_archives, listening_contents, skill_exercises, skill_exercise_questions, skill_exercise_options (lesson_skill),
  writings, speakings, media_assets, a2_audio_assets, a2_audio_transcripts, books
- **Learner activity:** lesson_skill_attempts, ai_evaluations, answer_key_reviews, student_progress, student_writings,
  student_writing_versions (student_writing), vocabulary_user_words (vocabulary), student_speakings, student_quizzes,
  learning_activity, homeworks, homework_submissions, enrollments, certificates, student_sessions + student_activity_events (student_activity:
  usage time for Medien statistics / Kontroll — never feeds the Lernserie or lesson progress)
- **Competency of a written task:** `writings.competency` NULL/SCHREIBEN · GRAMMATIK · WORTSCHATZ · LESEN
  (`models/writing.py:writing_competency_filter`).
- **Quiz/legacy exams:** quizzes, quiz_questions, quiz_options, answers, exams, exam_parts, exam_providers, exam_sessions,
  certification_providers
- **Assessment engine:** assessments, assessment_sections, assessment_tasks, assessment_attempts, assessment_results,
  section_results, task_attempts, task_questions, task_options, task_audio, teile, writing_tasks, writing_submissions,
  writing_evaluations, writing_rubric_criteria, speaking_tasks, speaking_submissions, speaking_evaluations
- **Vorbereitung (mock exams):** mock_exam_levels, model_tests, mock_questions, mock_question_options, mock_question_answers,
  mock_test_attempts, mock_attempt_sections, mock_writing_submissions, mock_speaking_submissions; scoring settings in
  `app_settings["multilevel_scoring"]`
- **VIZU-Multilevel:** vizu_mock_attempts, vizu_mock_audios, vizu_mock_tasks, vizu_mock_questions, vizu_mock_options,
  vizu_mock_answers, vizu_mock_writing_tasks, vizu_mock_writing_rubric_criteria, vizu_mock_writing_submissions,
  vizu_mock_writing_criterion_scores, vizu_multilevel_speaking_tasks, vizu_multilevel_speaking_submissions,
  vizu_multilevel_discarded_attempts
- **Payments:** subscription_orders (also the Multilevel Premium: `plan = ML_PREMIUM`), promo_codes, promo_code_redemptions,
  promo_code_requests, course_packages, user_entitlements (Multilevel Premium access); Premium price / sale in
  `app_settings["multilevel_premium"]`
- **Mobile app:** app_releases (APK files in `app/protected_storage/app-releases`)
- **Community:** global_chat_messages, global_chat_message_edits, global_chat_restrictions, global_chat_moderation_actions,
  global_chat_reads, study_groups, study_group_courses, study_group_members, study_group_join_codes, study_group_messages,
  study_group_announcements, study_group_tasks, study_group_audit_logs,
  video_rooms, video_room_participants, video_room_events, teacher_assignments, teacher_profiles (Kontroll permission)
- **Engagement/ops:** notifications, broadcast_notifications, broadcast_notification_reads, support_tickets, support_messages,
  advertisements, advertisement_events, achievement_categories, achievements, user_achievements, dictionary_entries,
  dictionary_user_words

## Cascades that matter

- `listenings` → questions, options, tracks, **`lesson_skill_attempts` (CASCADE)**; `listening_audio_archives` is RESTRICT.
- `a2_audio_assets.listening_id` SET NULL. `global_chat_messages.reply_to_id` SET NULL.
- `student_writing_versions` CASCADE from `student_writings` / `writings`; `vocabulary_user_words` CASCADE from
  `vocabularies`; `vocabularies.dictionary_entry_id` SET NULL.
