"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { CURRENT_USER_QUERY_KEY } from "@/features/auth/hooks/use-current-user";

import { updateProfile } from "../services/profile-service";

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateProfile,
    onSuccess: (user) => {
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
    },
  });
}
