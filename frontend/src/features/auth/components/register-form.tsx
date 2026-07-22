"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2 } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";

import { registerSchema, RegisterFormData } from "../validation/register.schema";

export default function RegisterForm() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  async function onSubmit() {
    // Registration is not yet available — this form validates and
    // presents a confirmation state without calling any backend.
    await new Promise((resolve) => setTimeout(resolve, 500));
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-success/10 p-6 text-center">
        <CheckCircle2 size={32} className="text-success" />
        <p className="text-sm font-medium text-text-primary">
          Danke für dein Interesse! Die Registrierung ist bald verfügbar.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Name</label>
        <Input placeholder="Dein Name" error={!!errors.name} {...register("name")} />
        {errors.name && <p className="mt-2 text-sm text-danger">{errors.name.message}</p>}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Email</label>
        <Input type="email" placeholder="Email" error={!!errors.email} {...register("email")} />
        {errors.email && <p className="mt-2 text-sm text-danger">{errors.email.message}</p>}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Passwort</label>
        <Input
          type="password"
          placeholder="Passwort"
          error={!!errors.password}
          {...register("password")}
        />
        {errors.password && (
          <p className="mt-2 text-sm text-danger">{errors.password.message}</p>
        )}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">
          Passwort bestätigen
        </label>
        <Input
          type="password"
          placeholder="Passwort wiederholen"
          error={!!errors.confirmPassword}
          {...register("confirmPassword")}
        />
        {errors.confirmPassword && (
          <p className="mt-2 text-sm text-danger">{errors.confirmPassword.message}</p>
        )}
      </div>

      <Button type="submit" fullWidth disabled={isSubmitting}>
        {isSubmitting ? "Wird erstellt..." : "Konto erstellen"}
      </Button>
    </form>
  );
}
