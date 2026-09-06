"use client";

import { useEffect } from "react";

/** Registers /sw.js once the app has mounted. A service worker only
 * ever runs in a secure context (HTTPS, or localhost for dev) — the
 * browser itself refuses registration anywhere else, so no extra guard
 * is needed here beyond feature-detecting the API. Renders nothing. */
export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    navigator.serviceWorker.register("/sw.js").catch((error) => {
      // Registration failing (e.g. unsupported browser, insecure
      // context in some edge deployment) must never break the app —
      // the site keeps working exactly as a normal website. But
      // swallowing the error completely left zero way to diagnose a
      // real production failure (wrong MIME type, non-HTTPS origin,
      // scope conflict, syntax error in sw.js, etc.) — surfaced to the
      // console (not the UI) so it's visible in DevTools without being
      // user-facing.
      console.error("[PWA] Service worker registration failed:", error);
    });
  }, []);

  return null;
}
