# Android app (Capacitor)

## Project

- Folder `mobile/`: `package.json` (pinned Capacitor 8.5.3, app 8.1.2, splash-screen 8.0.2, status-bar 8.0.4, sharp 0.34.5),
  `capacitor.config.json`, `www/` (only `offline.html` matters: shown when the site cannot load), `android/` (native project),
  `keys/` (release key, gitignored, see below). Icons since 1.0.1 (2026-11-24) = the official logo: launcher (legacy = the tile,
  round = tile on a navy circle, adaptive foreground = tile inside the 66 dp safe zone on `@color/ic_launcher_background` navy),
  splash (navy + tile), Android 12+ splash icon, status-bar icon `drawable-*/ic_stat_vizu.png` (the tile's gold / white parts as
  white) — all written by `frontend/scripts/generate-brand-assets.py` (`npm run assets` runs it); `assets/vizu-logo.png` = copy.
- App: name **VIZU-DEUTSCH**, package **`com.vizuacademy.vizudeutsch`** (set 2026-11-23 before the first published release, owner's
  spec; never change it again: another package = another app, no updates), minSdk 24 (Android 7.0), target/compile SDK 36.
  Version: `android/app/build.gradle` `versionCode` / `versionName` (or `"-PvizuVersionCode=…" "-PvizuVersionName=…"` — quote them in
  PowerShell, else `1.0.0` is split). versionCode must grow with every release.
- WebView: `server.url = https://vizu-deutsch.com`; other hosts open in the system browser (Capacitor default); `allowBackup=false`;
  debugging off; UA suffix `VIZU-DEUTSCH-Android`. Theme: navy status / navigation bar, Android 12+ splash = navy + the official logo.
- Permissions: INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO + MODIFY_AUDIO_SETTINGS (Sprechen), CAMERA (photo in the file picker),
  FOREGROUND_SERVICE + FOREGROUND_SERVICE_MEDIA_PLAYBACK + POST_NOTIFICATIONS (music with the screen off).
- Native code (`android/app/src/main/java/com/vizuacademy/vizudeutsch/`):
  - `MainActivity.java`: registers the two app plugins; https downloads go to the Android DownloadManager (notification; the user
    installs). http / blob downloads are ignored on purpose. No silent install.
  - `SecureSessionPlugin.java` (`VizuSession`): the login session in AES-256-GCM-encrypted SharedPreferences with a key inside the
    Android Keystore ("Angemeldet bleiben" off = memory only); handed to the page before its scripts run by a document-start script
    for the app's own origin only (`window.__VIZU_SESSION__`; never other origins / embedded frames). The website
    (`fe/lib/token.ts`) then never writes tokens to localStorage and moves tokens of an older install once. Rules:
    `mobile-authentication.md`.
  - `MediaSessionPlugin.java` (`VizuMedia`) + `MediaPlaybackService.java`: the Musik player mirrored into a MediaSession + media
    notification (lock screen, headset): play / pause / previous / next / stop / seek go back to the page
    (`fe/features/medien/hooks/use-native-media.ts`); foreground service of type mediaPlayback only while the user plays; removing
    the app from the recents ends it. Small icon `res/drawable-*/ic_stat_vizu.png`.
- Back button (`fe/components/pwa/native-back-button.tsx` + pure `fe/features/mobile-app/utils/back-button.ts`): an open dialog /
  drawer closes first (Escape), inner pages go back (no history → the panel's start page), on /dashboard, /teacher, /admin, /login a
  first press shows "Zum Beenden erneut drücken", a second one within 2 s closes the app.
- Offline: `www/offline.html` when the site cannot load; a connection that drops while a page is open shows
  `fe/components/pwa/network-status.tsx` (every platform; refetches when back, no reload, login kept).
- App Links: intent filter for `https://vizu-deutsch.com` (`autoVerify`) + `frontend/public/.well-known/assetlinks.json`
  (package + release certificate SHA-256).
- Gradle wrapper must stay 8.14.x (AGP 8.13 breaks on Gradle ≥ 9.6).

## Build environment (Windows, all on D:)

- JDK 21 `D:\Android\jdk-21`, SDK `D:\Android\Sdk` (platform-tools, platforms 35/36, build-tools 35/36, emulator, image
  `android-35 google_apis x86_64`), AVD `vizu35` (start with `ANDROID_AVD_HOME=D:\Android\.android\avd`; its WebView is 124 = old,
  good for compatibility checks). User env: `JAVA_HOME`, `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `ANDROID_USER_HOME`,
  `GRADLE_USER_HOME=D:\Android\.gradle`. No Android Studio needed (the `android/` folder opens in Android Studio as is).
- Build: `cd mobile; npm ci; npx cap sync android; cd android; .\gradlew.bat assembleDebug` (debug APK) /
  `assembleRelease bundleRelease` (signed APK + AAB). Output `android/app/build/outputs/{apk,bundle}/`.

## Release signing

- Key (created 2026-11-23): `mobile/keys/vizu-deutsch-release.jks` (owner's wish 2026-11-24: kept in the project, local only —
  ignored by Git through `mobile/keys/`, `*.jks`, `*.dpapi` in the root `.gitignore` + `mobile/keys/.gitignore` = `*`; never force-add)
  (PKCS12, alias `vizu-deutsch`, RSA 4096, valid to 2054), password only in `mobile/keys/vizu-deutsch-release.pass.dpapi` (Windows
  DPAPI, this user); folder readable by this user only; `mobile/keys/README.txt` = backup + signing steps. Same two files also in
  `D:\vz_keys\`. Certificate SHA-256
  `EF:1E:4A:05:0C:50:1C:BC:E2:F4:DF:6F:24:48:D9:F3:44:64:FF:36:8B:52:FF:96:68:CE:DC:0B:E5:4E:00:0C`.
  **Losing the key = no more updates** (owner must back up the .jks + password offline). Never in Git, chat, docs.
- Gradle reads `VIZU_KEYSTORE_PATH`, `VIZU_KEYSTORE_PASSWORD`, `VIZU_KEY_ALIAS`, `VIZU_KEY_PASSWORD` (session env only; without them
  the release APK is unsigned and the server refuses it). Check: `apksigner verify --print-certs <apk>` (v2 scheme; v1 is not used
  with minSdk 24).
- E2E test APKs use a throwaway key in `D:\vz_tmp\work\apk-test` (`build_test_apks.ps1`; never production).
- Releases: 1.0.0 (code 1, 2026-11-24), 1.0.1 (code 2, 2026-11-24: new launcher icon + splash = official logo; installed over 1.0.0
  on the emulator with the same key, data kept). Deliverables `D:\vz_tmp\work\apk-release\` (+ `SHA256SUMS.txt`).
