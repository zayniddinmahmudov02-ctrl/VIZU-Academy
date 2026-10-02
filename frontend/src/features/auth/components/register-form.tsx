"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, Eye, EyeOff } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { useTranslation } from "@/lib/i18n/use-translation";

import { useRegister } from "../hooks/use-register";
import { getAuthErrorKey } from "../utils/get-error-message";
import { registerSchema, RegisterFormData } from "../validation/register.schema";

export default function RegisterForm() {
  const router = useRouter();
  const { t } = useTranslation();
  const registerMutation = useRegister();

  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  async function onSubmit(data: RegisterFormData) {
    setFormError(null);

    try {
      await registerMutation.mutateAsync({
        email: data.email,
        username: data.username,
        password: data.password,
      });

      setSubmitted(true);

      setTimeout(() => {
        router.push("/login");
      }, 1800);
    } catch (error) {
      setFormError(getAuthErrorKey(error, "auth.errRegisterFailed"));
    }
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-success/10 p-6 text-center">
        <CheckCircle2 size={32} className="text-success" />
        <p className="text-sm font-medium text-text-primary">
          {t("auth.registerSuccess")}
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {formError && (
        <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{t(formError)}</span>
        </div>
      )}

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.username")}</label>
        <Input placeholder={t("auth.usernamePlaceholder")} error={!!errors.username} {...register("username")} />
        {errors.username && <p className="mt-2 text-sm text-danger">{t(errors.username.message ?? "")}</p>}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.email")}</label>
        <Input type="email" placeholder={t("auth.emailPlaceholder")} error={!!errors.email} {...register("email")} />
        {errors.email && <p className="mt-2 text-sm text-danger">{t(errors.email.message ?? "")}</p>}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.password")}</label>
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            placeholder={t("auth.password")}
            error={!!errors.password}
            className="pr-11"
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
            tabIndex={-1}
            aria-label={showPassword ? t("auth.hidePassword") : t("auth.showPassword")}
          >
            {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
        {errors.password && (
          <p className="mt-2 text-sm text-danger">{t(errors.password.message ?? "")}</p>
        )}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">
          {t("auth.passwordConfirm")}
        </label>
        <div className="relative">
          <Input
            type={showConfirmPassword ? "text" : "password"}
            placeholder={t("auth.passwordRepeatPlaceholder")}
            error={!!errors.confirmPassword}
            className="pr-11"
            {...register("confirmPassword")}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
            tabIndex={-1}
            aria-label={showConfirmPassword ? t("auth.hidePassword") : t("auth.showPassword")}
          >
            {showConfirmPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
        {errors.confirmPassword && (
          <p className="mt-2 text-sm text-danger">{t(errors.confirmPassword.message ?? "")}</p>
        )}
      </div>

      <Button type="submit" fullWidth disabled={registerMutation.isPending}>
        {registerMutation.isPending ? t("auth.registering") : t("auth.register")}
      </Button>
    </form>
  );
}
