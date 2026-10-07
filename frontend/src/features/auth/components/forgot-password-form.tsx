"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle, CheckCircle2, Eye, EyeOff, MailCheck } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { useTranslation } from "@/lib/i18n/use-translation";

import { formatCountdown, useCountdown } from "../hooks/use-countdown";
import { forgotPasswordService, resetPasswordService, verifyResetCodeService } from "../services/auth.service";
import { getAuthErrorKey } from "../utils/get-error-message";
import { maskEmail, setAuthNotice } from "../utils/pending-email";
import { resetPasswordSchema, type ResetPasswordFormData } from "../validation/reset-password.schema";
import OtpInput from "./otp-input";

const RESEND_SECONDS = 60;

/** Epoch ms when "Code erneut senden" becomes available again. */
function resendDeadline(): number {
  return Date.now() + RESEND_SECONDS * 1000;
}

const emailSchema = z.object({ email: z.email("auth.errEmailInvalid") });
type EmailData = z.infer<typeof emailSchema>;

export type ForgotStep = "email" | "code" | "password" | "done";

/** Passwort vergessen: e-mail -> 6-digit code -> new password -> login.
 * The answer to step 1 is always the same generic message (no account
 * enumeration); the code lives only in component state. */
export default function ForgotPasswordForm({ onStepChange }: { onStepChange?: (step: ForgotStep) => void }) {
  const { t } = useTranslation();
  const router = useRouter();

  const [step, setStepState] = useState<ForgotStep>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resendUntil, setResendUntil] = useState<number | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const remaining = useCountdown(resendUntil);

  const emailForm = useForm<EmailData>({ resolver: zodResolver(emailSchema) });
  const passwordForm = useForm<ResetPasswordFormData>({ resolver: zodResolver(resetPasswordSchema) });

  function setStep(next: ForgotStep) {
    setStepState(next);
    onStepChange?.(next);
  }

  async function requestCode(target: string) {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      await forgotPasswordService({ email: target });
      setEmail(target);
      setCode("");
      setInfo("auth.resetGeneric");
      setResendUntil(resendDeadline());
      setStep("code");
    } catch (e) {
      setError(getAuthErrorKey(e, "auth.errGeneric"));
      if (step === "code") setResendUntil(resendDeadline());
    } finally {
      setBusy(false);
    }
  }

  async function checkCode(value = code) {
    if (!/^\d{6}$/.test(value)) {
      setError("auth.errCodeFormat");
      return;
    }
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      await verifyResetCodeService({ email, code: value });
      setStep("password");
    } catch (e) {
      setCode("");
      setError(getAuthErrorKey(e, "auth.errGeneric"));
    } finally {
      setBusy(false);
    }
  }

  async function savePassword(data: ResetPasswordFormData) {
    setBusy(true);
    setError(null);
    try {
      await resetPasswordService({ email, code, new_password: data.password });
      setCode("");
      passwordForm.reset();
      setAuthNotice("password-reset");
      setStep("done");
      setTimeout(() => router.push("/login"), 1800);
    } catch (e) {
      const key = getAuthErrorKey(e, "auth.errGeneric");
      setError(key);
      // The code became invalid meanwhile (expired / used up): back to the code step.
      if (key === "auth.errCodeExpired" || key === "auth.errCodeInvalid" || key === "auth.errTooManyAttempts") {
        setCode("");
        setStep("code");
      }
    } finally {
      setBusy(false);
    }
  }

  const errorBox = error && (
    <div role="alert" className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
      <AlertCircle size={16} className="mt-0.5 shrink-0" />
      <span>{t(error)}</span>
    </div>
  );

  if (step === "done") {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-success/10 p-6 text-center" role="status" data-testid="reset-success">
        <CheckCircle2 size={32} className="text-success" />
        <p className="text-sm font-semibold text-text-primary">{t("auth.resetSuccess")}</p>
      </div>
    );
  }

  if (step === "email") {
    return (
      <form onSubmit={emailForm.handleSubmit((d) => requestCode(d.email.trim()))} noValidate className="space-y-5">
        {errorBox}
        <div>
          <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.email")}</label>
          <Input
            type="email"
            autoComplete="email"
            placeholder={t("auth.emailPlaceholder")}
            error={!!emailForm.formState.errors.email}
            {...emailForm.register("email")}
          />
          {emailForm.formState.errors.email && (
            <p className="mt-2 text-sm text-danger">{t(emailForm.formState.errors.email.message ?? "")}</p>
          )}
        </div>
        <Button type="submit" fullWidth disabled={busy}>
          {busy ? t("auth.sending") : t("auth.sendCode")}
        </Button>
      </form>
    );
  }

  if (step === "code") {
    return (
      <form
        noValidate
        className="space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          void checkCode();
        }}
      >
        {info && (
          <div className="flex items-start gap-2 rounded-xl bg-accent-blue/10 px-4 py-3 text-sm text-accent-blue" role="status" data-testid="reset-generic">
            <MailCheck size={16} className="mt-0.5 shrink-0" />
            <span>{t(info)}</span>
          </div>
        )}
        {errorBox}
        <p className="text-center text-sm font-semibold text-text-primary">{maskEmail(email)}</p>
        <div>
          <label className="mb-3 block text-center text-sm font-medium text-text-primary">{t("auth.codeLabel")}</label>
          <OtpInput value={code} onChange={setCode} onComplete={(v) => void checkCode(v)} disabled={busy} error={!!error} />
        </div>
        <Button type="submit" fullWidth disabled={busy || code.length !== 6}>
          {busy ? t("auth.verifying") : t("auth.next")}
        </Button>
        <div className="text-center text-sm">
          {remaining > 0 ? (
            <span className="text-text-secondary" data-testid="resend-countdown">
              {t("auth.resendIn", { time: formatCountdown(remaining) })}
            </span>
          ) : (
            <button
              type="button"
              disabled={busy}
              onClick={() => void requestCode(email)}
              className="font-medium text-accent-blue hover:text-accent-blue-hover disabled:opacity-50"
            >
              {t("auth.resendCode")}
            </button>
          )}
        </div>
        <button
          type="button"
          onClick={() => {
            setCode("");
            setError(null);
            setInfo(null);
            setStep("email");
          }}
          className="block w-full text-center text-xs text-text-muted hover:text-text-secondary"
        >
          {t("auth.changeEmail")}
        </button>
      </form>
    );
  }

  const pErrors = passwordForm.formState.errors;
  return (
    <form onSubmit={passwordForm.handleSubmit(savePassword)} noValidate className="space-y-5">
      {errorBox}
      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.newPassword")}</label>
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            placeholder={t("auth.newPassword")}
            error={!!pErrors.password}
            className="pr-11"
            autoFocus
            {...passwordForm.register("password")}
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
        {pErrors.password && <p className="mt-2 text-sm text-danger">{t(pErrors.password.message ?? "")}</p>}
      </div>
      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.passwordConfirm")}</label>
        <div className="relative">
          <Input
            type={showConfirm ? "text" : "password"}
            autoComplete="new-password"
            placeholder={t("auth.passwordRepeatPlaceholder")}
            error={!!pErrors.confirmPassword}
            className="pr-11"
            {...passwordForm.register("confirmPassword")}
          />
          <button
            type="button"
            onClick={() => setShowConfirm((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
            tabIndex={-1}
            aria-label={showConfirm ? t("auth.hidePassword") : t("auth.showPassword")}
          >
            {showConfirm ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
        {pErrors.confirmPassword && <p className="mt-2 text-sm text-danger">{t(pErrors.confirmPassword.message ?? "")}</p>}
      </div>
      <Button type="submit" fullWidth disabled={busy}>
        {busy ? t("auth.saving") : t("auth.savePassword")}
      </Button>
    </form>
  );
}
