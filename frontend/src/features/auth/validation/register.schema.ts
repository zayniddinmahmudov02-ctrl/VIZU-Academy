import { z } from "zod";

import { isValidIdentifier } from "../utils/identifier";

// Messages are translation keys (namespace "auth") — the form renders them
// with t(), so validation errors follow the selected language (DE / UZ).
export const registerSchema = z
  .object({
    fullName: z.string().trim().min(1, "auth.errRequired").min(2, "auth.errFullName").max(120, "auth.errFullName"),
    identifier: z
      .string()
      .trim()
      .min(1, "auth.errRequired")
      .refine(isValidIdentifier, "auth.errIdentifierInvalid"),
    password: z.string().min(1, "auth.errRequired").min(6, "auth.errPasswordMin").max(128, "auth.errPasswordMin"),
    confirmPassword: z.string().min(1, "auth.errRequired"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "auth.errPasswordMismatch",
    path: ["confirmPassword"],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;
