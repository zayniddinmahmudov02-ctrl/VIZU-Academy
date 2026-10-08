import { z } from "zod";

// Messages are translation keys (namespace "auth") — the forms render them
// with t(), so validation errors follow the selected language (DE / UZ).
// Login only checks that something was entered: existing accounts must keep
// working whatever their identifier / password format.
export const loginSchema = z.object({
  identifier: z.string().trim().min(1, "auth.errRequired"),
  password: z.string().min(1, "auth.errRequired"),
});

export type LoginFormData = z.infer<typeof loginSchema>;
