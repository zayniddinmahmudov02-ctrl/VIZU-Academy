"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle, MailCheck } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";

import { forgotPasswordService } from "../services/auth.service";
import { getErrorMessage } from "../utils/get-error-message";

const forgotPasswordSchema = z.object({
  email: z.email("Please enter a valid email."),
});

type ForgotPasswordData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordForm() {
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  async function onSubmit(data: ForgotPasswordData) {
    setFormError(null);

    try {
      await forgotPasswordService(data);
      setSent(true);
    } catch (error) {
      setFormError(getErrorMessage(error, "Etwas ist schiefgelaufen. Bitte versuche es erneut."));
    }
  }

  if (sent) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-accent-blue/10 p-6 text-center">
        <MailCheck size={32} className="text-accent-blue" />
        <p className="text-sm font-medium text-text-primary">
          Falls ein Konto mit dieser E-Mail existiert, senden wir dir einen Link zum
          Zurücksetzen deines Passworts.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {formError && (
        <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Email</label>
        <Input type="email" placeholder="Email" error={!!errors.email} {...register("email")} />
        {errors.email && <p className="mt-2 text-sm text-danger">{errors.email.message}</p>}
      </div>

      <Button type="submit" fullWidth disabled={isSubmitting}>
        {isSubmitting ? "Wird gesendet..." : "Link senden"}
      </Button>
    </form>
  );
}
