"use client";

import Link from "next/link";
import { BookText, UserRoundSearch } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

// Quick buttons (owner 2026-11-25): Mein Lehrer/in and Lug'at right in the welcome header — on the right on wide screens (no extra
// height: the hub stays one row and the Battle banner above the fold), under the greeting on phones.
const QUICK = [
  { id: "my-teacher", href: "/my-teacher", icon: UserRoundSearch, title: "hub.teacherTitle", desc: "hub.teacherDesc", gradient: "from-sky-500 to-indigo-600" },
  { id: "dictionary", href: "/woerterbuch", icon: BookText, title: "hub.dictTitle", desc: "hub.dictDesc", gradient: "from-teal-600 to-cyan-500" },
] as const;

export default function DashboardWelcome() {
  const { t } = useTranslation();

  return (
    <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" data-testid="dashboard-welcome">
      <div className="min-w-0 space-y-1">
        <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
          {t("dashboard.welcomeBack")}
        </h1>
        <p className="text-sm text-text-secondary sm:text-base">
          {t("dashboard.heroSubtitle")}
        </p>
      </div>
      <nav aria-label={t("hub.quickNav")} className="grid shrink-0 grid-cols-2 gap-2 sm:flex" data-testid="dashboard-quick-links">
        {QUICK.map(({ id, href, icon: Icon, title, desc, gradient }) => (
          <Link key={id} href={href} prefetch={false} title={t(desc)} data-testid="quick-link" data-link={id}
                className={`inline-flex min-h-11 min-w-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-br px-4 text-sm font-bold text-white shadow-[var(--shadow-card)] transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-hover)] ${gradient}`}>
            <Icon size={17} aria-hidden="true" className="shrink-0" />
            <span className="truncate">{t(title)}</span>
          </Link>
        ))}
      </nav>
    </header>
  );
}
