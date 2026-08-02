import { z } from "zod";

export const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, "Benutzername muss mindestens 3 Zeichen lang sein.")
      .regex(/^[a-zA-Z0-9_]+$/, "Nur Buchstaben, Zahlen und Unterstriche erlaubt."),
    email: z.email("Please enter a valid email."),
    password: z.string().min(6, "Password must be at least 6 characters."),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;
