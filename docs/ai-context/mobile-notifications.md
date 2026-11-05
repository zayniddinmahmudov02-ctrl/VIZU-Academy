# Mobile notifications

Status 2026-11-05: **no push**. In-app notifications (bell, `/notifications`, backend `notifications` + admin
`/admin/notifications`) work unchanged in the Android app and the iOS PWA.

What push would need (owner input, then build):
- **Android:** a Firebase project → `mobile/android/app/google-services.json` (build.gradle applies the plugin when present),
  `@capacitor/push-notifications`, a FCM service-account key on the server (setting name only in docs), a device-token table
  (user, token, platform, created/last seen; delete on logout / token refresh), sending from the notification service.
- **iOS (16.4+, Home-Screen app only):** Web Push with VAPID keys (server settings), a push handler in `sw.js`, permission asked
  only after an explicit user tap, subscription table as above.
- Types planned: new lesson, course update, Battle invitation / opponent found, rank up, certificate ready, account notices;
  per-type opt-out in Settings. Devices without push keep the in-app list.
