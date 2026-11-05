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
| `/quizzes` `/quiz-questions` `/quiz-options` `/homeworks` `/exams` `/exam-providers` | legacy | mixed |
| `/books` `/dictionary` `/notifications` `/support` `/achievements` `/advertisements` `/dashboard` `/enrollments` | student features | `get_current_user` |
| `/vizu-pay` | `vizu_pay/router.py` | `get_current_user` |
| `/payments` | `payment/router.py` (legacy) | — |
| `/groups` | `study_groups/router.py` | members / teachers |
| `/global-chat` | `global_chat/router.py` | `get_current_user` |
| `/battle` (home, summary, themes, leaderboard, profile/avatar, queue, practice, rooms, matches/{id}[/answer,/leave]) | `battle/router.py` | `get_current_user` (match routes: players only, else 404); public: `GET /battle/media/{token}` (HMAC, 90 s), `GET /battle/themes/assets/{name}` |
| `/admin/battle` (overview, words, images, commons, themes) | `battle/router.py` | read `require_admin_panel_access`, write + Commons search `require_content_editor` |
| `/app` (`releases/latest`, `android/latest.apk`, `download-qr.svg`) | `app_releases/router.py` | public by design (download page, no user data) |
| `/admin/app-releases` (list, upload, `PATCH /{id}` notes, `/{id}/publish`, `/{id}/archive`, `DELETE /{id}` draft, `/{id}/file`) | `app_releases/router.py` | `require_super_admin` (read + write) |
| `/vizu-multilevel` (alias `/vizu-mock`) | `vizu_multilevel/router.py` | `get_current_user` |
| `/mock-exam`, `/mock-exam/public` | `mock_exam/*_router.py` | mixed |
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
