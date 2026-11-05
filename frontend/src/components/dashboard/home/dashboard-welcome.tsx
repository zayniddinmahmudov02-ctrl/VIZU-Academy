"use client";

import { useTranslation } from "@/lib/i18n/use-translation";

export default function DashboardWelcome() {
  const { t } = useTranslation();

  return (
    <header className="space-y-1" data-testid="dashboard-welcome">
      <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
        {t("dashboard.welcomeBack")}
      </h1>
      <p className="text-sm text-text-secondary sm:text-base">
        {t("dashboard.heroSubtitle")}
      </p>
    </header>
  );
}
