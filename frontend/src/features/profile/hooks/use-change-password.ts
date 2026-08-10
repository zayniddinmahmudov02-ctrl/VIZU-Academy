"use client";

import { useMutation } from "@tanstack/react-query";

import { changePassword } from "../services/profile-service";

export function useChangePassword() {
  return useMutation({
    mutationFn: changePassword,
  });
}
