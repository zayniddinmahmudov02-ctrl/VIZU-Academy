# Mobile authentication

- No new auth: Android app and iOS PWA use the website's login/register/logout/password reset and token refresh
  (`fe/services/api.ts`, `fe/lib/token.ts`; backend `/auth`). Same accounts and roles everywhere.
- Tokens stay where the website keeps them (localStorage / sessionStorage of the vizu-deutsch.com origin). In the Android app
  that is the WebView's private storage: other apps cannot read it, `allowBackup=false` keeps it out of backups. No tokens in
  URLs, logs or native code; the shell never touches them.
- Logout clears the service-worker runtime cache (`CLEAR_RUNTIME_CACHE`) so another account never sees cached data.
- Deep links: only `https://vizu-deutsch.com` (App Links), no custom-scheme login callbacks; other hosts open externally.
- Not done: native secure storage (Keystore-backed) for tokens — would need moving token handling into the shell; not needed
  while the WebView keeps the site's storage private. Revisit if the app ever loads third-party content.
