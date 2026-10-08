"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, Eye, EyeOff } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { useTranslation } from "@/lib/i18n/use-translation";

import { saveRefreshToken, saveToken } from "@/lib/token";

import { useLogin } from "../hooks/use-login";
import { useRegister } from "../hooks/use-register";
import { getAuthErrorKey } from "../utils/get-error-message";
import { registerSchema, RegisterFormData } from "../validation/register.schema";

export default function RegisterForm() {
  const router = useRouter();
  const { t } = useTranslation();
  const registerMutation = useRegister();
  const loginMutation = useLogin();

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

    const identifier = data.identifier.trim();
    try {
      await registerMutation.mutateAsync({
        full_name: data.fullName.trim(),
        identifier,
        password: data.password,
        password_confirm: data.confirmPassword,
      });
    } catch (error) {
      setFormError(getAuthErrorKey(error, "auth.errRegisterFailed"));
      return;
    }

    // The account is active immediately (no confirmation code): log straight in.
    try {
      const tokens = await loginMutation.mutateAsync({ identifier, password: data.password });
      saveToken(tokens.access_token, true);
      saveRefreshToken(tokens.refresh_token, true);
      router.push("/dashboard");
    } catch {
      router.push("/login");
    }
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
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.fullName")}</label>
        <Input autoComplete="name" placeholder={t("auth.fullNamePlaceholder")} error={!!errors.fullName} {...register("fullName")} />
        {errors.fullName && <p className="mt-2 text-sm text-danger">{t(errors.fullName.message ?? "")}</p>}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.identifier")}</label>
        <Input
          type="text"
          inputMode="email"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          placeholder={t("auth.identifierPlaceholder")}
          error={!!errors.identifier}
          {...register("identifier")}
        />
        {errors.identifier ? (
          <p className="mt-2 text-sm text-danger">{t(errors.identifier.message ?? "")}</p>
        ) : (
          <p className="mt-2 text-xs text-text-muted">{t("auth.identifierHint")}</p>
        )}
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

      <Button type="submit" fullWidth disabled={registerMutation.isPending || loginMutation.isPending}>
        {registerMutation.isPending || loginMutation.isPending ? t("auth.registering") : t("auth.register")}
      </Button>
    </form>
  );
}
