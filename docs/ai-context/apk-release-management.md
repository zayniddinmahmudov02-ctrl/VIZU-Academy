# APK release management

- Table `app_releases` (model `be/models/app_release.py`, migration `f2b6d8a4c1e9`); files in
  `app/protected_storage/app-releases/<random>.apk`. Service `be/services/app_releases/service.py`, APK reader `apk.py`.
- Admin page **App Management** `/admin/app-management` (Super Admin only, API `require_super_admin`).

## Rules (enforced server-side, `service.check_apk`)

- Upload: `.apk`, ≤ 150 MB, a real APK. Package (`ANDROID_PACKAGE` = `com.vizuacademy.vizudeutsch`), versionCode, versionName, minSdk
  and the signing certificate are **read from the file**. Refused: unsigned, debug-signed, other package, a certificate different
  from earlier releases (would break updates), an existing versionCode. Upload = draft (not downloadable).
- Publish: versionCode must be higher than the current latest; exactly one `is_latest` per platform (partial unique index).
- Archive published releases (history kept); delete only drafts (file removed). Audit log entries `APP_RELEASE_*`.

## Public side

- `GET /api/v1/app/releases/latest` metadata (version, size, sha256, min Android, notes, date, `page_url` `/download/android`); 404
  `NO_APP_RELEASE` → the pages show "Bald verfügbar" (never an active button). `GET /api/v1/app/android/latest.apk` stream
  (`application/vnd.android.package-archive`, attachment `VIZU-DEUTSCH-<version>.apk`, no-cache, `X-APK-SHA256`), counts downloads.
  `download_url` (button + update prompt) is `…/latest.apk?v=<versionCode>`: Cloudflare turns no-cache into a 4 h browser cache for
  `.apk`, so every release needs its own URL (the endpoint ignores `v`; `deployment-map.md`).
  Short links (Next redirects): **`/downloads/vizu-deutsch.apk`** (the stable public address) and `/downloads/android/latest.apk`.
- Pages: `/download` (Android + iPhone + desktop QR), **`/download/android`** (icon, description, version, size, date, Android
  7.0+, APK button, install guide in German and Uzbek side by side; `fe/features/mobile-app/components/android-download-view.tsx`).
- Installed app: `NativeAppUpdate` compares `App.getInfo().build` (versionCode) with the latest once per start: "Eine neue Version
  von VIZU-DEUTSCH ist verfügbar." + "Update herunterladen" (DownloadManager, the user installs; same package + key, data kept);
  "Später" holds for the session. Never installed automatically.

## Release procedure

1. Bump versionCode / versionName → signed `assembleRelease bundleRelease` (`android-capacitor.md`) → `apksigner verify`.
2. Either Admin → App Management → upload + notes → "Als aktuell veröffentlichen", or on the server (no admin login needed):
   `python -m app.scripts.app_release_publish plan --apk <file> --notes-file <txt>` → `apply --confirm <plan id> --apk … --notes-file …
   --backup-dir /var/backups/vizu/<dir>` (same `check_apk` rules, JSON copy of the release rows first, audit without a user).
3. Check `/download/android` shows the version and the SHA-256 of `/downloads/vizu-deutsch.apk` matches the file.

Production: 1.0.0 (versionCode 1, 3 289 594 bytes, SHA-256 `96939a72…58574`, signer `EF:1E:4A:05…`) published 2026-11-24 through the
script (plan `16fb3e19b202`); **1.0.1** (versionCode 2, 4 378 784 bytes, SHA-256 `0d5ee536…09c5b`, same signer; new launcher icon + splash =
the official logo) published the same day (plan `14d86c2ac48a`), 1.0.0 kept as history. Public address: `https://vizu-deutsch.com/downloads/vizu-deutsch.apk`.
