import { z } from "zod";

export const profileSchema = z.object({
  firstName: z.string().max(100, "Maximal 100 Zeichen.").optional().or(z.literal("")),
  lastName: z.string().max(100, "Maximal 100 Zeichen.").optional().or(z.literal("")),
  phoneNumber: z.string().max(30, "Maximal 30 Zeichen.").optional().or(z.literal("")),
  country: z.string().max(100, "Maximal 100 Zeichen.").optional().or(z.literal("")),
});

export type ProfileFormData = z.infer<typeof profileSchema>;

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, "Bitte gib dein aktuelles Passwort ein."),
    newPassword: z.string().min(6, "Das neue Passwort muss mindestens 6 Zeichen lang sein."),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Die Passwörter stimmen nicht überein.",
    path: ["confirmPassword"],
  })
  .refine((data) => data.currentPassword !== data.newPassword, {
    message: "Das neue Passwort muss sich vom aktuellen unterscheiden.",
    path: ["newPassword"],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export const ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024;
