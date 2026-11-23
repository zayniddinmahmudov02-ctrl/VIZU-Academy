"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { readNextParam } from "@/lib/auth-redirect";

import { useBfcacheAuthRecheck } from "../hooks/use-bfcache-auth-recheck";
import { useCurrentUser } from "../hooks/use-current-user";

/** If a still-valid session already exists (e.g. the user hits /login again
 * in a fresh tab), skip straight past the form instead of making them log
 * in twice. Renders nothing — the form underneath stays visible during the
 * brief check, and this only redirects once it resolves. */
export default function SessionRedirect() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const home = user?.role === "SUPER_ADMIN" ? "/admin" : user?.role === "TEACHER" ? "/teacher" : "/dashboard";
  // back/forward to an old /login page while logged in: continue, no stale form
  useBfcacheAuthRecheck("login", home);

  useEffect(() => {
    if (!loading && user) {
      router.replace(readNextParam() ?? home);
    }
  }, [loading, user, router, home]);

  return null;
}
