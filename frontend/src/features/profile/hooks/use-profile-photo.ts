"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { CURRENT_USER_QUERY_KEY } from "@/features/auth/hooks/use-current-user";

import { removeProfilePhoto, uploadProfilePhoto } from "../services/profile-service";

export function useUploadProfilePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadProfilePhoto,
    onSuccess: (user) => {
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
    },
  });
}

export function useRemoveProfilePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeProfilePhoto,
    onSuccess: (user) => {
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
    },
  });
}
