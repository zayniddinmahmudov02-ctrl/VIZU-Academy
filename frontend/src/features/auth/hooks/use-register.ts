"use client";

import { useMutation } from "@tanstack/react-query";

import { registerService } from "../services/auth.service";

export function useRegister() {
  return useMutation({
    mutationFn: registerService,
  });
}
