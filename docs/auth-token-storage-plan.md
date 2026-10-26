# Auth token storage — risk assessment and HttpOnly-cookie migration plan

Status: **plan only, not implemented.** Written 2026-10-26 alongside the
remember-me / welcome-page release. That release does not change where
tokens are stored.

## Current architecture

| Piece | Where | Lifetime |
|---|---|---|
| Access token (JWT, HS256, `sub`, `role`, `iat`, `exp`) | `localStorage` (remember me) or `sessionStorage` (not remembered), key `vizu_access_token` | 60 min (`ACCESS_TOKEN_EXPIRE_MINUTES`) |
| Refresh token (opaque, `secrets.token_urlsafe(48)`) | same storage, key `vizu_refresh_token`; server row in `refresh_tokens` | remember: 30 days, sliding; otherwise 24 h, fixed (`REFRESH_TOKEN_SESSION_EXPIRE_HOURS`) |

Server side already has: refresh rotation (single use), logout revokes the
refresh row, `users.tokens_valid_after` (password reset ends sessions),
ban/suspend re-checked on every request, login/registration rate limits.
The password is never stored on the client (covered by an e2e test).

Clients that read the token from JS: `src/lib/token.ts`,
`src/services/api.ts` + `src/lib/api.ts` (Bearer header and the 401 refresh
flow), `use-current-user.ts`, `use-bfcache-auth-recheck.ts`,
`book-viewer.tsx`, `vizu-pay-service.ts`, the admin/teacher headers and
`app/api/admin/flags/route.ts` (forwards the Bearer to the backend).

## Risks

1. **XSS = account takeover.** Any script that runs on the origin can read
   both tokens. With remember me, the refresh token gives the attacker up to
   30 days of renewable access. That risk grows with every HTML-rendering
   feature (lesson content, admin rich text, ads). Mitigations in place:
   server-side HTML sanitising (`core/utils/safe_html.py`), React escaping.
   A strict CSP is **not** in place.
2. ~~**Logout does not end the current access token.**~~ Fixed by
   per-session revocation (below). Before that fix, a copied access JWT kept
   working up to 60 minutes after logout.
3. **Shared devices.** A remembered refresh token stays in `localStorage`
   until logout or expiry.
4. **Rate-limit IP comes from client headers.** `_client_ip()` trusts
   `cf-connecting-ip` / `x-forwarded-for`. Behind Cloudflare/nginx that is
   right only if nginx overwrites or strips those headers from direct
   traffic. Check the nginx config. Out of scope for the token move, but
   related.

## Per-session access revocation (fixes risk 2) — implemented, migration e5b1c7d9a3f2

- `refresh_tokens.session_id` (nullable, indexed). Every login (password or
  Telegram) starts a session. Rotation keeps the id, so access tokens issued
  before a refresh stay valid and parallel requests have no race.
- The access token carries the session as claim `sid`. `get_current_user`
  (the only place that reads a Bearer token; every `require_*` gate goes
  through it) refuses a `sid` that no longer has an unexpired refresh token,
  with 401 "Session ended". That is one indexed lookup per request.
- `POST /auth/logout` deletes every row of the session. A password change
  deletes every row of the user. Both now end the matching access tokens on
  the next request, not only after `exp`.
- Purpose-scoped tokens (video stream, LMS resource, admin preview) are no
  longer accepted as a login token (they are signed with the same key).
- Still accepted with only their plain expiry: tokens without `sid`. These
  are tokens issued before the deploy (gone ≤ 60 min after it) and admin
  impersonation tokens (30 min, no session).
- Not covered: the short-lived signed stream/resource URLs already handed
  out (≤ `VIDEO_STREAM_TOKEN_EXPIRE_MINUTES`; they recheck the user's
  access, not the session).
- Tests: `tests/test_session_revocation.py` (unit) and
  `tests/test_auth_session_flow.py` (real HTTP + PostgreSQL: logout, second
  device, refresh, expired session, password change, Telegram, every gate).

## Target: HttpOnly cookies (fixes risks 1 and 3 for the refresh token)

- Backend sets `vizu_rt` (refresh) as `HttpOnly; Secure; SameSite=Lax;
  Path=/api/v1/auth`. Use `Max-Age` only for remember me, so a plain session
  is a browser-session cookie. `/auth/login`, `/auth/telegram` and
  `/auth/refresh` read and set it; `/auth/logout` deletes it. The body field
  `refresh_token` stays accepted for a transition period (old PWA/Telegram
  clients).
- Access token: keep it in memory only (a module variable), not in
  storage. On page load, call `/auth/refresh` (the cookie is sent) to get
  one. Even after an XSS, the attacker gets at most one short-lived token
  and never a refresh token.
- CSRF: only the refresh endpoint is cookie-authenticated, and it returns a
  token in the body. `SameSite=Lax` plus an `Origin` check against
  `ALLOWED_ORIGINS` on `/auth/refresh` and `/auth/logout` is enough. All
  other endpoints stay Bearer-only, so they cannot be CSRF'd.
- Same-site requirement: the frontend and the API share one origin through
  the nginx `/api` split, so `SameSite` cookies work. CORS already has
  `allow_credentials=True`. The axios clients need
  `withCredentials: true` for the auth calls.
- Telegram WebApp: the in-app webview supports first-party cookies on
  the same domain. Test `/auth/telegram` on iOS and Android Telegram before
  switching. Fallback: keep the body-token path for the WebApp only.
- `app/api/admin/flags/route.ts` (server-side Next route) keeps receiving
  the Bearer header from the client. No change needed.
- Remember me maps cleanly: cookie `Max-Age` = refresh lifetime, or no
  `Max-Age` for a browser-session cookie.

### Rollout

1. Backend: dual mode (cookie and body). Deploy. No client change.
2. Frontend: switch `token.ts` to cookie + in-memory access token. Keep the
   `localStorage` read for one release, to migrate existing sessions with
   one refresh call, then delete the keys.
3. Remove the body `refresh_token` path once metrics show no more use.

### Tests to write with it

- Backend: Set-Cookie flags (HttpOnly, Secure, SameSite, Path, Max-Age vs
  session); refresh by cookie; logout clears the cookie; `Origin` check
  rejects a foreign origin.
- E2E (`e2e/`): no token in `localStorage`/`sessionStorage` after login;
  remember me survives a context restart (cookie persisted), and without
  remember me it does not; Telegram login still works.
