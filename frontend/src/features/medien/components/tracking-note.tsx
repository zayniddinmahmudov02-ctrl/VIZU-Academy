"use client";

import { Info } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

/** Folded transparency note at the bottom of Medien: what the server measures and who may see it (Teacher Kontroll).
 * No numbers: students do not see their own media statistics (owner, 2026-11-24). */
export function MedienTrackingNote() {
  const { t } = useTranslation();
  return (
    <details className="rounded-2xl bg-accent-blue/5 px-4 py-3 text-sm ring-1 ring-accent-blue/15" data-testid="medien-tracking-note">
      <summary className="flex cursor-pointer select-none items-center gap-2 font-medium text-text-primary">
        <Info size={15} className="text-accent-blue" aria-hidden />{t("mstats.privacyTitle")}
      </summary>
      <p className="mt-2 text-text-secondary">{t("mstats.privacyText")}</p>
    </details>
  );
}
