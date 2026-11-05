# VIZU DEUTSCH BATTLE — overview and decisions

Status 2026-11-05: **built + design "Futuristic German Experience"** (spec: owner's master prompt + Phase 2 design prompt,
2026-11-05). 2-player picture-vocabulary battle, Battle Points, ranks A1…C1+, admin Game Management. One doc instead of the
planned `battle-*` set (paths and decisions only).

## Owner decisions (2026-11-05)

| Topic | Decision |
|---|---|
| Vocabulary | Only VERIFIED Wörterbuch rows (`dictionary_entries`), copied into `battle_words` (lemma, article, translation) + a category. C1+ has no source. Nothing invented. |
| Images | Wikimedia Commons (no key), licence CC0 / PD / CC BY / CC BY-SA, author + licence + page stored; checked visually before Published. Manual upload always possible. |
| Real-time | **Polling, not WebSocket**: production = 1 uvicorn worker, no `websockets` lib, nginx without upgrade headers. State in PostgreSQL, server clock, ~0.7 s polls. |
| 3D | No three.js / R3F (bundle + phones): layered SVG avatars with gradients, rim light, CSS 3D tilt/float, parallax backgrounds; `bt-lowfx` fallback (<40 fps, reduced motion, data saver). |

## Where things are

- **Backend:** `be/api/battle/router.py` (`/battle`, `/admin/battle`), `be/services/battle/` — `config` (stages, ranks 50 BP each,
  timing 12 s + 3 s reveal, scoring / points / bot levels: see Rules, avatars, achievements),
  `engine` (matchmaking, clock `tick`, answers, AFK 20 s, forfeit, ledger), `questions` (pool + distractors), `media` (WebP
  re-encode, signed 90 s round URLs), `themes` (draft → publish), `admin`, `commons`, `profiles`, `home`, `seed`.
- **Data:** `be/data/battle/words.json` (89 A1 words, 11 categories, conflict pairs), `images.json` + `images/*.webp`
  (checked pictures with attribution), `themes.json` (6 stages). Seed: `python -m app.scripts.battle_seed plan|apply --confirm <id>`.
- **Files:** pictures `app/protected_storage/battle-images`, admin backgrounds `app/protected_storage/battle-themes`;
  default backgrounds `fe/public/battle/themes/<city>-{desktop,mobile}.webp`.
- **Frontend:** route group `fe/app/(battle)/battle/{page,match/[matchId],rangliste,erfolge}` (own shell + nav, no dashboard
  sidebar), `fe/features/battle/{components,hooks,lib,admin}`, CSS `fe/features/battle/battle.css`, strings
  `fe/lib/i18n/battle-translations.ts`, variant `landscape-short:` in `globals.css`. Admin `fe/app/admin/battle`.
- **Audio (2026-11-05):** `fe/features/battle/audio/battle-audio.ts` = the one manager; everything is synthesised with Web Audio
  (original loops home / search / arena / final, distinct effects per event, no audio files). Event mapping with once-per-event
  keys: `use-battle-audio.ts` (timer sounds follow the server deadline). Started by the first gesture, paused in a hidden
  tab, stopped on leaving Battle (`battle-shell.tsx`). Settings panel `components/audio-settings.tsx`, localStorage
  `vizu-battle-audio`. Extra animations (timer warning, image entrance, score bump, round slide) in `battle.css`, off in
  low-FX / reduced motion.
- **Tests:** `test_battle` (unit + DB), `test_battle_migration`, unit `battle-utils.test.mjs`, E2E `battle.spec.ts`,
  `battle-audio.spec.ts`.

## Rules

- The client never sends score, time or correctness; the correct option leaves the server only after the round ends.
- Stages: A1 Berlin · A2 München · B1 Hamburg · B2 Köln · C1 Frankfurt · C1+ Neuschwanstein. A stage without ≥14 playable words
  plays with the words of the stages below.
- Ranked = same stage, points window ±10 → ±25 → any (by waiting time).
- Scoring (owner rule 2026-11-05, `config.py`): +1 per correct word (0 wrong / no answer, no speed bonus); more correct
  words wins. Battle Points per finished **ranked or bot** match = own score + 3 for the winner (draw / loss: own score,
  never negative), once per user + match via `battle_points_ledger`. Private rooms: no Battle Points. Rank = 50 BP
  (was 150; stored points unchanged). Bot strength per stage `BOT_LEVELS` (accuracy + answer time, A1 ≈ 6/10 … C1 ≈ 8.7/10,
  always beatable); bot results count for wins / streak / rank.
- A theme / picture is published only with author + licence; the photo credit is shown on every Battle page.
- Open to every logged-in user (student routes depend only on `get_current_user`; no course / premium / LMS check).
- Player picture = uploaded profile photo (`users.profile_image`), else the game avatar; ranked rank-ups create a
  notification (type `battle`, link `/battle`). Dashboard: top banner; icon: `fe/components/icons/battle-icon.tsx`.
