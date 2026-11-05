# Mobile known issues / next actions (2026-11-05)

1. **Release keystore** not created yet (owner). Until then no production APK; `/download` shows "Bald verfügbar".
2. **App Links**: add `frontend/public/.well-known/assetlinks.json` with package `com.vizu.deutsch` and the release
   certificate SHA-256 once the keystore exists; without it links open in the browser (app still works).
3. **Push notifications** not built (`mobile-notifications.md`; needs Firebase project + VAPID keys).
4. **New logo** (`docs/new_logo/`) not delivered: app icons, splash and PWA icons use the current VIZU mark; regenerate with
   `mobile/npm run assets` + new PWA PNGs when it arrives.
5. Real-device checks still open (`mobile-testing.md`): mic recording in the APK, camera picker, update over an older APK,
   iPhone Home-Screen install.
6. Battle is polling-based (no WebSocket, no WebGL/3D), so the requested 3D quality levels / 2D fallback do not apply.
7. Blob downloads (e.g. admin "APK" button, PDF generated in the page) are not handled by the Android shell's download
   listener (https only); student certificate PDF download inside the APK needs a check.
8. E2E `battle-dashboard` "profile photo … leaderboard" fails once the E2E DB holds many Battle profiles (new 0-BP user not
   on page 1); test-data issue, not app code — reset `vizu_gcr_e2e` Battle data or make the test look up its own row.
