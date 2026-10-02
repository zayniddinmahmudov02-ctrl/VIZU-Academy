import { z } from "zod";

// Messages are translation keys (namespace "auth") — the forms render them
// with t(), so validation errors follow the selected language (DE / UZ).
export const loginSchema = z.object({
  email: z.email("auth.errEmailInvalid"),
  password: z.string().min(6, "auth.errPasswordMin"),
});

export type LoginFormData = z.infer<typeof loginSchema>;
