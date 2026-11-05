# Mobile testing

- Backend: `tests/test_app_releases.py` (APK reader with generated manifests + PKCS#7 signers, API contract, HTTP 401/403,
  release rules on PostgreSQL), `tests/test_app_releases_migration.py`, `/app/*` in `test_route_protection` allowlist.
- Frontend unit: `tests/unit/mobile-platform.test.mjs` (UA detection incl. iPadOS, update compare, sizes, checksum).
- E2E `e2e/tests/mobile-app.spec.ts` (local stack; desktop + Pixel 7 + iPhone Safari 360 px + iPhone Chrome 390 px):
  download page, guide, QR, manifest/meta, no horizontal scroll; admin flow (debug APK refused, signed upload, publish,
  version must grow, APK bytes = SHA-256); update prompt with a simulated `window.Capacitor`. Needs the test APKs from
  `D:\vz_tmp\work\build_test_apks.ps1` (throwaway key) and `mobile` debug build; clears `app_releases` in `vizu_gcr_e2e`.
- Android emulator (`D:\Android\Sdk\emulator\emulator.exe -avd vizu35 -no-window`, `adb install`, screenshots via
  `adb shell screencap -p /sdcard/s.png` + `adb pull` — PowerShell `>` corrupts binary output). Checked 2026-11-05 on
  Android 15: install, splash, live site full-screen, in-app navigation, back button, offline screen.
- Not yet checked on real hardware: mic recording + upload in the APK, camera/gallery picker, APK update install over an
  older version, weak devices; iOS Home-Screen install on a real iPhone/iPad (no Apple device here).
