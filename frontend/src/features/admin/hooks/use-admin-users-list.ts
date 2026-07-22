"use client";

import { useCallback, useEffect, useState } from "react";

import { listUsers } from "../services/users-service";
import type { AdminUserListResponse, UserListQuery } from "../types/user";

const DEFAULT_QUERY: UserListQuery = {
  page: 1,
  pageSize: 20,
  sortBy: "created_at",
  sortDir: "desc",
};

export function useAdminUsersList() {
  const [query, setQuery] = useState<UserListQuery>(DEFAULT_QUERY);
  const [data, setData] = useState<AdminUserListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchList = useCallback(() => {
    setLoading(true);
    setError(false);

    listUsers(query)
      .then(setData)
      .catch((err) => {
        console.warn("Failed to load users:", err);
        setError(true);
      })
      .finally(() => setLoading(false));
  }, [query]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const setSearch = (search: string) => setQuery((q) => ({ ...q, search: search || undefined, page: 1 }));
  const setRole = (role: string | undefined) => setQuery((q) => ({ ...q, role, page: 1 }));
  const setStatus = (status: string | undefined) => setQuery((q) => ({ ...q, status, page: 1 }));
  const setTag = (tag: string | undefined) => setQuery((q) => ({ ...q, tag, page: 1 }));
  const setPage = (page: number) => setQuery((q) => ({ ...q, page }));
  const setSort = (sortBy: string) =>
    setQuery((q) => ({
      ...q,
      sortBy,
      sortDir: q.sortBy === sortBy && q.sortDir === "asc" ? "desc" : "asc",
      page: 1,
    }));

  return {
    query,
    data,
    loading,
    error,
    refetch: fetchList,
    setSearch,
    setRole,
    setStatus,
    setTag,
    setPage,
    setSort,
  };
}
