"use client";

import Link from "next/link";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import { useTranslation } from "@/lib/i18n/use-translation";
import RegisterForm from "./register-form";

export default function RegisterCard() {
  const { t } = useTranslation();

  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-purple)_0%,transparent_60%)] opacity-[0.05]" />

      <div className="relative">
        <div className="mb-2 flex justify-end">
          <LanguageSwitcher variant="segmented" />
        </div>
        <div className="mb-8 flex flex-col items-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary">
            {t("auth.registerTitle")}
          </h1>
          <p className="mt-2 text-center text-sm leading-6 text-text-secondary">
            {t("auth.registerSubtitle")}
          </p>
        </div>

        <RegisterForm />

        <p className="mt-6 text-center text-sm text-text-secondary">
          {t("auth.haveAccount")}{" "}
          <Link href="/login" className="font-medium text-accent-blue hover:text-accent-blue-hover">
            {t("auth.toLogin")}
          </Link>
        </p>
      </div>
    </div>
  );
}
