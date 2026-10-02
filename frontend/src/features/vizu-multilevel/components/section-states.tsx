"use client";

import { AlertCircle, Hourglass, RotateCw } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

import type { VizuMultilevelSkill } from "../types/vizu-multilevel.types";

const PREPARING_KEY: Record<VizuMultilevelSkill, string> = {
  lesen: "vizuMultilevel.preparingLesen",
  hoeren: "vizuMultilevel.preparingHoeren",
  schreiben: "vizuMultilevel.preparingSchreiben",
  sprechen: "vizuMultilevel.preparingSprechen",
};

export function SectionLoading() {
  const { t } = useTranslation();
  return <p className="py-10 text-center text-sm text-text-secondary">{t("common.loading")}</p>;
}

export function SectionError() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-center">
      <AlertCircle size={26} className="text-orange-500" />
      <p className="text-sm font-semibold text-slate-900 dark:text-white">{t("vizuMultilevel.loadError")}</p>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-transform hover:bg-blue-700 active:scale-95"
      >
        <RotateCw size={14} />
        {t("vizuMultilevel.retry")}
      </button>
    </div>
  );
}

/** Shown while a competency has no published content yet. No placeholder
 * questions are ever generated — the student simply continues. */
export function SectionPreparing({ skill }: { skill: VizuMultilevelSkill }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-center">
      <Hourglass size={30} className="text-text-muted" />
      <p className="text-base font-semibold text-text-primary">{t(PREPARING_KEY[skill])}</p>
      <p className="max-w-sm text-sm text-text-secondary">{t("vizuMultilevel.preparingBody")}</p>
    </div>
  );
}
