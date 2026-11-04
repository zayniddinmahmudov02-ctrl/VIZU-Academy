# VIZU DEUTSCH BATTLE — overview and decisions

Status 2026-11-05: **not started (Phase 1 audit only).** Spec: the owner's master prompt "VIZU DEUTSCH BATTLE"
(2026-11-05) — 2-player real-time picture-vocabulary battle, Battle Points, CEFR ranks A1…C1+, admin Game Management.

## Owner decisions (2026-11-05)

| Topic | Decision |
|---|---|
| Vocabulary source | Verified `dictionary_entries` (Wörterbuch A1–C1: word, article, plural, translation, example). Claude assigns semantic categories for the distractor engine. C1+ has no source → stays empty until the owner supplies words. Nothing invented. |
| Images | Wikimedia Commons API (no key) with per-file licence + attribution stored; Claude checks every imported image visually and only then marks it Verified. Start: A1 (~200), other levels in later phases. Manual upload + Image Library always work without any API key. Unsplash/Pexels: no key on the server (2026-11-05). |
| Local environment | C: was full (0 MB); owner restarts Claude Code with `CLAUDE_CODE_TMPDIR=D:\vz_tmp\claude-tmp`. Helper scripts: `D:\vz_tmp\work\srv\` (`remote.ps1`, `u2_backup.sh`, `k1_sync.sh`, `env.ps1`). |

## Audit facts (2026-11-05)

- Backend has no WebSocket code yet; frontend has no three.js / R3F (only `framer-motion`).
- Still to check on the server (script did not run, disk full): nginx WebSocket upgrade headers for `/api`,
  uvicorn worker count (in-memory state only works with 1 worker; otherwise PostgreSQL-backed state), Redis (assume none).

## Phase plan (spec §21)

1. Audit + architecture (server checks above; decide WS vs. polling fallback).
2. DB + backend core: `battle_*` tables (one migration, additive), profiles, ranks/levels config, points ledger (idempotent).
3. Vocabulary import from Wörterbuch + categories + distractor engine (same category / word type / CEFR, no ambiguity, balanced answer position).
4. Image Library (Wikimedia search/import, upload with validation, statuses Draft→Verified→Published) + Admin Game Management.
5. Matchmaking (same CEFR, ±10→±25 points by wait time, private room code, bot practice without rating) + WebSocket server-authoritative matches (timer, answers, reconnection 20 s, AFK).
6. 3D arena (React Three Fiber) with mobile/low-end 2D fallback.
7. Dashboard card, profile, leaderboard, achievements.
8. Security / anti-cheat review. 9. Tests (backend, unit, E2E desktop + Pixel 7). 10. Production deploy (backup, migration preview, slots).

Docs to create as the work proceeds: `battle-architecture`, `battle-database`, `battle-api`, `battle-matchmaking`,
`battle-vocabulary`, `battle-image-management`, `battle-admin`, `battle-deployment`, `battle-known-issues` (all in this folder).
