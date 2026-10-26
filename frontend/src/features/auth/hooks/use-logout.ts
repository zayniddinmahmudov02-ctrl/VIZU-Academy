"use client";

import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { getRefreshToken, removeRefreshToken, removeToken } from "@/lib/token";

import { logoutService } from "../services/auth.service";
import { CURRENT_USER_QUERY_KEY } from "./use-current-user";

/** Student logout (header menu + mobile menu): clears the local session,
 * leaves for /login without keeping the protected page in history, and
 * revokes the refresh token server-side (best effort — the local session is
 * gone either way). */
export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return async function logout() {
    const refreshToken = getRefreshToken();

    removeToken();
    removeRefreshToken();
    queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    router.replace("/login");

    if (refreshToken) {
      try {
        await logoutService(refreshToken);
      } catch {
        // already logged out locally; the token expires on its own
      }
    }
  };
}
