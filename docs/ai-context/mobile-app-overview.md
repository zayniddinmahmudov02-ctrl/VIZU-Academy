# VIZU DEUTSCH mobile app — overview

Started 2026-11-05. Start here; details live in the linked docs (one fact, one place).

## Architecture (decision)

```text
                vizu-deutsch.com (Next.js, existing)
     WEB (browser)    ANDROID (Capacitor APK)    iOS (PWA, Safari)
                 \            |                     /
                  FastAPI (existing) — PostgreSQL (existing, one DB)
```

- **Android = thin native shell** (`mobile/`, Capacitor 8) whose WebView loads the live site (`server.url`). Chosen over a
  bundled static export because the site is server-rendered, client-fetched and deployed several times a week: one UI,
  content and UI updates reach the app without a new APK. Trade-off: needs a connection (offline = offline screen).
- **iOS = installable PWA** (manifest + service worker + Apple meta tags). No App Store, no Apple account, no IPA.
- Same accounts, login, roles, courses, Battle, Wörterbuch, payments, progress. No second backend, DB or auth system.
  In the Android app the session is kept in Keystore-encrypted storage, not in the WebView storage (`mobile-authentication.md`).

## Status (2026-11-24)

| Part | State | Doc |
|---|---|---|
| Android shell `com.vizuacademy.vizudeutsch` "VIZU-DEUTSCH": icons, splash, theme, permissions, downloads | built; 28 / 28 checks on the Android 15 emulator | `android-capacitor.md`, `mobile-testing.md` |
| Secure session, lock-screen music controls, back button (dialog first, press twice to close), offline banner | built + emulator-tested | `android-capacitor.md` |
| Release signing | release key created 2026-11-23 (`mobile/keys/`, gitignored; copy in `D:\vz_keys`; owner must back it up offline); 1.0.0 + 1.0.1 signed APK + AAB built | `android-capacitor.md` |
| APK release management (admin upload, release script, download, update prompt) | built + tested; 1.0.0 then 1.0.1 (official logo as icon + splash) published on production (see `current-state.md`) | `apk-release-management.md` |
| Logo / icons | the owner's official logo everywhere (web, favicon, PWA, Android launcher / splash / status bar) since 2026-11-24 | `ios-pwa.md`, `android-capacitor.md` |
| `/download` + `/download/android` pages, `/downloads/vizu-deutsch.apk` | built + tested | `apk-release-management.md`, `ios-pwa.md` |
| iOS PWA (manifest, icons, meta, offline) | existing PWA renamed / tuned | `ios-pwa.md` |
| Push notifications | not built (needs Firebase + Web Push keys) | `mobile-notifications.md` |
| Tests | `mobile-testing.md` · Deploy `mobile-deployment.md` · Open points `mobile-known-issues.md` |

## When a new APK is needed

Only when the native shell changes: Capacitor / plugins, permissions, icons, splash, `MainActivity`, package config.
Everything rendered by the website (dashboard, courses, Battle, Wörterbuch, content) updates with a normal web deploy.
