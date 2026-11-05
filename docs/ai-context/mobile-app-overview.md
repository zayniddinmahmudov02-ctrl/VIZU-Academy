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
- Same accounts, login (JWT in WebView storage, as on the web), courses, Battle, Wörterbuch, payments, progress.
  No second backend, DB or auth system.

## Status (2026-11-05)

| Part | State | Doc |
|---|---|---|
| Android shell, icons, splash, permissions, back button, downloads | built, debug + test-signed release verified on Android 15 emulator | `android-capacitor.md` |
| Release signing | waits for the owner's release keystore | `android-capacitor.md` |
| APK release management (admin upload, publish, download, update prompt) | built + tested locally | `apk-release-management.md` |
| `/download` page (Android card, iPhone guide, desktop QR) | built + tested locally | `ios-pwa.md` |
| iOS PWA (manifest, icons, meta, offline) | existing PWA renamed / tuned | `ios-pwa.md` |
| Push notifications | not built (needs Firebase + Web Push keys) | `mobile-notifications.md` |
| Auth on mobile | unchanged existing auth | `mobile-authentication.md` |
| Tests | `mobile-testing.md` · Deploy `mobile-deployment.md` · Open points `mobile-known-issues.md` |

## When a new APK is needed

Only when the native shell changes: Capacitor / plugins, permissions, icons, splash, `MainActivity`, package config.
Everything rendered by the website (dashboard, courses, Battle, Wörterbuch, content) updates with a normal web deploy.
