# Mobile testing

- Backend: `tests/test_app_releases.py` (APK reader with generated manifests + PKCS#7 signers, API contract, HTTP 401/403,
  release rules on PostgreSQL, the release script plan / apply / refusals), `tests/test_app_releases_migration.py`, `/app/*` in
  `test_route_protection` allowlist.
- Frontend unit: `tests/unit/mobile-platform.test.mjs` (UA detection incl. iPadOS, update compare, sizes, checksum),
  `tests/unit/native-back-button.test.mjs` (dialog first, back, start page twice to close).
- E2E `e2e/tests/mobile-app.spec.ts` (local stack; desktop + Pixel 7 + iPhone Safari 360 px + iPhone Chrome 390 px):
  download page, guide, QR, manifest/meta, no horizontal scroll; admin flow (debug APK refused, signed upload, publish,
  version must grow, APK bytes = SHA-256); `/download/android` (facts, real APK bytes, German + Uzbek guide, `/downloads/vizu-deutsch.apk`);
  update prompt with a simulated `window.Capacitor`. Needs the test APKs from `D:\vz_tmp\work\build_test_apks.ps1` (throwaway key,
  current package) and the `mobile` debug build; clears `app_releases` in `vizu_gcr_e2e`.
- **Real Android emulator run** (2026-11-23, Android 15, WebView 124): `D:\vz_tmp\work\device\device_test.cjs` drives the app's
  WebView over the raw DevTools protocol (Playwright cannot attach to a WebView) + adb, against a debug build whose
  `server.url` points at the local stack (`adb reverse` 3000 / 8000; temporary config, restored afterwards). 28 / 28: plugins in
  the page, session injected, login, no token in browser storage, session after restart, update screen, back (dialog first,
  exit hint, second press closes, inner page back), music plays, MediaSession PLAYING, media notification, PAUSE / PLAY from the
  system reach the page, music continues with the app in the background, offline banner + recovery, logout + restart = logged out.
  Also checked: PDF reader (needed the pdf.js legacy build on WebView 124) and video playback.
  2026-11-24: the release APK downloaded from `https://vizu-deutsch.com/downloads/vizu-deutsch.apk` (SHA-256 = the built file) installs
  on the emulator (1.0.0 / code 1), opens the live site, and Back on the start page shows the exit hint (no login: no test users on production).
  Emulator: `ANDROID_AVD_HOME=D:\Android\.android\avd emulator -avd vizu35 -no-window -gpu swiftshader_indirect`.
- Not yet checked on real hardware: mic recording + upload in the APK, camera/gallery picker, APK update install over an
  older version, weak devices; iOS Home-Screen install on a real iPhone/iPad (no Apple device here).
