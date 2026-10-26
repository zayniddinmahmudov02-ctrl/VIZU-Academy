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
2. **Logout does not end the current access token.** `POST /auth/logout`
   deletes the refresh row. An access JWT that was already issued keeps
   working until `exp`, up to 60 minutes, because `get_current_user` does
   not check a session id. The browser forgets the token immediately, but a
   copied token keeps working. (Verified: `tests/test_auth_session_flow.py`
   covers refresh revocation; access-token revocation is the gap.)
3. **Shared devices.** A remembered refresh token stays in `localStorage`
   until logout or expiry.
4. **Rate-limit IP comes from client headers.** `_client_ip()` trusts
   `cf-connecting-ip` / `x-forwarded-for`. Behind Cloudflare/nginx that is
   right only if nginx overwrites or strips those headers from direct
   traffic. Check the nginx config. Out of scope for the token move, but
   related.

## Quick win, independent of cookies: per-session access revocation (fixes risk 2)

- Add claim `sid` = `refresh_tokens.id` to the access token in
  `issue_token_pair`.
- `get_current_user`: if `sid` is present, require that row to exist (one
  primary-key lookup per request; the user row is already loaded).
- Rotation deletes the old row. In-flight requests with the old access token
  get 401 and the existing interceptor refreshes again. To avoid a refresh
  storm, keep the replaced row for a short grace period (e.g. 30 s,
  `replaced_at` column) instead of deleting it right away. That needs a
  migration.
- Tests: logout → `/users/me` with the old access token → 401; refresh →
  old access token accepted only within the grace period.

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
