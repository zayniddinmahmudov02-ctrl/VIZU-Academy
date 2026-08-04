"use client";

import { useQuery } from "@tanstack/react-query";

import { getToken } from "@/lib/token";

import { getCurrentUser } from "../services/user-service";
import type { CurrentUser } from "../types/user";

interface UseCurrentUserResult {
  user: CurrentUser | null;
  loading: boolean;
  error: boolean;
}

/** The one shared cache key for "who is logged in" — every caller below
 * reads this same React Query cache entry instead of firing its own
 * `/users/me` request, so an admin session with AdminGuard + AdminHeader +
 * a settings page mounted together still issues exactly one request, not
 * three. Exported so the login/logout flows can invalidate it on session
 * change (see use-login.ts, admin-header.tsx, dashboard/header.tsx). */
export const CURRENT_USER_QUERY_KEY = ["current-user"] as const;

export function useCurrentUser(): UseCurrentUserResult {
  const hasToken = typeof window !== "undefined" && !!getToken();

  const { data, isLoading, isError } = useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: getCurrentUser,
    // No token at all -> definitely unauthenticated, skip the guaranteed
    // 401 instead of firing it just to find that out.
    enabled: hasToken,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  return {
    user: data ?? null,
    loading: hasToken && isLoading,
    error: hasToken && isError,
  };
}
