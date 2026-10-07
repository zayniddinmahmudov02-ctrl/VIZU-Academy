"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowLeft, CheckCircle2, MailCheck } from "lucide-react";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { useTranslation } from "@/lib/i18n/use-translation";

import { useCountdown, formatCountdown } from "../hooks/use-countdown";
import { resendVerificationService, verifyEmailService } from "../services/auth.service";
import { getAuthErrorKey } from "../utils/get-error-message";
import {
  clearPendingEmail,
  getPendingEmail,
  maskEmail,
  setAuthNotice,
  setPendingEmail,
  getPendingSendFailed,
} from "../utils/pending-email";
import OtpInput from "./otp-input";

const RESEND_SECONDS = 60;

/** Epoch ms when "Code erneut senden" becomes available again. */
function resendDeadline(): number {
  return Date.now() + RESEND_SECONDS * 1000;
}

/** "E-Mail-Adresse bestätigen": 6-digit code from the registration e-mail,
 * resend with a 60-second countdown, then on to the login page. The address
 * comes from this tab's sessionStorage (never the URL); without one, the
 * page asks for it first. */
export default function VerifyEmailCard() {
  const { t } = useTranslation();
  const router = useRouter();

  const [email, setEmail] = useState<string | null>(null);
  const [emailInput, setEmailInput] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [resendUntil, setResendUntil] = useState<number | null>(null);
  const [ready, setReady] = useState(false);
  const remaining = useCountdown(resendUntil);

  // Read this tab's pending address once after mount (sessionStorage is
  // browser-only). Deferred so it is not a synchronous effect update.
  useEffect(() => {
    const timer = setTimeout(() => {
      const pending = getPendingEmail();
      if (pending) {
        setEmail(pending);
        if (getPendingSendFailed()) setError("auth.emailNotSent");
        else setResendUntil(resendDeadline());
      }
      setReady(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  async function verify(value = code) {
    if (!email) return;
    if (!/^\d{6}$/.test(value)) {
      setError("auth.errCodeFormat");
      return;
    }
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      await verifyEmailService({ email, code: value });
      setCode("");
      setDone(true);
      clearPendingEmail();
      setAuthNotice("verified");
      setTimeout(() => router.push("/login"), 1800);
    } catch (e) {
      setCode("");
      setError(getAuthErrorKey(e, "auth.errGeneric"));
    } finally {
      setBusy(false);
    }
  }

  async function resend(target = email) {
    if (!target) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      await resendVerificationService(target);
      setPendingEmail(target);
      setEmail(target);
      setCode("");
      setInfo("auth.resendDone");
      setResendUntil(resendDeadline());
    } catch (e) {
      setError(getAuthErrorKey(e, "auth.errGeneric"));
      setResendUntil(resendDeadline());
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-blue)_0%,transparent_60%)] opacity-[0.05]" />
      <div className="relative">
        <div className="mb-2 flex justify-end">
          <LanguageSwitcher variant="segmented" />
        </div>
        <div className="mb-7 flex flex-col items-center text-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary">{t("auth.verifyTitle")}</h1>
          {email && !done && (
            <>
              <p className="mt-2 text-sm leading-6 text-text-secondary">{t("auth.verifySent")}</p>
              <p className="mt-1 text-sm font-semibold text-text-primary" data-testid="masked-email">
                {t("auth.verifySentTo", { email: maskEmail(email) })}
              </p>
            </>
          )}
          {ready && !email && !done && <p className="mt-2 text-sm leading-6 text-text-secondary">{t("auth.verifyEmailPrompt")}</p>}
        </div>

        {done ? (
          <div className="flex flex-col items-center gap-3 rounded-2xl bg-success/10 p-6 text-center" role="status" data-testid="verify-success">
            <CheckCircle2 size={32} className="text-success" />
            <p className="text-sm font-semibold text-text-primary">{t("auth.verifySuccess")}</p>
            <p className="text-sm text-text-secondary">{t("auth.verifySuccessLogin")}</p>
          </div>
        ) : !ready ? null : !email ? (
          <form
            noValidate
            className="space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (/^\S+@\S+\.\S+$/.test(emailInput.trim())) void resend(emailInput.trim());
              else setError("auth.errEmailInvalid");
            }}
          >
            {error && <ErrorBox>{t(error)}</ErrorBox>}
            <div>
              <label className="mb-2 block text-sm font-medium text-text-primary">{t("auth.email")}</label>
              <Input type="email" value={emailInput} onChange={(e) => setEmailInput(e.target.value)} placeholder={t("auth.emailPlaceholder")} />
            </div>
            <Button type="submit" fullWidth disabled={busy}>
              {busy ? t("auth.sending") : t("auth.sendCode")}
            </Button>
          </form>
        ) : (
          <form
            noValidate
            className="space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              void verify();
            }}
          >
            {error && <ErrorBox>{t(error)}</ErrorBox>}
            {info && (
              <div className="flex items-start gap-2 rounded-xl bg-accent-blue/10 px-4 py-3 text-sm text-accent-blue" role="status">
                <MailCheck size={16} className="mt-0.5 shrink-0" />
                <span>{t(info)}</span>
              </div>
            )}
            <div>
              <label className="mb-3 block text-center text-sm font-medium text-text-primary">{t("auth.codeLabel")}</label>
              <OtpInput value={code} onChange={setCode} onComplete={(v) => void verify(v)} disabled={busy} error={!!error} />
            </div>
            <Button type="submit" fullWidth disabled={busy || code.length !== 6}>
              {busy ? t("auth.verifying") : t("auth.verifyButton")}
            </Button>
            <div className="text-center text-sm">
              {remaining > 0 ? (
                <span className="text-text-secondary" data-testid="resend-countdown">
                  {t("auth.resendIn", { time: formatCountdown(remaining) })}
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => void resend()}
                  disabled={busy}
                  className="font-medium text-accent-blue hover:text-accent-blue-hover disabled:opacity-50"
                >
                  {t("auth.resendCode")}
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                clearPendingEmail();
                setEmail(null);
                setCode("");
                setError(null);
              }}
              className="block w-full text-center text-xs text-text-muted hover:text-text-secondary"
            >
              {t("auth.changeEmail")}
            </button>
          </form>
        )}

        <Link href="/login" className="mt-6 flex items-center justify-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary">
          <ArrowLeft size={15} />
          {t("auth.backToLogin")}
        </Link>
      </div>
    </div>
  );
}

function ErrorBox({ children }: { children: React.ReactNode }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
      <AlertCircle size={16} className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </div>
  );
}
