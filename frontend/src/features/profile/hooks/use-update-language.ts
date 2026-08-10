"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { CURRENT_USER_QUERY_KEY } from "@/features/auth/hooks/use-current-user";

import { updateLanguage } from "../services/profile-service";

export function useUpdateLanguage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateLanguage,
    onSuccess: (user) => {
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
    },
  });
}
