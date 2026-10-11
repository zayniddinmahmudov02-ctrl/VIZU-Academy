"use client";

import { useEffect } from "react";

import { loginUrl, readNextParam } from "@/lib/auth-redirect";
import { getToken } from "@/lib/token";

/** Browser back/forward can restore a whole page from the back-forward cache
 * (bfcache) exactly as it was — React effects do not run again, so a page
 * frozen in an old auth state would be shown as-is. On such a restore the
 * session is checked again:
 * - "protected": no session any more -> leave for /login?next=<this page>
 *   (a protected page must never be shown from the cache after logout).
 * - "login": a session exists now -> continue to `next` / the default page
 *   instead of showing a stale login form. */
export function useBfcacheAuthRecheck(mode: "protected" | "login", defaultTarget = "/dashboard") {
  useEffect(() => {
    function onPageShow(event: PageTransitionEvent) {
      if (!event.persisted) return;
      const loggedIn = !!getToken();
      if (mode === "protected" && !loggedIn) {
        window.location.replace(loginUrl());
      } else if (mode === "login" && loggedIn) {
        window.location.replace(readNextParam() ?? defaultTarget);
      }
    }
    window.addEventListener("pageshow", onPageShow);
    return () => window.removeEventListener("pageshow", onPageShow);
  }, [mode, defaultTarget]);
}
