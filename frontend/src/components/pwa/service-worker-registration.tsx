"use client";

import { useEffect } from "react";

/** Registers /sw.js once the app has mounted. A service worker only
 * ever runs in a secure context (HTTPS, or localhost for dev) — the
 * browser itself refuses registration anywhere else, so no extra guard
 * is needed here beyond feature-detecting the API. Renders nothing. */
export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Registration failing (e.g. unsupported browser, insecure
      // context in some edge deployment) must never break the app —
      // the site keeps working exactly as a normal website.
    });
  }, []);

  return null;
}
