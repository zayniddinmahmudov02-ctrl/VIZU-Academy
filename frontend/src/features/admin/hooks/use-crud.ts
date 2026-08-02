"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { CrudApi } from "../lib/crud-api";

/** One hook pair (list + mutations) reused by every content-type manager —
 * the CRUD shape is identical everywhere, only the endpoint/types differ. */
export function useCrudList<TResponse>(
  key: string,
  api: Pick<CrudApi<TResponse, unknown, unknown>, "list">,
  params?: Record<string, string>,
) {
  return useQuery({
    queryKey: [key, params],
    queryFn: () => api.list(params),
  });
}

export function useCrudMutations<TResponse, TCreate, TUpdate>(
  key: string,
  api: CrudApi<TResponse, TCreate, TUpdate>,
) {
  const queryClient = useQueryClient();

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: [key] });

  const create = useMutation({
    mutationFn: (data: TCreate) => api.create(data),
    onSuccess: invalidate,
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TUpdate }) =>
      api.update(id, data),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.remove(id),
    onSuccess: invalidate,
  });

  return { create, update, remove };
}
