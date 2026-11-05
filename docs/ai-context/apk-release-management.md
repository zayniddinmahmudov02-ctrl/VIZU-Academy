# APK release management

- Table `app_releases` (model `be/models/app_release.py`, migration `f2b6d8a4c1e9`); files in
  `app/protected_storage/app-releases/<random>.apk`. Service `be/services/app_releases/service.py`, APK reader `apk.py`.
- Admin page **App Management** `/admin/app-management` (Super Admin only, API `require_super_admin`).

## Rules (enforced server-side)

- Upload: `.apk`, ≤ 150 MB, a real APK. Package, versionCode, versionName, minSdk and the signing certificate are **read from
  the file** (form fields cannot override). Refused: unsigned, debug-signed, other package, a certificate different from
  earlier releases (would break updates), an existing versionCode. Upload = draft (not downloadable).
- Publish: versionCode must be higher than the current latest; exactly one `is_latest` per platform (partial unique index).
- Archive published releases (history kept); delete only drafts (file removed). Audit log entries `APP_RELEASE_*`.
- Note: the certificate is read, not cryptographically verified — Android verifies on install; the check prevents mistakes.

## Public side

- `GET /api/v1/app/releases/latest` metadata (version, size, sha256, min Android, notes, date); 404 `NO_APP_RELEASE` → page
  shows "Bald verfügbar". `GET /api/v1/app/android/latest.apk` stream (`application/vnd.android.package-archive`, attachment
  `VIZU-DEUTSCH-<version>.apk`, no-cache, `X-APK-SHA256`), counts downloads. Short link `/downloads/android/latest.apk` (Next
  redirect). QR: `GET /api/v1/app/download-qr.svg` → `PUBLIC_SITE_URL/download`.
- Installed app: `NativeAppUpdate` compares `App.getInfo().build` (versionCode) with the latest once per start; "Später" holds
  for the session; download via DownloadManager; the user installs (same package + same key, data kept).

## Release procedure

1. Bump versionCode/versionName → signed `assembleRelease` (`android-capacitor.md`) → `apksigner verify`.
2. Admin → App Management → upload + release notes → check version/size/signature → "Als aktuell veröffentlichen".
3. Check `/download` shows the version and the SHA-256 matches the file.
