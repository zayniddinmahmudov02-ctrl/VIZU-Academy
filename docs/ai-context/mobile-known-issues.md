# Mobile known issues / next actions (2026-11-24)

1. **Release key backup** (owner): `mobile/keys/vizu-deutsch-release.jks` (= `D:\vz_keys\…`) + its password (`README.txt` there) must
   ALSO be copied offline (both copies are on the same disk); lost key = no updates for installed apps.
2. **Push notifications** not built (`mobile-notifications.md`; needs Firebase project + VAPID keys).
3. Logo source quality: `known-issues.md` #35.
4. Real phones still to check by the owner (the emulator run covered the rest, `mobile-testing.md`): mic recording in Sprechen,
   camera picker, App Links opening from Telegram. (Update 1.0.0 → 1.0.1 with the same key: checked on the emulator.)
5. Blob downloads (e.g. a PDF generated in the page) are not handled by the shell's download listener (https only).
6. Exam answers typed while offline: the network banner warns and nothing reloads, but answers are saved only when the server is
   reachable (the exam pages' own retry).
7. E2E `battle-dashboard` "profile photo … leaderboard" fails once the E2E DB holds many Battle profiles (test data, not app code).
