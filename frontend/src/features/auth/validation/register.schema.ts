import { z } from "zod";

// Messages are translation keys (namespace "auth") — the form renders them
// with t(), so validation errors follow the selected language (DE / UZ).
export const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, "auth.errUsernameMin")
      .regex(/^[a-zA-Z0-9_]+$/, "auth.errUsernameChars"),
    email: z.email("auth.errEmailInvalid"),
    password: z.string().min(6, "auth.errPasswordMin"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "auth.errPasswordMismatch",
    path: ["confirmPassword"],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;
