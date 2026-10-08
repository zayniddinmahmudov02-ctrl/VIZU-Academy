"use client";

import Link from "next/link";
import { ArrowLeft, Send } from "lucide-react";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import { useTranslation } from "@/lib/i18n/use-translation";

export const SUPPORT_TELEGRAM_USERNAME = "Mahmudow_Z";
export const SUPPORT_TELEGRAM_URL = `https://t.me/${SUPPORT_TELEGRAM_USERNAME}`;

/** "Parolni unutdingizmi?" — there is no automatic reset (no e-mail, code
 * or token is ever sent): the student contacts support on Telegram, where
 * the account is checked and the password is reset manually. */
export default function ForgotPasswordCard() {
  const { t } = useTranslation();
  // The sentence is translated as a whole; {telegram} marks where the link goes.
  const [before, after = ""] = t("auth.forgotTelegram").split("{telegram}");

  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-blue)_0%,transparent_60%)] opacity-[0.05]" />

      <div className="relative">
        <div className="mb-2 flex justify-end">
          <LanguageSwitcher variant="segmented" />
        </div>
        <div className="mb-7 flex flex-col items-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-center text-2xl font-bold tracking-tight text-text-primary">{t("auth.forgotPassword")}</h1>
        </div>

        <div className="rounded-2xl bg-accent-blue/5 p-6 text-center ring-1 ring-accent-blue/15" data-testid="forgot-telegram">
          <p className="text-[15px] leading-7 text-text-primary">
            {before}
            <a
              href={SUPPORT_TELEGRAM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-[#229ED9] underline decoration-[#229ED9]/40 underline-offset-4 hover:decoration-[#229ED9]"
            >
              @{SUPPORT_TELEGRAM_USERNAME}
            </a>
            {after}
          </p>
          <a
            href={SUPPORT_TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-[#229ED9] px-5 py-2.5 text-sm font-bold text-white shadow-md transition-colors hover:bg-[#1c8cc0] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-sky-300"
          >
            <Send size={15} />
            {t("auth.openTelegram")}
          </a>
        </div>

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
