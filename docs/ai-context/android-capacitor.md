# Android app (Capacitor)

## Project

- Folder `mobile/`: `package.json` (pinned Capacitor 8.5.3, app 8.1.2, splash-screen 8.0.2, status-bar 8.0.4, sharp 0.34.5),
  `capacitor.config.json`, `www/` (only `offline.html` matters: shown when the site cannot load), `android/` (native project),
  `assets/vizu-mark.svg` + `scripts/generate-assets.mjs` (launcher, round, adaptive, splash images; `npm run assets`).
- App: name **VIZU DEUTSCH**, package **`com.vizu.deutsch`** (never change: updates would break), minSdk 24 (Android 7.0),
  target/compile SDK 36. Version: `android/app/build.gradle` `versionCode` / `versionName` (or `-PvizuVersionCode=…
  -PvizuVersionName=…`). versionCode must grow with every release.
- WebView: `server.url = https://vizu-deutsch.com`; other hosts open in the system browser (Capacitor default); back button =
  WebView history; `allowBackup=false` (session must not leave the device); debugging off; UA suffix `VIZU-DEUTSCH-Android`.
- Permissions: INTERNET, ACCESS_NETWORK_STATE, RECORD_AUDIO + MODIFY_AUDIO_SETTINGS (Sprechen), CAMERA (photo in the file
  picker). Mic/camera are asked at runtime by Capacitor when the page calls getUserMedia / opens the picker; denial = the
  page's normal "no permission" state, no crash.
- `MainActivity.java`: https downloads go to Android DownloadManager (notification; user installs). No silent install.
- App Links: intent filter for `https://vizu-deutsch.com` (`autoVerify`); works after `/.well-known/assetlinks.json` lists the
  release certificate SHA-256 (todo, `mobile-known-issues.md`).
- Gradle wrapper must stay 8.14.x (AGP 8.13 breaks on Gradle ≥ 9.6; something rewrote it to 9.7.1 once on 2026-11-05).

## Build environment (Windows, all on D:)

- JDK 21 `D:\Android\jdk-21`, SDK `D:\Android\Sdk` (platform-tools, platforms 35/36, build-tools 35/36, emulator, image
  `android-35 google_apis x86_64`), AVD `vizu35` in `D:\Android\.android\avd`. User env: `JAVA_HOME`, `ANDROID_HOME`,
  `ANDROID_SDK_ROOT`, `ANDROID_USER_HOME`, `GRADLE_USER_HOME=D:\Android\.gradle`. No Android Studio needed.
- Build: `cd mobile; npm ci; npx cap sync android; cd android; .\gradlew.bat assembleDebug` (or `assembleRelease`). From
  PowerShell call `.\gradlew.bat` directly (`cmd /c` loses the directory). Output `android/app/build/outputs/apk/`.

## Release signing (owner)

1. Create the keystore once, outside the repo (owner chooses the password; back it up — losing it = no more updates):
   `D:\Android\jdk-21\bin\keytool -genkeypair -v -keystore D:\vz_keys\vizu-release.jks -alias vizu -keyalg RSA -keysize 4096 -validity 10000`
2. Before `assembleRelease` set (session only): `VIZU_KEYSTORE_PATH`, `VIZU_KEYSTORE_PASSWORD`, `VIZU_KEY_ALIAS`,
   `VIZU_KEY_PASSWORD`. Without them the release APK is unsigned and the admin upload refuses it.
3. Check: `D:\Android\Sdk\build-tools\36.0.0\apksigner.bat verify --print-certs <apk>`.
`*.jks`, `*.keystore` are git-ignored. Test builds use a throwaway key in `D:\vz_tmp\work\apk-test` (never production).
