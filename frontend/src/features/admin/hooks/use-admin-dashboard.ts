"use client";

import { useEffect, useState } from "react";

import { getDashboardOverview } from "../services/dashboard-service";
import type { AdminDashboardOverview } from "../types/dashboard";

interface UseAdminDashboardResult {
  data: AdminDashboardOverview | null;
  loading: boolean;
  error: boolean;
}

export function useAdminDashboard(): UseAdminDashboardResult {
  const [data, setData] = useState<AdminDashboardOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const overview = await getDashboardOverview();
        if (isMounted) setData(overview);
      } catch (err) {
        console.warn("Failed to load admin dashboard overview:", err);
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

  return { data, loading, error };
}
