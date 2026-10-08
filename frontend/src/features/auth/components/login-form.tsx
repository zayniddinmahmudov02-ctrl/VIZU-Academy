"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, Eye, EyeOff, ShieldCheck } from "lucide-react";

import Button from "@/components/ui/button";
import Checkbox from "@/components/ui/checkbox";
import Input from "@/components/ui/input";
import { useTranslation } from "@/lib/i18n/use-translation";
import { decodeJwtPayload } from "@/lib/jwt";
import { saveRefreshToken, saveToken } from "@/lib/token";

import { useLogin } from "../hooks/use-login";
import { verifyAdminPasswordService } from "../services/auth.service";
import type { JwtPayload } from "../types/auth.types";
import { getAuthErrorKey } from "../utils/get-error-message";

import {
  loginSchema,
  LoginFormData,
} from "../validation/login.schema";

export default function LoginForm() {
  const router = useRouter();
  const { t } = useTranslation();

  const loginMutation = useLogin();

  const [step, setStep] = useState<"credentials" | "admin-verify">("credentials");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  const [adminPassword, setAdminPassword] = useState("");
  const [showAdminPassword, setShowAdminPassword] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [adminVerifying, setAdminVerifying] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginFormData) {
    setFormError(null);

    try {
      const response = await loginMutation.mutateAsync(data);

      saveToken(response.access_token, rememberMe);
      saveRefreshToken(response.refresh_token, rememberMe);

      const payload = decodeJwtPayload<JwtPayload>(response.access_token);

      if (payload?.role === "SUPER_ADMIN") {
        setStep("admin-verify");
        return;
      }

      router.push("/dashboard");
    } catch (error) {
      setFormError(getAuthErrorKey(error, "auth.errInvalidCredentials"));
    }
  }

  async function onVerifyAdminPassword() {
    setAdminError(null);
    setAdminVerifying(true);

    try {
      await verifyAdminPasswordService({ password: adminPassword });
      router.push("/admin");
    } catch (error) {
      setAdminError(getAuthErrorKey(error, "auth.errAdminPassword"));
    } finally {
      setAdminVerifying(false);
    }
  }

  if (step === "admin-verify") {
    return (
      <div className="space-y-5">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-blue/10">
            <ShieldCheck size={26} className="text-accent-blue" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-text-primary">
              {t("auth.adminVerifyTitle")}
            </h2>
            <p className="mt-1 text-sm text-text-secondary">
              {t("auth.adminVerifyText")}
            </p>
          </div>
        </div>

        {adminError && (
          <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{t(adminError)}</span>
          </div>
        )}

        <div>
          <label className="mb-2 block text-sm font-medium text-text-primary">
            {t("auth.adminPassword")}
          </label>
          <div className="relative">
            <Input
              type={showAdminPassword ? "text" : "password"}
              placeholder={t("auth.adminPassword")}
              value={adminPassword}
              error={!!adminError}
              onChange={(e) => setAdminPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  onVerifyAdminPassword();
                }
              }}
              className="pr-11"
              autoFocus
            />
            <button
              type="button"
              onClick={() => setShowAdminPassword((v) => !v)}
              className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
              tabIndex={-1}
              aria-label={showAdminPassword ? t("auth.hidePassword") : t("auth.showPassword")}
            >
              {showAdminPassword ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </div>

        <Button
          type="button"
          fullWidth
          disabled={adminVerifying || adminPassword.length === 0}
          onClick={onVerifyAdminPassword}
        >
          {adminVerifying ? t("auth.adminVerifying") : t("auth.adminConfirm")}
        </Button>

        <button
          type="button"
          onClick={() => {
            setStep("credentials");
            setAdminPassword("");
            setAdminError(null);
          }}
          className="w-full text-center text-sm font-medium text-text-secondary hover:text-text-primary"
        >
          {t("auth.backToLogin")}
        </button>
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

        {errors.identifier && (
          <p className="mt-2 text-sm text-danger">{t(errors.identifier.message ?? "")}</p>
        )}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.password")}</label>

        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            placeholder={t("auth.password")}
            autoComplete="current-password"
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

      <div className="flex items-center justify-between">
        <label className="flex cursor-pointer items-center gap-2.5 select-none">
          <Checkbox checked={rememberMe} onCheckedChange={setRememberMe} aria-label={t("auth.rememberMe")} />
          <span className="text-sm text-text-secondary">{t("auth.rememberMe")}</span>
        </label>

        <Link href="/forgot-password" className="text-sm font-medium text-accent-blue hover:text-accent-blue-hover">
          {t("auth.forgotPassword")}
        </Link>
      </div>

      <Button type="submit" fullWidth disabled={loginMutation.isPending}>
        {loginMutation.isPending ? t("auth.loggingIn") : t("auth.login")}
      </Button>

      <p className="text-center text-sm text-text-secondary">
        {t("auth.noAccount")}{" "}
        <Link href="/register" className="font-medium text-accent-blue hover:text-accent-blue-hover">
          {t("auth.toRegister")}
        </Link>
      </p>
    </form>
  );
}
