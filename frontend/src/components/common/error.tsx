"use client";

import { AlertTriangle } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  message: string;
}

export default function ErrorState({ message }: Props) {
  const { t } = useTranslation();

  return (
    <div className="flex items-start gap-4 rounded-card bg-surface-card p-8 shadow-[var(--shadow-md)] ring-1 ring-danger/20">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-danger/10 text-danger">
        <AlertTriangle size={20} />
      </div>
      <div>
        <h2 className="text-lg font-bold text-text-primary">{t("common.errorTitle")}</h2>
        <p className="mt-1 text-sm text-text-secondary">{t(message)}</p>
      </div>
    </div>
  );
}
