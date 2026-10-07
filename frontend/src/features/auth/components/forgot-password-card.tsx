"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import { useTranslation } from "@/lib/i18n/use-translation";

import ForgotPasswordForm, { type ForgotStep } from "./forgot-password-form";

const TITLES: Record<ForgotStep, string> = {
  email: "auth.resetTitle",
  code: "auth.resetCodeTitle",
  password: "auth.resetNewTitle",
  done: "auth.resetTitle",
};

export default function ForgotPasswordCard() {
  const { t } = useTranslation();
  const [step, setStep] = useState<ForgotStep>("email");

  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-blue)_0%,transparent_60%)] opacity-[0.05]" />

      <div className="relative">
        <div className="mb-2 flex justify-end">
          <LanguageSwitcher variant="segmented" />
        </div>
        <div className="mb-8 flex flex-col items-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-center text-2xl font-bold tracking-tight text-text-primary">{t(TITLES[step])}</h1>
          {step === "email" && (
            <p className="mt-2 text-center text-sm leading-6 text-text-secondary">{t("auth.resetIntro")}</p>
          )}
        </div>

        <ForgotPasswordForm onStepChange={setStep} />

        <Link
          href="/login"
          className="mt-6 flex items-center justify-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary"
        >
          <ArrowLeft size={15} />
          {t("auth.backToLogin")}
        </Link>
      </div>
    </div>
  );
}
