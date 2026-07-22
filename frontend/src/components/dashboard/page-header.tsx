"use client";

import type { LucideIcon } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  icon: LucideIcon;
  titleKey: string;
  subtitleKey?: string;
  subtitleVars?: Record<string, string | number>;
  gradient: string;
}

export default function PageHeader({
  icon: Icon,
  titleKey,
  subtitleKey,
  subtitleVars,
  gradient,
}: Props) {
  const { t } = useTranslation();

  return (
    <header className="mx-auto mb-9 mt-10 flex w-full max-w-[800px] flex-col items-center text-center">
      <div
        className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${gradient} text-white shadow-md`}
      >
        <Icon size={22} />
      </div>

      <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        {t(titleKey)}
      </h1>

      {subtitleKey && (
        <p className="mt-2 text-text-secondary">{t(subtitleKey, subtitleVars)}</p>
      )}

      <div className="mt-8 h-px w-full bg-surface-border" />
    </header>
  );
}
