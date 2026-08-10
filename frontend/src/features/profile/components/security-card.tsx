"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, Eye, EyeOff, ShieldCheck } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { getErrorMessage } from "@/features/auth/utils/get-error-message";
import { removeRefreshToken, removeToken } from "@/lib/token";
import { useTranslation } from "@/lib/i18n/use-translation";

import { useChangePassword } from "../hooks/use-change-password";
import { changePasswordSchema, type ChangePasswordFormData } from "../validation/profile.schema";

export default function SecurityCard() {
  const { t } = useTranslation();
  const router = useRouter();
  const changePassword = useChangePassword();
  const [success, setSuccess] = useState(false);

  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  });

  function onSubmit(data: ChangePasswordFormData) {
    changePassword.mutate(
      { currentPassword: data.currentPassword, newPassword: data.newPassword },
      {
        onSuccess: () => {
          reset();
          setSuccess(true);
          // The backend revokes every outstanding refresh token for this
          // account on a password change (see change_password() in
          // app/services/auth/service.py) — including this session's. The
          // current access token stays valid for its remaining lifetime,
          // but silently letting it expire later would surface as a
          // confusing out-of-nowhere logout, so we end the session now
          // with a clear reason instead.
          setTimeout(() => {
            removeToken();
            removeRefreshToken();
            router.push("/login");
          }, 2500);
        },
      },
    );
  }

  return (
    <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
        <ShieldCheck size={18} className="text-accent-blue" />
        {t("profile.security")}
      </h2>
      <h3 className="mt-4 text-sm font-semibold text-text-primary">{t("profile.changePassword")}</h3>

      {success ? (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-success/10 px-4 py-3 text-sm text-success">
          <CheckCircle2 size={16} className="shrink-0" />
          {t("profile.passwordChanged")}
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          {changePassword.isError && (
            <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              {getErrorMessage(changePassword.error, t("profile.wrongCurrentPassword"))}
            </div>
          )}

          <PasswordField
            label={t("profile.currentPassword")}
            show={showCurrent}
            onToggle={() => setShowCurrent((v) => !v)}
            error={errors.currentPassword?.message}
            inputProps={register("currentPassword")}
          />

          <PasswordField
            label={t("profile.newPassword")}
            show={showNew}
            onToggle={() => setShowNew((v) => !v)}
            error={errors.newPassword?.message}
            hint={t("profile.passwordHint")}
            inputProps={register("newPassword")}
          />

          <PasswordField
            label={t("profile.confirmPassword")}
            show={showConfirm}
            onToggle={() => setShowConfirm((v) => !v)}
            error={errors.confirmPassword?.message}
            inputProps={register("confirmPassword")}
          />

          <Button type="submit" size="sm" disabled={changePassword.isPending}>
            {changePassword.isPending ? t("profile.saving") : t("profile.changePassword")}
          </Button>
        </form>
      )}
    </section>
  );
}

function PasswordField({
  label,
  show,
  onToggle,
  error,
  hint,
  inputProps,
}: {
  label: string;
  show: boolean;
  onToggle: () => void;
  error?: string;
  hint?: string;
  inputProps: ReturnType<
    ReturnType<typeof useForm<ChangePasswordFormData>>["register"]
  >;
}) {
  const { t } = useTranslation();

  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-text-secondary">{label}</label>
      <div className="relative">
        <Input
          type={show ? "text" : "password"}
          autoComplete={label === t("profile.currentPassword") ? "current-password" : "new-password"}
          error={!!error}
          className="pr-11"
          {...inputProps}
        />
        <button
          type="button"
          onClick={onToggle}
          tabIndex={-1}
          className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
          aria-label={show ? t("profile.hidePassword") : t("profile.showPassword")}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
      {!error && hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
    </div>
  );
}
