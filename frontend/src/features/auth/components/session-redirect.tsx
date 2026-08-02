"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "../hooks/use-current-user";

/** If a still-valid session already exists (e.g. the user hits /login again
 * in a fresh tab), skip straight past the form instead of making them log
 * in twice. Renders nothing — the form underneath stays visible during the
 * brief check, and this only redirects once it resolves. */
export default function SessionRedirect() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();

  useEffect(() => {
    if (!loading && user) {
      router.replace(user.role === "SUPER_ADMIN" ? "/admin" : "/dashboard");
    }
  }, [loading, user, router]);

  return null;
}
