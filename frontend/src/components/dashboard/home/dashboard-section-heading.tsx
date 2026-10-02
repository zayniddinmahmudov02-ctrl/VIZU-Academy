"use client";

import { useTranslation } from "@/lib/i18n/use-translation";

/** Section title in the dashboard's existing heading style (same as "Schnellzugriff"). */
export default function DashboardSectionHeading({ titleKey }: { titleKey: string }) {
  const { t } = useTranslation();
  return <h2 className="mb-5 text-base font-bold text-text-primary">{t(titleKey)}</h2>;
}
