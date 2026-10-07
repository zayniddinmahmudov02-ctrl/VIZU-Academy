import { z } from "zod";

// Messages are translation keys (namespace "auth") — the form renders them
// with t(), so validation errors follow the selected language (DE / UZ).
export const registerSchema = z
  .object({
    fullName: z.string().trim().min(2, "auth.errFullName").max(120, "auth.errFullName"),
    email: z.email("auth.errEmailInvalid"),
    password: z.string().min(6, "auth.errPasswordMin").max(128, "auth.errPasswordMin"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "auth.errPasswordMismatch",
    path: ["confirmPassword"],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;
