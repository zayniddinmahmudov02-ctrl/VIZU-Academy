# Mobile authentication

- No new auth: Android app and iOS PWA use the website's login/register/logout/password reset and token refresh
  (`fe/services/api.ts`, `fe/lib/token.ts`; backend `/auth`). Same accounts, roles and permissions everywhere (all checked by the server).
- Browser / iOS PWA: tokens in localStorage ("Angemeldet bleiben") or sessionStorage of the vizu-deutsch.com origin.
- **Android app (since 2026-11-23):** tokens never in the WebView storage. `SecureSessionPlugin` (`VizuSession`) keeps access + refresh
  token AES-256-GCM-encrypted with a key that never leaves the Android Keystore ("Angemeldet bleiben" off = memory only, gone when the
  app process ends); a document-start script for the app's own origin only gives the page `window.__VIZU_SESSION__` before any page
  script runs, so `lib/token.ts` stays synchronous; every change goes back through `VizuSession.set`. An older install's localStorage
  tokens are moved once and deleted. Old WebViews without document-start scripts fall back to the browser storage.
  Verified on the Android 15 emulator: no token in localStorage / sessionStorage after login, session kept after an app restart,
  logout + restart = logged out.
- Token expiry, refresh rotation, session revocation (logout, password change, admin) are unchanged server rules.
- Logout clears the service-worker runtime cache (`CLEAR_RUNTIME_CACHE`) so another account never sees cached data.
- `allowBackup=false`; no tokens in URLs, logs or native logs. Deep links: only `https://vizu-deutsch.com` (App Links).
