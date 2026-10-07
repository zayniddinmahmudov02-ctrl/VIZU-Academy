import { z } from "zod";

// Same password policy as registration; messages are "auth" translation keys.
export const resetPasswordSchema = z
  .object({
    password: z.string().min(6, "auth.errPasswordMin").max(128, "auth.errPasswordMin"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "auth.errPasswordMismatch",
    path: ["confirmPassword"],
  });

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
