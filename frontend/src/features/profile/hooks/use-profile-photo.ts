"use client";

import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";

import { CURRENT_USER_QUERY_KEY } from "@/features/auth/hooks/use-current-user";
import type { CurrentUser } from "@/features/auth/types/user";

import { removeProfilePhoto, uploadProfilePhoto } from "../services/profile-service";

/** The photo is also the Battle player picture: refresh the Battle screens that show it. */
function store(queryClient: QueryClient, user: CurrentUser) {
  queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
  for (const key of ["battle-home", "battle-summary", "battle-leaderboard", "battle-match"]) {
    queryClient.invalidateQueries({ queryKey: [key] });
  }
}

export function useUploadProfilePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadProfilePhoto,
    onSuccess: (user) => store(queryClient, user),
  });
}

export function useRemoveProfilePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeProfilePhoto,
    onSuccess: (user) => store(queryClient, user),
  });
}
