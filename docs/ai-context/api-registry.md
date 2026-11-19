# API registry

Updated 2026-11-01 · source: `prefix=` of every `APIRouter` in `backend/app/api/**`, `app/main.py`.
Every router is mounted twice: bare (legacy) and under `/api/v1` (official; nginx + frontend use it).
Endpoint details: open the router file. Auth deps: `backend/app/api/dependencies/auth.py`.

| Prefix | Router file (`backend/app/api/…`) | Typical dependency |
|---|---|---|
| `/auth` | `auth/router.py` | public / `get_current_user` |
| `/users` (me, password, language, `POST/DELETE /me/photo` with optional `crop_x/crop_y/crop_size`) | `users/router.py` | `get_current_user` |
| `/lms` | `lms/router.py` | `require_lesson_access` for lesson content |
| `/lesson-skills` | `lesson_skills/router.py` (Lesen, Hören, exercises, results, level progress, `/{lesson}/wortschatz/words` (+`?scope=level`) and `…/words/{id}/state` saved/learned) | `require_lesson_access` |
| `/courses` `/modules` `/lessons` `/languages` | legacy CRUD | mixed |
| `/videos` | `videos/router.py`, `video_progress/router.py` | stream token / `get_current_user` |
| `/vocabularies` `/grammars` `/readings` `/reading-questions` `/reading-options` `/listenings` `/speakings` | legacy content CRUD | staff for writes |
| `/writings` | `writing/router.py`: `GET /lesson/{id}?competency=SCHREIBEN` (default; also GRAMMATIK/WORTSCHATZ/LESEN), submit, `/submissions/me`, `/submissions/me/history` (own versions + evaluations) | `require_lesson_access` / `get_current_user`; create/update/delete `require_content_editor` |
| `/student-progress` `/student-writings` `/student-speakings` `/student-quizzes` | learner submissions | own data only |
| `/quizzes` `/quiz-questions` `/quiz-options` `/homeworks` `/exams` `/exam-providers` | legacy; `GET /quiz-questions`, `/quiz-questions/{id}`, `/quiz-options` (optional `?quiz_id=`): staff see all, others only published items of lessons they may open (lesson gate) | mixed |
| `/books` `/dictionary` `/notifications` `/support` `/achievements` `/advertisements` `/dashboard` `/enrollments` | student features | `get_current_user` |
| `/vizu-pay` (+ `POST/GET /promo/requests`: approval requests of promo codes; `POST /promo/course-requests` "Promo so'rovi"; Multilevel Premium: `GET /multilevel` (own status, server price, card), `GET /multilevel/quote?promo_code=`, `POST /multilevel/orders` (multipart: `proof` or `no_receipt` + `paid_date` / `paid_time`, `note`, `promo_code` — never an amount), `POST /multilevel/redeem` (100 % Multilevel code)) | `vizu_pay/router.py` | `get_current_user` |
| `/admin/vizu-pay` packages (`GET/POST /packages`, `PUT /packages/{code}`), `GET /promo-requests?kind=CODE_APPROVAL\|COURSE_REQUEST`, `POST /promo-requests/{id}/review`, `POST /promo-requests/{id}/course-review` (create / attach a code), `POST /promo-codes/{id}/review` (approve / approve_activate / activate / reject / disable), `PATCH /orders/{id}/note`, `GET /orders?kind=course\|multilevel`, `GET /overview`, `GET\|PUT /payment-settings` (Multilevel price / sale), `GET /multilevel-entitlements`, `GET /discount-statistics`, promo history filters `search`/`plan` | `admin/vizu_pay_router.py` | `require_super_admin` |
| `/payments` | `payment/router.py` (legacy) | — |
| `/groups` | `study_groups/router.py` | members / teachers |
| `/global-chat` | `global_chat/router.py` | `get_current_user` |
| `/battle` (home, summary, themes, leaderboard, profile/avatar, queue, practice, rooms, matches/{id}[/answer,/leave]) | `battle/router.py` | `get_current_user` (match routes: players only, else 404); public: `GET /battle/media/{token}` (HMAC, 90 s), `GET /battle/themes/assets/{name}` |
| `/admin/battle` (overview, words, images, commons, themes) | `battle/router.py` | read `require_admin_panel_access`, write + Commons search `require_content_editor` |
| `/app` (`releases/latest`, `android/latest.apk`, `download-qr.svg`) | `app_releases/router.py` | public by design (download page, no user data) |
| `/admin/app-releases` (list, upload, `PATCH /{id}` notes, `/{id}/publish`, `/{id}/archive`, `DELETE /{id}` draft, `/{id}/file`) | `app_releases/router.py` | `require_super_admin` (read + write) |
| `/vizu-multilevel` (alias `/vizu-mock`) | `vizu_multilevel/router.py` | `get_current_user` |
| `/mock-exam`, `/mock-exam/public` | `mock_exam/*_router.py` | mixed |
| `/multilevel-exam` (exams, history, attempts, sections start/paper/answers/submit, writing, speaking upload, finish, results, own recordings) | `mock_exam/multilevel_exam_router.py` | `get_current_user`, own attempts only (else 404) |
| `/admin/multilevel-exam` (attempts, attempt detail, `PUT .../sections/{type}/grade`, recordings, statistics, `model-tests/{id}/preview`, `model-tests/{id}/answer-keys` (GET table, PUT save, POST `/import` check / apply), settings) | `mock_exam/multilevel_exam_router.py` | results/grading/recordings/statistics `require_teacher_panel_access`; preview + settings read `require_admin_panel_access`; settings write `require_super_admin`; answer keys read `require_admin_panel_access`, write `require_content_editor` |
| `/admin/audio-files` (`POST` upload original, `POST /{id}/trim`, `GET /{id}`, `GET /{id}/file` preview) | `audio_files/router.py` | write `require_content_editor`, read `require_admin_panel_access` |
| `/medien` (overview, categories, books / songs / films lists + detail, `POST …/open` (books: full or preview PDF), `…/download-link` (books), `…/play`, `…/watch`, progress (+ film `state`, book `scroll`), book payments (`GET /book-payment-info`, `POST /books/{id}/payment-requests`, `GET /book-payments/mine`, `POST /book-payments/{id}/cancel`, `GET /book-payments/{id}/receipt` = owner / Super Admin), continue, favorites, playlists, history, purchases, `GET|PUT /player-prefs`, `GET /lookup?word=`) | `medien/router.py` | `get_current_user`; public by design: `GET /medien/cover/{kind}/{id}`, token streams `/medien/stream/{kind}/{id}`, `/medien/download/book/{id}`, `/medien/subtitles/{id}` (+ `/cues`), `/medien/rendition/{id}` |
| `/admin/medien` (stats, categories, books / songs / films CRUD + cover / file / chunked video (+ extra `quality`) / subtitles (check, preview, re-check, language / label, delete, `POST …/{sid}/approve` {approved}, `PUT …/{sid}/cues`, `GET …/{sid}/download?format=srt` or `vtt`), `GET /films/{id}` (one card), AI subtitles (`GET /subtitle-ai/status`, `POST /films/{id}/subtitles/ai` {language auto / de / en / uz / ru, translate_to, replace} → 202 job, `POST …/subtitles/{sid}/translate`, `GET /films/{id}/subtitle-jobs`, `POST …/subtitle-jobs/{job}/retry` and `/cancel`; reads = admin panel, writes = content editor), renditions, official playlists, book payment requests `GET /book-payments`, `…/{id}`, `…/{id}/receipt`, `POST …/{id}/decision`, `GET|PUT /book-payment-settings`) | `medien/admin_router.py` | read `require_admin_panel_access`, write `require_content_editor`; `/purchases*`, `/book-payments*`, `PUT /book-payment-settings` `require_super_admin` |
| `/admin/multilevel-audio` (list, `GET\|PUT\|DELETE /slots/{content_id}`, `POST …/trim`, `GET …/file`; Modelltest 1: `GET\|PUT\|DELETE /shared/{model_test_id}`, `POST …/trim`, `GET …/file` = one audio for all Hören Teile) | `audio_files/router.py` | write `require_content_editor`, read `require_admin_panel_access`; slot of another provider/level → 404 |
| `GET /multilevel-exam/audio/{content_id}?token=`, `GET /multilevel-exam/audio-shared/{kompetenz_id}?token=` (Modelltest 1) | `audio_files/router.py` | public by design: signed token issued with the exam paper (slot + user bound, published tests only for non-staff) |
| `/mock-exam` `PUT questions/{id}/key\|text`, `PUT question-options/{id}/text`, `GET model-tests/{id}/review\|source-pdf` | `mock_exam/content_router.py` | `require_super_admin`; public `kompetenzen/{id}` returns questions without keys (`PublicQuestion`) |
| `/certificates` (only `/api/v1`), `/my-certificates` | `v1/certificate/` | public verify / own |
| `/upload` `/media-library` | legacy upload | staff |
| `/teacher` | `teacher/router.py` | `require_teacher_panel_access` |
| `/health` | `health/router.py` | public |
| `/admin` | `admin/router.py` | `require_admin_panel_access` |
| `/admin/users` `/admin/vizu-pay` `/admin/videos` `/admin/books` `/admin/zertifikate` `/admin/notifications` `/admin/page-management` `/admin/teacher-assignments` `/admin/vizu-multilevel` | `admin/*_router.py` | staff read / role-specific writes |
| `/admin/media-management` | `admin/media_management_router.py` (tree, items, videos preview, `a2-audio/*`, `a2-audio/processing`, `a2/lesson-4/hoeren/*`, `a2-readiness*`) | read `require_admin_panel_access`, write `require_content_editor`, readiness confirm `require_super_admin` |
| `/admin/hoeren-a1` `/admin/loesung` | `admin/hoeren_a1_router.py`, `admin/loesung_router.py` | staff |
| `/admin/lesson-skills` | `lesson_skills/admin_router.py` (questions, Hören audio + tracks, results, overrides, words + CSV `GET /lessons/{id}/words.csv`, `POST /lessons/{id}/words/import`) | staff; words write + CSV import `require_content_editor` |
| `/admin/lms` `/admin/content-import` | `lms/admin_router.py`, `content_import/router.py` | staff |
| `/admin/global-chat` `/admin/support` `/admin/advertisements` `/admin/achievements` | in their module router | moderators / staff |

Error shape: `{"message": <detail>}`; validation errors 422. Anonymous calls to protected routes → 401, wrong role → 403.
