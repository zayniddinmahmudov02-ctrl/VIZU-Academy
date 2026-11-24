# iOS web app (PWA) and the download page

## PWA

- Manifest `fe/app/manifest.ts` → `/manifest.webmanifest`: name **VIZU DEUTSCH**, short_name VIZU, `start_url /`, `scope /`,
  standalone, orientation any, theme/background `#0e1834`; icons = the official logo in `fe/public/branding/` (`fe/constants/brand.ts`):
  192 + 512 "any" (tile on transparent), 192 + 512 "maskable" (tile in the safe zone on navy).
- `fe/app/layout.tsx`: `apple-mobile-web-app-capable=yes`, title "VIZU DEUTSCH", status bar `black-translucent`,
  apple-touch-icon 180 (`/branding/apple-touch-icon.png`, tile on navy), favicon `fe/app/favicon.ico` (16/32/48) + `/branding/favicon-32.png`,
  `viewport-fit=cover` (safe areas in `globals.css`), `metadataBase` vizu-deutsch.com.
- Service worker `fe/public/sw.js` (cache v4 since the logo change 2026-11-24; registration `fe/components/pwa/service-worker-registration.tsx`):
  never cached: auth, admin, payments, Battle, `/api/v1/app/*`; other API GETs network-first (cache only when offline, cleared on
  logout); static assets incl. `/branding/` cache-first; offline navigation → `/offline`. Bumping the cache names purges old caches —
  bump again whenever the brand files change (they keep their names).
- All icons come from the owner's logo (`frontend/scripts/generate-brand-assets.py`); check with `npm run verify:pwa` (its old lesson-section
  check at the end fails for unrelated reasons since the lesson sections changed).

## iOS limits (do not promise more)

Works like the website in Safari: login, courses, audio/video, Sprechen mic recording (permission prompt per Safari rules),
file/photo upload, Battle (polling, no WebSocket/3D). No background execution; storage may be cleared by iOS after weeks of
non-use (user then logs in again). Web Push exists only for Home-Screen apps on iOS 16.4+ and is not built yet
(`mobile-notifications.md`). Install only from Safari (other iOS browsers: the guide says so).

## Download page `/download`

`fe/app/download/page.tsx` + `fe/features/mobile-app/components/download-view.tsx`: hero (slogan "Lerne Deutsch. Überall.
Jederzeit."), Android card (APK button + version, size, date, min Android, SHA-256, notes, install steps), iPhone card
(`ios-install-guide.tsx`: 5 steps, non-Safari / in-app-browser warning, copy link), desktop QR. Device detection
`fe/features/mobile-app/utils/platform.ts` (iPadOS desktop UA handled). Entry links: welcome card and dashboard footer
(`app-download-link.tsx`, hidden inside the app). `/app` redirects to `/download`. Strings: `fe/lib/i18n/mobile-app-translations.ts`.
