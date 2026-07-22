"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { MailCheck } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";

const forgotPasswordSchema = z.object({
  email: z.email("Please enter a valid email."),
});

type ForgotPasswordData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordForm() {
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  async function onSubmit() {
    // No backend endpoint exists yet — show the standard, security-conscious
    // confirmation message without sending any request.
    await new Promise((resolve) => setTimeout(resolve, 500));
    setSent(true);
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
