"use client";

import Link from "next/link";
import { ArrowRight, LogIn, UserPlus } from "lucide-react";

import Logo from "@/components/common/logo";
import LanguageSwitcher from "@/components/dashboard/languages/language-switcher";
import { useTranslation } from "@/lib/i18n/use-translation";
import SessionRedirect from "./session-redirect";

const CHOICES = [
  { href: "/login", icon: LogIn, titleKey: "auth.welcomeHaveAccount", hintKey: "auth.welcomeHaveAccountHint", ctaKey: "auth.welcomeHaveAccountCta", primary: true },
  { href: "/register", icon: UserPlus, titleKey: "auth.welcomeNew", hintKey: "auth.welcomeNewHint", ctaKey: "auth.welcomeNewCta", primary: false },
];

export default function WelcomeCard() {
  const { t } = useTranslation();

  return (
    <div className="mx-auto w-full max-w-xl rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <SessionRedirect />

      <div className="mb-2 flex justify-end">
        <LanguageSwitcher variant="segmented" />
      </div>

      <div className="flex flex-col items-center text-center">
        <Logo size={56} showText={false} />
        <h1 className="mt-5 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          {t("auth.welcomeTitle")}
        </h1>
        <p className="mt-2 text-sm leading-6 text-text-secondary sm:text-base">
          {t("auth.welcomeSubtitle")}
        </p>
      </div>

      <div className="mt-8 grid gap-3">
        {/* Text colours sit on the children: the unlayered `a { color: inherit }`
            in globals.css beats a colour utility on the <Link> itself. */}
        {CHOICES.map(({ href, icon: Icon, titleKey, hintKey, ctaKey, primary }) => {
          const strong = primary ? "text-white" : "text-text-primary";
          return (
            <Link
              key={href}
              href={href}
              className={`group flex items-center gap-4 rounded-2xl p-5 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-blue ${
                primary
                  ? "bg-brand-900 hover:opacity-95"
                  : "bg-surface-card ring-2 ring-brand-900/80 hover:bg-surface-hover"
              }`}
            >
              <span
                className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${strong} ${
                  primary ? "bg-white/15" : "bg-brand-900/10"
                }`}
              >
                <Icon size={22} aria-hidden="true" />
              </span>
              <span className="min-w-0 flex-1">
                <span className={`block text-base font-bold ${strong}`}>{t(titleKey)}</span>
                <span className={`block text-sm ${primary ? "text-white/80" : "text-text-secondary"}`}>
                  {t(hintKey)}: {t(ctaKey)}
                </span>
              </span>
              <ArrowRight size={18} aria-hidden="true" className={`shrink-0 transition group-hover:translate-x-0.5 ${strong}`} />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
