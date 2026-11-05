# Mobile deployment

- Web side (download page, admin, PWA, update prompt, `/app` API) ships with the normal deploy (skill `vizu-deploy`):
  backup → migration `f2b6d8a4c1e9` (one new table) → backend restart → frontend slot deploy → smoke.
- Storage: `backend/app/protected_storage/app-releases/` (created on first upload; in the server backup like other
  protected storage). nginx must allow the APK upload size (`client_max_body_size` ≥ the APK, check before the first upload).
- Smoke after deploy: `/download` 200, `/manifest.webmanifest` name "VIZU DEUTSCH", `/api/v1/app/releases/latest` 404 until
  the first release (then 200), `/api/v1/admin/app-releases` anonymous 401, `/downloads/android/latest.apk` 307.
- APK itself is not deployed with git: the owner builds and signs it and uploads it in App Management
  (`apk-release-management.md`). Rollback of an APK = publish a newer versionCode (Android cannot downgrade in place).
