"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, Eye, EyeOff } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";

import { resetPasswordService } from "../services/auth.service";
import { getErrorMessage } from "../utils/get-error-message";
import { resetPasswordSchema, ResetPasswordFormData } from "../validation/reset-password.schema";

export default function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  async function onSubmit(data: ResetPasswordFormData) {
    setFormError(null);

    if (!token) {
      setFormError("Dieser Link ist ungültig. Bitte fordere einen neuen Link an.");
      return;
    }

    try {
      await resetPasswordService({ token, new_password: data.password });
      setSubmitted(true);
      setTimeout(() => router.push("/login"), 1800);
    } catch (error) {
      setFormError(
        getErrorMessage(
          error,
          "Dieser Link ist ungültig oder abgelaufen. Bitte fordere einen neuen Link an.",
        ),
      );
    }
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-success/10 p-6 text-center">
        <CheckCircle2 size={32} className="text-success" />
        <p className="text-sm font-medium text-text-primary">
          Passwort erfolgreich zurückgesetzt! Du wirst zur Anmeldung weitergeleitet...
        </p>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="space-y-5">
        <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>Dieser Link ist ungültig. Bitte fordere einen neuen Link an.</span>
        </div>
        <Link href="/forgot-password">
          <Button type="button" fullWidth>
            Neuen Link anfordern
          </Button>
        </Link>
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
        <label className="mb-2 block text-sm font-medium text-text-primary">Neues Passwort</label>
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            placeholder="Neues Passwort"
            error={!!errors.password}
            className="pr-11"
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
            tabIndex={-1}
            aria-label={showPassword ? "Passwort verbergen" : "Passwort anzeigen"}
          >
            {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
        {errors.password && (
          <p className="mt-2 text-sm text-danger">{errors.password.message}</p>
        )}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">
          Passwort bestätigen
        </label>
        <div className="relative">
          <Input
            type={showConfirmPassword ? "text" : "password"}
            placeholder="Passwort wiederholen"
            error={!!errors.confirmPassword}
            className="pr-11"
            {...register("confirmPassword")}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
            tabIndex={-1}
            aria-label={showConfirmPassword ? "Passwort verbergen" : "Passwort anzeigen"}
          >
            {showConfirmPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
        {errors.confirmPassword && (
          <p className="mt-2 text-sm text-danger">{errors.confirmPassword.message}</p>
        )}
      </div>

      <Button type="submit" fullWidth disabled={isSubmitting}>
        {isSubmitting ? "Wird gespeichert..." : "Passwort zurücksetzen"}
      </Button>
    </form>
  );
}
