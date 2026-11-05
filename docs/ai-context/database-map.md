# Database map

Updated 2026-11-01 · source: `backend/app/models/*.py` (`__tablename__`), `backend/alembic/versions/` (107 files).
PostgreSQL; connection from settings `DATABASE_HOST/PORT/NAME/USER/PASSWORD` (names only).

## Migrations

- Linear history, one head. **Head = `f2b6d8a4c1e9`** (see `current-state.md` for production).
- Latest: `f3a8c1d5e7b2` Global Chat `reply_to_id` → `a6d2f9c4e8b1` `a2_audio_assets` → `b8e3d1a7c5f2` `listenings.task_key` →
  `c4f7a9e2d6b3` `a2_audio_transcripts` → `d7e2b4f8a1c6` A2 module separation (`writings.competency` + CHECK, vocabularies
  grammar fields + `dictionary_entry_id` + `data_sources`, `vocabulary_user_words`, `student_writing_versions`,
  `ai_evaluations.attempt_number`) → `e5a9c3f1b7d2` Battle: 7 new `battle_*` tables (additive; `battle_words.entry_id` →
  `dictionary_entries` ON DELETE SET NULL) → `f2b6d8a4c1e9` `app_releases` (Android APK releases; additive, partial unique
  index = one `is_latest` per platform).
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
  learning_activity, homeworks, homework_submissions, enrollments, certificates
- **Competency of a written task:** `writings.competency` NULL/SCHREIBEN · GRAMMATIK · WORTSCHATZ · LESEN
  (`models/writing.py:writing_competency_filter`).
- **Quiz/legacy exams:** quizzes, quiz_questions, quiz_options, answers, exams, exam_parts, exam_providers, exam_sessions,
  certification_providers
- **Assessment engine:** assessments, assessment_sections, assessment_tasks, assessment_attempts, assessment_results,
  section_results, task_attempts, task_questions, task_options, task_audio, teile, writing_tasks, writing_submissions,
  writing_evaluations, writing_rubric_criteria, speaking_tasks, speaking_submissions, speaking_evaluations
- **Vorbereitung (mock exams):** mock_exam_levels, model_tests, mock_questions, mock_question_options, mock_question_answers,
  mock_test_attempts, mock_writing_submissions, mock_speaking_submissions
- **VIZU-Multilevel:** vizu_mock_attempts, vizu_mock_audios, vizu_mock_tasks, vizu_mock_questions, vizu_mock_options,
  vizu_mock_answers, vizu_mock_writing_tasks, vizu_mock_writing_rubric_criteria, vizu_mock_writing_submissions,
  vizu_mock_writing_criterion_scores, vizu_multilevel_speaking_tasks, vizu_multilevel_speaking_submissions,
  vizu_multilevel_discarded_attempts
- **Payments:** subscription_orders, promo_codes, promo_code_redemptions
- **Mobile app:** app_releases (APK files in `app/protected_storage/app-releases`)
- **Community:** global_chat_messages, global_chat_message_edits, global_chat_restrictions, global_chat_moderation_actions,
  global_chat_reads, study_groups, study_group_courses, study_group_members, study_group_join_codes, study_group_messages,
  study_group_announcements, study_group_tasks, study_group_audit_logs, teacher_assignments
- **Engagement/ops:** notifications, broadcast_notifications, broadcast_notification_reads, support_tickets, support_messages,
  advertisements, advertisement_events, achievement_categories, achievements, user_achievements, dictionary_entries,
  dictionary_user_words

## Cascades that matter

- `listenings` → questions, options, tracks, **`lesson_skill_attempts` (CASCADE)**; `listening_audio_archives` is RESTRICT.
- `a2_audio_assets.listening_id` SET NULL. `global_chat_messages.reply_to_id` SET NULL.
- `student_writing_versions` CASCADE from `student_writings` / `writings`; `vocabulary_user_words` CASCADE from
  `vocabularies`; `vocabularies.dictionary_entry_id` SET NULL.
