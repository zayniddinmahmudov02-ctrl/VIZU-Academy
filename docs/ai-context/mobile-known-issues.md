# Mobile known issues / next actions (2026-11-23)

1. **Release key backup** (owner): `D:\vz_keys\vizu-deutsch-release.jks` + its password (`README.txt` there) must be copied offline;
   lost key = no updates for installed apps.
2. **Push notifications** not built (`mobile-notifications.md`; needs Firebase project + VAPID keys).
3. **New logo** (`docs/new_logo/`) not delivered: app icons, splash and PWA icons use the current VIZU mark; regenerate with
   `mobile/npm run assets` + new PWA PNGs when it arrives.
4. Real phones still to check by the owner (the emulator run covered the rest, `mobile-testing.md`): mic recording in Sprechen,
   camera picker, App Links opening from Telegram, an update over 1.0.0 with the same key.
5. Blob downloads (e.g. a PDF generated in the page) are not handled by the shell's download listener (https only).
6. Exam answers typed while offline: the network banner warns and nothing reloads, but answers are saved only when the server is
   reachable (the exam pages' own retry).
7. E2E `battle-dashboard` "profile photo … leaderboard" fails once the E2E DB holds many Battle profiles (test data, not app code).
