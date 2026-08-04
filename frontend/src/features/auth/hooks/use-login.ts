"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { loginService } from "../services/auth.service";
import { CURRENT_USER_QUERY_KEY } from "./use-current-user";

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: loginService,
    // A stale cached user from a previous session (e.g. someone else logged
    // out and back in as a different account in the same tab) must not
    // leak into the freshly authenticated session.
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    },
  });
}