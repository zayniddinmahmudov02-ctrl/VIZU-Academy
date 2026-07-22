"use client";

import { useEffect, useState } from "react";

import { getCurrentUser } from "../services/user-service";
import type { CurrentUser } from "../types/user";

interface UseCurrentUserResult {
  user: CurrentUser | null;
  loading: boolean;
  error: boolean;
}

export function useCurrentUser(): UseCurrentUserResult {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const data = await getCurrentUser();
        if (isMounted) setUser(data);
      } catch (err) {
        console.warn("Failed to load current user:", err);
        if (isMounted) setError(true);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, []);

  return { user, loading, error };
}
